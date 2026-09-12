"""Pembantu bersama seluruh rangkaian uji.

Selain menaruh konftes.py di jalur impor, berkas ini memegang fixture
peramban: server statis yang menyajikan situs dengan CSP yang sama persis
dengan yang disajikan Cloudflare, dan halaman Playwright yang mengumpulkan
galat konsol.

Fixture-nya ada di sini, bukan di salah satu berkas uji, karena dipakai dua
berkas. Fixture yang tinggal di satu berkas uji tidak pernah terlihat berkas
lain, dan kegagalannya berbunyi "fixture not found" yang menyesatkan.
"""

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Pembatas laju menghitung per alamat, dan seluruh rangkaian uji datang dari
# satu alamat yang sama, "testclient". Dengan batas produksi 120 permintaan
# per menit, berkas uji yang dijalankan sendiri sendiri lolos sedangkan yang
# dijalankan bersama sama mulai dijawab 429 di tengah jalan, dan pesan
# gagalnya menyesatkan: ia berbunyi seolah passkey-nya yang ditolak.
#
# Yang dinaikkan hanya batas laju, bukan penguncian setelah lima sandi salah.
# Keduanya sama sama menjawab 429 tetapi mekanismenya berbeda, dan justru
# karena batas laju dinaikkan di sini, 429 di test_auth.py hanya mungkin
# datang dari penguncian yang memang sedang diujinya.
os.environ.setdefault("LAJU_JUMLAH", "100000")

import http.server
import socket
import threading

import pytest

from konftes import AKAR

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError:  # playwright belum terpasang, fixture-nya tidak akan dipakai
    Page = object  # type: ignore[assignment,misc]
    sync_playwright = None  # type: ignore[assignment]


# CSP yang sama dengan yang disajikan Cloudflare. Tanpa ini, uji berjalan di
# bawah aturan yang lebih longgar daripada produksi, dan justru kegagalan
# akibat CSP yang paling sulit ditemukan belakangan: pelanggaran di dalam
# worker tidak muncul di konsol halaman sama sekali.
def _csp() -> str:
    for baris in (AKAR / "_headers").read_text(encoding="utf-8").splitlines():
        if "Content-Security-Policy:" in baris:
            return baris.split(":", 1)[1].strip()
    raise RuntimeError("_headers kehilangan CSP-nya")


class Penyaji(http.server.SimpleHTTPRequestHandler):
    csp = ""

    def translate_path(self, path):
        import os

        hasil = super().translate_path(path)
        if not os.path.exists(hasil) and not os.path.splitext(hasil)[1]:
            if os.path.exists(hasil + ".html"):
                return hasil + ".html"
        return hasil

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", self.csp)
        super().end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture(scope="session")
def situs():
    """Menyajikan situs statis persis seperti Cloudflare menyajikannya."""
    Penyaji.csp = _csp()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", porta),
        lambda *a, **k: Penyaji(*a, directory=str(AKAR), **k),
    )
    utas = threading.Thread(target=server.serve_forever, daemon=True)
    utas.start()
    try:
        yield f"http://127.0.0.1:{porta}"
    finally:
        server.shutdown()


@pytest.fixture(scope="session")
def peramban():
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as galat:  # pragma: no cover
            pytest.skip(f"chromium belum diunduh: {galat}")
        yield b
        b.close()


@pytest.fixture
def halaman(peramban):
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    p = konteks.new_page()
    p.galat = []
    p.on("pageerror", lambda e: p.galat.append(str(e)))
    p.on("console", lambda m: p.galat.append(m.text) if m.type == "error" else None)
    yield p
    konteks.close()


def buka(halaman: Page, situs: str, jalur: str) -> None:
    halaman.goto(f"{situs}{jalur}", wait_until="networkidle")
