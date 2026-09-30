from __future__ import annotations

import pathlib
from html.parser import HTMLParser

AKAR = pathlib.Path(__file__).resolve().parent.parent

EMAIL_UJI = "kuswantoro.hendro01@gmail.com"
SANDI_UJI = "sandi-uji-lokal-panjang"


def loop_untuk_psycopg() -> None:
    import asyncio
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def ada_basis_data(dsn: str) -> bool:
    if not dsn:
        return False
    try:
        import psycopg

        with psycopg.connect(dsn, connect_timeout=3):
            return True
    except Exception:
        return False

BUKAN_HALAMAN = {"next", "dist", "content", "backend", ".claude", "hasil-uji-keamanan"}

HALAMAN = sorted(
    p for p in AKAR.rglob("*.html")
    if not BUKAN_HALAMAN & set(p.parts)
)


class Pemindai(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tag: list[tuple[str, dict[str, str | None]]] = []
        self.judul: list[int] = []
        self.id: list[str] = []
        self.gambar: list[dict[str, str | None]] = []
        self.tautan: list[str] = []
        self.sumber: list[str] = []
        self.dwibahasa: list[tuple[str, dict[str, str | None]]] = []
        self._teks: list[str] = []
        self.teks = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        atur = dict(attrs)
        self.tag.append((tag, atur))

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.judul.append(int(tag[1]))
        if "id" in atur and atur["id"]:
            self.id.append(atur["id"])
        if tag == "img":
            self.gambar.append(atur)
        if tag == "a" and atur.get("href"):
            self.tautan.append(atur["href"] or "")
        if tag in ("script", "img", "source") and atur.get("src"):
            self.sumber.append(atur["src"] or "")
        if tag == "link" and atur.get("href"):
            self.sumber.append(atur["href"] or "")
        if "data-ind" in atur:
            self.dwibahasa.append((tag, atur))

    def handle_data(self, data: str) -> None:
        self._teks.append(data)

    def close(self) -> None:
        super().close()
        self.teks = "".join(self._teks)


def pindai(berkas: pathlib.Path) -> Pemindai:
    p = Pemindai()
    p.feed(berkas.read_text(encoding="utf-8"))
    p.close()
    return p


def nama(berkas: pathlib.Path) -> str:
    return berkas.relative_to(AKAR).as_posix()


def berkas_dari_jalur(jalur: str) -> pathlib.Path:
    bersih = jalur.split("#")[0].split("?")[0]
    if bersih in ("", "/"):
        return AKAR / "index.html"
    if bersih.endswith("/"):
        return AKAR / bersih.strip("/") / "index.html"
    if bersih.startswith("/unggahan/"):
        return AKAR / "content" / bersih.lstrip("/")
    calon = AKAR / bersih.lstrip("/")
    if calon.suffix:
        return calon
    return calon.with_suffix(".html")
