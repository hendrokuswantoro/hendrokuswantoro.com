"""Aturan masuk, perpanjang, dan keluar.

Empat hal yang dikerjakan di sini dan tidak boleh pindah ke router:

1. Jawaban untuk email yang tidak ada dan sandi yang salah dibuat **sama
   persis**, termasuk lamanya. Jawaban yang berbeda memberi tahu penebak
   bahwa email itu benar ada, dan itu separuh pekerjaannya.
2. Refresh token diputar tiap dipakai. Bab 15.10.
3. Token lama yang dipakai ulang bukan sekadar ditolak: seluruh sesi
   penggunanya dicabut, sebab token yang sudah diputar lalu muncul lagi
   berarti salinannya ada di tangan orang lain.
4. Hash sandi diperbarui diam diam kalau parameter Argon2 sudah naik.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from backend.core import keamanan
from backend.core.konfigurasi import pengaturan
from backend.repositori import pengguna as repo


class Ditolak(Exception):
    """Kredensial salah, atau terlalu banyak percobaan."""

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


async def _terbitkan(pengguna: dict) -> Masuk:
    atur = pengaturan()
    akses, umur = keamanan.buat_access_token(str(pengguna["id"]), pengguna["peran"])
    refresh = keamanan.refresh_token_baru()
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=atur.refresh_umur_hari)
    await repo.buat_sesi(pengguna["id"], keamanan.ringkas(refresh), kadaluarsa)
    return Masuk(
        akses=akses, umur_detik=umur, refresh=refresh, refresh_kadaluarsa=kadaluarsa,
        nama=pengguna.get("nama", ""), peran=pengguna["peran"],
    )


async def masuk(email: str, sandi: str, alamat_hash: str) -> Masuk:
    atur = pengaturan()

    if await repo.jumlah_gagal(email, atur.masuk_jendela_menit) >= atur.masuk_gagal_maks:
        raise Ditolak("terlalu banyak percobaan masuk", terkunci=True)

    pengguna = await repo.cari_email(email)

    # Hash palsu dihitung juga saat penggunanya tidak ada, supaya lama
    # jawabannya sama. Tanpa ini, selisih waktu saja sudah membocorkan
    # email mana yang terdaftar.
    hash_tersimpan = (pengguna or {}).get("sandi_hash") or keamanan.HASH_UMPAN
    cocok = keamanan.sandi_cocok(sandi, hash_tersimpan)

    if not pengguna or not pengguna.get("sandi_hash") or not cocok:
        await repo.catat_gagal(email, alamat_hash)
        raise Ditolak("email atau sandi salah")

    if keamanan.perlu_dihash_ulang(pengguna["sandi_hash"]):
        await repo.simpan_hash(pengguna["id"], keamanan.hash_sandi(sandi))

    await repo.bersihkan_gagal(email)
    return await _terbitkan(pengguna)


async def perpanjang(refresh: str) -> Masuk:
    ringkas = keamanan.ringkas(refresh)
    sesi = await repo.sesi_hidup(ringkas)

    if sesi is None:
        raise Ditolak("sesi tidak berlaku")

    # putar: yang lama langsung mati sebelum yang baru terbit
    await repo.cabut(ringkas)

    pengguna = await repo.cari_id(sesi["pengguna_id"])
    if pengguna is None:
        raise Ditolak("sesi tidak berlaku")
    return await _terbitkan(pengguna)


async def keluar(refresh: str) -> None:
    await repo.cabut(keamanan.ringkas(refresh))


async def keluar_semua(pengguna_id: str) -> int:
    return await repo.cabut_semua(pengguna_id)
