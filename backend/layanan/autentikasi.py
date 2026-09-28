from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from backend.core import cabut as daftar_cabut
from backend.core import keamanan
from backend.core.konfigurasi import pengaturan
from backend.layanan import kabar
from backend.repositori import keamanan as repo_keamanan
from backend.repositori import pengguna as repo

TENGGANG_PUTAR_DETIK = 30


class Ditolak(Exception):
    def __init__(self, pesan: str, terkunci: bool = False) -> None:
        super().__init__(pesan)
        self.terkunci = terkunci


@dataclass(frozen=True)
class Masuk:
    akses: str
    umur_detik: int
    refresh: str
    refresh_kadaluarsa: dt.datetime
    nama: str
    peran: str
    faktor_kedua: bool = False


async def terbitkan(
    pengguna: dict, faktor_kedua: bool = False, awal: dt.datetime | None = None
) -> Masuk:
    atur = pengaturan()
    refresh = keamanan.refresh_token_baru()
    sekarang = dt.datetime.now(dt.timezone.utc)
    kadaluarsa = sekarang + dt.timedelta(days=atur.refresh_umur_hari)
    if awal is not None:
        awal = awal.astimezone(dt.timezone.utc)
        kadaluarsa = min(kadaluarsa, awal + dt.timedelta(days=atur.sesi_maks_hari))
    sesi_id = await repo.buat_sesi(
        pengguna["id"], keamanan.ringkas(refresh), kadaluarsa, faktor_kedua, awal
    )
    akses, umur = keamanan.buat_access_token(
        str(pengguna["id"]), pengguna["peran"], str(sesi_id), faktor_kedua
    )
    return Masuk(
        akses=akses, umur_detik=umur, refresh=refresh, refresh_kadaluarsa=kadaluarsa,
        nama=pengguna.get("nama", ""), peran=pengguna["peran"],
        faktor_kedua=faktor_kedua,
    )


async def periksa_sandi(email: str, sandi: str, alamat_hash: str) -> dict:
    atur = pengaturan()

    jendela = atur.masuk_jendela_menit
    if (
        await repo.jumlah_gagal(email, jendela, alamat_hash) >= atur.masuk_gagal_maks
        or await repo.jumlah_gagal(email, jendela) >= atur.masuk_gagal_maks * 20
    ):
        raise Ditolak("terlalu banyak percobaan masuk", terkunci=True)

    pengguna = await repo.cari_email(email)

    hash_tersimpan = (pengguna or {}).get("sandi_hash") or keamanan.HASH_UMPAN
    cocok = keamanan.sandi_cocok(sandi, hash_tersimpan)

    if not pengguna or not pengguna.get("sandi_hash") or not cocok:
        await repo.catat_gagal(email, alamat_hash)
        if pengguna and await repo.jumlah_gagal(email, jendela, alamat_hash) == atur.masuk_gagal_maks:
            await kabar.kabari_tebakan(pengguna, atur.masuk_gagal_maks, jendela)
        raise Ditolak("email atau sandi salah")

    if keamanan.perlu_dihash_ulang(pengguna["sandi_hash"]):
        await repo.simpan_hash(pengguna["id"], keamanan.hash_sandi(sandi))

    await repo.bersihkan_gagal(email)
    return pengguna


async def perpanjang(refresh: str) -> Masuk:
    ringkas = keamanan.ringkas(refresh)
    sesi = await repo.sesi_hidup(ringkas)

    if sesi is None:
        await _tangkap_pemakaian_ulang(ringkas)
        raise Ditolak("sesi tidak berlaku")

    sekarang = dt.datetime.now(dt.timezone.utc)
    if sekarang - sesi["awal"] > dt.timedelta(days=pengaturan().sesi_maks_hari):
        await daftar_cabut.catat(await repo.cabut(ringkas, "lewat"))
        raise Ditolak("sesi sudah terlalu lama, masuk lagi")

    lama = await repo.cabut(ringkas, "putar")
    await daftar_cabut.catat(lama)

    pengguna = await repo.cari_id(sesi["pengguna_id"])
    if pengguna is None:
        raise Ditolak("sesi tidak berlaku")

    return await terbitkan(pengguna, bool(sesi.get("faktor_kedua")), sesi["awal"])


async def _tangkap_pemakaian_ulang(ringkas: str) -> None:
    bekas = await repo.sesi_bekas(ringkas)
    if not bekas or bekas["dicabut_karena"] != "putar":
        return
    umur = dt.datetime.now(dt.timezone.utc) - bekas["dicabut_pada"]
    if umur.total_seconds() < TENGGANG_PUTAR_DETIK:
        return

    pengguna_id = str(bekas["pengguna_id"])
    dicabut = await repo.cabut_semua(pengguna_id, "curi")
    await daftar_cabut.catat(dicabut)
    await repo_keamanan.catat(
        pengguna_id, "refresh_dipakai_ulang", False, f"{len(dicabut)} sesi dicabut", None
    )
    pengguna = await repo.cari_id(pengguna_id)
    if pengguna:
        await kabar.kabari_perubahan_keamanan(
            pengguna,
            "token sesi lama dipakai lagi, tanda salinannya dicuri. "
            "Seluruh perangkat sudah dikeluarkan",
            paksa=True,
        )


async def keluar(refresh: str) -> None:
    await daftar_cabut.catat(await repo.cabut(keamanan.ringkas(refresh), "keluar"))


async def keluar_semua(pengguna_id: str) -> int:
    dicabut = await repo.cabut_semua(pengguna_id)
    await daftar_cabut.catat(dicabut)
    return len(dicabut)


async def sesi_saya(pengguna_id: str, refresh: str | None) -> list[dict]:
    sekarang = keamanan.ringkas(refresh) if refresh else None
    hasil = []
    for baris in await repo.daftar_sesi(pengguna_id):
        hasil.append(
            {
                "id": str(baris["id"]),
                "dibuat_pada": baris["dibuat_pada"],
                "kadaluarsa": baris["kadaluarsa"],
                "perangkat_ini": baris["token_hash"] == sekarang,
            }
        )
    return hasil


async def keluar_dari_yang_lain(pengguna_id: str, refresh: str | None) -> int:
    if not refresh:
        return await keluar_semua(pengguna_id)

    dicabut = await repo.cabut_lain(pengguna_id, keamanan.ringkas(refresh))
    await daftar_cabut.catat(dicabut)
    return len(dicabut)
