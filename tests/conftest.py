import contextlib
import collections
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

os.environ.setdefault("LAJU_JUMLAH", "100000")

import http.server
import socket
import subprocess
import threading
import time

import pytest

from konftes import AKAR

os.environ.setdefault("FAKTOR_KEDUA_WAJIB", "false")

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError:
    Page = object  # type: ignore[assignment,misc]
    sync_playwright = None  # type: ignore[assignment]


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


PORTA_UJI = 8099

INANG_UJI = "localhost"


def _porta() -> int:
    def bebas(porta: int) -> bool:
        for keluarga, alamat in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            try:
                with socket.socket(keluarga) as s:
                    s.bind((alamat, porta))
            except OSError:
                return False
        return True

    if bebas(PORTA_UJI):
        return PORTA_UJI
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _server(keluarga: int, alamat: str, porta: int):
    class Loopback(http.server.ThreadingHTTPServer):
        address_family = keluarga
        daemon_threads = True
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            import sys
            if isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
                return
            super().handle_error(request, client_address)

    server = Loopback((alamat, porta), lambda *a, **k: Penyaji(*a, directory=str(AKAR), **k))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="session")
def situs():
    Penyaji.csp = _csp()
    porta = _porta()

    server = [_server(socket.AF_INET, "127.0.0.1", porta)]
    try:
        server.append(_server(socket.AF_INET6, "::1", porta))
    except OSError:
        pass

    try:
        yield f"http://{INANG_UJI}:{porta}"
    finally:
        for satu in server:
            satu.shutdown()


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

    p.tolakan = []
    p.on("response", lambda r: p.tolakan.append((r.url, r.status)) if r.status >= 400 else None)

    yield p
    konteks.close()


def buka(halaman: Page, situs: str, jalur: str) -> None:
    halaman.goto(f"{situs}{jalur}", wait_until="load")
    halaman.wait_for_selector("html[data-siap]", state="attached", timeout=15000)


from konftes import EMAIL_UJI, SANDI_UJI  # noqa: E402

TITIPAN = AKAR / "cadangan" / "sandi-admin-sebelum-uji.txt"


def _titipan_tulis(hash_asli: str) -> None:
    TITIPAN.parent.mkdir(parents=True, exist_ok=True)
    TITIPAN.write_text(hash_asli, encoding="utf-8")


def _titipan_baca() -> str | None:
    if not TITIPAN.exists():
        return None
    nilai = TITIPAN.read_text(encoding="utf-8").strip()
    return nilai or None


def _titipan_hapus() -> None:
    with contextlib.suppress(OSError):
        TITIPAN.unlink()


def _dsn() -> str:
    sys.path.insert(0, str(AKAR / "tools"))
    from muat_env import muat

    muat()
    return os.environ.get("DSN", "")


TITIPAN_FAKTOR = AKAR / "cadangan" / "faktor-kedua-sebelum-uji.json"
KOLOM_FAKTOR = ("totp_rahasia", "totp_aktif_pada", "email_terverifikasi_pada")


@pytest.fixture(scope="session", autouse=True)
def faktor_kedua_untuk_uji():
    import json

    dsn = _dsn()
    if not dsn:
        yield
        return

    try:
        import psycopg
    except Exception:
        yield
        return

    def tulis(nilai):
        TITIPAN_FAKTOR.parent.mkdir(parents=True, exist_ok=True)
        TITIPAN_FAKTOR.write_text(json.dumps(nilai, default=str), encoding="utf-8")

    def pulihkan(simpanan):
        kolom, kode = simpanan["kolom"], simpanan["kode"]
        with psycopg.connect(dsn) as s, s.cursor() as k:
            k.execute(
                "UPDATE users SET totp_rahasia=%s, totp_aktif_pada=%s, "
                "email_terverifikasi_pada=%s WHERE lower(email)=lower(%s)",
                (*kolom, EMAIL_UJI),
            )
            k.execute("SELECT id FROM users WHERE lower(email)=lower(%s)", (EMAIL_UJI,))
            baris = k.fetchone()
            if baris and kode:
                k.execute("DELETE FROM kode_pemulihan WHERE pengguna_id=%s", (baris[0],))
                for satu in kode:
                    k.execute(
                        "INSERT INTO kode_pemulihan (pengguna_id, kode_hash, dibuat_pada, "
                        "dipakai_pada) VALUES (%s, %s, %s, %s)",
                        (baris[0], *satu),
                    )
            s.commit()

    try:
        with psycopg.connect(dsn, connect_timeout=3) as s, s.cursor() as k:
            if TITIPAN_FAKTOR.exists():
                with contextlib.suppress(Exception):
                    pulihkan(json.loads(TITIPAN_FAKTOR.read_text(encoding="utf-8")))

            k.execute(
                f"SELECT id, {', '.join(KOLOM_FAKTOR)} FROM users "
                "WHERE lower(email)=lower(%s)",
                (EMAIL_UJI,),
            )
            baris = k.fetchone()
            if baris is None:
                yield
                return

            k.execute(
                "SELECT kode_hash, dibuat_pada, dipakai_pada FROM kode_pemulihan "
                "WHERE pengguna_id=%s ORDER BY dibuat_pada",
                (baris[0],),
            )
            semula = {"kolom": list(baris[1:]), "kode": [list(r) for r in k.fetchall()]}
            tulis(semula)
    except Exception:
        yield
        return

    try:
        yield
    finally:
        with contextlib.suppress(Exception):
            pulihkan(semula)
        with contextlib.suppress(OSError):
            TITIPAN_FAKTOR.unlink()


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
            tertinggal = _titipan_baca()
            if tertinggal:
                k.execute("UPDATE users SET sandi_hash=%s WHERE lower(email)=lower(%s)",
                          (tertinggal, EMAIL_UJI))
                s.commit()

            k.execute("SELECT sandi_hash FROM users WHERE lower(email)=lower(%s)", (EMAIL_UJI,))
            baris = k.fetchone()
            if baris is None:
                yield
                return
            semula = baris[0]
            _titipan_tulis(semula)
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
        _titipan_hapus()


TENGGAT_SERVER_DETIK = 45


def _porta_bebas() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _ada_basis_data() -> bool:
    sys.path.insert(0, str(AKAR / "tools"))
    from basis_data_hidup import dsn, hidup

    return hidup(dsn())


@pytest.fixture(scope="module")
def server_admin():
    if not _ada_basis_data():
        pytest.skip("tidak ada basis data. cd infrastructure && docker compose up -d")

    porta = _porta_bebas()
    asal = f"http://localhost:{porta}"

    lingkungan = dict(os.environ)
    lingkungan["WEBAUTHN_RP_ID"] = "localhost"
    lingkungan["WEBAUTHN_ASAL"] = f'["{asal}"]'
    lingkungan["COOKIE_AMAN"] = "false"

    proses = subprocess.Popen(
        [sys.executable, str(AKAR / "backend" / "jalan.py"), "--port", str(porta)],
        cwd=str(AKAR), env=lingkungan,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    catatan: collections.deque[str] = collections.deque(maxlen=1000)

    def kuras() -> None:
        for baris in proses.stdout:  # type: ignore[union-attr]
            catatan.append(baris)

    utas = threading.Thread(target=kuras, daemon=True)
    utas.start()

    def ekor(bita: int = 800) -> str:
        return "".join(catatan)[-bita:]

    import urllib.error
    import urllib.request

    batas = time.time() + TENGGAT_SERVER_DETIK
    hidup = False
    while time.time() < batas:
        if proses.poll() is not None:
            utas.join(timeout=2)
            pytest.skip("server berhenti sendiri: " + ekor())
        try:
            with urllib.request.urlopen(f"{asal}/health", timeout=2) as j:
                if j.status == 200:
                    hidup = True
                    break
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)

    if not hidup:
        proses.terminate()
        pytest.skip("server tidak menjawab dalam waktu yang diberikan")

    try:
        yield asal
    finally:
        proses.terminate()
        try:
            proses.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proses.kill()


def tab_dengan_otentikator(peramban):
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()

    cdp = konteks.new_cdp_session(tab)
    cdp.send("WebAuthn.enable")
    hasil = cdp.send("WebAuthn.addVirtualAuthenticator", {
        "options": {
            "protocol": "ctap2",
            "transport": "internal",
            "hasResidentKey": True,
            "hasUserVerification": True,
            "isUserVerified": True,
            "automaticPresenceSimulation": True,
        }
    })
    tab.authenticator = hasil["authenticatorId"]
    tab.galat = []
    tab.on("pageerror", lambda e: tab.galat.append(str(e)))
    return konteks, tab


def masuk_admin(tab, asal):
    tab.goto(f"{asal}/admin", wait_until="domcontentloaded")
    tab.wait_for_selector("#tombol-masuk")
    tab.fill("#email", EMAIL_UJI)
    tab.fill("#sandi", SANDI_UJI)
    tab.click("#tombol-masuk")
    tab.wait_for_selector("#layar-daftar:not(.sembunyi)", timeout=15000)
