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


def _peta_siap(halaman, situs) -> None:
    buka(halaman, situs, "/parkir-jogja")
    _siap(halaman)
    _tunggu(halaman, "() => Boolean(window.HK_PARKIR_MAP)"
                     " && Boolean(document.querySelector('.parkir .peta__frame.is-ready'))")


def _filter_tetap(halaman) -> str:
    return halaman.evaluate(
        "() => JSON.stringify(window.HK_PARKIR_MAP.getStyle().layers"
        ".find(l => l.id === 'parkir-tetap').filter)"
    )


def test_legenda_bisa_ditutup_dibuka_dan_menyaring_peta(halaman, situs):
    halaman.set_viewport_size({"width": 1024, "height": 768})
    _peta_siap(halaman, situs)
    isi = halaman.locator(".parkir__legenda-isi")
    tombol = halaman.locator(".parkir__legenda-tombol")
    assert isi.is_hidden() and tombol.is_visible(), "legenda terbuka sendiri di layar 1024"

    tombol.click()
    assert isi.is_visible() and tombol.is_hidden()

    dua = halaman.locator('.parkir__lapis[data-lapis="II"]')
    assert dua.get_attribute("aria-pressed") == "true"
    assert '"II"' in _filter_tetap(halaman)
    dua.click()
    assert dua.get_attribute("aria-pressed") == "false"
    _tunggu(halaman, "() => !JSON.stringify(window.HK_PARKIR_MAP.getStyle().layers"
                     ".find(l => l.id === 'parkir-tetap').filter).includes('\"II\"')", 8000)
    assert '"I"' in _filter_tetap(halaman), "menyembunyikan Kawasan II ikut menyembunyikan Kawasan I"

    aset = halaman.locator('.parkir__lapis[data-lapis="aset"]')
    aset.click()
    _tunggu(halaman, "() => window.HK_PARKIR_MAP.getLayoutProperty('parkir-aset', 'visibility') === 'none'", 8000)

    halaman.locator(".parkir__legenda-tutup").click()
    assert isi.is_hidden() and tombol.is_visible()
    halaman.reload(wait_until="load")
    _siap(halaman)
    assert halaman.locator(".parkir__legenda-isi").is_hidden(), "pilihan menutup legenda tidak diingat"


def test_legenda_di_layar_lebar_terbuka_dan_tidak_ada_yang_dilabeli_ilegal(halaman, situs):
    halaman.set_viewport_size({"width": 1440, "height": 900})
    _peta_siap(halaman, situs)
    assert halaman.locator(".parkir__legenda-isi").is_visible()
    teks = halaman.locator(".parkir__legenda-isi").inner_text().lower()
    for kata in ("ilegal", "illegal", "liar"):
        assert kata not in teks


def test_pilihan_tarif_bisa_diringkas(halaman, situs):
    _peta_siap(halaman, situs)
    lipat = halaman.locator(".parkir__lipat")
    assert lipat.get_attribute("aria-expanded") == "true"
    assert halaman.locator(".parkir__atur").is_visible()
    lipat.click()
    assert lipat.get_attribute("aria-expanded") == "false"
    assert halaman.locator(".parkir__atur").is_hidden()
    assert "Rp" in halaman.locator(".parkir__harga").inner_text(), "ringkasan kehilangan tarifnya"
    lipat.click()
    assert halaman.locator(".parkir__atur").is_visible()


def test_mengetuk_peta_memindahkan_pin_ke_sana(halaman, situs):
    _peta_siap(halaman, situs)
    sebelum = halaman.evaluate("() => window.HK_PARKIR_MAP.getCenter().toArray()")
    kotak = halaman.locator(".parkir .peta__frame").bounding_box()
    halaman.mouse.click(kotak["x"] + kotak["width"] - 160, kotak["y"] + 140)
    _tunggu(halaman, f"() => Math.abs(window.HK_PARKIR_MAP.getCenter().lng - {sebelum[0]}) > 0.0005", 6000)


def test_ruas_terpilih_menunjuk_parkir_aset_terdekat(halaman, situs):
    _peta_siap(halaman, situs)
    terdekat = halaman.locator(".parkir__terdekat")
    assert terdekat.is_visible(), "Malioboro jauh dari parkir aset provinsi?"
    assert terdekat.locator("strong").inner_text().strip()
    halaman.evaluate("() => window.HK_PARKIR_MAP.jumpTo({ center: [110.33, -7.90], zoom: 14 })")
    _tunggu(halaman, "() => document.querySelector('.parkir__kartu').dataset.kawasan === 'luar'", 10000)
    assert terdekat.is_hidden(), "di luar kota tetap menawarkan parkir aset"


@pytest.mark.parametrize("lebar, tinggi", [(320, 640), (375, 812), (768, 1024), (1024, 768), (1440, 900)])
def test_aplikasi_parkir_muat_di_setiap_layar(peramban, situs, lebar, tinggi):
    konteks = peramban.new_context(viewport={"width": lebar, "height": tinggi}, has_touch=lebar < 860)
    halaman = konteks.new_page()
    galat = []
    halaman.on("pageerror", lambda e: galat.append(str(e)))
    try:
        buka(halaman, situs, "/parkir-jogja")
        _siap(halaman)
        _tunggu(halaman, "() => Boolean(document.querySelector('.parkir .peta__frame.is-ready'))")
        ukur = halaman.evaluate("""() => {
          const kotak = (s) => document.querySelector(s).getBoundingClientRect();
          const f = kotak('.parkir .peta__frame'), k = kotak('.parkir__kartu'), c = kotak('.parkir__cari');
          const l = kotak('.parkir__legenda-kotak');
          return {
            geser: document.documentElement.scrollWidth - innerWidth,
            frame: [f.left, f.right, f.top, f.bottom], kartu: [k.left, k.right],
            cari: [c.left, c.right, c.top, c.bottom], legenda: [l.left, l.right, l.top, l.bottom],
            tinggi: f.height
          };
        }""")
        assert ukur["geser"] <= 0, f"halaman bergeser mendatar {ukur['geser']} piksel di {lebar}"
        f = ukur["frame"]
        assert ukur["kartu"][0] >= 0 and ukur["kartu"][1] <= lebar, f"kartu keluar layar: {ukur}"
        for nama in ("cari", "legenda"):
            b = ukur[nama]
            assert b[0] >= f[0] and b[1] <= f[1] and b[2] >= f[2] and b[3] <= f[3], f"{nama} keluar dari peta: {ukur}"
        assert ukur["tinggi"] >= 360, f"peta terlalu pendek di {lebar}: {ukur['tinggi']}"
        assert not galat, galat
    finally:
        konteks.close()
