"""Apakah basis datanya benar benar menjawab, bukan sekadar tertulis di .env.

    python tools/basis_data_hidup.py     # keluar 0 kalau hidup, 1 kalau tidak

Kenapa berkas ini ada.

`tools/verifikasi.sh` sempat memutuskan dua langkah dari pertanyaan yang
salah. Yang ditanyakan "apakah DSN terisi", padahal yang menentukan
"apakah ada yang menjawab di ujung sana". Di mesin pengembangan keduanya
sering berbeda: DSN memang tertulis di .env, sedangkan Docker Desktop sedang
mati. Akibatnya langkah cadangan GAGAL, bukan DILEWATI, dan berkas itu sendiri
berjanji melewatkan langkah yang memang tidak bisa dijalankan.

Bedanya bukan soal rapi rapi. Kegagalan yang sebabnya di luar kode mengajari
siapa pun yang menjalankannya untuk mengabaikan warna merah, dan sesudah itu
kegagalan yang sungguhan ikut terlewat.

Yang diperiksa cuma sambungan TCP, bukan otentikasi maupun isi basis datanya.
Itu memang cukup: yang ingin dibedakan adalah "tidak ada apa apa di sana"
dari "ada, mari kita periksa". Selebihnya biar langkah yang sesungguhnya yang
menilai, sebab langkah yang menduplikasi pemeriksaan langkah lain akan hanyut
dari yang ditirunya.
"""

from __future__ import annotations

import os
import pathlib
import socket
import sys
import urllib.parse

AKAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR / "tools"))

TENGGAT_DETIK = 3.0


def dsn() -> str:
    nilai = os.environ.get("DSN", "")
    if nilai:
        return nilai
    berkas = AKAR / ".env"
    if not berkas.exists():
        return ""
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        baris = baris.strip()
        if baris.startswith("DSN=") and not baris.startswith("#"):
            return baris.split("=", 1)[1].strip()
    return ""


def hidup(alamat: str) -> bool:
    if not alamat:
        return False
    urai = urllib.parse.urlparse(alamat)
    inang = urai.hostname or "127.0.0.1"
    porta = urai.port or 5432
    try:
        with socket.create_connection((inang, porta), timeout=TENGGAT_DETIK):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(0 if hidup(dsn()) else 1)
