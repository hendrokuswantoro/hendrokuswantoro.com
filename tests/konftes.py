"""Shared helpers for the test suite.

The site is plain HTML, so the tests read it with the standard library only.
Nothing here parses with a regular expression where a parser will do: a
regex that looks right on today's markup quietly stops matching the day an
attribute moves, and a test that silently stops checking is worse than no
test at all.
"""

from __future__ import annotations

import pathlib
from html.parser import HTMLParser

AKAR = pathlib.Path(__file__).resolve().parent.parent

# every page that is actually served, the Next.js port excluded because it is
# a separate application with its own toolchain
HALAMAN = sorted(
    p for p in AKAR.rglob("*.html")
    if "next" not in p.parts and "dist" not in p.parts
)


class Pemindai(HTMLParser):
    """Collects the handful of things the tests ask about."""

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

    def close(self) -> None:  # type: ignore[override]
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
    """Turns an address into the file that answers it.

    The site hands out addresses without .html, because Cloudflare answers
    /about.html with a 307 to /about. This mirrors the rule the host uses:
    a trailing slash means index.html inside that folder, an address with no
    extension means the file of that name plus .html, and anything that
    already carries an extension is taken as written.
    """
    bersih = jalur.split("#")[0].split("?")[0]
    if bersih in ("", "/"):
        return AKAR / "index.html"
    if bersih.endswith("/"):
        return AKAR / bersih.strip("/") / "index.html"
    calon = AKAR / bersih.lstrip("/")
    if calon.suffix:
        return calon
    return calon.with_suffix(".html")
