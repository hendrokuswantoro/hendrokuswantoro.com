"""The two languages must stay level with each other.

English lives in the markup so a crawler sees real text; Indonesian rides
along in a data-ind attribute next to it. The failure this guards against is
silent: someone edits the English and forgets the attribute, and half the
site switches language while the other half does not.
"""

from __future__ import annotations

import re

import pytest

from konftes import HALAMAN, nama, pindai

PASANGAN = [
    ("data-ind", None),
    ("data-ind-label", "aria-label"),
    ("data-ind-alt", "alt"),
    ("data-ind-gagal", "data-gagal"),
]


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_terjemahan_tidak_kosong(berkas):
    p = pindai(berkas)
    for tag, atur in p.dwibahasa:
        nilai = atur.get("data-ind")
        assert nilai is not None and nilai.strip(), (
            f"{nama(berkas)}: empty data-ind on <{tag}>"
        )


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_pasangan_atribut_lengkap(berkas):
    """An Indonesian attribute with no English counterpart has nothing to
    switch back to, so the first switch to English would blank it."""
    p = pindai(berkas)
    for tag, atur in p.tag:
        for indo, inggris in PASANGAN:
            if indo not in atur or inggris is None:
                continue
            assert atur.get(inggris), (
                f"{nama(berkas)}: <{tag}> has {indo} but no {inggris}"
            )


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_judul_dan_keterangan_diterjemahkan(berkas):
    """What a search engine shows must switch too, not just the body."""
    isi = berkas.read_text(encoding="utf-8")
    judul = re.search(r"<title[^>]*>(.*?)</title>", isi, re.S)
    assert judul
    # a proper name reads the same in both languages and carries no attribute
    if judul.group(1).strip() != "Hendro Kuswantoro":
        assert re.search(r"<title[^>]*data-ind=", isi), f"{nama(berkas)}: title not translated"
    assert re.search(
        r'<meta[^>]+name="description"[^>]+data-ind=', isi
    ), f"{nama(berkas)}: meta description not translated"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_tombol_bahasa_ada(berkas):
    """Both buttons, on every page, or the switch is unreachable somewhere."""
    p = pindai(berkas)
    bahasa = sorted(
        atur.get("data-lang") for tag, atur in p.tag if atur.get("data-lang")
    )
    assert bahasa == ["en", "id"], f"{nama(berkas)}: language buttons are {bahasa}"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_tidak_ada_strip_panjang(berkas):
    """House style: no em dash, in either language."""
    isi = berkas.read_text(encoding="utf-8")
    assert "\u2014" not in isi, f"{nama(berkas)}: contains an em dash"
