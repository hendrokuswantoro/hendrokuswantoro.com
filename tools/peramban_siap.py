"""Apakah Chromium benar benar bisa dinyalakan, bukan sekadar terpasang.

    python tools/peramban_siap.py     # keluar 0 kalau siap, 1 kalau tidak

Kenapa berkas ini ada.

`tools/verifikasi.sh` memutuskan menjalankan uji peramban dari pertanyaan
`import playwright`. Itu membuktikan PAKETNYA ada, bukan bahwa perambannya
ada. Keduanya berbeda, dan bedanya sempat menyembunyikan banyak sekali:

    4 passed, 44 skipped, 605 deselected
       ok

Empat puluh empat dari empat puluh delapan uji peramban tidak berjalan sama
sekali, sebab berkas `headless_shell.exe` belum pernah diunduh, dan langkahnya
tetap melaporkan `ok`. Uji yang dilewati memang bukan uji yang gagal, jadi
tidak ada yang berwarna merah. Yang hilang cuma seluruh isinya.

Ini persis kekeliruan yang sama dengan `command -v docker`, yang membuktikan
perintahnya ada sedangkan yang menentukan mesinnya menjawab. Pola yang sama
muncul tiga kali dalam satu hari di berkas yang sama, jadi pertanyaannya
sekarang selalu ditanyakan pada benda yang sesungguhnya dipakai.

Perambannya benar benar dinyalakan lalu ditutup lagi. Ongkosnya sekitar satu
detik, dan itu jauh lebih murah daripada satu langkah hijau yang tidak
menjaga apa pun.
"""

from __future__ import annotations

import sys


def siap() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    try:
        with sync_playwright() as p:
            peramban = p.chromium.launch()
            peramban.close()
    except Exception:
        return False
    return True


if __name__ == "__main__":
    sys.exit(0 if siap() else 1)
