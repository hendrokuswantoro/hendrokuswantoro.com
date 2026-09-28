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


def tajuk_cloudflare() -> dict[str, str]:
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
    konf = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(
        encoding="utf-8"
    )
    tanda = re.search(r"^ *" + re.escape(awalan) + r" *\{$", konf, re.M)
    assert tanda, f"{awalan} tidak ada di konfigurasi nginx"
    mulai = tanda.start()
    blok = konf[mulai:konf.index("\n    }", mulai)]
    hasil = dict(re.findall(r'add_header ([A-Za-z-]+) "([^"]*)" always;', blok))
    if "add_header Content-Security-Policy $csp_admin always;" in blok:
        bawaan = re.search(r'map \$upstream_http_x_hk_csp \$csp_admin \{\s*""\s*"([^"]+)";', konf)
        assert bawaan, "peta $csp_admin tidak punya kebijakan bawaan"
        hasil["Content-Security-Policy"] = bawaan.group(1)
    assert "Content-Security-Policy" in hasil, f"{awalan} tidak menyebut CSP"
    return hasil


class _Situs(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _server(akar: pathlib.Path, tajuk: dict[str, str], porta: int):
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
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto(situs_bertajuk + "/project.html", wait_until="load")
        tab.evaluate("() => document.querySelector('.peta').scrollIntoView()")

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


@pytest.fixture(scope="module")
def dasbor_bertajuk():
    import shutil
    import tempfile

    sumber = AKAR / "backend" / "admin"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uji-csp-"))
    (tmp / "admin").mkdir()
    shutil.copy(sumber / "index.html", tmp / "admin" / "index.html")
    shutil.copy(sumber / "dasbor.css", tmp / "admin" / "dasbor.css")
    for skrip in sumber.glob("dasbor*.js"):
        shutil.copy(skrip, tmp / "admin" / skrip.name)
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
        assert tab.evaluate(
            "() => getComputedStyle(document.querySelector('.kartu')).borderRadius"
        ) != "0px", "lembar gaya dashboard tidak terpakai"
    finally:
        konteks.close()


def test_kebijakan_dashboard_lebih_ketat_daripada_situs_publik():
    csp = tajuk_nginx("location ^~ /admin")["Content-Security-Policy"]

    assert "'unsafe-inline'" not in csp, csp
    assert "sha256-" not in csp, "masih ada hash skrip sebaris di CSP dashboard"
    assert "mapbox" not in csp and "openfreemap" not in csp, (
        "dashboard tidak memuat peta, jadi asal ubin tidak perlu ada di sini"
    )
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


NEXT_OUT = AKAR / "next" / "out"


@pytest.fixture(scope="module")
def dasbor_next_bertajuk():
    halaman = NEXT_OUT / "admin" / "index.html"
    if not halaman.exists():
        pytest.skip("next/out belum dibangun")
    import sys

    sys.path.insert(0, str(AKAR))
    from backend.core.csp_admin import kebijakan

    tajuk = dict(tajuk_nginx("location ^~ /admin"))
    tajuk["Content-Security-Policy"] = kebijakan(halaman.read_text(encoding="utf-8"))
    srv = _server(NEXT_OUT, tajuk, 8133)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:8133/admin/"
    finally:
        srv.shutdown()


def test_dashboard_next_jalan_di_balik_kebijakan_yang_dihitung_aplikasi(peramban, dasbor_next_bertajuk):
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto(dasbor_next_bertajuk, wait_until="load")
        tab.wait_for_timeout(2500)
        langgar = _pelanggaran(tab)
        assert langgar == [], f"dashboard Next: {langgar}"
        assert tab.evaluate("() => typeof window.next === 'object'"), (
            "React di dashboard Next tidak pernah jalan, padahal tidak ada pelanggaran tercatat"
        )
    finally:
        konteks.close()


def test_kebijakan_tanpa_hash_memang_mematikan_dashboard_next(peramban):
    halaman = NEXT_OUT / "admin" / "index.html"
    if not halaman.exists():
        pytest.skip("next/out belum dibangun")
    srv = _server(NEXT_OUT, tajuk_nginx("location ^~ /admin"), 8134)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    konteks = peramban.new_context()
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    try:
        tab.goto("http://127.0.0.1:8134/admin/", wait_until="load")
        tab.wait_for_timeout(1500)
        assert _pelanggaran(tab), "tanpa hash pun tidak ada yang ditolak, jadi uji di atas tidak membuktikan apa pun"
    finally:
        konteks.close()
        srv.shutdown()
