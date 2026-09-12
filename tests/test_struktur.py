"""Structure of every page that gets served.

These are the checks a browser will not complain about but a screen reader,
a search engine, or a visitor on a broken link will. Two of them caught real
defects already: card titles were h3 sitting directly under the page h1, and
the map caption still credited a basemap the site had stopped using.
"""

from __future__ import annotations

import collections
import re

import pytest

from konftes import AKAR, HALAMAN, berkas_dari_jalur, nama, pindai

SITUS = "https://www.hendrokuswantoro.com"


def test_ada_halaman():
    assert len(HALAMAN) >= 8, "the site lost pages"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_satu_h1(berkas):
    p = pindai(berkas)
    assert p.judul.count(1) == 1, f"{nama(berkas)} has {p.judul.count(1)} h1"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_urutan_judul(berkas):
    """No level may be skipped. A h3 under a h1 is a hole in the outline."""
    p = pindai(berkas)
    for a, b in zip(p.judul, p.judul[1:]):
        assert b <= a + 1, f"{nama(berkas)}: h{a} followed by h{b}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_id_unik(berkas):
    p = pindai(berkas)
    ganda = [k for k, v in collections.Counter(p.id).items() if v > 1]
    assert not ganda, f"{nama(berkas)}: duplicate id {ganda}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_gambar_punya_alt(berkas):
    p = pindai(berkas)
    for g in p.gambar:
        assert g.get("alt") is not None, f"{nama(berkas)}: img without alt, src={g.get('src')}"
        assert g.get("data-ind-alt"), f"{nama(berkas)}: alt not translated, src={g.get('src')}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_tautan_dalam_hidup(berkas):
    p = pindai(berkas)
    for t in p.tautan:
        if not t.startswith("/"):
            continue
        tujuan = berkas_dari_jalur(t)
        assert tujuan.exists(), f"{nama(berkas)}: dead link {t}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_aset_ada(berkas):
    p = pindai(berkas)
    for s in p.sumber:
        if not s.startswith("/"):
            continue
        tujuan = berkas_dari_jalur(s)
        assert tujuan.exists(), f"{nama(berkas)}: missing asset {s}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_kepala_halaman(berkas):
    """Language, title, description and canonical, the four a crawler reads."""
    isi = berkas.read_text(encoding="utf-8")
    p = pindai(berkas)

    assert re.search(r'<html[^>]+lang="[a-z]{2}"', isi), f"{nama(berkas)}: no lang on html"

    judul = re.search(r"<title[^>]*>(.*?)</title>", isi, re.S)
    assert judul and judul.group(1).strip(), f"{nama(berkas)}: empty title"
    assert len(judul.group(1).strip()) <= 60, f"{nama(berkas)}: title longer than 60 characters"

    keterangan = [t for t in p.tag if t[0] == "meta" and t[1].get("name") == "description"]
    assert keterangan, f"{nama(berkas)}: no meta description"
    assert keterangan[0][1].get("content"), f"{nama(berkas)}: empty meta description"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_kanonis(berkas):
    """Every page except the 404 must say which address is the real one."""
    if berkas.name == "404.html":
        pytest.skip("a 404 has no canonical address")
    p = pindai(berkas)
    kanonis = [t for t in p.tag if t[0] == "link" and t[1].get("rel") == "canonical"]
    assert kanonis, f"{nama(berkas)}: no canonical link"
    alamat = kanonis[0][1].get("href") or ""
    assert alamat.startswith(SITUS), f"{nama(berkas)}: canonical points elsewhere, {alamat}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_umpan_ditawarkan(berkas):
    p = pindai(berkas)
    umpan = [
        t for t in p.tag
        if t[0] == "link" and t[1].get("type") == "application/rss+xml"
    ]
    assert umpan, f"{nama(berkas)}: the feed is not offered"
    assert umpan[0][1].get("href") == "/feed.xml"

def test_setiap_filter_punya_isi():
    """A filter button that matches nothing is a button that leads to an
    empty page for ever. The empty state is for a filter that happens to be
    empty today, not for one that can never fill."""
    berkas = AKAR / "project.html"
    p = pindai(berkas)

    tombol = {atur["data-filter"] for tag, atur in p.tag if atur.get("data-filter")}
    jenis = set()
    for tag, atur in p.tag:
        if atur.get("data-category"):
            jenis.update(atur["data-category"].split())

    assert "all" in tombol, "the All button is gone"
    kosong = tombol - {"all"} - jenis
    assert not kosong, f"these filters match no project at all: {sorted(kosong)}"


def test_keadaan_kosong_ada():
    """Without it, filtering to nothing shows a blank stretch of page with no
    explanation."""
    p = pindai(AKAR / "project.html")
    kosong = [atur for tag, atur in p.tag if "data-empty" in atur]
    assert kosong, "project.html has no empty state"
    assert kosong[0].get("data-ind"), "the empty state is not translated"


def test_peta_punya_keadaan_gagal():
    """The map is fetched over the network and can fail. When it does the
    section has to say so rather than leave a grey rectangle."""
    p = pindai(AKAR / "project.html")
    gagal = [atur for tag, atur in p.tag if atur.get("data-gagal")]
    assert gagal, "the map has no failure message"
    assert gagal[0].get("data-ind-gagal"), "the failure message is not translated"


def test_lompat_ke_isi():
    """The first thing a keyboard reaches must be a way past the header."""
    for berkas in HALAMAN:
        p = pindai(berkas)
        lompat = [t for t in p.tag if t[0] == "a" and "skip-link" in (t[1].get("class") or "")]
        assert lompat, f"{nama(berkas)}: no skip link"
        assert lompat[0][1].get("href") == "#main", f"{nama(berkas)}: skip link points elsewhere"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_alamat_tanpa_html(berkas):
    """Cloudflare answers /about.html with a 307 to /about. Handing out the
    long form means every internal navigation pays for a redirect, and a
    canonical that redirects is a canonical pointing at the wrong address."""
    p = pindai(berkas)
    for t in p.tautan:
        if t.startswith("/"):
            assert not t.endswith(".html"), f"{nama(berkas)}: {t} will be redirected"

    isi = berkas.read_text(encoding="utf-8")
    panjang = re.findall(r"https://www\.hendrokuswantoro\.com/[A-Za-z0-9/_-]+\.html", isi)
    assert not panjang, f"{nama(berkas)}: addresses that redirect: {sorted(set(panjang))}"
