"""Mengabari pemilik akun ketika ada yang penting terjadi pada akunnya.

Jejak keamanan sudah lengkap sejak Fase 5, dan ia punya satu kelemahan yang
tidak bisa diperbaiki dengan menambah barisnya: **ia hanya terbaca kalau ada
yang membukanya.** Orang yang akunnya diambil orang lain tidak sedang membuka
halaman jejak; ia sedang mengerjakan hal lain. Surat datang sendiri.

Yang dikabarkan dipilih dengan dua aturan:

1. **Hanya yang perlu ditindaklanjuti.** Masuk dari perangkat yang belum
   pernah terlihat, dan tiap perubahan pada jalan masuk itu sendiri. Surat
   yang datang untuk hal yang biasa saja akan berhenti dibaca, dan sesudah itu
   ia tidak menjaga apa apa.
2. **Tidak pernah membocorkan lebih banyak daripada yang sudah diketahui
   penerimanya.** Isinya tidak memuat alamat IP, tidak memuat token, dan
   tidak memuat kode apa pun. Ia menyebut apa yang terjadi dan kapan, lalu
   menyuruh membuka halaman keamanan kalau itu bukan Anda. Surat bisa
   nyasar, dan surat yang nyasar tidak boleh jadi hadiah.

Kalau SMTP belum dikonfigurasi, `surat.kirim` menulis berkas `.eml` ke
`cadangan/surat/` dan menjawab `terkirim=False`. Ia tidak pernah berpura pura
suratnya berangkat, dan berkas ini tidak menambahkan kepura puraan itu.

**Kegagalan mengirim tidak pernah menggagalkan yang memicunya.** Masuk yang
ditolak karena servernya sedang tidak bisa berkirim surat adalah kerugian yang
lebih besar daripada kabar yang terlewat.
"""

from __future__ import annotations

from backend.core import surat
from backend.core.catat import pasang
from backend.repositori import keamanan as repo


async def perangkat_baru(pengguna_id: str, alamat: str | None, peramban: str | None) -> bool:
    """Apakah pasangan alamat dan peramban ini belum pernah berhasil masuk.

    Alamatnya sudah berupa ringkasan SHA-256 sebelum sampai ke sini; yang
    dibandingkan ringkasannya, dan yang tersimpan juga ringkasannya. Tidak ada
    satu pun alamat IP yang disimpan apa adanya, bahkan untuk keperluan ini.

    Bukan pengenal perangkat yang sebenarnya, dan tidak berpura pura begitu:
    alamat rumah yang berganti membuat perangkat lama terlihat baru, dan dua
    perangkat di belakang satu router terlihat sama. Arah kelirunya dipilih:
    yang pertama menghasilkan surat yang tidak perlu, yang kedua menghasilkan
    kabar yang terlewat. Yang pertama jauh lebih tidak merugikan.
    """
    return not await repo.pernah_masuk_dari(pengguna_id, alamat, peramban)


async def kabari_masuk(
    pengguna: dict, cara: str, alamat: str | None, peramban: str | None
) -> None:
    """Dipanggil sesudah sesi terbit, bukan sebelum.

    Kalau ia dipanggil lebih dulu dan pengirimannya lambat, yang menunggu
    adalah orang yang sedang menekan tombol Masuk.
    """
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
    except Exception as galat:  # pragma: no cover - jalur gagal kirim
        # Hanya jenisnya yang dicatat, tidak pernah isinya. Pesan galat SMTP
        # bisa memuat alamat surat dan kadang isi perintah yang gagal.
        pasang().warning(
            "kabar masuk gagal dikirim",
            extra={"tambahan": {"jenis": type(galat).__name__}},
        )


async def kabari_perubahan_keamanan(pengguna: dict, apa: str) -> None:
    """Perubahan pada jalan masuk itu sendiri.

    Mematikan authenticator, menghapus passkey, mengganti sandi. Ketiganya
    adalah yang pertama dikerjakan orang yang baru saja mengambil sebuah akun,
    sebab ketiganya menutup jalan pulang pemiliknya.
    """
    alamat_surat = pengguna.get("email")
    if not alamat_surat:
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
    except Exception as galat:  # pragma: no cover - jalur gagal kirim
        pasang().warning(
            "kabar perubahan keamanan gagal dikirim",
            extra={"tambahan": {"jenis": type(galat).__name__}},
        )
