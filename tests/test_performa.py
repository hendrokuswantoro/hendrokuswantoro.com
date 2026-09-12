"""Anggaran performa, diukur bukan ditebak. Bab 15.20.

Sampai hari ini seluruh optimasi di situs ini masuk akal tetapi tidak satu
pun angkanya pernah dilihat. Optimasi tanpa pengukuran adalah tebakan yang
kebetulan rapi.

Yang diuji di sini anggaran, bukan angka persis. Angka persis akan berbeda
tiap mesin dan tiap jaringan, dan uji yang menuntutnya akan gagal karena
alasan yang salah. Anggaran hanya gagal kalau ada yang benar benar memburuk,
misalnya seseorang menambahkan gambar 4 MB atau memuat pustaka dari CDN.

Menjalankan sendiri, dengan angkanya dicetak:

    python -m pytest tests/test_performa.py -q -s
"""

from __future__ import annotations

import json

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

from conftest import buka  # noqa: E402
from test_peramban import peta_siap  # noqa: E402

# Anggaran per halaman: kilobyte, lalu jumlah permintaan.
#
# Longgar dengan sengaja. Yang dijaga kemerosotan besar, bukan selisih
# beberapa kilobyte antar commit: uji yang menuntut angka persis akan gagal
# karena jaringan, bukan karena kodenya.
#
# /project punya anggaran sendiri yang jauh lebih besar, dan itu jujur:
# halaman itu memuat MapLibre plus ubin peta. Pustakanya sendiri sekitar 1 MB
# karena maplibre-gl-shared.mjs diunduh dua kali, sekali oleh halaman dan
# sekali oleh worker-nya yang berjalan di konteks terpisah. Menyatukan semua
# halaman di bawah satu anggaran besar justru membuat halaman lain bisa
# membengkak tanpa ketahuan.
ANGGARAN = {
    "/":                      (300, 12),
    "/about":                 (200, 10),
    "/blog/":                 (200, 10),
    "/blog/kapan-peta-diam":  (200, 10),
    "/project":              (3200, 45),
}

HALAMAN = list(ANGGARAN)


def ukur(halaman, situs: str, jalur: str) -> dict:
    berkas: list[dict] = []
    halaman.on("response", lambda r: berkas.append({
        "url": r.url, "jenis": r.request.resource_type,
    }))
    buka(halaman, situs, jalur)

    ukuran = halaman.evaluate("""() => {
        const e = performance.getEntriesByType('resource');
        const nav = performance.getEntriesByType('navigation')[0] || {};
        const jumlah = e.reduce((n, x) => n + (x.transferSize || x.encodedBodySize || 0), 0);
        return {
            bytes: jumlah + (nav.transferSize || 0),
            permintaan: e.length + 1,
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
    kb = round(hasil["bytes"] / 1024)

    print(f"\n  {jalur:28} {kb:5} KB  {hasil['permintaan']:3} permintaan  "
          f"DOM {hasil['domSiap']} ms")
    for b in hasil["terbesar"]:
        print(f"      {b['kb']:5} KB  {b['nama']}")

    batas_kb, batas_permintaan = ANGGARAN[jalur]
    assert kb <= batas_kb, (
        f"{jalur} membengkak jadi {kb} KB, anggaran {batas_kb} KB.\n"
        f"terbesar: {json.dumps(hasil['terbesar'])}"
    )
    assert hasil["permintaan"] <= batas_permintaan, (
        f"{jalur} meminta {hasil['permintaan']} berkas, anggaran {batas_permintaan}"
    )


def test_hanya_google_fonts_yang_dari_luar(halaman, situs):
    """MapLibre disimpan sendiri, bukan dari CDN. Kalau suatu saat ada yang
    menggantinya dengan tautan CDN demi kepraktisan, uji ini yang menolak:
    pihak ketiga di jalur render adalah pihak ketiga yang bisa mematikan
    situs ini kapan saja, dan CSP-nya pun akan menolaknya."""
    hasil = ukur(halaman, situs, "/about")
    diizinkan = {"fonts.googleapis.com", "fonts.gstatic.com"}
    asing = set(hasil["luar"]) - diizinkan
    assert not asing, f"ada permintaan ke pihak ketiga yang tidak diharapkan: {asing}"


@pytest.mark.parametrize("jalur", ["/", "/about", "/blog/", "/blog/kapan-peta-diam"])
def test_maplibre_hanya_diunduh_di_halaman_yang_berpeta(halaman, situs, jalur):
    """Pustaka petanya sekitar 1 MB, jauh lebih berat daripada seluruh sisa
    situs digabung. Empat halaman ini tidak punya peta dan tidak boleh
    membayarnya.

    Perhatikan apa yang **tidak** diuji di sini: bahwa di /project pun
    MapLibre baru diunduh sesudah digulir. Bagian petanya duduk tinggi di
    halaman itu, di dalam rootMargin 500px milik pengamatnya, jadi ia memang
    langsung dimuat. Menulis uji yang seolah membuktikan penundaan di sana
    berarti menuliskan klaim yang tidak benar.
    """
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
    """Diukur dari berkasnya, bukan dari peramban: lebih cepat dan hasilnya
    sama. Tujuh gambar PNG bisa menggandakan berat halaman Proyek."""
    proyek = (AKAR / "project.html").read_text(encoding="utf-8")
    import re

    for tag in re.findall(r"<img\b[^>]*>", proyek):
        sumber = re.search(r'src="([^"]+)"', tag)
        assert sumber and sumber.group(1).endswith(".webp"), f"bukan webp: {tag[:70]}"
        assert 'loading="lazy"' in tag, f"tidak dimuat malas: {tag[:70]}"
        assert re.search(r'width="\d+"', tag) and re.search(r'height="\d+"', tag), (
            f"tanpa ukuran, halaman akan melompat saat gambarnya datang: {tag[:70]}"
        )

    total_kb = sum(
        p.stat().st_size for p in (AKAR / "assets" / "img" / "work").glob("*.webp")
    ) // 1024
    print(f"\n  tujuh gambar karya: {total_kb} KB")
    assert total_kb < 800, f"gambar karya membengkak jadi {total_kb} KB"
