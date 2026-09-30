from __future__ import annotations

import json

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

from conftest import buka
from test_peramban import peta_siap

ANGGARAN = {
    "/":                      (210, 12),
    "/about":                 (150, 10),
    "/blog/":                 (150, 10),
    "/blog/kapan-peta-diam":  (150, 10),
    "/project":              (2200, 32),
}

HALAMAN = list(ANGGARAN)


def ukur(halaman, situs: str, jalur: str) -> dict:
    berkas: list[dict] = []
    halaman.on("response", lambda r: berkas.append({
        "url": r.url, "jenis": r.request.resource_type,
    }))
    buka(halaman, situs, jalur)

    if halaman.locator("[data-peta]").count():
        peta_siap(halaman)

    ukuran = halaman.evaluate("""() => {
        const e = performance.getEntriesByType('resource');
        const nav = performance.getEntriesByType('navigation')[0] || {};
        const berat = x => x.transferSize || x.encodedBodySize || 0;
        const jumlah = e.reduce((n, x) => n + berat(x), 0);
        const sendiri = e.filter(x => x.name.startsWith(location.origin));
        return {
            bytes: jumlah + (nav.transferSize || 0),
            bytesSendiri: sendiri.reduce((n, x) => n + berat(x), 0) + (nav.transferSize || 0),
            permintaan: e.length + 1,
            permintaanSendiri: sendiri.length + 1,
            domSiap: Math.round(nav.domContentLoadedEventEnd || 0),
            muatSelesai: Math.round(nav.loadEventEnd || 0),
            terbesar: e.map(x => ({
                nama: x.name.split('/').pop().slice(0, 40),
                kb: Math.round((x.transferSize || x.encodedBodySize || 0) / 1024),
            })).sort((a, b) => b.kb - a.kb).slice(0, 3),
        };
    }""")
    ukuran["luar"] = sorted({
        b["url"].split("/")[2] for b in berkas
        if not b["url"].startswith(situs) and b["url"].startswith("http")
    })
    return ukuran


@pytest.mark.parametrize("jalur", HALAMAN)
def test_anggaran_halaman(halaman, situs, jalur):
    hasil = ukur(halaman, situs, jalur)
    kb = round(hasil["bytesSendiri"] / 1024)
    semua_kb = round(hasil["bytes"] / 1024)

    print(f"\n  {jalur:28} {kb:5} KB  {hasil['permintaanSendiri']:3} permintaan"
          f"   (seluruhnya {semua_kb} KB, {hasil['permintaan']} permintaan)"
          f"  DOM {hasil['domSiap']} ms")
    for b in hasil["terbesar"]:
        print(f"      {b['kb']:5} KB  {b['nama']}")

    batas_kb, batas_permintaan = ANGGARAN[jalur]
    assert kb <= batas_kb, (
        f"{jalur} membengkak jadi {kb} KB dari asal sendiri, anggaran {batas_kb} KB.\n"
        f"terbesar: {json.dumps(hasil['terbesar'])}"
    )
    assert hasil["permintaanSendiri"] <= batas_permintaan, (
        f"{jalur} meminta {hasil['permintaanSendiri']} berkas dari asal sendiri, "
        f"anggaran {batas_permintaan}"
    )


def test_tidak_ada_pihak_ketiga_sama_sekali(halaman, situs):
    for jalur in ("/", "/about", "/blog/kapan-peta-diam"):
        hasil = ukur(halaman, situs, jalur)
        assert not hasil["luar"], (
            f"{jalur} meminta berkas dari luar: {hasil['luar']}"
        )


@pytest.mark.parametrize("jalur", ["/", "/about", "/blog/", "/blog/kapan-peta-diam"])
def test_maplibre_hanya_diunduh_di_halaman_yang_berpeta(halaman, situs, jalur):
    buka(halaman, situs, jalur)
    jumlah = halaman.evaluate(
        "() => performance.getEntriesByType('resource')"
        ".filter(e => e.name.includes('maplibre')).length"
    )
    assert jumlah == 0, f"{jalur} mengunduh MapLibre padahal tidak punya peta"


def test_peta_memang_dimuat_di_halaman_proyek(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    jumlah = halaman.evaluate(
        "() => performance.getEntriesByType('resource')"
        ".filter(e => e.name.includes('maplibre')).length"
    )
    assert jumlah >= 3, f"MapLibre kurang lengkap, cuma {jumlah} berkas"


def test_gambar_karya_semuanya_webp_dan_dimuat_malas():
    proyek = (AKAR / "project.html").read_text(encoding="utf-8")
    import re

    for tag in re.findall(r"<img\b[^>]*>", proyek):
        sumber = re.search(r'src="([^"?]+)', tag)
        assert sumber and sumber.group(1).endswith(".webp"), f"bukan webp: {tag[:70]}"
        assert 'loading="lazy"' in tag, f"tidak dimuat malas: {tag[:70]}"
        assert re.search(r'width="\d+"', tag) and re.search(r'height="\d+"', tag), (
            f"tanpa ukuran, halaman akan melompat saat gambarnya datang: {tag[:70]}"
        )


@pytest.mark.parametrize("berkas", ["index.html", "project.html"])
def test_gambar_karya_punya_tiga_lebar(berkas):
    import re

    teks = (AKAR / berkas).read_text(encoding="utf-8")
    tag_karya = [t for t in re.findall(r"<img\b[^>]*>", teks) if "/img/work/" in t]
    assert tag_karya, f"tidak ada gambar karya di {berkas}"

    for tag in tag_karya:
        assert 'srcset="' in tag, f"tanpa srcset: {tag[:80]}"
        assert 'sizes="' in tag, f"srcset tanpa sizes tidak menghemat apa pun: {tag[:80]}"
        lebar = sorted(int(x) for x in re.findall(r"(\d+)w", tag))
        assert lebar == [400, 600, 800], f"lebar yang ditawarkan {lebar}: {tag[:80]}"
        for jalur in re.findall(r"(/assets/img/work/[a-z0-9-]+\.webp)", tag):
            assert (AKAR / jalur.lstrip("/")).exists(), f"berkas tidak ada: {jalur}"


def test_berat_gambar_karya_masih_wajar():
    karya = AKAR / "assets" / "img" / "work"
    per_lebar: dict[str, int] = {}
    for p in karya.glob("*.webp"):
        kunci = p.stem.split("-")[-1] if p.stem[-3:].isdigit() else "800"
        per_lebar[kunci] = per_lebar.get(kunci, 0) + p.stat().st_size

    for kunci in sorted(per_lebar):
        print(f"\n  tujuh gambar pada {kunci}w: {per_lebar[kunci] / 1024:.0f} KB")

    terbesar = per_lebar["800"] // 1024
    total = sum(per_lebar.values()) // 1024
    assert terbesar < 400, f"berkas 800w berjumlah {terbesar} KB"
    assert total < 800, f"seluruh gambar karya {total} KB"


LAYAR = [(1920, 900), (1504, 900), (1280, 900), (1024, 768), (768, 1024), (390, 844)]


@pytest.mark.parametrize("jalur", ["/", "/project"])
def test_lebar_gambar_yang_dipilih_peramban_pas(peramban, situs, jalur):
    for lebar, tinggi in LAYAR:
        konteks = peramban.new_context(viewport={"width": lebar, "height": tinggi})
        halaman = konteks.new_page()
        try:
            buka(halaman, situs, jalur)
            halaman.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            halaman.wait_for_timeout(700)

            dipakai = halaman.evaluate("""() => Array.from(
                document.querySelectorAll('img[src*="/img/work/"]'))
                .filter(g => g.currentSrc)
                .map(g => ({
                    berkas: g.currentSrc.split('/').pop(),
                    sizesCss: Math.round(g.naturalWidth),
                    kotak: Math.round(g.clientWidth),
                }))""")

            assert dipakai, f"{jalur} pada {lebar}px: tidak ada gambar karya yang dimuat"

            for d in dipakai:
                nama_dasar = d["berkas"].rsplit(".", 1)[0]
                ekor = nama_dasar.rsplit("-", 1)[-1]
                d["lebar"] = int(ekor) if ekor.isdigit() else 800

            contoh = dipakai[0]
            print(f"\n  {jalur:14} layar {lebar:5}px  kotak {contoh['kotak']:4}px  "
                  f"sizes {contoh['sizesCss']:4}px  -> "
                  f"{sorted({d['lebar'] for d in dipakai})}")

            for d in dipakai:
                assert d["lebar"] >= d["kotak"], (
                    f"{jalur} pada {lebar}px: {d['berkas']} hanya {d['lebar']} px "
                    f"untuk kotak {d['kotak']} px, jadi direntangkan dan kabur"
                )
                assert d["lebar"] <= d["kotak"] * 2 + 120, (
                    f"{jalur} pada {lebar}px: {d['berkas']} selebar {d['lebar']} px "
                    f"untuk kotak {d['kotak']} px, terlalu besar"
                )
                assert d["sizesCss"] >= d["kotak"] * 0.96, (
                    f"{jalur} pada {lebar}px: sizes mengaku {d['sizesCss']} px "
                    f"sedangkan kotaknya {d['kotak']} px. Di layar padat peramban "
                    "akan mengambil berkas yang kurang lebar."
                )
        finally:
            konteks.close()
