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


async def terbitkan(pengguna: dict) -> Masuk:
    """Menerbitkan sesi. Dipakai jalur sandi dan jalur passkey.

    Satu tempat dengan sengaja: kalau umur token atau cara refresh
    berputar berubah, tidak mungkin salah satu jalur ikut berubah dan
    satunya tertinggal."""
    atur = pengaturan()
    akses, umur = keamanan.buat_access_token(str(pengguna["id"]), pengguna["peran"])
    refresh = keamanan.refresh_token_baru()
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=atur.refresh_umur_hari)
    await repo.buat_sesi(pengguna["id"], keamanan.ringkas(refresh), kadaluarsa)
    return Masuk(
        akses=akses, umur_detik=umur, refresh=refresh, refresh_kadaluarsa=kadaluarsa,
        nama=pengguna.get("nama", ""), peran=pengguna["peran"],
    )


async def periksa_sandi(email: str, sandi: str, alamat_hash: str) -> dict:
    """Memeriksa faktor pertama saja, lalu mengembalikan penggunanya.

    Dipisah dari `masuk` pada 13 September 2026 supaya router bisa menyisipkan
    faktor kedua di antaranya. Yang TIDAK berubah: seluruh perilaku
    penolakannya, termasuk hash umpan yang tetap dihitung saat penggunanya
    tidak ada, supaya lama jawabannya sama.
    """
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
    return pengguna


async def masuk(email: str, sandi: str, alamat_hash: str) -> Masuk:
    """Sandi benar lalu langsung terbit sesi, tanpa faktor kedua.

    Tetap ada karena dipakai jalur yang memang tidak punya faktor kedua, dan
    karena uji yang sudah ada memanggilnya. Jalur masuk lewat HTTP TIDAK
    memakainya lagi: router memanggil `periksa_sandi` lalu memutuskan sendiri
    apakah masih ada langkah berikutnya.
    """
    return await terbitkan(await periksa_sandi(email, sandi, alamat_hash))


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
    return await terbitkan(pengguna)


async def keluar(refresh: str) -> None:
    await repo.cabut(keamanan.ringkas(refresh))


async def keluar_semua(pengguna_id: str) -> int:
    return await repo.cabut_semua(pengguna_id)


async def sesi_saya(pengguna_id: str, refresh: str | None) -> list[dict]:
    """Sesi yang masih hidup, dengan penanda mana yang sedang dipakai.

    Sidik tokennya TIDAK ikut keluar dari sini. Ia dipakai sekali untuk
    membandingkan lalu dibuang, sebab sidik yang sampai ke peramban adalah
    sidik yang bisa dibaca siapa pun yang membuka halamannya.
    """
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
    """Mengeluarkan perangkat lain dan menyisakan yang sedang dipakai.

    Tanpa cookie refresh yang sah, tidak ada yang bisa disisakan, jadi yang
    benar adalah mengeluarkan semuanya. Menyisakan sesi yang tidak bisa
    dibuktikan miliknya berarti menyisakan justru sesi yang dicurigai.
    """
    if not refresh:
        return await repo.cabut_semua(pengguna_id)
    return await repo.cabut_lain(pengguna_id, keamanan.ringkas(refresh))
