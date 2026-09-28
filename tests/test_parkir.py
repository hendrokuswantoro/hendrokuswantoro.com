from __future__ import annotations

import re
import sys
from collections import Counter

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

import bangun_parkir  # noqa: E402
import parkir_rujukan as rujukan  # noqa: E402

PARKIR_JS = (AKAR / "assets" / "js" / "parkir.js").read_text(encoding="utf-8")
GAYA = (AKAR / "assets" / "css" / "style.css").read_text(encoding="utf-8")
HALAMAN = (AKAR / "parkir-jogja.html").read_text(encoding="utf-8")


def _kontras(a: str, b: str) -> float:
    def terang(h: str) -> float:
        h = h.lstrip("#")
        kanal = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in kanal]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    la, lb = sorted((terang(a), terang(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _warna(tema: str) -> dict:
    blok = re.search(tema + r': \{ I: "(#\w+)", II: "(#\w+)", aset: "(#\w+)", halo: "(#\w+)"', PARKIR_JS)
    assert blok, f"WARNA.{tema} tidak terbaca"
    return dict(zip(("I", "II", "aset", "halo"), blok.groups()))


def test_data_parkir_utuh():
    fitur = rujukan.KAWASAN["features"]
    assert len(fitur) == 495
    assert Counter(f["properties"]["k"] for f in fitur) == {"I": 27, "II": 468}
    assert "III" not in {f["properties"]["k"] for f in fitur}, "Kawasan III adalah sisa, tidak didaftar"
    assert len(rujukan.TARIF) == 77
    assert all(isinstance(t["tarif_2jam_pertama"], int) for t in rujukan.TARIF)


def test_ruas_usulan_ditandai():
    usulan = {f["properties"]["n"] for f in rujukan.KAWASAN["features"] if f["properties"]["u"] == 1}
    for sirip in ("Pajeksan", "Beskalan", "Reksobayan", "Perwakilan", "Suryatmajan"):
        assert any(sirip in n for n in usulan), f"sirip {sirip} tidak ditandai usulan"


def test_berkas_data_sama_dengan_sumbernya():
    tertulis = (AKAR / "assets" / "js" / "parkir-data.js").read_text(encoding="utf-8")
    assert tertulis == bangun_parkir.isi(), "jalankan python tools/bangun_parkir.py"


def test_rujukan_menolak_di_luar_kota():
    assert rujukan.cari_kawasan(-6.9175, 107.6191)["luar"], "Bandung diberi kawasan"
    assert rujukan.cari_kawasan(-8.3, 110.3)["luar"], "laut selatan diberi kawasan"
    assert rujukan.hitung_tarif("Sepeda motor", None, 1, "reguler") is None


def test_rujukan_malioboro_kawasan_satu_progresif():
    tempat = rujukan.cari_kawasan(-7.7925, 110.3656)
    assert tempat["kawasan"] == "I" and tempat["ruas"] == "Jalan Malioboro"
    mobil = "Sedan, jip, pickup, station wagon, kendaraan roda tiga"
    assert rujukan.hitung_tarif(mobil, "I", 4, "reguler") == 10000


@pytest.mark.parametrize("tema", ["terang", "gelap"])
def test_warna_kawasan_lolos_ambang_grafis_terhadap_halonya(tema):
    w = _warna(tema)
    for kunci in ("I", "II", "aset"):
        nilai = _kontras(w[kunci], w["halo"])
        assert nilai >= 3.0, f"{tema} {kunci} {w[kunci]} hanya {nilai:.2f}:1 terhadap halo"


@pytest.mark.parametrize("tema, awalan", [("terang", ".parkir {"), ("gelap", ':root[data-theme="dark"] .parkir {')])
def test_legenda_memakai_warna_yang_sama_dengan_peta(tema, awalan):
    w = _warna(tema)
    blok = GAYA.split(awalan, 1)[1].split("}", 1)[0]
    assert f"--parkir-satu: {w['I']};" in blok
    assert f"--parkir-dua: {w['II']};" in blok
    assert f"--parkir-aset: {w['aset']};" in blok


def test_tidak_ada_label_ilegal():
    rendah = PARKIR_JS.lower()
    for kata in ("ilegal", "illegal", "liar", "tidak resmi", "unofficial", "unlicensed"):
        assert kata not in rendah, f"peta parkir melabeli sesuatu {kata!r}"


def test_lapisan_parkir_masuk_lewat_gaya_bukan_tambal():
    assert "addLayer" not in PARKIR_JS
    assert "window.HK_PETA.gaya(" in PARKIR_JS, "peta parkir tidak memakai gaya peta karya"
    assert "setStyle(gaya, { diff: true })" in PARKIR_JS


def test_tidak_ada_token_atau_layanan_luar():
    assert "pk.eyJ" not in PARKIR_JS
    assert "nominatim" not in PARKIR_JS.lower(), "pencarian tempat mengirim ketikan pembaca ke luar"
    assert "mapbox://" not in PARKIR_JS


def test_halaman_menyediakan_peta_dan_jalannya():
    assert "data-parkir" in HALAMAN and "data-parkir-kanvas" in HALAMAN
    assert 'href="#coba"' in HALAMAN
    assert "bukan keputusan" in HALAMAN, "halaman tidak lagi menyebut peta ini panduan, bukan keputusan"
