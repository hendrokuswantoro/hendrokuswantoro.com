"""Tiap halaman disajikan BESERTA tajuk produksinya, lalu dibuka peramban.

Kenapa berkas ini ada, dan kenapa ia berbeda dari `test_terbit.py`.

`test_terbit.py` membaca `_headers` dan memastikan kalimatnya benar. Itu tidak
cukup, dan buktinya mahal: sampai 19 September 2026, CSP untuk `/admin` di
`infrastructure/nginx/hendrokuswantoro.conf` menolak SELURUH skrip dashboard.
Skripnya sebaris 44 KB, `script-src` di sana `'self'` ditambah satu hash
sha256 milik skrip tema tiga baris di situs publik, dan tidak ada yang cocok.

Akibatnya dashboard mati total di balik nginx: tombol Masuk tidak melakukan
apa apa, tidak ada satu pun pesan di layar, dan satu satunya jejaknya ada di
konsol peramban. Tidak ada satu pun uji yang menangkapnya, sebab tidak ada
satu pun uji yang pernah benar benar MENYAJIKAN halamannya dengan tajuk itu.
CLAUDE.md sudah menulis larangannya, dan larangan tanpa uji cuma kalimat.

Yang dikerjakan di sini: tajuknya dibaca dari berkas yang benar benar dipakai
produksi, tidak diketik ulang, lalu halamannya disajikan dengan tajuk itu dan
dibuka Chromium sungguhan. Yang dihitung pelanggaran CSP, bukan kata kata di
dalam berkas konfigurasi.
"""

from __future__ import annotations

import http.server
import pathlib
import re
import socketserver
import threading

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban


# ----------------------------------------------------------- tajuk aslinya ---


def tajuk_cloudflare() -> dict[str, str]:
    """Tajuk untuk `/*` di `_headers`, yaitu yang berlaku untuk tiap halaman."""
    baris = (AKAR / "_headers").read_text(encoding="utf-8").splitlines()
    hasil: dict[str, str] = {}
    di_dalam = False
    for satu in baris:
        if satu.startswith("#"):
            continue
        if not satu.strip():
            continue
        if not satu.startswith(" "):
            di_dalam = satu.strip() == "/*"
            continue
        if di_dalam and ":" in satu:
            nama, _, nilai = satu.strip().partition(":")
            hasil[nama.strip()] = nilai.strip()
    assert "Content-Security-Policy" in hasil, "_headers tidak menyebut CSP untuk /*"
    return hasil


def tajuk_nginx(awalan: str) -> dict[str, str]:
    """Tajuk `add_header` di dalam satu `location` pada konfigurasi nginx."""
    konf = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(
        encoding="utf-8"
    )
    # Dicari yang benar benar membuka blok, yaitu yang diakhiri "{" di baris
    # yang sama. Nama location yang sama juga muncul di dalam komentar di
    # atasnya, dan yang pertama ketemu di sana bukan bloknya.
    tanda = re.search(r"^ *" + re.escape(awalan) + r" *\{$", konf, re.M)
    assert tanda, f"{awalan} tidak ada di konfigurasi nginx"
    mulai = tanda.start()
    blok = konf[mulai:konf.index("\n    }", mulai)]
    hasil = dict(re.findall(r'add_header ([A-Za-z-]+) "([^"]*)" always;', blok))
    assert "Content-Security-Policy" in hasil, f"{awalan} tidak menyebut CSP"
    return hasil


# ------------------------------------------------------------- servernya ---


class _Situs(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _server(akar: pathlib.Path, tajuk: dict[str, str], porta: int):
    """Server berkas statis yang memasang tajuk yang diberikan pada tiap jawaban."""

    class Tangan(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(akar), **k)

        def end_headers(self):
            for nama, nilai in tajuk.items():
                self.send_header(nama, nilai)
            super().end_headers()

        def log_message(self, *a):
            pass

    return _Situs(("127.0.0.1", porta), Tangan)


def _pelanggaran(tab) -> list[str]:
    """Pelanggaran CSP yang dilaporkan halamannya sendiri.

    Dibaca dari peristiwa `securitypolicyviolation`, bukan dari teks pesan
    konsol. Pesan konsol berbeda kalimatnya antar peramban dan antar versi;
    peristiwanya tidak.
    """
    return tab.evaluate("() => window.__pelanggaranCsp || []")


def _pasang_pengintai(tab) -> None:
    tab.add_init_script("""
      window.__pelanggaranCsp = [];
      document.addEventListener('securitypolicyviolation', (p) => {
        window.__pelanggaranCsp.push(
          p.effectiveDirective + ' menolak ' + (p.blockedURI || 'inline')
        );
      });
    """)


# ------------------------------------------------------------ situs publik ---

HALAMAN = ["/", "/about.html", "/project.html", "/blog/", "/blog/kapan-peta-diam.html",
           "/parkir-jogja.html", "/404.html"]


@pytest.fixture(scope="module")
def situs_bertajuk():
    srv = _server(AKAR, tajuk_cloudflare(), 8131)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:8131"
    finally:
        srv.shutdown()


@pytest.mark.parametrize("jalur", HALAMAN)
def test_halaman_tidak_melanggar_kebijakannya_sendiri(peramban, situs_bertajuk, jalur):
    """Tajuknya dibaca dari `_headers`, bukan diketik ulang di sini."""
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto(situs_bertajuk + jalur, wait_until="load")
        tab.wait_for_timeout(1200)
        langgar = _pelanggaran(tab)
        assert langgar == [], f"{jalur}: {langgar}"
    finally:
        konteks.close()


def test_peta_tidak_melanggar_kebijakannya_sendiri(peramban, situs_bertajuk):
    """Peta dimuat belakangan lewat IntersectionObserver, jadi ia perlu
    digulir ke layar dulu. Ia juga bagian yang paling banyak menuntut
    kelonggaran CSP: pekerja blob, tekstur data URL, dan ubin dari luar."""
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto(situs_bertajuk + "/project.html", wait_until="load")
        tab.evaluate("() => document.querySelector('.peta').scrollIntoView()")

        # Ditunggu sampai petanya benar benar berdiri. Tanpa ini, "tidak ada
        # pelanggaran" bisa berarti "tidak ada yang dimuat", dan itu uji yang
        # lulus tanpa memeriksa apa apa. Ubinnya boleh gagal, sebab token
        # Mapbox belum tentu ada di mesin ini; yang dituntut MapLibre-nya
        # sendiri sudah jalan.
        #
        # Ditunggu dengan gelung sendiri, bukan `wait_for_function`. Yang
        # terakhir menyuntikkan pemantaunya lewat eval, dan eval memang
        # dilarang kebijakan yang sedang diuji. Kegagalannya berbunyi
        # "Refused to evaluate a string as JavaScript", yaitu kebijakannya
        # bekerja dengan benar terhadap alat ujinya sendiri.
        for _ in range(50):
            if tab.evaluate("() => !!window.HK_PETA_MAP"):
                break
            tab.wait_for_timeout(500)
        else:
            pytest.fail("peta tidak pernah dibuat dalam 25 detik")
        tab.wait_for_timeout(3000)

        langgar = _pelanggaran(tab)
        assert langgar == [], f"peta: {langgar}"
    finally:
        konteks.close()


# --------------------------------------------------------- dashboard admin ---


@pytest.fixture(scope="module")
def dasbor_bertajuk():
    """Halaman dashboard beserta kedua berkas asetnya, di bawah /admin.

    Disusun jadi pohon sementara supaya alamatnya sama persis dengan yang
    dipakai produksi: /admin, /admin/dasbor.css, /admin/dasbor.js.
    """
    import shutil
    import tempfile

    sumber = AKAR / "backend" / "admin"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uji-csp-"))
    (tmp / "admin").mkdir()
    shutil.copy(sumber / "index.html", tmp / "admin" / "index.html")
    shutil.copy(sumber / "dasbor.css", tmp / "admin" / "dasbor.css")
    for skrip in sumber.glob("dasbor*.js"):
        shutil.copy(skrip, tmp / "admin" / skrip.name)
    # Huruf yang dilayani backend di /admin/, supaya font-src ikut diuji
    # dengan berkas yang benar benar dimuat, bukan dengan 404.
    for tebal in ("400", "600", "700"):
        shutil.copy(
            AKAR / "assets" / "fonts" / f"poppins-v24-{tebal}-latin.woff2",
            tmp / "admin" / f"poppins-{tebal}.woff2",
        )

    srv = _server(tmp, tajuk_nginx("location ^~ /admin"), 8132)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:8132/admin/"
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


def test_dashboard_benar_benar_jalan_di_balik_kebijakannya(peramban, dasbor_bertajuk):
    """Uji yang seharusnya ada sejak CSP untuk /admin ditulis.

    Yang diperiksa bukan ada tidaknya pelanggaran saja, melainkan apakah
    skripnya benar benar jalan. Halaman yang seluruh skripnya ditolak tetap
    tergambar rapi dan tetap tidak melakukan apa apa.
    """
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto(dasbor_bertajuk, wait_until="load")
        tab.wait_for_timeout(1200)

        langgar = _pelanggaran(tab)
        assert langgar == [], f"dashboard: {langgar}"

        assert tab.evaluate("() => typeof panggil === 'function'"), (
            "skrip dashboard tidak jalan, padahal tidak ada pelanggaran yang "
            "tercatat. Periksa apakah berkasnya memang terkirim."
        )
        assert tab.evaluate("() => !!document.getElementById('tombol-masuk').onclick"), (
            "tombol Masuk tidak punya penanganan, jadi halamannya diam"
        )
        # Gayanya juga sampai: tanpa lembar gayanya, kartunya tidak berlatar.
        assert tab.evaluate(
            "() => getComputedStyle(document.querySelector('.kartu')).borderRadius"
        ) != "0px", "lembar gaya dashboard tidak terpakai"
    finally:
        konteks.close()


def test_kebijakan_dashboard_lebih_ketat_daripada_situs_publik():
    """Dashboard tidak memuat peta dan tidak punya skrip sebaris, jadi ia
    tidak perlu satu pun kelonggaran yang dipakai situs publik.

    Dijaga supaya kelonggaran tidak menyelinap balik lewat penyalinan."""
    csp = tajuk_nginx("location ^~ /admin")["Content-Security-Policy"]

    assert "'unsafe-inline'" not in csp, csp
    assert "sha256-" not in csp, "masih ada hash skrip sebaris di CSP dashboard"
    assert "mapbox" not in csp and "openfreemap" not in csp, (
        "dashboard tidak memuat peta, jadi asal ubin tidak perlu ada di sini"
    )
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
