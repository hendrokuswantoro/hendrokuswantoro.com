"""Menghitung rasio kontras seluruh warna teks terhadap seluruh warna latar.

    python tools/kontras.py

Angkanya dibaca langsung dari `assets/css/style.css`, bukan diketik ulang di
sini. Palet yang berubah tanpa angkanya ikut berubah adalah cara paling
mudah membuat komentar di kepala berkas CSS itu berbohong.

Ambangnya WCAG 2.1: 4,5:1 untuk teks biasa, 3,0:1 untuk teks besar dan untuk
grafis. `--line` dan `--line-strong` sengaja tidak diuji terhadap ambang teks:
keduanya garis pemisah, bukan pembawa makna, dan garis yang cukup gelap untuk
lolos 3:1 di atas latar seterang #f6f6f6 akan terlihat seperti pagar.

Dipakai `tests/test_gaya.py`, jadi angka yang melorot akan menggagalkan uji,
bukan hanya mencetak peringatan yang tidak dibaca siapa pun.
"""

from __future__ import annotations

import pathlib
import re
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent
GAYA = AKAR / "assets" / "css" / "style.css"

TEKS = ("ink", "ink-2", "ink-3", "accent")
LATAR = ("bg", "card", "surface", "surface-2")

# Ambang per peran. --ink-3 dan --accent membawa teks biasa, jadi 4,5:1.
AMBANG = 4.5


def _linier(nilai: int) -> float:
    c = nilai / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminansi(heks: str) -> float:
    h = heks.lstrip("#")
    if len(h) == 3:
        h = "".join(dua * 2 for dua in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linier(r) + 0.7152 * _linier(g) + 0.0722 * _linier(b)


def rasio(satu: str, dua: str) -> float:
    a, b = luminansi(satu), luminansi(dua)
    tinggi, rendah = max(a, b), min(a, b)
    return (tinggi + 0.05) / (rendah + 0.05)


def _blok(teks: str, pembuka: str) -> str:
    mulai = teks.index(pembuka) + len(pembuka)
    return teks[mulai:teks.index("\n}", mulai)]


def token(tema: str) -> dict[str, str]:
    """Membaca --nama: #rrggbb dari blok :root yang diminta."""
    teks = GAYA.read_text(encoding="utf-8")
    pembuka = ':root[data-theme="dark"] {' if tema == "gelap" else "\n:root {"
    return {
        nama: nilai.lower()
        for nama, nilai in re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,6});", _blok(teks, pembuka))
    }


def matriks(tema: str) -> list[tuple[str, str, float]]:
    warna = token(tema)
    hilang = [n for n in (*TEKS, *LATAR) if n not in warna]
    if hilang:
        sys.exit(f"token tidak ditemukan di tema {tema}: {', '.join(hilang)}")
    return [
        (t, l, rasio(warna[t], warna[l]))
        for t in TEKS
        for l in LATAR
    ]


def main() -> int:
    gagal = 0
    for tema in ("terang", "gelap"):
        warna = token(tema)
        print(f"\n{tema.upper()}")
        print("            " + "  ".join(f"{l:>11}" for l in LATAR))
        for t in TEKS:
            baris = [f"--{t}".ljust(10) + f" {warna[t]}"]
            for l in LATAR:
                nilai = rasio(warna[t], warna[l])
                tanda = " " if nilai >= AMBANG else "!"
                baris.append(f"{nilai:8.2f}{tanda}  ")
                if nilai < AMBANG:
                    gagal += 1
            print("".join(baris))

    if gagal:
        print(f"\n{gagal} pasangan di bawah {AMBANG}:1. Tanda ! menandainya.")
        return 1
    print(f"\nseluruh pasangan teks lolos {AMBANG}:1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
