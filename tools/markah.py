from __future__ import annotations

import html
import re
from dataclasses import dataclass


class MarkahSalah(ValueError):
    pass


@dataclass(frozen=True)
class Blok:
    jenis: str
    teks: str
    baris: int
    alamat: str = ""
    butir: tuple[str, ...] = ()


DITOLAK = [
    (re.compile(r"^\s{0,3}#(?!#\s)"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}#{3,}\s"), "hanya '## ' yang didukung untuk judul"),
    (re.compile(r"^\s{0,3}(```|~~~)"), "blok kode berpagar belum didukung"),
    (re.compile(r"^\s{0,3}\|"), "tabel belum didukung"),
    (re.compile(r"^\s{0,3}<"), "HTML mentah tidak diterima"),
]

GAMBAR = re.compile(r"^!\[(?P<teks>[^\]]*)\]\((?P<alamat>[^)\s]+)\)$")
VIDEO = re.compile(r"^!video\[(?P<teks>[^\]]*)\]\((?P<alamat>[^)\s]+)\)$")
BUTIR_UL = re.compile(r"^\s{0,3}[-*+]\s+(?P<teks>.+)$")
BUTIR_OL = re.compile(r"^\s{0,3}\d{1,3}\.\s+(?P<teks>.+)$")

AWALAN_MEDIA = ("/unggahan/", "/assets/img/")
AKHIRAN_GAMBAR = (".webp", ".avif", ".png", ".jpg", ".jpeg", ".gif")
AKHIRAN_VIDEO = (".mp4", ".webm")

UKURAN = re.compile(r"-(\d{1,5})x(\d{1,5})\.[a-z0-9]+$")

SEBARIS = re.compile(
    r"(?P<kode>`[^`]+`)"
    r"|(?P<tautan>\[[^\]]+\]\([^)\s]+\))"
    r"|(?P<tebal>\*\*[^*]+\*\*)"
    r"|(?P<miring>\*[^*]+\*)"
)


def periksa_media(alamat: str, jenis: str) -> None:
    if not alamat.startswith(AWALAN_MEDIA):
        raise MarkahSalah(
            f"alamat {jenis} harus berkas yang diunggah ke situs ini, "
            f"yaitu diawali {' atau '.join(AWALAN_MEDIA)}. "
            f"Yang ditulis: {alamat[:60]!r}"
        )
    if ".." in alamat:
        raise MarkahSalah(f"alamat {jenis} tidak boleh memuat '..': {alamat[:60]!r}")

    boleh = AKHIRAN_GAMBAR if jenis == "gambar" else AKHIRAN_VIDEO
    if not alamat.lower().endswith(boleh):
        raise MarkahSalah(
            f"berkas {jenis} harus berakhiran {', '.join(boleh)}. "
            f"Yang ditulis: {alamat[:60]!r}"
        )


def ukuran(alamat: str) -> tuple[int, int] | None:
    cocok = UKURAN.search(alamat)
    if cocok is None:
        return None
    return int(cocok.group(1)), int(cocok.group(2))


def blok(sumber: str) -> list[Blok]:
    hasil: list[Blok] = []
    kumpul: list[str] = []
    butir: list[str] = []
    mulai = 0
    jenis = "p"

    def tutup() -> None:
        nonlocal kumpul, butir, jenis, mulai
        if butir:
            hasil.append(Blok(jenis, "", mulai, butir=tuple(butir)))
        elif kumpul:
            hasil.append(Blok(jenis, " ".join(kumpul).strip(), mulai))
        kumpul = []
        butir = []
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

        telanjang = isi.lstrip()
        if telanjang.startswith("!"):
            for pola, ini in ((VIDEO, "video"), (GAMBAR, "gambar")):
                cocok = pola.match(telanjang)
                if cocok is None:
                    continue
                tutup()
                alamat = cocok.group("alamat")
                try:
                    periksa_media(alamat, ini)
                except MarkahSalah as galat:
                    raise MarkahSalah(f"baris {nomor}: {galat}") from galat
                hasil.append(
                    Blok(ini, cocok.group("teks").strip(), nomor, alamat=alamat)
                )
                break
            else:
                raise MarkahSalah(
                    f"baris {nomor}: bentuk gambar atau video tidak dikenali. "
                    "Yang benar: ![keterangan](/unggahan/berkas.webp) "
                    "atau !video[keterangan](/unggahan/berkas.mp4)\n"
                    f"  {isi[:70]}"
                )
            continue

        if telanjang.startswith(">"):
            if jenis != "quote":
                tutup()
                jenis, mulai = "quote", nomor
            kumpul.append(telanjang[1:].strip())
            continue

        for pola, ini in ((BUTIR_UL, "ul"), (BUTIR_OL, "ol")):
            cocok = pola.match(isi)
            if cocok is None:
                continue
            if jenis != ini:
                tutup()
                jenis, mulai = ini, nomor
            butir.append(cocok.group("teks").strip())
            break
        else:
            for pola, alasan in DITOLAK:
                if pola.match(isi):
                    raise MarkahSalah(f"baris {nomor}: {alasan}\n  {isi[:70]}")

            if butir:
                tutup()
            if not kumpul:
                mulai = nomor
            kumpul.append(isi.strip())

    tutup()
    for b in hasil:
        for potong in (b.teks, *b.butir):
            try:
                sebaris(potong)
            except MarkahSalah as galat:
                raise MarkahSalah(f"baris {b.baris}: {galat}") from galat

    return hasil


SKEMA_BOLEH = ("https:", "http:", "mailto:")


def periksa_alamat(alamat: str) -> None:
    bersih = alamat.strip()

    if bersih.startswith(("#", "/", "./", "../")):
        return

    kecil = bersih.lower()
    if kecil.startswith(SKEMA_BOLEH):
        return

    if ":" not in kecil.split("/")[0]:
        return

    raise MarkahSalah(
        f"skema tautan tidak diizinkan: {bersih[:40]!r}. "
        f"Yang boleh: {', '.join(SKEMA_BOLEH)}, atau alamat relatif."
    )


def sebaris(teks: str) -> str:
    keluar: list[str] = []
    posisi = 0

    for cocok in SEBARIS.finditer(teks):
        keluar.append(html.escape(teks[posisi:cocok.start()], quote=False))
        potong = cocok.group(0)

        if cocok.lastgroup == "kode":
            keluar.append("<code>" + html.escape(potong[1:-1], quote=False) + "</code>")
        elif cocok.lastgroup == "tautan":
            label, _, alamat = potong[1:-1].partition("](")
            periksa_alamat(alamat)
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
    bersih = SEBARIS.sub(_telanjangi, teks)
    return html.escape(bersih, quote=True)


def untuk_ind(teks: str) -> str:
    return html.escape(polos(teks), quote=True)


def _telanjangi(cocok: re.Match[str]) -> str:
    potong = cocok.group(0)
    if cocok.lastgroup == "kode":
        return potong[1:-1]
    if cocok.lastgroup == "tautan":
        return potong[1:-1].partition("](")[0]
    if cocok.lastgroup == "tebal":
        return potong[2:-2]
    return potong[1:-1]
