"""Membangkitkan `next/app/globals.css` dari `assets/css/style.css`.

    python tools/gaya_next.py            # tulis ulang
    python tools/gaya_next.py --periksa  # hanya periksa, untuk CI

Dua salinan sistem desain adalah dua tempat yang harus diubah tiap kali satu
warna bergeser, dan yang kedua selalu tertinggal. Itu sudah terjadi: port
Next.js masih memakai palet abu abu kebiruan yang lama berhari hari setelah
versi HTML pindah ke abu abu netral Uber.

Bedanya dengan berkas induk cuma satu hal, dan itu memang harus berbeda:
`next/font` memuat Poppins sendiri dan mengekspornya sebagai variabel CSS
`--font-poppins`, sehingga situs hasil ekspor tidak meminta apa pun ke Google
saat dijalankan. Jadi tiap `font-family: "Poppins",` diganti
`font-family: var(--font-poppins),`. Tidak ada perbedaan lain, dan
`tests/test_gaya.py` yang memastikannya.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent
SUMBER = AKAR / "assets" / "css" / "style.css"
TUJUAN = AKAR / "next" / "app" / "globals.css"

DARI = 'font-family: "Poppins",'
JADI = "font-family: var(--font-poppins),"

KEPALA = """/* DIBANGKITKAN, JANGAN DISUNTING.
   Sumbernya assets/css/style.css. Jalankan: python tools/gaya_next.py
   Satu satunya perbedaan: Poppins datang dari next/font, bukan dari Google. */
"""


def bangkitkan() -> str:
    teks = SUMBER.read_text(encoding="utf-8")
    if DARI not in teks:
        sys.exit(f"tidak menemukan {DARI!r} di {SUMBER.name}; pola fontnya berubah?")
    return KEPALA + teks.replace(DARI, JADI)


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true",
                        help="keluar 1 kalau berkasnya tidak sama dengan yang seharusnya")
    pilihan = alasan.parse_args()

    harus = bangkitkan()
    ada = TUJUAN.read_text(encoding="utf-8") if TUJUAN.exists() else ""

    if pilihan.periksa:
        if ada == harus:
            print(f"cocok: {TUJUAN.relative_to(AKAR)} sama dengan sumbernya")
            return 0
        print(f"BEDA: {TUJUAN.relative_to(AKAR)} tertinggal dari {SUMBER.relative_to(AKAR)}")
        print("Jalankan: python tools/gaya_next.py")
        return 1

    TUJUAN.write_text(harus, encoding="utf-8")
    print(f"ditulis: {TUJUAN.relative_to(AKAR)}, {len(harus)} bita, "
          f"{harus.count(JADI)} tempat memakai --font-poppins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
