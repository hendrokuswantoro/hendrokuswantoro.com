from __future__ import annotations

from backend.core import surat
from backend.core.catat import pasang
from backend.repositori import keamanan as repo


async def _mau(pengguna_id: str, kolom: str) -> bool:
    setelan = await repo.setelan(pengguna_id)
    return setelan is None or bool(setelan[kolom])


async def perangkat_baru(pengguna_id: str, alamat: str | None, peramban: str | None) -> bool:
    return not await repo.pernah_masuk_dari(pengguna_id, alamat, peramban)


async def kabari_masuk(
    pengguna: dict, cara: str, alamat: str | None, peramban: str | None
) -> None:
    if not await _mau(str(pengguna["id"]), "kabar_masuk"):
        return
    if not await perangkat_baru(str(pengguna["id"]), alamat, peramban):
        return

    alamat_surat = pengguna.get("email")
    if not alamat_surat:
        return

    try:
        surat.kirim(
            alamat_surat,
            "Ada yang masuk ke akun hendrokuswantoro.com",
            "Ada yang baru saja masuk ke akun Anda dari perangkat yang belum "
            f"pernah terlihat sebelumnya.\n\nCara masuknya: {cara}.\n\n"
            "Kalau itu Anda, tidak ada yang perlu dikerjakan.\n\n"
            "Kalau bukan Anda: buka halaman keamanan, tekan Keluarkan "
            "perangkat lain, lalu ganti sandi Anda.",
        )
    except Exception as galat:  # pragma: no cover
        pasang().warning(
            "kabar masuk gagal dikirim",
            extra={"tambahan": {"jenis": type(galat).__name__}},
        )


async def kabari_tebakan(pengguna: dict, jumlah: int, menit: int) -> None:
    alamat_surat = pengguna.get("email")
    if not alamat_surat or not await _mau(str(pengguna["id"]), "kabar_masuk"):
        return

    try:
        surat.kirim(
            alamat_surat,
            "Ada yang berulang kali salah memasukkan sandi Anda",
            f"Sandi akun Anda salah dimasukkan {jumlah} kali dalam {menit} menit, "
            "jadi percobaan dari tempat itu dikunci sementara.\n\n"
            "Kalau itu Anda, tunggu sebentar lalu coba lagi.\n\n"
            "Kalau bukan Anda, seseorang sedang menebak sandi Anda. Sandinya belum "
            "tertebak. Pastikan authenticator atau sidik jari sudah terpasang.",
        )
    except Exception as galat:  # pragma: no cover
        pasang().warning(
            "kabar tebakan sandi gagal dikirim",
            extra={"tambahan": {"jenis": type(galat).__name__}},
        )


async def kabari_perubahan_keamanan(pengguna: dict, apa: str, paksa: bool = False) -> None:
    alamat_surat = pengguna.get("email")
    if not alamat_surat:
        return
    if not paksa and not await _mau(str(pengguna["id"]), "kabar_perubahan"):
        return

    try:
        surat.kirim(
            alamat_surat,
            "Pengaturan keamanan akun Anda berubah",
            f"Perubahan yang baru saja terjadi: {apa}.\n\n"
            "Kalau itu Anda, tidak ada yang perlu dikerjakan.\n\n"
            "Kalau bukan Anda, akun Anda kemungkinan sudah diambil orang. "
            "Buka halaman keamanan, keluarkan semua perangkat, lalu ganti "
            "sandi Anda.",
        )
    except Exception as galat:  # pragma: no cover
        pasang().warning(
            "kabar perubahan keamanan gagal dikirim",
            extra={"tambahan": {"jenis": type(galat).__name__}},
        )
