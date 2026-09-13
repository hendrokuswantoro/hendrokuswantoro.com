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
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

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


# Porta tetap, dengan porta acak sebagai cadangan.
#
# Alasannya bukan kerapian melainkan Mapbox. Token petanya dibatasi per URL,
# dan pembatasan itu mencocokkan asal, bukan jalur. Porta yang berganti tiap
# kali uji dijalankan berarti asal yang tidak pernah bisa didaftarkan, dan
# ubinnya dijawab 403 selamanya. Dengan porta tetap, satu baris
# "http://127.0.0.1:8099" di console.mapbox.com cukup untuk seluruh mesin
# pengembangan.
PORTA_UJI = 8099


def _porta() -> int:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", PORTA_UJI))
            return PORTA_UJI
        except OSError:
            pass
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def situs():
    """Menyajikan situs statis persis seperti Cloudflare menyajikannya."""
    Penyaji.csp = _csp()
    porta = _porta()

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

    # Jawaban yang ditolak ikut dicatat beserta alamatnya.
    #
    # Pesan konsol untuk berkas yang gagal dimuat berbunyi "Failed to load
    # resource: the server responded with a status of 403 ()", tanpa menyebut
    # alamatnya sama sekali. Tanpa daftar ini, 403 dari ubin Mapbox yang
    # dibatasi per URL tidak bisa dibedakan dari 403 yang benar benar salah.
    p.tolakan = []
    p.on("response", lambda r: p.tolakan.append((r.url, r.status)) if r.status >= 400 else None)

    yield p
    konteks.close()


def buka(halaman: Page, situs: str, jalur: str) -> None:
    halaman.goto(f"{situs}{jalur}", wait_until="networkidle")


# --------------------------------------------------------------- sandi uji ---

# Rangkaian uji yang butuh basis data ikut masuk sebagai admin, dan selama ini
# ia mengandalkan sandi yang kebetulan terpasang di basis data pengembangan.
# Begitu pemiliknya mengganti sandinya sendiri, sebelas uji gagal sekaligus
# dengan pesan 401 yang tidak menyebut sebabnya sama sekali.
#
# Jadi ujinya memasang sandinya sendiri di awal sesi lalu MENGEMBALIKAN hash
# yang tadi ada di akhir sesi. Yang disimpan dan dikembalikan hashnya, bukan
# sandinya: sandinya memang tidak diketahui siapa pun di sini, dan memang
# tidak perlu diketahui.

SANDI_UJI = "sandi-uji-lokal-panjang"
EMAIL_UJI = "kuswantoro.hendro01@gmail.com"


def _dsn() -> str:
    sys.path.insert(0, str(AKAR / "tools"))
    from muat_env import muat

    muat()
    return os.environ.get("DSN", "")


@pytest.fixture(scope="session", autouse=True)
def sandi_admin_untuk_uji():
    dsn = _dsn()
    if not dsn:
        yield
        return

    try:
        import psycopg

        from backend.core.keamanan import hash_sandi
    except Exception:
        yield
        return

    try:
        with psycopg.connect(dsn, connect_timeout=3) as s, s.cursor() as k:
            k.execute("SELECT sandi_hash FROM users WHERE lower(email)=lower(%s)", (EMAIL_UJI,))
            baris = k.fetchone()
            if baris is None:
                yield
                return
            semula = baris[0]
            k.execute("UPDATE users SET sandi_hash=%s WHERE lower(email)=lower(%s)",
                      (hash_sandi(SANDI_UJI), EMAIL_UJI))
            s.commit()
    except Exception:
        yield
        return

    try:
        yield
    finally:
        with psycopg.connect(dsn) as s, s.cursor() as k:
            k.execute("UPDATE users SET sandi_hash=%s WHERE lower(email)=lower(%s)",
                      (semula, EMAIL_UJI))
            s.commit()
