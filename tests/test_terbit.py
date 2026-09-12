"""What actually reaches the web server, and whether it agrees with itself.

The first test here exists because the bug it catches fooled me twice in one
day: the version string on style.css and app.js drifted apart between pages,
so a returning visitor got the new HTML and the old stylesheet on every page
but one. Nothing errors. The site just looks wrong for some people.
"""

from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET

import pytest

from konftes import AKAR, HALAMAN, berkas_dari_jalur, nama

SITUS = "https://www.hendrokuswantoro.com"
HEADERS = (AKAR / "_headers").read_text(encoding="utf-8")
WRANGLER = (AKAR / "wrangler.toml").read_text(encoding="utf-8")


def versi(berkas: pathlib.Path, aset: str) -> str | None:
    cocok = re.search(re.escape(aset) + r"\?v=([0-9]+)", berkas.read_text(encoding="utf-8"))
    return cocok.group(1) if cocok else None


@pytest.mark.parametrize("aset", ["/assets/css/style.css", "/assets/js/app.js"])
def test_versi_seragam(aset):
    """One version per asset across the whole site, or the cache serves a
    mixture of old and new to anyone who has been here before."""
    dipakai = {nama(b): versi(b, aset) for b in HALAMAN}
    hilang = [k for k, v in dipakai.items() if v is None]
    assert not hilang, f"{aset} has no version string on {hilang}"
    assert len(set(dipakai.values())) == 1, f"{aset} versions drifted apart: {dipakai}"


def test_peta_ikut_diberi_versi():
    app = (AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"peta\.js\?v=[0-9]+", app), "peta.js is loaded without a version"


def test_dua_pembangun_sepakat():
    """The zip and the folder Cloudflare serves must contain the same files.
    They are built by different scripts and drifted once already."""
    py = (AKAR / "tools" / "build_dist.py").read_text(encoding="utf-8")
    sh = (AKAR / "tools" / "bangun_situs.sh").read_text(encoding="utf-8")

    daftar_py = set(re.findall(r'^\s+"([\w.\-]+)",', py, re.M))
    blok = re.search(r"for berkas in (.*?); do", sh, re.S)
    assert blok, "the copy loop in bangun_situs.sh changed shape"
    # the shell wraps the list across lines with backslashes, which are
    # separators, not file names
    daftar_sh = {k for k in blok.group(1).split() if k != chr(92)}

    assert daftar_py == daftar_sh, (
        f"only in the zip: {sorted(daftar_py - daftar_sh)}\n"
        f"only in dist/  : {sorted(daftar_sh - daftar_py)}"
    )


def test_sitemap_menunjuk_berkas_nyata():
    akar = ET.parse(AKAR / "sitemap.xml").getroot()
    ruang = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    alamat = [e.text or "" for e in akar.findall(".//s:loc", ruang)]
    assert alamat, "the sitemap is empty"

    for a in alamat:
        assert a.startswith(SITUS), f"sitemap lists a foreign address: {a}"
        berkas = berkas_dari_jalur(a[len(SITUS):])
        assert berkas.exists(), f"sitemap lists {a}, which does not exist"


def test_setiap_tulisan_terdaftar():
    """A post nobody can find is a post that was never published."""
    # addresses carry no .html, so the slug is what has to appear
    tulisan = sorted(p.stem for p in (AKAR / "blog").glob("*.html") if p.stem != "index")
    sitemap = (AKAR / "sitemap.xml").read_text(encoding="utf-8")
    umpan = (AKAR / "feed.xml").read_text(encoding="utf-8")
    for t in tulisan:
        assert f"/blog/{t}<" in sitemap, f"{t} is missing from the sitemap"
        assert f"/blog/{t}<" in umpan, f"{t} is missing from the feed"


def test_umpan_terbaca():
    akar = ET.parse(AKAR / "feed.xml").getroot()
    item = akar.findall(".//item")
    assert len(item) >= 3, "the feed lost posts"
    for i in item:
        for bagian in ("title", "link", "guid", "description", "pubDate"):
            assert (i.find(bagian) is not None) and i.find(bagian).text, (
                f"a feed item is missing {bagian}"
            )


def test_robots_menunjuk_sitemap():
    robots = (AKAR / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {SITUS}/sitemap.xml" in robots


@pytest.mark.parametrize("arahan", [
    "X-Content-Type-Options: nosniff",
    "X-Frame-Options: DENY",
    "Referrer-Policy: strict-origin-when-cross-origin",
    "Strict-Transport-Security:",
    "Content-Security-Policy:",
])
def test_header_keamanan_ada(arahan):
    assert arahan in HEADERS, f"_headers lost {arahan}"


@pytest.mark.parametrize("sumber", [
    "default-src 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "script-src 'self' blob:",
    "https://api.mapbox.com",
])
def test_csp_menahan_yang_penting(sumber):
    csp = [b for b in HEADERS.splitlines() if "Content-Security-Policy:" in b][0]
    assert sumber in csp, f"the CSP lost {sumber}"


def test_tidak_ada_redirects_lagi():
    """Cloudflare Workers rejects a cross host rule in _redirects and fails
    the whole deploy. The apex to www redirect lives in a Redirect Rule."""
    assert not (AKAR / "_redirects").exists(), (
        "_redirects is back. Workers will refuse the deploy with code 100324."
    )


def test_wrangler_menunjuk_dist():
    assert 'name = "hendrokuswantoro-com"' in WRANGLER, "the worker name no longer matches"
    assert 'directory = "./dist"' in WRANGLER
    assert 'not_found_handling = "404-page"' in WRANGLER
