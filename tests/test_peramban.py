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
    assert not halaman.galat, f"{jalur}: {halaman.galat[:3]}"


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


def test_peta_benar_benar_menggambar(halaman, situs):
    """Inti dari seluruh berkas ini.

    Peta ini sudah tiga kali rusak diam diam: sekali karena lapisan yang tidak
    didukung, sekali karena worker yang diblokir CSP, sekali karena berkas
    pustaka yang kurang. Ketiganya tidak menimbulkan galat apa pun; petanya
    hanya diam. Uji ini yang menggantikan mata manusia.
    """
    buka(halaman, situs, "/project")
    peta_siap(halaman)

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
