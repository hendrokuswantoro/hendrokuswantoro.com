"""Menyandikan satu kolom rahasia sebelum ia masuk basis data.

Dipakai untuk satu hal saja sejauh ini: rahasia TOTP.

Kenapa ia tidak boleh tersimpan apa adanya. Faktor kedua ada supaya sandi yang
bocor tidak cukup untuk masuk. Kalau rahasia TOTP tersimpan apa adanya di tabel
yang sama dengan hash sandinya, maka basis data yang bocor memberi penyerang
keduanya sekaligus, dan faktor kedua yang bocor bersama yang pertama bukan
faktor kedua. Ia cuma langkah tambahan yang menyusahkan pemiliknya.

Kuncinya datang dari `KUNCI_KOLOM`, terpisah dari basis datanya. Dengan begitu
salinan basis data, cadangan, atau dump yang jatuh ke tangan lain tidak memuat
satu pun rahasia TOTP yang bisa dipakai. Kunci yang disimpan di sebelah data
yang dikuncinya bukan kunci.

Yang TIDAK dilakukan di sini: menulis kriptografi sendiri. Seluruh kerjanya
diserahkan ke `backend/db/enkripsi.py`, yaitu AES-256-GCM dari pustaka
`cryptography` yang sudah dipakai cadangan dan sudah diuji dua puluh uji.
Bedanya cuma kuncinya datang dari variabel lain, sebab cadangan dan kolom
basis data tidak seharusnya dibuka oleh satu kunci yang sama.
"""

from __future__ import annotations

import base64

from backend.core.konfigurasi import pengaturan
from backend.db import enkripsi

NAMA_ENV = "KUNCI_KOLOM"


class KunciTidakAda(RuntimeError):
    """Tidak ada KUNCI_KOLOM, jadi tidak ada yang bisa dikunci atau dibuka."""


def siap() -> bool:
    """Apakah penyandian kolom bisa dipakai sama sekali.

    Dipakai lapisan di atasnya untuk menolak menyalakan TOTP, bukan untuk
    diam diam menyimpan rahasianya apa adanya. Fitur yang menurunkan
    jaminannya sendiri ketika konfigurasinya kurang adalah fitur yang
    jaminannya tidak pernah bisa dipercaya.
    """
    try:
        _kunci()
    except KunciTidakAda:
        return False
    return True


def _kunci() -> bytes:
    # Lewat Pengaturan, bukan os.environ.get. Aplikasi web ini tidak pernah
    # memuat .env ke dalam os.environ; yang membaca .env adalah
    # pydantic-settings. Kunci yang hanya tertulis di .env karena itu tidak
    # pernah terlihat oleh os.environ, dan fitur yang membacanya begitu akan
    # melaporkan "belum ada kunci" sambil kuncinya ada di berkas sebelahnya.
    # Variabel lingkungan sungguhan tetap menang, sebab pydantic-settings
    # membacanya lebih dulu daripada .env.
    nilai = (pengaturan().kunci_kolom or "").strip()
    if not nilai:
        raise KunciTidakAda(
            f"{NAMA_ENV} belum diisi. Buat satu dengan: "
            f"python backend/db/enkripsi.py kunci, lalu ganti nama variabelnya "
            f"jadi {NAMA_ENV} di .env"
        )
    try:
        mentah = base64.b64decode(nilai, validate=True)
    except Exception as galat:  # noqa: BLE001 - base64 apa pun salahnya sama
        raise KunciTidakAda(f"{NAMA_ENV} bukan base64 yang sah") from galat
    if len(mentah) != enkripsi.PANJANG_KUNCI:
        raise KunciTidakAda(
            f"{NAMA_ENV} panjangnya {len(mentah)} bita, seharusnya {enkripsi.PANJANG_KUNCI}"
        )
    return mentah


def sandikan(teks: str) -> str:
    """Teks biasa jadi satu untai base64 yang aman disimpan di kolom TEXT."""
    return base64.b64encode(enkripsi.kunci(teks.encode("utf-8"), _kunci())).decode("ascii")


def bukakan(tersimpan: str) -> str:
    """Kebalikannya. Melempar TidakBisaDibuka kalau kuncinya salah atau isinya
    diubah satu bit pun; itu memang gunanya GCM."""
    return enkripsi.buka(base64.b64decode(tersimpan), _kunci()).decode("utf-8")
