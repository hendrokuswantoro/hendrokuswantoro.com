"""The two ports of the map must not drift apart.

The static site and the Next.js port each carry their own copy of the style.
Nobody notices a difference between them until someone opens the port a year
from now and finds a map that lost half its layers. These tests hold the two
copies to the same shape, and they hold the token out of the repository.
"""

from __future__ import annotations

import re

from konftes import AKAR

PETA = (AKAR / "assets" / "js" / "peta.js").read_text(encoding="utf-8")
PORT = (AKAR / "next" / "components" / "WorkMap.tsx").read_text(encoding="utf-8")


def lapisan(sumber: str, awal: str, akhir: str) -> list[str]:
    i = sumber.index(awal)
    j = sumber.index(akhir, i)
    return re.findall(r'id: "([a-z0-9-]+)"', sumber[i:j])


STATIS = lapisan(PETA, "      layers: [", "\n      ]\n    };\n  }")
NEXTJS = lapisan(PORT, "    layers: [", "  } as StyleSpecification;")


def test_jumlah_lapisan_masuk_akal():
    assert len(STATIS) >= 30, f"the style lost layers, now {len(STATIS)}"


def test_urutan_lapisan_sama():
    """Order is not cosmetic. MapLibre places symbols from the top of the
    stack downwards, so a reordering silently changes which labels win."""
    assert STATIS == NEXTJS, (
        "the two ports disagree.\n"
        f"  only static: {[x for x in STATIS if x not in NEXTJS]}\n"
        f"  only next  : {[x for x in NEXTJS if x not in STATIS]}"
    )


def test_lapisan_nama_benar_benar_ada():
    """LAYER_NAMA drives the language switch. An id listed there that does
    not exist in the style means one layer stops switching language, and
    nothing raises."""
    blok = re.search(r"var LAYER_NAMA = \[(.*?)\];", PETA, re.S)
    assert blok, "LAYER_NAMA is gone"
    for id_ in re.findall(r'"([a-z0-9-]+)"', blok.group(1)):
        assert id_ in STATIS, f"LAYER_NAMA names {id_}, which the style does not draw"


def test_setiap_lapisan_nama_ikut_saklar_bahasa():
    """The other direction: a label layer missing from LAYER_NAMA keeps its
    first language forever."""
    blok = re.search(r"var LAYER_NAMA = \[(.*?)\];", PETA, re.S)
    terdaftar = set(re.findall(r'"([a-z0-9-]+)"', blok.group(1)))
    for id_ in STATIS:
        if id_.startswith("nama-"):
            assert id_ in terdaftar, f"{id_} draws names but never switches language"


def test_provinsi_lengkap():
    """Thirty eight, the number of provinces Indonesia has. Mapbox carries no
    state labels here, so the site carries them itself."""
    for sumber, label in ((PETA, "peta.js"), (PORT, "WorkMap.tsx")):
        blok = re.search(r"PROVINSI_ID = \{(.*?)\n  \};", sumber, re.S) or re.search(
            r"PROVINSI_ID = \{(.*?)\n\};", sumber, re.S
        )
        assert blok, f"{label}: PROVINSI_ID is gone"
        baris = re.findall(r'\["([^"]+)", "([^"]+)", (-?\d+\.?\d*), (-?\d+\.?\d*)\]', blok.group(1))
        assert len(baris) == 38, f"{label}: {len(baris)} provinces, expected 38"
        for indo, inggris, bujur, lintang in baris:
            assert 94 <= float(bujur) <= 142, f"{label}: {indo} sits outside Indonesia"
            assert -12 <= float(lintang) <= 7, f"{label}: {indo} sits outside Indonesia"


def test_nama_provinsi_sama_di_kedua_port():
    def daftar(sumber: str) -> list[str]:
        blok = re.search(r"PROVINSI_ID = \{(.*?)\n\s*\};", sumber, re.S)
        return re.findall(r'\["([^"]+)", "[^"]+", -?\d', blok.group(1))

    assert daftar(PETA) == daftar(PORT), "the province lists differ between ports"


def test_token_tidak_pernah_ikut():
    """A public Mapbox token is still a credential the repository must not
    carry. konfigurasi.js is written at build time and is gitignore'd."""
    abaikan = {"dist", "node_modules", ".git", ".next"}
    for berkas in AKAR.rglob("*"):
        if not berkas.is_file() or abaikan & set(berkas.parts):
            continue
        if berkas.name == "konfigurasi.js" or berkas.suffix in {".zip", ".png", ".webp", ".svg", ".ico"}:
            continue
        try:
            isi = berkas.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        assert not re.search(r"\bpk\.eyJ[A-Za-z0-9]", isi), f"{berkas} carries a Mapbox token"


def test_konfigurasi_diabaikan_git():
    abaikan = (AKAR / ".gitignore").read_text(encoding="utf-8")
    assert "assets/js/konfigurasi.js" in abaikan


def test_maplibre_terkunci():
    """The vendored library is the one piece of third party code that reaches
    a visitor. It carries GHSA-jrc7-96c5-q579, a critical sanitizer bypass
    that is unfixed below 6.4.1 and cannot be fixed by swapping the file,
    because MapLibre 6 ships ESM only. See docs/keamanan.md.

    This test does not pretend the advisory is handled. It makes sure the
    version in the file, the version pinned beside it, and the version the
    Next.js port asks for cannot drift apart, so nobody upgrades one and
    believes all three moved.
    """
    versi = (AKAR / "assets" / "vendor" / "maplibre" / "VERSI").read_text(encoding="utf-8").strip()

    pustaka = (AKAR / "assets" / "vendor" / "maplibre" / "maplibre-gl.js").read_text(
        encoding="utf-8", errors="ignore"
    )[:2000]
    assert f"/v{versi}/" in pustaka, f"the vendored file is not {versi}"

    paket = (AKAR / "next" / "package.json").read_text(encoding="utf-8")
    mayor = versi.split(".")[0]
    assert f'"maplibre-gl": "^{mayor}.' in paket, (
        f"the Next.js port asks for a different major than the vendored {versi}"
    )


def test_csp_menahan_muatan_sanitizer():
    """The CSP is what stops GHSA-jrc7-96c5-q579 from executing: an inline
    event handler needs 'unsafe-inline' in script-src, and there is none.
    Adding it would quietly turn an unexploitable advisory into a live one."""
    headers = (AKAR / "_headers").read_text(encoding="utf-8")
    csp = [b for b in headers.splitlines() if "Content-Security-Policy:" in b][0]
    naskah = [b for b in csp.split(";") if "script-src" in b][0]
    assert "unsafe-inline" not in naskah, (
        "script-src accepted unsafe-inline, which un-mitigates the MapLibre "
        "sanitizer bypass. See docs/keamanan.md."
    )
