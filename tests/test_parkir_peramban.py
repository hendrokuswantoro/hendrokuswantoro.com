from __future__ import annotations

import itertools
import time

import pytest

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

import parkir_rujukan as rujukan  # noqa: E402
from conftest import buka  # noqa: E402


def _tunggu(halaman, ungkapan: str, batas_ms: int = 45000) -> None:
    akhir = time.monotonic() + batas_ms / 1000
    while time.monotonic() < akhir:
        if halaman.evaluate(ungkapan):
            return
        halaman.wait_for_timeout(200)
    raise AssertionError(f"tidak pernah terpenuhi: {ungkapan}")


def _siap(halaman) -> None:
    halaman.locator("[data-parkir]").scroll_into_view_if_needed()
    _tunggu(halaman, "() => Boolean(window.HK_PARKIR && window.HK_PARKIR_DATA)")


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


def test_kawasan_di_peramban_sepakat_dengan_rujukan(halaman, situs):
    buka(halaman, situs, "/parkir-jogja")
    _siap(halaman)
    titik = _titik()
    js = halaman.evaluate(
        "(t) => t.map(([lat, lon]) => { const r = window.HK_PARKIR.cariKawasan(lat, lon);"
        " return [r.kawasan, r.ruas, r.luar]; })",
        titik,
    )
    beda = []
    for (lat, lon), dari_js in zip(titik, js):
        r = rujukan.cari_kawasan(lat, lon)
        if [r["kawasan"], r["ruas"], r["luar"]] != dari_js:
            beda.append(((lat, lon), r, dari_js))
    assert len(titik) > 650
    assert not beda, f"{len(beda)} titik berbeda, contoh: {beda[:3]}"
    assert sum(1 for x in js if x[2]) >= 4, "tidak ada titik di luar cakupan yang diuji"
    assert sum(1 for x in js if x[0] == "I") > 0 and sum(1 for x in js if x[0] == "III") > 0


def test_tarif_di_peramban_sepakat_dengan_rujukan(halaman, situs):
    buka(halaman, situs, "/parkir-jogja")
    _siap(halaman)
    kendaraan = sorted({t["kendaraan"] for t in rujukan.TARIF})
    kombinasi = [
        (k, w, j, lay)
        for k in kendaraan
        for w in ("I", "II", "III", None)
        for j in (1, 2, 3, 5, 8)
        for lay in ("reguler", "insidental", "pasar")
    ]
    js = halaman.evaluate(
        "(k) => k.map(([a, b, c, d]) => { const h = window.HK_PARKIR.hitungTarif(a, b, c, d);"
        " return h ? h.total : null; })",
        kombinasi,
    )
    beda = [
        (kom, rujukan.hitung_tarif(*kom), hasil)
        for kom, hasil in zip(kombinasi, js)
        if rujukan.hitung_tarif(*kom) != hasil
    ]
    assert len(kombinasi) == 660
    assert not beda, f"{len(beda)} kombinasi berbeda, contoh: {beda[:3]}"


def test_kartu_menolak_memberi_angka_di_luar_kota(halaman, situs):
    buka(halaman, situs, "/parkir-jogja")
    _siap(halaman)
    _tunggu(halaman, "() => Boolean(window.HK_PARKIR_MAP)")
    halaman.evaluate("() => window.HK_PARKIR_MAP.jumpTo({ center: [110.33, -7.90], zoom: 14 })")
    _tunggu(halaman, "() => document.querySelector('.parkir__kartu').dataset.kawasan === 'luar'", 10000)
    harga = halaman.locator(".parkir__harga").inner_text()
    assert "Rp" not in harga, f"di luar cakupan tetap ada angka: {harga!r}"
