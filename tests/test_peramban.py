"""Uji peramban. Bab 15.16, baris E2E Test.

Ini lubang terbesar di rangkaian uji sampai hari ini. Semua uji lain membaca
berkas atau memanggil API; tidak satu pun membuktikan halamannya benar benar
tergambar. Peta di situs ini sudah tiga kali rusak diam diam, dan tiap kali
yang menemukannya adalah mata manusia, bukan uji.

Yang dijaga di sini hanya hal yang **cuma bisa dibuktikan di peramban**:
peta yang benar benar menggambar, tombol 3D yang benar benar menegakkan
bangunan, saklar bahasa yang benar benar mengganti teks, dan halaman yang
tidak berantakan di layar ponsel. Yang bisa dibuktikan dengan membaca berkas
sudah dijaga uji lain, dan mengulanginya di sini hanya memperlambat.

Dilewati kalau Playwright atau server ujinya tidak ada.
"""

from __future__ import annotations

import contextlib
import time

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

from conftest import buka  # noqa: E402
from playwright.sync_api import Page  # noqa: E402

# ------------------------------------------------------- halaman biasa ---


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

    # 403 dari ubin Mapbox disisihkan, dan hanya itu. Tokennya dibatasi per
    # URL, jadi asal mana pun yang belum terdaftar akan ditolak; itu setelan
    # token, bukan cacat halaman. Yang tidak disisihkan: 403 dari alamat lain,
    # 404 mana pun, dan seluruh galat JavaScript.
    ditolak_mapbox = [u for u, k in halaman.tolakan if k == 403 and "api.mapbox.com" in u]
    lain = [u for u, k in halaman.tolakan if not (k == 403 and "api.mapbox.com" in u)]
    assert not lain, f"{jalur}: permintaan gagal yang bukan ubin Mapbox: {lain[:3]}"

    sisa = [g for g in halaman.galat if not (ditolak_mapbox and "Failed to load resource" in g)]
    assert not sisa, f"{jalur}: {sisa[:3]}"


def test_tidak_ada_geser_mendatar_di_ponsel(peramban, situs):
    """Halaman yang meluber ke samping di ponsel adalah cacat yang tidak
    pernah terlihat di layar lebar."""
    konteks = peramban.new_context(viewport={"width": 360, "height": 740})
    p = konteks.new_page()
    try:
        for jalur in ("/", "/about", "/project", "/blog/", "/blog/kapan-peta-diam"):
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
    """Daftar isi dibangun JavaScript dari judul yang ada, jadi hanya bisa
    dibuktikan di peramban."""
    buka(halaman, situs, "/blog/kapan-peta-diam")
    assert halaman.locator(".rail__daftar ol a").count() >= 2
    assert halaman.locator(".article h2 .anchor").count() >= 2


# ------------------------------------------------------------------ peta ---


def tunggu(halaman: Page, ungkapan: str, batas_ms: int = 45000, alasan: str = "") -> None:
    """Menunggu dengan page.evaluate, bukan page.wait_for_function.

    wait_for_function menyuntikkan pemantau yang memakai eval, dan CSP situs
    ini menolak `unsafe-eval`. Menambahkan `unsafe-eval` demi ujinya berarti
    menguji situs yang aturannya lebih longgar daripada yang terbit, yaitu
    menguji sesuatu yang bukan situs ini.
    """
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
    """Membedakan "petanya rusak" dari "ubinnya tidak diizinkan dari sini".

    Dipanggil hanya oleh uji yang memang menuntut ubin tergambar. Perilaku
    kamera, saklar putar, dan Jelajah tidak menuntutnya: objek petanya tetap
    hidup walau tiap ubin dijawab 403, dan menghentikan uji itu juga berarti
    kehilangan penjagaan atas hal yang sebenarnya masih bisa dijaga.

    Keduanya tampak sama persis di layar: peta kosong. Tanpa pembedaan ini,
    kegagalannya berbunyi "peta melaporkan galat", dan menemukan sebabnya
    menuntut membuka satu per satu galat yang tercatat. Sudah terjadi, dan
    memakan waktu lama.

    Token Mapbox dibatasi per URL. Kalau asal tempat uji ini berjalan tidak
    ada di daftarnya, tiap ubin dijawab 403. Itu bukan cacat pada kode situs
    ini, dan menggagalkan uji karenanya akan menunjuk ke arah yang salah.
    Dilewati, dengan alasan yang menyebut persis apa yang harus dikerjakan,
    dan pytest.ini memakai -rs supaya alasan itu selalu tercetak.
    """
    # Tanpa token, peta jatuh ke OpenFreeMap. Gayanya jauh lebih sedikit
    # lapisannya dan tidak membawa nama jalan maupun tinggi bangunan, jadi
    # yang diuji bukan lagi peta yang terbit. Dilewati, dan dikatakan.
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
        f"    Buka console.mapbox.com, pilih tokennya, tambahkan {asal}\n"
        f"    pada URL restrictions, lalu jalankan ulang.\n"
        f"    Selama belum, uji peta tidak menjaga apa apa."
    )


def test_peta_benar_benar_menggambar(halaman, situs):
    """Inti dari seluruh berkas ini.

    Peta ini sudah tiga kali rusak diam diam: sekali karena lapisan yang tidak
    didukung, sekali karena worker yang diblokir CSP, sekali karena berkas
    pustaka yang kurang. Ketiganya tidak menimbulkan galat apa pun; petanya
    hanya diam. Uji ini yang menggantikan mata manusia.
    """
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


# ------------------------------------------------------------------ tema ---
#
# Warna latar hanya bisa dibuktikan di peramban. Membaca CSS membuktikan
# tokennya ada; ia tidak membuktikan token itu yang benar benar dipakai, dan
# tidak membuktikan halamannya tidak berkedip putih lebih dulu.


def latar(halaman) -> str:
    return halaman.evaluate("() => getComputedStyle(document.body).backgroundColor")


def test_latar_bawaan_putih_keabuan(halaman, situs):
    """#f6f6f6. Bukan putih polos, bukan gelap, walau sistem pembacanya gelap."""
    buka(halaman, situs, "/about")
    assert latar(halaman) == "rgb(246, 246, 246)", latar(halaman)


def test_sistem_yang_gelap_tidak_lagi_memaksa_halaman_jadi_gelap(peramban, situs):
    """Ini yang dulu membuat permintaan "latar putih keabuan" tidak pernah
    terlihat: paletnya menempel pada prefers-color-scheme, jadi pembaca yang
    laptopnya gelap melihat halaman gelap dan tidak punya cara memintanya
    terang."""
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
    """Kedipannya yang penting. app.js dimuat dengan defer, jadi kalau tema
    baru dipasang dari sana, pembaca yang memilih gelap melihat satu bingkai
    putih lebih dulu. Yang mencegahnya skrip sebaris di <head>, dan satu
    satunya cara membuktikannya adalah menanyakan warna latar pada saat
    dokumennya baru selesai diurai, sebelum skrip defer mana pun berjalan."""
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
    """Tema mengganti warna halaman, bukan warna peta. Kalau suatu saat
    keduanya tersambung tanpa sengaja, petanya yang akan diam."""
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


# ------------------------------------------------------- peta yang diam ---
#
# Keluhannya: "petanya masih berputar putar ke sana kemari ketika di-zoom".
# Tiga sebabnya, dan ketiganya hanya bisa dibuktikan di peramban.


def test_peta_datar_tidak_bisa_diputar(halaman, situs):
    """Cubitan dua jari bawaannya memutar sekaligus memperbesar, dan seret
    tombol kanan juga memutar. Di peta datar keduanya hanya kejutan."""
    buka(halaman, situs, "/project")
    peta_siap(halaman)

    hasil = halaman.evaluate("""() => ({
        seret: window.HK_PETA_MAP.dragRotate.isEnabled(),
        bearing: window.HK_PETA_MAP.getBearing(),
    })""")
    assert hasil["seret"] is False, "seret-putar masih hidup di mode datar"
    assert hasil["bearing"] == 0


def test_seret_putar_kembali_hidup_di_mode_3d(halaman, situs):
    """Dimatikan karena di peta datar ia tidak berguna, bukan karena memutar
    itu buruk. Begitu ada sudut pandang, memutar justru maksudnya."""
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
    """Ini yang sebenarnya bikin petanya terasa liar. Jelajah dulu hanya
    berhenti pada dragstart, wheel, dan touchstart; tombol + dan -
    menggerakkan kamera lewat easeTo, yang bagi MapLibre tidak berbeda
    dengan gerakan yang dimulai Jelajah sendiri. Jadi pembaca memperbesar,
    lalu tujuh detik kemudian petanya terbang ke kota lain."""
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


# ----------------------------------------------------- perlindungan isi ---


def test_menyalin_ditolak_dan_papan_tempel_diisi_keterangan(halaman, situs):
    """Yang dijanjikan hanya ini: menyalin sambil lalu jadi tidak berhasil.
    Bukan bahwa isinya tidak bisa diambil sama sekali."""
    buka(halaman, situs, "/blog/kapan-peta-diam")

    hasil = halaman.evaluate("""() => {
        const ev = new ClipboardEvent('copy', {bubbles: true, cancelable: true,
                                               clipboardData: new DataTransfer()});
        document.querySelector('.article p').dispatchEvent(ev);
        return {dicegah: ev.defaultPrevented, isi: ev.clipboardData.getData('text/plain')};
    }""")
    assert hasil["dicegah"], "menyalin tidak dicegah"
    assert "Hendro Kuswantoro" in hasil["isi"]
    # Alamat halaman yang sedang dibuka, bukan alamat produksi: server uji
    # menjawab di 127.0.0.1, dan menuntut nama domain di sini akan menguji
    # tempat ujinya berjalan, bukan kodenya.
    assert halaman.url.split("?")[0] in hasil["isi"]


def test_teks_tidak_bisa_diblok_tetapi_kolom_isian_tetap_bisa(halaman, situs):
    buka(halaman, situs, "/blog/kapan-peta-diam")
    assert halaman.evaluate(
        "() => getComputedStyle(document.querySelector('.article p')).userSelect"
    ) == "none"

    # Kalau pengecualian ini hilang, setiap formulir dan halaman admin jadi
    # tidak bisa dipakai, dan cacatnya baru ketahuan lama sesudahnya.
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
    """Cetak ke PDF adalah jalan paling mudah membawa seluruh tulisan keluar,
    dan ia tidak menyentuh papan ketik sama sekali."""
    buka(halaman, situs, "/blog/kapan-peta-diam")
    halaman.emulate_media(media="print")
    terlihat = halaman.evaluate("""() => {
        const a = document.querySelector('.article');
        return a ? a.getClientRects().length : -1;
    }""")
    halaman.emulate_media(media="screen")
    assert terlihat == 0, "isi tulisan masih ikut tercetak"


def test_teksnya_tetap_ada_di_html_untuk_mesin_pencari(halaman, situs):
    """Perlindungan ini menaikkan ongkos menyalin, bukan menyembunyikan isi.
    Yang disembunyikan dari mesin pencari adalah halaman yang tidak ada."""
    buka(halaman, situs, "/blog/kapan-peta-diam")
    panjang = halaman.evaluate("() => document.querySelector('.article').textContent.length")
    assert panjang > 1000, f"isi tulisannya cuma {panjang} karakter di DOM"


# --------------------------------------------------------------- hidup ---


def test_jam_yogyakarta_berjalan_dan_benar(halaman, situs):
    """Satu satunya angka di halaman ini yang berubah sendiri, dan ia nyata:
    dihitung dari zona waktu Yogyakarta, bukan dari jam perangkat pembaca."""
    import datetime as dt

    buka(halaman, situs, "/about")
    tampil = halaman.locator("[data-jam]").first.inner_text().strip()
    assert len(tampil) == 5 and tampil[2] == ":", tampil

    benar = dt.datetime.now(dt.timezone(dt.timedelta(hours=7)))
    jam_benar = benar.strftime("%H:%M")
    # Satu menit toleransi: ujinya bisa berjalan persis saat menitnya berganti.
    assert abs(int(tampil[:2]) * 60 + int(tampil[3:])
               - (benar.hour * 60 + benar.minute)) <= 1, f"{tampil} vs {jam_benar}"


def test_kartu_punya_kilau_yang_mengikuti_kursor(halaman, situs):
    buka(halaman, situs, "/project")
    kartu = halaman.locator(".card").first

    # Digulir ke dalam layar lebih dulu. Kartu pertama di /project duduk di
    # y=982, di luar viewport 1280x720, dan peristiwa tetikus ke titik di
    # luar viewport tidak pernah sampai ke halaman sama sekali. Uji pertama
    # gagal karena itu, bukan karena kodenya.
    kartu.scroll_into_view_if_needed()
    halaman.wait_for_timeout(200)

    kotak = kartu.bounding_box()
    halaman.mouse.move(kotak["x"] + 30, kotak["y"] + 20)
    halaman.mouse.move(kotak["x"] + 60, kotak["y"] + 40, steps=4)
    halaman.wait_for_timeout(300)
    assert kartu.evaluate("el => el.style.getPropertyValue('--mx')") != ""
