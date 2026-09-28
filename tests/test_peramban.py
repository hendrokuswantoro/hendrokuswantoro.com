from __future__ import annotations

import contextlib
import time

import pytest


pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

from conftest import buka  # noqa: E402
from playwright.sync_api import Page  # noqa: E402


@pytest.mark.parametrize("jalur,judul", [
    ("/", "Hendro Kuswantoro"),
    ("/about", "About"),
    ("/project", "Project"),
    ("/blog/", "Blog"),
    ("/blog/kapan-peta-diam", "When a map should say I do not know"),
])
def test_halaman_terbuka_tanpa_galat(halaman, situs, jalur, judul):
    buka(halaman, situs, jalur)
    assert halaman.title() == judul

    ditolak_mapbox = [u for u, k in halaman.tolakan if k == 403 and "api.mapbox.com" in u]
    lain = [u for u, k in halaman.tolakan if not (k == 403 and "api.mapbox.com" in u)]
    assert not lain, f"{jalur}: permintaan gagal yang bukan ubin Mapbox: {lain[:3]}"

    sisa = [g for g in halaman.galat if not (ditolak_mapbox and "Failed to load resource" in g)]
    assert not sisa, f"{jalur}: {sisa[:3]}"


@pytest.mark.parametrize("lebar", [360, 768, 1024])
def test_tidak_ada_geser_mendatar_di_lebar_mana_pun(peramban, situs, lebar):
    konteks = peramban.new_context(viewport={"width": lebar, "height": 900})
    p = konteks.new_page()
    try:
        for jalur in ("/", "/about", "/project", "/parkir-jogja", "/blog/",
                      "/blog/kapan-peta-diam", "/404"):
            p.goto(f"{situs}{jalur}", wait_until="networkidle")
            lebar = p.evaluate(
                "() => [document.documentElement.scrollWidth, window.innerWidth]"
            )
            assert lebar[0] <= lebar[1] + 1, f"{jalur} meluber: {lebar[0]} > {lebar[1]}"
    finally:
        konteks.close()


def test_saklar_bahasa_mengganti_seluruh_teks(halaman, situs):
    buka(halaman, situs, "/about")
    inggris = halaman.locator("h1").inner_text()

    halaman.click('[data-lang="id"]')
    halaman.wait_for_timeout(300)
    indonesia = halaman.locator("h1").inner_text()

    assert inggris != indonesia, "judul tidak berganti bahasa"
    assert halaman.evaluate("() => document.documentElement.lang") == "id"

    halaman.click('[data-lang="en"]')
    halaman.wait_for_timeout(300)
    assert halaman.locator("h1").inner_text() == inggris, "tidak kembali ke Inggris"


def test_pilihan_bahasa_bertahan_setelah_dimuat_ulang(halaman, situs):
    buka(halaman, situs, "/about")
    halaman.click('[data-lang="id"]')
    halaman.wait_for_timeout(300)
    buka(halaman, situs, "/project")
    assert halaman.evaluate("() => document.documentElement.lang") == "id"


def test_saring_proyek(halaman, situs):
    buka(halaman, situs, "/project")
    semua = halaman.locator(".card:not(.is-hidden)").count()
    halaman.click('[data-filter="satellite"]')
    halaman.wait_for_timeout(200)
    tersaring = halaman.locator(".card:not(.is-hidden)").count()
    assert 0 < tersaring < semua, f"filter tidak menyaring: {semua} jadi {tersaring}"


def test_daftar_isi_tulisan_terbentuk(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")
    assert halaman.locator(".rail__daftar ol a").count() >= 2
    assert halaman.locator(".article h2 .anchor").count() == 0, "tanda pagar di judul muncul lagi"


def test_daftar_isi_menggulir_tanpa_mengubah_alamat(halaman, situs):
    buka(halaman, situs, "/parkir-jogja")
    alamat = halaman.url
    tautan = halaman.locator(".rail__daftar ol a").nth(2)
    tujuan = tautan.get_attribute("href")[1:]
    tautan.click()
    halaman.wait_for_timeout(1200)
    assert halaman.url == alamat, f"alamat berubah jadi {halaman.url}"
    atas = halaman.evaluate(f"() => document.getElementById('{tujuan}').getBoundingClientRect().top")
    assert 0 <= atas < 250, f"judul tujuan tidak tergulir ke atas: {atas}"

    halaman.locator('.hero__actions a[href="#coba"]').click()
    halaman.wait_for_timeout(1200)
    assert "#" not in halaman.url


def test_alamat_lama_berpagar_tetap_sampai_lalu_pagarnya_hilang(halaman, situs):
    buka(halaman, situs, "/parkir-jogja#knowing-when-to-say-no")
    halaman.wait_for_timeout(600)
    assert "#" not in halaman.url
    atas = halaman.evaluate("() => document.getElementById('knowing-when-to-say-no').getBoundingClientRect().top")
    assert 0 <= atas < 250, f"alamat lama tidak lagi mengantar ke bagiannya: {atas}"


def tunggu(halaman: Page, ungkapan: str, batas_ms: int = 45000, alasan: str = "") -> None:
    batas = time.monotonic() + batas_ms / 1000
    while time.monotonic() < batas:
        with contextlib.suppress(Exception):
            if halaman.evaluate(ungkapan):
                return
        halaman.wait_for_timeout(250)
    raise AssertionError(alasan or f"tidak pernah benar dalam {batas_ms} ms: {ungkapan}")


def peta_siap(halaman: Page, batas_ms: int = 45000) -> None:
    halaman.evaluate("() => document.querySelector('[data-peta]').scrollIntoView()")
    tunggu(halaman, "() => !!window.HK_PETA_MAP", batas_ms, "peta tidak pernah dibuat")
    tunggu(halaman, "() => window.HK_PETA_MAP.isStyleLoaded()", batas_ms,
           "gaya peta tidak pernah selesai dimuat")


def butuh_ubin(halaman: Page) -> None:
    if not halaman.evaluate("() => (window.HK_KONFIG || {}).mapboxToken"):
        pytest.skip(
            "MAPBOX_TOKEN kosong, jadi petanya memakai OpenFreeMap.\n"
            "    Yang diuji bukan lagi peta yang terbit.\n"
            "    Lokal   : isi MAPBOX_TOKEN di .env lalu sh tools/konfigurasi.sh\n"
            "    Di CI   : pasang rahasia repositori bernama MAPBOX_TOKEN"
        )

    galat = halaman.evaluate("() => (window.HK_PETA_ERRORS || []).map(g => g.message)")
    tertolak = [g for g in galat if "403" in g and "api.mapbox.com" in g]
    if not tertolak:
        return

    asal = halaman.url.split("/")[0] + "//" + halaman.url.split("/")[2]
    pytest.skip(
        f"Mapbox menolak ubinnya dengan 403 untuk asal {asal}.\n"
        f"    Tokennya sah, hanya asal ini belum ada di daftar URL-nya.\n"
        f"    Buka console.mapbox.com, pilih tokennya, tambahkan\n"
        f"        {asal}\n"
        f"    pada URL restrictions, lalu Save changes.\n"
        f"    Salin persis seperti itu: tanpa garis miring di belakang, tanpa\n"
        f"    jalur, dan tanpa tanda bintang. Mapbox juga menolak alamat IP,\n"
        f"    jadi jangan ditukar dengan 127.0.0.1.\n"
        f"    Selama belum, uji peta tidak menjaga apa apa."
    )


def test_peta_benar_benar_menggambar(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    butuh_ubin(halaman)

    hasil = halaman.evaluate("""() => {
        const m = window.HK_PETA_MAP;
        const n = (id) => { try { return m.queryRenderedFeatures({layers:[id]}).length; }
                            catch (e) { return -1; } };
        return {
            lapisan: m.getStyle().layers.length,
            galat: (window.HK_PETA_ERRORS || []).length,
            air: n('air'),
            kota: n('nama-kota'),
            penanda: document.querySelectorAll('.maplibregl-marker').length,
        };
    }""")

    assert hasil["lapisan"] >= 30, f"gaya kehilangan lapisan: {hasil['lapisan']}"
    assert hasil["galat"] == 0, "peta melaporkan galat"
    assert hasil["air"] > 0, "tidak ada satu pun ubin tergambar"
    assert hasil["kota"] > 0, "tidak ada nama kota tergambar"
    assert hasil["penanda"] == 7, f"penanda karya {hasil['penanda']}, seharusnya 7"


def test_tombol_3d_menegakkan_bangunan(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    butuh_ubin(halaman)

    halaman.evaluate("""() => {
        const m = window.HK_PETA_MAP;
        m.stop();
        m.jumpTo({center: [110.3665, -7.7930], zoom: 16, pitch: 0});
    }""")
    halaman.wait_for_timeout(4000)

    halaman.locator("button", has_text="3D").first.click()
    halaman.wait_for_timeout(6000)

    hasil = halaman.evaluate("""() => {
        const m = window.HK_PETA_MAP;
        const n = (id) => { try { return m.queryRenderedFeatures({layers:[id]}).length; }
                            catch (e) { return -1; } };
        return {pitch: Math.round(m.getPitch()), terrain: !!m.getTerrain(),
                gedung3d: n('gedung3d')};
    }""")

    assert hasil["pitch"] > 30, f"peta tidak miring, pitch {hasil['pitch']}"
    assert hasil["terrain"], "terrain tidak menyala"
    assert hasil["gedung3d"] > 100, f"bangunan 3D cuma {hasil['gedung3d']}"


def test_nama_jalan_muncul_di_zoom_kota(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    butuh_ubin(halaman)

    halaman.evaluate("""() => {
        const m = window.HK_PETA_MAP;
        m.stop();
        m.jumpTo({center: [110.3690, -7.7880], zoom: 15.5, pitch: 0});
    }""")
    halaman.wait_for_timeout(6000)

    jumlah = halaman.evaluate(
        "() => window.HK_PETA_MAP.queryRenderedFeatures({layers:['nama-jalan']}).length"
    )
    assert jumlah > 0, "tidak ada nama jalan tergambar di zoom kota"


def test_gedung_3d_duduk_di_bawah_semua_nama(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    butuh_ubin(halaman)
    halaman.evaluate("() => window.HK_PETA_STATE.setThree(true)")
    tunggu(halaman, "() => !!window.HK_PETA_MAP.getLayer('gedung3d')", 20000,
           "lapisan gedung 3D tidak pernah dipasang")
    halaman.wait_for_timeout(800)

    urut = halaman.evaluate("() => window.HK_PETA_MAP.getStyle().layers.map(l => l.id)")
    tiga_d = urut.index("gedung3d")
    nama = [i for i, id_ in enumerate(urut) if id_.startswith("nama-")]
    assert nama, "tidak ada satu pun lapisan nama"
    assert tiga_d < min(nama), (
        f"gedung3d ada di urutan {tiga_d}, di atas lapisan nama pertama "
        f"({urut[min(nama)]} di urutan {min(nama)}), jadi ia menutupi namanya"
    )
    assert tiga_d < urut.index("panah-searah"), "gedung3d di atas panah searah"


def test_warna_gedung_mengikuti_tinggi_yang_benar_benar_ada(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    butuh_ubin(halaman)
    halaman.evaluate("() => window.HK_PETA_STATE.setThree(true)")
    tunggu(halaman, "() => !!window.HK_PETA_MAP.getLayer('gedung3d')", 20000)

    tangga = halaman.evaluate(
        "() => window.HK_PETA_MAP.getPaintProperty('gedung3d', 'fill-extrusion-color')")
    henti = [n for n in tangga if isinstance(n, (int, float))]
    assert henti, f"tangga warnanya bukan interpolasi: {tangga}"
    assert max(henti) <= 60, (
        f"tangga warnanya membentang sampai {max(henti)} m, jauh di atas "
        f"bangunan yang benar benar ada di sini"
    )
    assert any(n <= 3 for n in henti), (
        "tidak ada henti warna di 3 m ke bawah, padahal itu tinggi median di sini"
    )


def di_titik(halaman: Page, lng: float, lat: float, jarak: float = 0.4) -> None:
    pusat = halaman.evaluate("() => window.HK_PETA_MAP.getCenter()")
    assert abs(pusat["lng"] - lng) < jarak and abs(pusat["lat"] - lat) < jarak, (
        f"peta berhenti di {pusat['lng']:.3f}, {pusat['lat']:.3f}, bukan di {lng}, {lat}"
    )


def test_alamat_peta_membuka_karya_yang_disebutnya(halaman, situs):
    buka(halaman, situs, "/project#peta-fish")
    peta_siap(halaman)
    tunggu(halaman, "() => window.HK_PETA_MAP.getZoom() > 15", 25000,
           "peta tidak pernah terbang ke karya yang disebut alamatnya")
    di_titik(halaman, 108.22, 3.70)


def test_alamat_yang_bukan_karya_dibiarkan(halaman, situs):
    buka(halaman, situs, "/project#peta-entah")
    peta_siap(halaman)
    halaman.wait_for_timeout(3000)
    assert halaman.evaluate("() => window.HK_PETA_MAP.getZoom()") < 8


def test_tautan_di_kartu_membawa_pembaca_ke_peta(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    halaman.locator('[data-peta-buka="mimika"]').click()
    tunggu(halaman, "() => window.HK_PETA_MAP.getZoom() > 15", 25000,
           "menekan tautan di kartu tidak memindahkan peta")
    di_titik(halaman, 137.00, -4.35)

    assert halaman.evaluate("() => location.hash") == "#peta-mimika", (
        "alamatnya tidak ikut berganti, jadi tampilan ini tidak bisa disalin"
    )
    """Petanya berhenti persis di bawah header yang lengket, tidak di
       baliknya dan tidak jauh di bawahnya.

       Pernah meleset 196 piksel. Sebabnya popup MapLibre memindahkan fokus ke
       dalam dirinya begitu terbuka, dan pemindahan fokus itu menggulir
       halaman, mengalahkan gulir halus yang diminta tautannya."""
    letak = halaman.evaluate("""() => ({
      peta: Math.round(document.querySelector('.peta').getBoundingClientRect().top),
      header: Math.round(document.querySelector('header').getBoundingClientRect().bottom)
    })""")
    assert letak["peta"] >= letak["header"], (
        f"petanya berhenti di balik header: atas {letak['peta']}, header {letak['header']}"
    )
    assert letak["peta"] - letak["header"] < 40, (
        f"petanya berhenti {letak['peta'] - letak['header']} piksel di bawah header"
    )


def test_terbang_menuliskan_alamat_tanpa_menumpuk_riwayat(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    panjang = halaman.evaluate("() => history.length")

    halaman.evaluate("() => window.HK_PETA_STATE.buka('fire')")
    tunggu(halaman, "() => location.hash === '#peta-fire'", 20000,
           "alamatnya tidak pernah ditulis")
    assert halaman.evaluate("() => history.length") == panjang


def test_menyaring_legenda_terdengar_pembaca_layar(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    kabar = halaman.locator(".peta__kabar")
    assert kabar.get_attribute("aria-live") == "polite"

    baris = halaman.locator('.peta__baris[data-kind="satellite"]')
    nama = baris.locator(".peta__nama").inner_text()
    baris.click()

    tunggu(halaman,
           "() => (document.querySelector('.peta__kabar').textContent || '').trim().length > 0",
           8000, "menyaring legenda tidak mengumumkan apa apa")
    teks = halaman.evaluate("() => document.querySelector('.peta__kabar').textContent")
    assert nama in teks, f"pengumumannya tidak menyebut jenis yang disaring: {teks!r}"
    assert "2" in teks and "7" in teks, f"pengumumannya tidak menyebut hitungannya: {teks!r}"


def test_wilayah_kabar_tidak_pernah_tampil_di_layar(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    kotak = halaman.locator(".peta__kabar").bounding_box()
    assert kotak["width"] <= 1 and kotak["height"] <= 1, (
        f"wilayah kabar mengambil tempat di layar: {kotak}"
    )


def test_roda_tetikus_menggulir_halaman_bukan_memperbesar_peta(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    halaman.wait_for_timeout(500)

    kanvas = halaman.locator(".peta__kanvas").bounding_box()
    sebelum_y = halaman.evaluate("() => Math.round(scrollY)")
    sebelum_z = halaman.evaluate("() => window.HK_PETA_MAP.getZoom()")

    halaman.mouse.move(kanvas["x"] + kanvas["width"] / 2, kanvas["y"] + kanvas["height"] / 2)
    halaman.mouse.wheel(0, 400)
    halaman.wait_for_timeout(1000)

    assert halaman.locator(".maplibregl-cooperative-gesture-screen").count() == 0, (
        "tulisan gesturnya kembali"
    )
    assert halaman.evaluate("() => Math.round(scrollY)") > sebelum_y, (
        "halamannya tidak bergulir, jadi pembaca terjebak di atas peta"
    )
    assert abs(halaman.evaluate("() => window.HK_PETA_MAP.getZoom()") - sebelum_z) < 0.01, (
        "rodanya masih memperbesar peta"
    )


def test_layar_sentuh_tanpa_tulisan_dua_jari(peramban, situs):
    konteks = peramban.new_context(viewport={"width": 390, "height": 844},
                                   is_mobile=True, has_touch=True)
    p = konteks.new_page()
    try:
        p.goto(f"{situs}/project", wait_until="networkidle")
        p.locator(".peta").scroll_into_view_if_needed()
        peta_siap(p)
        assert p.evaluate("() => window.HK_PETA_MAP.cooperativeGestures.isEnabled()"), (
            "satu jari di layar sentuh kembali menggeser peta, jadi halamannya tidak bisa digulir"
        )
        layar = p.locator(".maplibregl-cooperative-gesture-screen")
        assert layar.count() == 1
        assert layar.evaluate("e => getComputedStyle(e).display") == "none", (
            "tulisan dua jari kembali tampil di atas peta"
        )
    finally:
        konteks.close()


def test_ctrl_sambil_menggulir_memperbesar_peta(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    halaman.wait_for_timeout(500)

    kanvas = halaman.locator(".peta__kanvas").bounding_box()
    halaman.mouse.move(kanvas["x"] + kanvas["width"] / 2, kanvas["y"] + kanvas["height"] / 2)
    sebelum_y = halaman.evaluate("() => Math.round(scrollY)")
    sebelum_z = halaman.evaluate("() => window.HK_PETA_MAP.getZoom()")

    halaman.keyboard.down("Control")
    halaman.mouse.wheel(0, -350)
    halaman.keyboard.up("Control")
    halaman.wait_for_timeout(1000)

    assert halaman.evaluate("() => window.HK_PETA_MAP.getZoom()") > sebelum_z + 0.1, (
        "Ctrl sambil menggulir tidak memperbesar peta, jadi rodanya mati sama sekali"
    )
    assert halaman.evaluate("() => Math.round(scrollY)") == sebelum_y, (
        "halamannya ikut bergulir sewaktu peta diperbesar"
    )


def test_menyeret_menggeser_peta_sejauh_yang_diseret(halaman, situs):
    import math

    buka(halaman, situs, "/project")
    peta_siap(halaman)

    halaman.evaluate("() => window.HK_PETA_MAP.jumpTo({center: [110.3656, -7.7925], zoom: 15.2})")
    halaman.wait_for_timeout(600)

    kanvas = halaman.locator(".peta__kanvas").bounding_box()
    x = kanvas["x"] + kanvas["width"] * 0.72
    y = kanvas["y"] + kanvas["height"] * 0.78
    sebelum = halaman.evaluate("() => window.HK_PETA_MAP.getCenter()")

    piksel = 320
    halaman.mouse.move(x, y)
    halaman.mouse.down()
    for i in range(1, 41):
        halaman.mouse.move(x - piksel * i / 40, y)
        halaman.wait_for_timeout(16)
    halaman.mouse.up()
    halaman.wait_for_timeout(600)

    sesudah = halaman.evaluate("() => window.HK_PETA_MAP.getCenter()")
    pindah = sesudah["lng"] - sebelum["lng"]

    lat = math.radians(sebelum["lat"])
    zoom = halaman.evaluate("() => window.HK_PETA_MAP.getZoom()")
    meter = 40075016.686 * math.cos(lat) / (512 * 2 ** zoom) * piksel
    semestinya = meter / (111320 * math.cos(lat))

    assert pindah > semestinya * 0.7, (
        f"menyeret {piksel} piksel cuma menggeser {pindah:.6f} derajat, "
        f"{pindah / semestinya * 100:.1f} persen dari {semestinya:.6f} yang semestinya"
    )


def test_tidak_ada_lagi_baris_petunjuk_di_bawah_peta(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    assert halaman.locator(".peta__cara").count() == 0


@pytest.mark.parametrize("jalur", ["/", "/project"])
def test_pengantar_peta_dua_kalimat_sebaris_dan_rapat(halaman, situs, jalur):
    buka(halaman, situs, jalur)
    letak = halaman.evaluate("""() => {
      const blok = document.querySelector('.peta__intro');
      const h = blok.querySelector('h2').getBoundingClientRect();
      const p = blok.querySelectorAll('p');
      const a = p[0].getBoundingClientRect();
      const b = p[1].getBoundingClientRect();
      return {
        jumlah: p.length,
        dibawahJudul: Math.round(a.top) >= Math.round(h.bottom) - 2,
        sebaris: Math.abs(a.top - b.top) < 3,
        jarak: Math.round(b.left - a.right),
      };
    }""")
    assert letak["jumlah"] == 2, f"{jalur}: pengantarnya bukan dua kalimat"
    assert letak["dibawahJudul"], f"{jalur}: kalimat pertama tidak di bawah judulnya"
    assert letak["sebaris"], f"{jalur}: kalimat kedua tidak sebaris dengan yang pertama"
    assert 0 < letak["jarak"] < 28, (
        f"{jalur}: jarak antar kalimatnya {letak['jarak']} piksel, "
        f"seukuran kolom bukan seukuran spasi"
    )


def test_pengantar_peta_bertumpuk_lagi_di_ponsel(peramban, situs):
    konteks = peramban.new_context(viewport={"width": 390, "height": 844})
    hal = konteks.new_page()
    try:
        hal.goto(f"{situs}/project", wait_until="load")
        hal.wait_for_selector("html[data-siap]", state="attached", timeout=15000)
        bertumpuk = hal.evaluate("""() => {
          const p = document.querySelectorAll('.peta__intro p');
          return p[1].getBoundingClientRect().top >= p[0].getBoundingClientRect().bottom - 1;
        }""")
        assert bertumpuk, "di ponsel keduanya dipaksa sebaris"
    finally:
        konteks.close()


def test_tombol_perbesar_tetap_bekerja(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)
    sebelum = halaman.evaluate("() => window.HK_PETA_MAP.getZoom()")
    halaman.locator(".maplibregl-ctrl-zoom-in").first.click()
    halaman.wait_for_timeout(900)
    assert halaman.evaluate("() => window.HK_PETA_MAP.getZoom()") > sebelum + 0.5


def test_studi_kasus_tidak_menyisakan_ruang_kosong_di_kanan(halaman, situs):
    halaman.set_viewport_size({"width": 1440, "height": 900})
    buka(halaman, situs, "/parkir-jogja")
    kotak = halaman.evaluate("""() => {
      const a = document.querySelector('.article').getBoundingClientRect();
      const r = document.querySelector('.article > .rail').getBoundingClientRect();
      return { kananArtikel: a.right, kananRail: r.right, kiriRail: r.left, lebarArtikel: a.width };
    }""")
    assert abs(kotak["kananRail"] - kotak["kananArtikel"]) <= 1, f"kolom kanan tidak sampai tepi: {kotak}"
    assert halaman.locator(".rail__daftar ol a").count() >= 5
    assert halaman.locator('.rail a[href="#coba"]').is_visible()


def test_angka_studi_kasus_berdiri_di_atas_keterangannya(halaman, situs):
    buka(halaman, situs, "/parkir-jogja")
    kotak = halaman.evaluate("""() => {
      const kartu = document.querySelector('.stat');
      const n = kartu.querySelector('.stat__num').getBoundingClientRect();
      const l = kartu.querySelector('.stat__label').getBoundingClientRect();
      return { bawahAngka: Math.round(n.bottom), atasLabel: Math.round(l.top),
               kiriAngka: Math.round(n.left), kiriLabel: Math.round(l.left) };
    }""")
    assert kotak["atasLabel"] >= kotak["bawahAngka"] - 1, (
        f"keterangannya masih sebaris dengan angkanya: {kotak}"
    )
    assert kotak["kiriLabel"] == kotak["kiriAngka"], (
        f"keduanya tidak rata kiri: {kotak}"
    )


def latar(halaman) -> str:
    return halaman.evaluate("() => getComputedStyle(document.body).backgroundColor")


def test_latar_bawaan_putih_keabuan(halaman, situs):
    buka(halaman, situs, "/about")
    assert latar(halaman) == "rgb(246, 246, 246)", latar(halaman)


def test_sistem_yang_gelap_tidak_lagi_memaksa_halaman_jadi_gelap(peramban, situs):
    konteks = peramban.new_context(color_scheme="dark")
    p = konteks.new_page()
    try:
        p.goto(f"{situs}/about", wait_until="networkidle")
        assert p.evaluate("() => getComputedStyle(document.body).backgroundColor") \
            == "rgb(246, 246, 246)"
    finally:
        konteks.close()


def test_saklar_tema_benar_benar_menggelapkan(halaman, situs):
    buka(halaman, situs, "/about")
    terang = latar(halaman)

    halaman.click(".tema")
    halaman.wait_for_timeout(200)
    gelap = latar(halaman)

    assert gelap != terang, "saklar tema tidak mengubah apa apa"
    assert halaman.evaluate("() => document.documentElement.dataset.theme") == "dark"
    assert halaman.locator(".tema").get_attribute("aria-pressed") == "true"

    halaman.click(".tema")
    halaman.wait_for_timeout(200)
    assert latar(halaman) == terang, "tidak kembali ke terang"


def test_tema_bertahan_antar_halaman_tanpa_berkedip(halaman, situs):
    buka(halaman, situs, "/about")
    halaman.click(".tema")
    halaman.wait_for_timeout(200)

    warna_saat_diurai = []
    halaman.once("domcontentloaded", lambda: warna_saat_diurai.append(
        halaman.evaluate("() => document.documentElement.dataset.theme")
    ))
    buka(halaman, situs, "/project")

    assert halaman.evaluate("() => document.documentElement.dataset.theme") == "dark"
    assert latar(halaman) != "rgb(246, 246, 246)"
    assert warna_saat_diurai == ["dark"], (
        f"tema belum terpasang saat dokumen selesai diurai: {warna_saat_diurai}"
    )


def test_saklar_tema_ikut_berganti_bahasa(halaman, situs):
    buka(halaman, situs, "/about")
    inggris = halaman.locator(".tema").get_attribute("aria-label")

    halaman.click('[data-lang="id"]')
    halaman.wait_for_timeout(300)
    assert halaman.locator(".tema").get_attribute("aria-label") != inggris


def test_peta_tetap_menggambar_dengan_tema_gelap(halaman, situs):
    buka(halaman, situs, "/project")
    halaman.click(".tema")
    peta_siap(halaman)
    butuh_ubin(halaman)

    hasil = halaman.evaluate("""() => ({
        galat: (window.HK_PETA_ERRORS || []).length,
        air: window.HK_PETA_MAP.queryRenderedFeatures({layers: ['air']}).length,
    })""")
    assert hasil["galat"] == 0
    assert hasil["air"] > 0


def test_peta_datar_tidak_bisa_diputar(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    hasil = halaman.evaluate("""() => ({
        seret: window.HK_PETA_MAP.dragRotate.isEnabled(),
        bearing: window.HK_PETA_MAP.getBearing(),
    })""")
    assert hasil["seret"] is False, "seret-putar masih hidup di mode datar"
    assert hasil["bearing"] == 0


def test_seret_putar_kembali_hidup_di_mode_3d(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    halaman.locator("button", has_text="3D").first.click()
    halaman.wait_for_timeout(2500)
    assert halaman.evaluate("() => window.HK_PETA_MAP.dragRotate.isEnabled()") is True


def test_memperbesar_tidak_menggeser_arah_hadap(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    halaman.evaluate("""() => {
        const m = window.HK_PETA_MAP;
        m.stop();
        m.jumpTo({center: [110.3665, -7.7930], zoom: 9, bearing: 0, pitch: 0});
    }""")
    for _ in range(4):
        halaman.locator(".maplibregl-ctrl-zoom-in").click()
        halaman.wait_for_timeout(500)

    hasil = halaman.evaluate("""() => ({
        bearing: Math.abs(window.HK_PETA_MAP.getBearing()),
        pitch: Math.abs(window.HK_PETA_MAP.getPitch()),
    })""")
    assert hasil["bearing"] < 0.01, f"arah hadap bergeser jadi {hasil['bearing']}"
    assert hasil["pitch"] < 0.01, f"peta ikut miring, pitch {hasil['pitch']}"


def test_tombol_zoom_menghentikan_jelajah(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    jelajah = halaman.locator("button[aria-pressed]", has_text="Tour").first
    jelajah.click()
    halaman.wait_for_timeout(400)
    assert jelajah.get_attribute("aria-pressed") == "true", "Jelajah tidak menyala"

    halaman.locator(".maplibregl-ctrl-zoom-in").click()
    halaman.wait_for_timeout(400)
    assert jelajah.get_attribute("aria-pressed") == "false", (
        "Jelajah masih berjalan sesudah tombol zoom ditekan"
    )


def test_jelajah_berhenti_saat_peta_diseret(halaman, situs):
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    jelajah = halaman.locator("button[aria-pressed]", has_text="Tour").first
    jelajah.click()
    halaman.wait_for_timeout(400)

    kotak = halaman.locator("[data-peta]").bounding_box()
    halaman.mouse.move(kotak["x"] + kotak["width"] / 2, kotak["y"] + kotak["height"] / 2)
    halaman.mouse.down()
    halaman.mouse.move(kotak["x"] + kotak["width"] / 2 - 80, kotak["y"] + kotak["height"] / 2)
    halaman.mouse.up()
    halaman.wait_for_timeout(400)

    assert jelajah.get_attribute("aria-pressed") == "false"


def test_menyalin_ditolak_dan_papan_tempel_diisi_keterangan(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")

    hasil = halaman.evaluate("""() => {
        const ev = new ClipboardEvent('copy', {bubbles: true, cancelable: true,
                                               clipboardData: new DataTransfer()});
        document.querySelector('.article p').dispatchEvent(ev);
        return {dicegah: ev.defaultPrevented, isi: ev.clipboardData.getData('text/plain')};
    }""")
    assert hasil["dicegah"], "menyalin tidak dicegah"
    assert "Hendro Kuswantoro" in hasil["isi"]
    assert halaman.url.split("?")[0] in hasil["isi"]


def test_teks_tidak_bisa_diblok_tetapi_kolom_isian_tetap_bisa(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")
    assert halaman.evaluate(
        "() => getComputedStyle(document.querySelector('.article p')).userSelect"
    ) == "none"

    terpilih = halaman.evaluate("""() => {
        const i = document.createElement('input');
        i.value = 'uji';
        document.body.appendChild(i);
        const gaya = getComputedStyle(i).userSelect;
        i.remove();
        return gaya;
    }""")
    assert terpilih in ("text", "auto"), terpilih


def test_klik_kanan_ditolak(halaman, situs):
    buka(halaman, situs, "/about")
    assert halaman.evaluate("""() => {
        const ev = new MouseEvent('contextmenu', {bubbles: true, cancelable: true});
        document.body.dispatchEvent(ev);
        return ev.defaultPrevented;
    }""")


def test_isi_tidak_ikut_tercetak(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")
    halaman.emulate_media(media="print")
    terlihat = halaman.evaluate("""() => {
        const a = document.querySelector('.article');
        return a ? a.getClientRects().length : -1;
    }""")
    halaman.emulate_media(media="screen")
    assert terlihat == 0, "isi tulisan masih ikut tercetak"


def test_teksnya_tetap_ada_di_html_untuk_mesin_pencari(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")
    panjang = halaman.evaluate("() => document.querySelector('.article').textContent.length")
    assert panjang > 1000, f"isi tulisannya cuma {panjang} karakter di DOM"


def test_jam_yogyakarta_berjalan_dan_benar(halaman, situs):
    import datetime as dt

    buka(halaman, situs, "/about")

    if halaman.locator("[data-jam]").count() == 0:
        pytest.skip("Intl di peramban ini tanpa zona waktu, jadi jamnya sengaja dibuang")

    tampil = halaman.locator("[data-jam]").first.inner_text().strip()
    assert len(tampil) == 5 and tampil[2] == ":", tampil

    benar = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
    jam_benar = benar.strftime("%H:%M")
    assert abs(int(tampil[:2]) * 60 + int(tampil[3:])
               - (benar.hour * 60 + benar.minute)) <= 1, f"{tampil} vs {jam_benar}"


def test_kepala_halaman_menyebut_tanggal_hari_ini_bukan_nama_kota(halaman, situs):
    import datetime as dt

    buka(halaman, situs, "/about")

    if halaman.locator("[data-tanggal]").count() == 0:
        pytest.skip("Intl di peramban ini tanpa zona waktu, jadi barisnya sengaja dibuang")

    baris = halaman.locator(".header .kini").first
    baris.wait_for(state="visible")

    teks = baris.inner_text()
    assert "Yogyakarta" not in teks, teks
    assert "WIB" in teks, teks

    hari_ini = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
    tanggal = halaman.locator("[data-tanggal]").first.inner_text()
    assert str(hari_ini.day) in tanggal, f"{tanggal!r} tidak menyebut tanggal {hari_ini.day}"
    assert str(hari_ini.year) in tanggal, f"{tanggal!r} tidak menyebut tahun {hari_ini.year}"

    label = halaman.locator("[data-jam]").first.get_attribute("aria-label") or ""
    assert "Yogyakarta" in label, label

    assert halaman.locator(".footer .kini").count() == 0


def test_nama_hari_di_kepala_halaman_ikut_ganti_bahasa(halaman, situs):
    buka(halaman, situs, "/about")

    if halaman.locator("[data-tanggal]").count() == 0:
        pytest.skip("Intl di peramban ini tanpa zona waktu, jadi barisnya sengaja dibuang")

    halaman.locator(".header .kini").first.wait_for(state="visible")
    inggris = halaman.locator("[data-tanggal]").first.inner_text()

    halaman.locator('.lang__btn[data-lang="id"]').first.click()
    halaman.wait_for_function(
        "teks => document.querySelector('[data-tanggal]').textContent !== teks",
        arg=inggris,
        timeout=3000,
    )
    indonesia = halaman.locator("[data-tanggal]").first.inner_text()
    assert indonesia != inggris, f"tetap {inggris!r} sesudah pindah bahasa"


def test_tanggalnya_pendek_supaya_muat_satu_baris_dengan_menunya(halaman, situs):
    buka(halaman, situs, "/about")

    if halaman.locator("[data-tanggal]").count() == 0:
        pytest.skip("Intl di peramban ini tanpa zona waktu, jadi barisnya sengaja dibuang")

    halaman.locator(".header .kini").first.wait_for(state="visible")

    ukur = halaman.evaluate("""() => {
      const k = document.querySelector('.header .kini');
      const n = document.querySelector('.header .nav');
      return {
        tinggi: Math.round(k.getBoundingClientRect().height),
        baris: Math.round(parseFloat(getComputedStyle(k).lineHeight)),
        jarak: Math.round(n.getBoundingClientRect().left - k.getBoundingClientRect().right),
        lebarDokumen: document.documentElement.scrollWidth,
        lebarLayar: window.innerWidth,
      };
    }""")

    assert ukur["tinggi"] <= ukur["baris"] + 2, (
        f"barisnya setinggi {ukur['tinggi']}px padahal satu baris {ukur['baris']}px, "
        "jadi ia sudah patah jadi dua"
    )
    assert ukur["jarak"] > 16, f"cuma {ukur['jarak']}px sebelum menunya"
    assert ukur["lebarDokumen"] <= ukur["lebarLayar"], (
        "kepala halaman mendorong halamannya melebar dari layarnya"
    )


@pytest.mark.parametrize("lebar,tampil", [(1280, True), (1079, False), (390, False)])
def test_tanggal_menyingkir_di_layar_yang_tidak_muat(halaman, situs, lebar, tampil):
    halaman.set_viewport_size({"width": lebar, "height": 900})
    buka(halaman, situs, "/about")

    if halaman.locator("[data-tanggal]").count() == 0:
        pytest.skip("Intl di peramban ini tanpa zona waktu, jadi barisnya sengaja dibuang")

    halaman.wait_for_timeout(300)
    assert halaman.locator(".header .kini").first.is_visible() is tampil

    assert halaman.evaluate("() => document.documentElement.scrollWidth") <= lebar


def test_baris_tanggal_tidak_tampil_sebelum_ada_angkanya(halaman, situs):
    bersih = halaman.context.browser.new_context(
        java_script_enabled=False, viewport={"width": 1280, "height": 900}
    )
    try:
        tab = bersih.new_page()
        tab.goto(f"{situs}/about", wait_until="domcontentloaded")
        baris = tab.locator(".header .kini")
        assert baris.count() == 1, "markupnya hilang, bukan sekadar disembunyikan"
        assert baris.first.is_hidden(), "baris kosong tetap tampil tanpa JavaScript"
        assert "Hendro Kuswantoro" in tab.locator(".footer__bottom").inner_text()
    finally:
        bersih.close()


def test_kartu_punya_kilau_yang_mengikuti_kursor(halaman, situs):
    buka(halaman, situs, "/project")

    if not halaman.evaluate(
        "() => matchMedia('(hover: hover) and (pointer: fine)').matches"
    ):
        pytest.skip("peramban ini melaporkan tidak punya kursor, jadi kilau memang mati")

    kartu = halaman.locator(".card").first

    kartu.scroll_into_view_if_needed()
    halaman.wait_for_timeout(200)

    kotak = kartu.bounding_box()
    halaman.mouse.move(kotak["x"] + 30, kotak["y"] + 20)
    halaman.mouse.move(kotak["x"] + 60, kotak["y"] + 40, steps=4)
    halaman.wait_for_timeout(300)
    assert kartu.evaluate("el => el.style.getPropertyValue('--mx')") != ""
