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
#
# Angka di bawah diturunkan pada 13 September 2026, dan dua hal berubah
# sekaligus. Pertama, fontnya sekarang terhitung: selama Poppins datang dari
# fonts.gstatic.com, Resource Timing melaporkan transferSize nol untuk berkas
# dari asal lain tanpa Timing-Allow-Origin, jadi 32 KB font tidak pernah masuk
# angka ini sama sekali dan anggarannya mengawasi halaman yang lebih ringan
# daripada yang sebenarnya dikirim. Kedua, gambar karya punya tiga lebar, dan
# peramban mengambil 400 px untuk kotak yang memang sekitar itu.
#
# Terukur setelah keduanya: / 158 KB dengan 10 permintaan, /about 113 KB
# dengan 7, /project 1927 KB dengan 29. Sebelumnya / terukur 201 KB dan
# sebenarnya mengirim 233 KB dari tiga asal.
ANGGARAN = {
    "/":                      (210, 12),
    "/about":                 (150, 10),
    "/blog/":                 (150, 10),
    "/blog/kapan-peta-diam":  (150, 10),
    # /project besar dan itu jujur: MapLibre sendiri sekitar 1 MB. Angka di
    # bawah menghitung berkas dari asal situs ini saja, jadi ubin peta tidak
    # ikut, dan tidak bisa ikut menggagalkannya karena cuaca.
    "/project":              (2200, 32),
}

HALAMAN = list(ANGGARAN)


def ukur(halaman, situs: str, jalur: str) -> dict:
    berkas: list[dict] = []
    halaman.on("response", lambda r: berkas.append({
        "url": r.url, "jenis": r.request.resource_type,
    }))
    buka(halaman, situs, jalur)

    # Halaman berpeta diukur sesudah petanya siap, bukan sesudah `load`.
    # MapLibre diimpor dari JavaScript, jadi ia datang setelah peristiwa load
    # dan tidak akan terhitung. Tanpa baris ini anggaran /project akan
    # melaporkan angka kecil yang menyenangkan dan tidak mengukur apa pun.
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
    """Anggarannya dipasang pada berkas dari asal situs ini, bukan pada seluruh
    permintaan, dan itu keputusan yang perlu dijelaskan.

    Ubin peta datang dari Mapbox atau, kalau tokennya kosong, dari OpenFreeMap.
    Jumlahnya diputuskan peta sendiri berdasarkan apa yang kebetulan terlihat,
    dan berubah antar putaran pada kode yang sama persis: /project terukur 29
    permintaan di sini, 51 di CI yang tidak punya token sehingga ubinnya benar
    benar dimuat. Anggaran yang menghitungnya akan gagal karena cuaca, bukan
    karena ada yang menggemukkan situs ini.

    Yang bisa digemukkan seseorang lewat commit adalah berkas dari asal sendiri:
    pustaka baru, gambar yang lupa dikecilkan, CSS yang membengkak. Itu yang
    dijaga. Jumlah seluruhnya tetap dicetak, supaya tetap terlihat, hanya tidak
    dijadikan syarat lulus.
    """
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
    """Tidak satu pun permintaan keluar dari asal situs ini.

    Dulu uji ini mengizinkan fonts.googleapis.com dan fonts.gstatic.com.
    Sekarang Poppins disimpan di assets/fonts, jadi daftar yang diizinkan
    kosong, dan itu perbedaan yang besar: halaman ini tidak lagi memberi tahu
    siapa pun di luar bahwa ada orang sedang membacanya.

    MapLibre pun disimpan sendiri, bukan dari CDN. Kalau suatu saat ada yang
    menggantinya dengan tautan CDN demi kepraktisan, uji ini yang menolak:
    pihak ketiga di jalur render adalah pihak ketiga yang bisa mematikan
    situs ini kapan saja, dan CSP-nya pun akan menolaknya.
    """
    for jalur in ("/", "/about", "/blog/kapan-peta-diam"):
        hasil = ukur(halaman, situs, jalur)
        assert not hasil["luar"], (
            f"{jalur} meminta berkas dari luar: {hasil['luar']}"
        )


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


@pytest.mark.parametrize("berkas", ["index.html", "project.html"])
def test_gambar_karya_punya_tiga_lebar(berkas):
    """Satu berkas 800 px untuk slot 329 px berarti membayar dua kali lipat
    piksel lalu membuangnya. `sizes` wajib ada bersama `srcset`: tanpanya
    peramban menganggap slotnya selebar layar dan selalu mengambil yang
    terbesar, jadi srcset tanpa sizes tidak menghemat apa pun."""
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

    # Yang benar benar diunduh pembaca adalah satu lebar, bukan ketiganya.
    # Anggarannya dipasang pada yang terbesar, dan pada jumlah di cakram supaya
    # lebar keempat tidak bisa ditambahkan tanpa ada yang menyadarinya.
    terbesar = per_lebar["800"] // 1024
    total = sum(per_lebar.values()) // 1024
    assert terbesar < 400, f"berkas 800w berjumlah {terbesar} KB"
    assert total < 800, f"seluruh gambar karya {total} KB"


# Lebar mana yang benar benar dipilih peramban, diukur bukan dihitung.
#
# `sizes` adalah satu satunya cara memberi tahu peramban selebar apa slotnya
# sebelum tata letaknya ada, dan ia mudah salah dengan dua cara yang sama
# sama tidak menimbulkan galat: terlalu kecil membuat gambar 400 px
# direntangkan di kotak 450 px dan terlihat kabur, terlalu besar membuat
# berkas 800 px diunduh untuk kotak 289 px dan seluruh gunanya srcset hilang.
# Keduanya hanya terlihat kalau diukur di peramban sungguhan.
LAYAR = [(1920, 900), (1504, 900), (1280, 900), (1024, 768), (768, 1024), (390, 844)]


@pytest.mark.parametrize("jalur", ["/", "/project"])
def test_lebar_gambar_yang_dipilih_peramban_pas(peramban, situs, jalur):
    for lebar, tinggi in LAYAR:
        konteks = peramban.new_context(viewport={"width": lebar, "height": tinggi})
        halaman = konteks.new_page()
        try:
            buka(halaman, situs, jalur)
            # Gambar yang dimuat malas perlu terlihat dulu sebelum ia punya
            # currentSrc sama sekali.
            halaman.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            halaman.wait_for_timeout(700)

            # `naturalWidth` TIDAK dipakai di sini, dan itu penting.
            #
            # Untuk gambar dengan srcset berdeskriptor w, Chromium melaporkan
            # naturalWidth sebagai lebar berkas dibagi kerapatan yang ia hitung
            # dari `sizes`, jadi nilainya selalu kira kira sama dengan nilai
            # `sizes` itu sendiri, bukan lebar berkasnya. Uji yang memakainya
            # sebagai lebar berkas akan menuduh gambar 400 px hanya 253 px, dan
            # itu sudah terjadi. Lebar berkasnya diambil dari namanya, sebab di
            # situlah ia memang tertulis.
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
                # Dua kali lebar kotak masih wajar; lebih dari itu berarti
                # bitanya dibayar lalu dibuang.
                assert d["lebar"] <= d["kotak"] * 2 + 120, (
                    f"{jalur} pada {lebar}px: {d['berkas']} selebar {d['lebar']} px "
                    f"untuk kotak {d['kotak']} px, terlalu besar"
                )
                # `sizes` yang lebih kecil daripada kotaknya tidak terlihat
                # pada layar biasa, tetapi pada layar padat ia membuat peramban
                # memilih berkas yang sebenarnya kurang lebar. Diberi kelonggaran
                # 4 persen untuk pembulatan dan batas jalur grid.
                assert d["sizesCss"] >= d["kotak"] * 0.96, (
                    f"{jalur} pada {lebar}px: sizes mengaku {d['sizesCss']} px "
                    f"sedangkan kotaknya {d['kotak']} px. Di layar padat peramban "
                    "akan mengambil berkas yang kurang lebar."
                )
        finally:
            konteks.close()
