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
    """Token Mapbox publik tetap kredensial, dan repositori tidak boleh
    membawanya. konfigurasi.js ditulis saat build dan ada di .gitignore.

    `.env` dikecualikan, dan pengecualian itu ada sebabnya yang mahal. Aturan
    lama melarang tokennya ada di sana juga, jadi satu satunya salinan di
    mesin pengembangan hidup di konfigurasi.js, berkas yang ditimpa tiap kali
    `tools/bangun_situs.sh` dijalankan. Tokennya hilang begitu saja, dan yang
    memberitahu bukan pesan galat melainkan empat uji peta yang gagal dengan
    alasan yang menuduh kodenya. Lihat docs/pemecahan-masalah.md.

    `.env` justru tempat yang benar: ia ada di .gitignore, seluruh alat di
    repositori ini membacanya, dan tidak ada satu pun jalan ia ikut git.
    Yang dijaga uji ini adalah berkas yang BISA ikut git.
    """
    abaikan = {"dist", "node_modules", ".git", ".next", "out"}
    for berkas in AKAR.rglob("*"):
        if not berkas.is_file() or abaikan & set(berkas.parts):
            continue
        if berkas.name in {"konfigurasi.js", ".env"}:
            continue
        if berkas.suffix in {".zip", ".png", ".webp", ".svg", ".ico"}:
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
    """MapLibre adalah satu satunya kode pihak ketiga yang sampai ke
    pengunjung. Versinya dikunci di satu berkas supaya berkas pustaka, angka
    yang dicatat, dan yang diminta port Next.js tidak bisa berpisah jalan.

    Sejak 6.x pustakanya terbit sebagai ES module dan terpecah empat berkas.
    Keempatnya wajib ada: tanpa maplibre-gl-worker.mjs peta memuat gayanya
    lalu diam selamanya, tanpa galat apa pun.
    """
    dasar = AKAR / "assets" / "vendor" / "maplibre"
    versi = (dasar / "VERSI").read_text(encoding="utf-8").strip()
    # Berkasnya duduk di dalam folder bernama versinya, bukan di samping
    # VERSI. Alasannya di tools/versi_aset.py: maplibre-gl.mjs mengimpor
    # maplibre-gl-shared.mjs secara relatif, jadi query pada modul induk
    # tidak menurun ke anaknya, dan anak yang basi sama merusaknya.
    rumah = dasar / versi

    for nama in ("maplibre-gl.mjs", "maplibre-gl-shared.mjs",
                 "maplibre-gl-worker.mjs", "maplibre-gl.css"):
        assert (rumah / nama).exists(), f"{nama} hilang dari assets/vendor/maplibre"

    kepala = (rumah / "maplibre-gl.mjs").read_text(encoding="utf-8", errors="ignore")[:600]
    assert f"/v{versi}/" in kepala, f"berkas pustaka bukan versi {versi}"

    assert not (rumah / "maplibre-gl.js").exists() and not (dasar / "maplibre-gl.js").exists(), (
        "bundel UMD lama masih ada, dan versinya membawa GHSA-jrc7-96c5-q579"
    )

    paket = (AKAR / "next" / "package.json").read_text(encoding="utf-8")
    mayor = versi.split(".")[0]
    assert f'"maplibre-gl": "^{mayor}.' in paket, (
        f"port Next.js meminta mayor yang berbeda dari {versi} yang dibawa"
    )


def test_versi_maplibre_sudah_di_atas_ghsa():
    """GHSA-jrc7-96c5-q579 baru diperbaiki di 6.4.1. Turun di bawahnya berarti
    membawa kembali celah sanitizer yang sudah ditutup."""
    versi = (AKAR / "assets" / "vendor" / "maplibre" / "VERSI").read_text(
        encoding="utf-8").strip()
    angka = tuple(int(x) for x in versi.split("."))
    assert angka >= (6, 4, 1), f"MapLibre {versi} masih terdampak GHSA-jrc7-96c5-q579"


def test_worker_boleh_dari_origin_sendiri():
    """MapLibre 6 memuat workernya sebagai modul dari origin ini lewat
    import.meta.url. Dengan worker-src blob: saja, peta memuat gayanya lalu
    diam tanpa satu pun permintaan ubin dan tanpa galat."""
    headers = (AKAR / "_headers").read_text(encoding="utf-8")
    csp = [b for b in headers.splitlines() if "Content-Security-Policy:" in b][0]
    worker = [b for b in csp.split(";") if "worker-src" in b][0]
    assert "'self'" in worker, "worker-src menolak origin sendiri, peta akan diam"


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
