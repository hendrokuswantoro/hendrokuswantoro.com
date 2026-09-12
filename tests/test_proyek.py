"""Proyek: satu sumber kebenaran, dijaga supaya tidak bercabang.

content/proyek/*.md sekarang memegang datanya. Sampai project.html dan
peta.js ikut dibangkitkan, keduanya masih ditulis tangan, jadi ada tiga
salinan data yang sama. Uji di berkas ini yang menahan ketiganya tetap
identik.

Tanpa uji ini, menyunting judul di satu tempat dan lupa di dua tempat lain
adalah kesalahan yang tidak akan pernah terlihat sampai seseorang
membandingkan halaman dengan petanya sendiri.
"""

from __future__ import annotations

import html
import re
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

from isi import SumberBerkas  # noqa: E402

PROYEK = SumberBerkas(AKAR / "content").proyek()
HTML = (AKAR / "project.html").read_text(encoding="utf-8")
PETA = (AKAR / "assets" / "js" / "peta.js").read_text(encoding="utf-8")

KATEGORI_SAH = {"app", "analysis", "satellite", "design"}


def rapikan(teks: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", teks)).strip()


def test_tujuh_proyek():
    assert len(PROYEK) == 7, f"ada {len(PROYEK)} proyek, bukan 7"


def test_slug_unik_dan_urut_rapat():
    slug = [p.slug for p in PROYEK]
    assert len(set(slug)) == len(slug), "slug proyek kembar"
    assert [p.urut for p in PROYEK] == list(range(1, len(PROYEK) + 1))


@pytest.mark.parametrize("p", PROYEK, ids=lambda p: p.slug)
def test_kategori_dikenal(p):
    asing = set(p.kategori) - KATEGORI_SAH
    assert not asing, f"{p.slug}: kategori tidak dikenal {asing}"
    assert p.jenis_peta in KATEGORI_SAH


@pytest.mark.parametrize("p", PROYEK, ids=lambda p: p.slug)
def test_gambar_ada(p):
    assert (AKAR / p.gambar.lstrip("/")).exists(), f"{p.slug}: {p.gambar} tidak ada"


@pytest.mark.parametrize("p", PROYEK, ids=lambda p: p.slug)
def test_kartu_di_halaman_sama_dengan_isi(p):
    kartu = re.search(
        r'<article class="card reveal" id="karya-%s" data-category="([^"]+)">(.*?)</article>'
        % re.escape(p.slug), HTML, re.S)
    assert kartu, f"{p.slug}: tidak ada kartunya di project.html"

    assert set(kartu.group(1).split()) == set(p.kategori), (
        f"{p.slug}: kategori di halaman {kartu.group(1)!r} lawan isi {p.kategori}"
    )

    dalam = kartu.group(2)
    judul = re.search(r'<h2 data-ind="([^"]*)">(.*?)</h2>', dalam, re.S)
    assert rapikan(judul.group(2)) == p.judul.en, f"{p.slug}: judul Inggris berbeda"
    assert html.unescape(judul.group(1)) == p.judul.id, f"{p.slug}: judul Indonesia berbeda"

    ringkas = re.search(r'<p data-ind="([^"]*)">(.*?)</p>', dalam, re.S)
    assert rapikan(ringkas.group(2)) == p.ringkas.en, f"{p.slug}: ringkasan Inggris berbeda"

    tag = re.findall(r'<li class="tag">([^<]*)</li>', dalam)
    assert tuple(tag) == p.teknologi, f"{p.slug}: daftar teknologi berbeda"

    assert p.gambar in dalam, f"{p.slug}: gambar di halaman berbeda"


@pytest.mark.parametrize("p", PROYEK, ids=lambda p: p.slug)
def test_titik_peta_sama_dengan_isi(p):
    titik = re.search(
        r'\{\s*id:\s*"%s",\s*kind:\s*"([^"]+)",\s*lng:\s*(-?[\d.]+),\s*lat:\s*(-?[\d.]+),\s*'
        r'en:\s*"([^"]*)",\s*ind:\s*"([^"]*)"' % re.escape(p.slug), PETA, re.S)
    assert titik, f"{p.slug}: tidak ada titiknya di peta.js"

    assert titik.group(1) == p.jenis_peta, f"{p.slug}: jenis penanda berbeda"
    assert float(titik.group(2)) == p.lng, f"{p.slug}: bujur berbeda"
    assert float(titik.group(3)) == p.lat, f"{p.slug}: lintang berbeda"
    assert titik.group(4) == p.judul.en, f"{p.slug}: judul Inggris di peta berbeda"
    assert titik.group(5) == p.judul.id, f"{p.slug}: judul Indonesia di peta berbeda"


def test_tidak_ada_proyek_yatim():
    """Kartu di halaman yang tidak punya berkas isinya, atau sebaliknya."""
    di_halaman = set(re.findall(r'id="karya-([a-z0-9-]+)"', HTML))
    di_isi = {p.slug for p in PROYEK}
    assert di_halaman == di_isi, (
        f"hanya di halaman: {sorted(di_halaman - di_isi)}\n"
        f"hanya di isi    : {sorted(di_isi - di_halaman)}"
    )
