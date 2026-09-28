from __future__ import annotations

import itertools
import json
import pathlib
import shutil
import subprocess

import pytest

import parkir_rujukan as rujukan
from konftes import AKAR

NEXT = AKAR / "next"
TS = NEXT / "node_modules" / "typescript"
HITUNG = NEXT / "components" / "peta" / "parkir-hitung.ts"
PETA_TS = (NEXT / "components" / "peta" / "parkir.ts").read_text(encoding="utf-8")
PARKIR_JS = (AKAR / "assets" / "js" / "parkir.js").read_text(encoding="utf-8")


def _node() -> str | None:
    ada = shutil.which("node")
    if ada:
        return ada
    windows = pathlib.Path("C:/Program Files/nodejs/node.exe")
    return str(windows) if windows.exists() else None


def _titik() -> list[tuple[float, float]]:
    kisi = [
        (-7.84 + i * 0.1 / 24, 110.30 + j * 0.13 / 24)
        for i, j in itertools.product(range(25), range(25))
    ]
    ruas = [
        (c[1] + 0.00008, c[0] - 0.00005)
        for f in rujukan.KAWASAN["features"][::7]
        for c in f["geometry"]["coordinates"][:1]
    ]
    luar = [(-6.9175, 107.6191), (-8.3, 110.3), (-7.90, 110.33), (-7.70, 110.50)]
    return kisi + ruas + luar


def _kombinasi() -> list[tuple]:
    kendaraan = sorted({t["kendaraan"] for t in rujukan.TARIF})
    return [
        (k, w, j, lay)
        for k in kendaraan
        for w in ("I", "II", "III", None)
        for j in (1, 2, 3, 5, 8)
        for lay in ("reguler", "insidental", "pasar")
    ]


@pytest.mark.skipif(_node() is None or not TS.exists(), reason="node atau typescript port Next belum terpasang")
def test_rumus_port_next_sepakat_dengan_rujukan():
    titik, kombinasi = _titik(), _kombinasi()
    jalan = subprocess.run(
        [_node(), str(AKAR / "tests" / "parkir_next.cjs"), str(TS), str(HITUNG),
         str(NEXT / "content" / "parkir-data.json")],
        input=json.dumps({"titik": titik, "kombinasi": kombinasi}),
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert jalan.returncode == 0, jalan.stderr
    hasil = json.loads(jalan.stdout)

    beda_kawasan = [
        ((lat, lon), r, ts)
        for (lat, lon), ts in zip(titik, hasil["kawasan"])
        if [(r := rujukan.cari_kawasan(lat, lon))["kawasan"], r["ruas"], r["luar"]] != ts
    ]
    beda_tarif = [
        (kom, rujukan.hitung_tarif(*kom), ts)
        for kom, ts in zip(kombinasi, hasil["tarif"])
        if rujukan.hitung_tarif(*kom) != ts
    ]
    assert len(titik) > 650 and len(kombinasi) == 660
    assert not beda_kawasan, f"{len(beda_kawasan)} titik berbeda, contoh: {beda_kawasan[:3]}"
    assert not beda_tarif, f"{len(beda_tarif)} kombinasi berbeda, contoh: {beda_tarif[:3]}"


def test_warna_dan_ambang_sama_dengan_situs_terbit():
    import re

    for pola in (r'terang: \{[^}]*\}', r'gelap: \{[^}]*\}'):
        js = re.search(pola, PARKIR_JS).group(0)
        ts = re.search(pola, PETA_TS).group(0)
        assert js == ts, f"warna port Next berbeda:\n{js}\n{ts}"
    assert "AMBANG_M = 30" in (NEXT / "components" / "peta" / "parkir-hitung.ts").read_text(encoding="utf-8")


def test_teks_aplikasi_sama_dengan_situs_terbit():
    import re

    pasangan = re.findall(r'\{ en: ("[^"]*"), ind: ("[^"]*") \}', PARKIR_JS)
    assert len(pasangan) > 40
    hilang = [p for p in pasangan if f"en: {p[0]}, ind: {p[1]}" not in PETA_TS]
    assert not hilang, f"teks port Next tertinggal: {hilang[:5]}"


def test_port_next_memegang_kaidah_yang_sama():
    assert "addLayer" not in PETA_TS
    assert "setStyle(gaya, { diff: true })" in PETA_TS
    assert "nominatim" not in PETA_TS.lower()
    rendah = PETA_TS.lower()
    for kata in ("ilegal", "illegal", "liar", "tidak resmi", "unofficial", "unlicensed"):
        assert kata not in rendah


def test_gambar_yang_dirujuk_port_next_ada_di_publiknya():
    import re

    rujukan_gambar = set()
    for berkas in list((NEXT / "components").rglob("*.tsx")) + list((NEXT / "content").glob("*.ts")):
        rujukan_gambar.update(re.findall(r"(/assets/img/[\w./-]+\.(?:webp|png|jpg|svg))", berkas.read_text(encoding="utf-8")))
    assert rujukan_gambar
    hilang = sorted(g for g in rujukan_gambar if not (NEXT / "public" / g.lstrip("/")).exists())
    assert not hilang, f"port Next merujuk gambar yang tidak ada di next/public: {hilang}"


def test_pekerja_maplibre_port_next_ada_dan_sama_versinya():
    import json

    versi = json.loads((NEXT / "package.json").read_text(encoding="utf-8"))["dependencies"]["maplibre-gl"]
    assert versi[0].isdigit(), f"maplibre-gl di port Next harus terkunci persis, bukan {versi}"
    pustaka = (NEXT / "components" / "peta" / "pustaka.ts").read_text(encoding="utf-8")
    assert f"/assets/vendor/maplibre/{versi}/maplibre-gl-worker.mjs" in pustaka
    for nama in ("maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"):
        salinan = NEXT / "public" / "assets" / "vendor" / "maplibre" / versi / nama
        asli = AKAR / "assets" / "vendor" / "maplibre" / versi / nama
        assert salinan.exists(), f"{nama} tidak ada di next/public, peta port Next tidak akan pernah memuat ubin"
        assert salinan.read_bytes() == asli.read_bytes(), f"{nama} di port Next berbeda dari salinan situs"
    for komponen in ("WorkMap.tsx", "ParkirMap.tsx"):
        isi = (NEXT / "components" / komponen).read_text(encoding="utf-8")
        assert "pustakaPeta()" in isi and 'import("maplibre-gl")' not in isi, (
            f"{komponen} memuat MapLibre tanpa menyetel alamat pekerjanya"
        )
