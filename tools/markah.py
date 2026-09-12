"""Markdown ke HTML, hanya sebatas yang dipakai blog ini.

Kenapa bukan pustaka Markdown yang sudah ada: situs ini tidak punya satu pun
dependensi runtime, dan langkah build-nya berjalan di mesin Cloudflare yang
tidak dijamin punya pip. Menambah satu paket demi empat bentuk markup adalah
kompleksitas yang dilarang bab 15.1.

Kenapa tidak berbahaya: pengurai ini **menolak** apa pun yang tidak dikenalnya
dengan galat yang menyebut nomor barisnya. Pengurai setengah jadi yang diam
diam menghasilkan HTML salah jauh lebih berbahaya daripada pengurai kecil yang
berhenti dan mengadu.

Yang didukung:

    ## Judul bagian          -> <h2>
    Paragraf biasa           -> <p>
    > Kutipan                -> <blockquote><p>
    **tebal**  *miring*      -> <strong> <em>
    `kode`                   -> <code>
    [teks](alamat)           -> <a href>

Yang ditolak dengan galat: heading selain ##, daftar, tabel, gambar, blok
kode berpagar, HTML mentah, dan tautan referensi.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass


class MarkahSalah(ValueError):
    """Sintaks yang tidak didukung, disertai nomor baris."""


@dataclass(frozen=True)
class Blok:
    """Satu blok tingkat atas. `jenis` salah satu dari h2, p, quote."""

    jenis: str
    teks: str
    baris: int


DITOLAK = [
    (re.compile(r"^\s{0,3}#(?!#\s)"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}#{3,}\s"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}([-*+]|\d+\.)\s"), "daftar belum didukung"),
    (re.compile(r"^\s{0,3}(```|~~~)"), "blok kode berpagar belum didukung"),
    (re.compile(r"^\s{0,3}\|"), "tabel belum didukung"),
    (re.compile(r"^\s{0,3}!\["), "gambar belum didukung"),
    (re.compile(r"^\s{0,3}<"), "HTML mentah tidak diterima"),
]

SEBARIS = re.compile(
    r"(?P<kode>`[^`]+`)"
    r"|(?P<tautan>\[[^\]]+\]\([^)\s]+\))"
    r"|(?P<tebal>\*\*[^*]+\*\*)"
    r"|(?P<miring>\*[^*]+\*)"
)


def blok(sumber: str) -> list[Blok]:
    """Memecah Markdown jadi blok tingkat atas, atau melempar MarkahSalah."""
    hasil: list[Blok] = []
    kumpul: list[str] = []
    mulai = 0
    jenis = "p"

    def tutup() -> None:
        nonlocal kumpul, jenis, mulai
        if kumpul:
            hasil.append(Blok(jenis, " ".join(kumpul).strip(), mulai))
        kumpul = []
        jenis = "p"

    for nomor, baris in enumerate(sumber.splitlines(), 1):
        isi = baris.rstrip()

        if not isi.strip():
            tutup()
            continue

        if isi.lstrip().startswith("## "):
            tutup()
            hasil.append(Blok("h2", isi.lstrip()[3:].strip(), nomor))
            continue

        if isi.lstrip().startswith(">"):
            if jenis != "quote":
                tutup()
                jenis, mulai = "quote", nomor
            kumpul.append(isi.lstrip()[1:].strip())
            continue

        for pola, alasan in DITOLAK:
            if pola.match(isi):
                raise MarkahSalah(f"baris {nomor}: {alasan}\n  {isi[:70]}")

        if not kumpul:
            mulai = nomor
        kumpul.append(isi.strip())

    tutup()
    return hasil


def sebaris(teks: str) -> str:
    """Markup sebaris jadi HTML. Selain itu di-escape."""
    keluar: list[str] = []
    posisi = 0

    for cocok in SEBARIS.finditer(teks):
        keluar.append(html.escape(teks[posisi:cocok.start()], quote=False))
        potong = cocok.group(0)

        if cocok.lastgroup == "kode":
            keluar.append("<code>" + html.escape(potong[1:-1], quote=False) + "</code>")
        elif cocok.lastgroup == "tautan":
            label, _, alamat = potong[1:-1].partition("](")
            keluar.append(
                '<a href="%s">%s</a>'
                % (html.escape(alamat, quote=True), html.escape(label, quote=False))
            )
        elif cocok.lastgroup == "tebal":
            keluar.append("<strong>" + html.escape(potong[2:-2], quote=False) + "</strong>")
        else:
            keluar.append("<em>" + html.escape(potong[1:-1], quote=False) + "</em>")

        posisi = cocok.end()

    keluar.append(html.escape(teks[posisi:], quote=False))
    return "".join(keluar)


def polos(teks: str) -> str:
    """Teks tanpa markup, untuk atribut data-ind. Tanda kutipnya di-escape."""
    bersih = SEBARIS.sub(_telanjangi, teks)
    return html.escape(bersih, quote=True)


def _telanjangi(cocok: re.Match[str]) -> str:
    potong = cocok.group(0)
    if cocok.lastgroup == "kode":
        return potong[1:-1]
    if cocok.lastgroup == "tautan":
        return potong[1:-1].partition("](")[0]
    if cocok.lastgroup == "tebal":
        return potong[2:-2]
    return potong[1:-1]
