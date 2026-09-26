from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from backend.core import cabut as daftar_cabut
from backend.core import keamanan
from backend.core.konfigurasi import pengaturan
from backend.repositori import pengguna as repo


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


async def terbitkan(pengguna: dict, faktor_kedua: bool = False) -> Masuk:
    atur = pengaturan()
    refresh = keamanan.refresh_token_baru()
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=atur.refresh_umur_hari)
    sesi_id = await repo.buat_sesi(
        pengguna["id"], keamanan.ringkas(refresh), kadaluarsa, faktor_kedua
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
        raise Ditolak("email atau sandi salah")

    if keamanan.perlu_dihash_ulang(pengguna["sandi_hash"]):
        await repo.simpan_hash(pengguna["id"], keamanan.hash_sandi(sandi))

    await repo.bersihkan_gagal(email)
    return pengguna


async def perpanjang(refresh: str) -> Masuk:
    ringkas = keamanan.ringkas(refresh)
    sesi = await repo.sesi_hidup(ringkas)

    if sesi is None:
        raise Ditolak("sesi tidak berlaku")

    lama = await repo.cabut(ringkas)
    await daftar_cabut.catat(lama)

    pengguna = await repo.cari_id(sesi["pengguna_id"])
    if pengguna is None:
        raise Ditolak("sesi tidak berlaku")

    return await terbitkan(pengguna, bool(sesi.get("faktor_kedua")))


async def keluar(refresh: str) -> None:
    await daftar_cabut.catat(await repo.cabut(keamanan.ringkas(refresh)))


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
