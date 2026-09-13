"""Membangkitkan `next/app/globals.css` dari `assets/css/style.css`.

    python tools/gaya_next.py            # tulis ulang
    python tools/gaya_next.py --periksa  # hanya periksa, untuk CI

Dua salinan sistem desain adalah dua tempat yang harus diubah tiap kali satu
warna bergeser, dan yang kedua selalu tertinggal. Itu sudah terjadi: port
Next.js masih memakai palet abu abu kebiruan yang lama berhari hari setelah
versi HTML pindah ke abu abu netral Uber.

Bedanya dengan berkas induk ada dua, dan keduanya memang harus berbeda:

1. `next/font` memuat Poppins sendiri dan mengekspornya sebagai variabel CSS
   `--font-poppins`, sehingga situs hasil ekspor tidak meminta apa pun ke
   Google saat dijalankan. Jadi tiap `font-family: "Poppins",` diganti
   `font-family: var(--font-poppins),`.
2. Blok `@font-face` yang ditulis `tools/ambil_font.py` dibuang seluruhnya.
   Berkasnya ada di `/assets/fonts/`, alamat yang tidak eksis di dalam hasil
   ekspor Next, jadi membawanya ikut berarti delapan permintaan yang pasti
   dijawab 404 sekaligus dua deklarasi Poppins yang saling bertengkar.

Tidak ada perbedaan lain, dan `tests/test_gaya.py` yang memastikannya.
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

MULAI = "/* >>> font, dibangkitkan tools/ambil_font.py, jangan disunting */"
SELESAI = "/* <<< font */"

KEPALA = """/* DIBANGKITKAN, JANGAN DISUNTING.
   Sumbernya assets/css/style.css. Jalankan: python tools/gaya_next.py
   Dua perbedaan: Poppins datang dari next/font, dan blok @font-face yang
   menunjuk ke /assets/fonts dibuang karena alamat itu tidak ada di sini. */
"""


def tanpa_font_face(teks: str) -> str:
    """Membuang blok @font-face beserta penandanya. Kalau penandanya tidak ada,
    berkas induknya belum pernah disentuh tools/ambil_font.py, dan itu bukan
    keadaan yang boleh lolos diam diam."""
    if MULAI not in teks:
        sys.exit(
            f"tidak menemukan penanda font di {SUMBER.name}. "
            "Jalankan: python tools/ambil_font.py"
        )
    mulai = teks.index(MULAI)
    akhir = teks.index(SELESAI) + len(SELESAI)
    return (teks[:mulai] + teks[akhir:]).lstrip("\n")


def bangkitkan() -> str:
    teks = SUMBER.read_text(encoding="utf-8")
    if DARI not in teks:
        sys.exit(f"tidak menemukan {DARI!r} di {SUMBER.name}; pola fontnya berubah?")
    return KEPALA + tanpa_font_face(teks).replace(DARI, JADI)


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
