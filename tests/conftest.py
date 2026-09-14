"""Pembantu bersama seluruh rangkaian uji.

Selain menaruh konftes.py di jalur impor, berkas ini memegang fixture
peramban: server statis yang menyajikan situs dengan CSP yang sama persis
dengan yang disajikan Cloudflare, dan halaman Playwright yang mengumpulkan
galat konsol.

Fixture-nya ada di sini, bukan di salah satu berkas uji, karena dipakai dua
berkas. Fixture yang tinggal di satu berkas uji tidak pernah terlihat berkas
lain, dan kegagalannya berbunyi "fixture not found" yang menyesatkan.
"""

import contextlib
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
import subprocess
import threading
import time

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
    """Membuka halaman lalu menunggu sampai app.js selesai menyiapkannya.

    Dulu yang ditunggu "networkidle", dan itu salah untuk satu halaman:
    /project memuat peta, peta terus meminta ubin selama masih terlihat, dan
    jaringan yang tidak pernah diam selama 500 ms tidak pernah memenuhi
    syarat itu. Hasilnya Page.goto berjalan sampai batas 30 detik lalu gagal,
    dengan pesan yang hanya menyebut timeout dan tidak menyebut peta sama
    sekali. Di mesin ini ia lolos justru karena tokennya dibatasi per URL:
    tiap ubin dijawab 403 dalam sekejap, jaringannya diam, dan ujinya hijau
    karena petanya rusak. Di CI, OpenFreeMap menjawab sungguhan, ubinnya
    mengalir, dan ujinya gagal.

    Sekarang yang ditunggu `data-siap`, dipasang app.js di akhir boot(). Itu
    pernyataan dari kode yang menyiapkan halamannya, bukan tebakan dari
    perilaku jaringan. Uji yang butuh petanya benar benar siap memanggil
    `peta_siap()` sendiri, dan itu memang urusan uji peta, bukan urusan
    pembuka halaman.
    """
    halaman.goto(f"{situs}{jalur}", wait_until="load")
    halaman.wait_for_selector("html[data-siap]", state="attached", timeout=15000)


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

# Titipan hash asli, supaya pengembaliannya selamat dari sesi yang mati.
#
# Rancangan "simpan di memori, kembalikan di finally" hanya benar selama
# prosesnya hidup sampai akhir. Pada 14 September 2026 satu jalannya pytest
# dihentikan paksa di tengah, finally-nya tidak pernah jalan, dan sandi uji
# tertinggal terpasang di akun admin. Yang lebih buruk: sesi berikutnya
# membaca hash yang sudah tertukar itu sebagai "yang asli" lalu menyimpannya,
# sehingga sandi aslinya hilang untuk selamanya, bukan sekadar tertunda
# kembalinya.
#
# Karena itu hash aslinya dititipkan ke berkas lebih dulu. Sesi berikutnya
# mengembalikannya sebelum mengerjakan apa pun, jadi satu sesi yang mati
# paling jauh cuma menunda, tidak lagi menghancurkan.
#
# Isinya hash, bukan sandi, dan letaknya di cadangan/ yang sudah diabaikan
# git. Berkasnya dihapus begitu pengembaliannya berhasil.
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


# Keadaan faktor kedua milik akun sungguhan, dijaga dengan cara yang sama.
#
# `tests/test_keamanan_alur.py` menjalankan
#
#     UPDATE users SET totp_rahasia = NULL, totp_aktif_pada = NULL,
#                      email_terverifikasi_pada = NULL
#
# tanpa WHERE, sebab tiap uji memang harus mulai dari akun yang faktor
# keduanya mati. Yang tidak disadari: di basis data pengembangan tabel itu
# berisi akun sungguhan, jadi sekali rangkaian uji dijalankan, TOTP yang sudah
# dipasang ikut mati dan email yang sudah terbukti kembali jadi belum terbukti.
# Tidak ada galat dan tidak ada peringatan. Yang terjadi cuma authenticator
# yang tiba tiba tidak diminta lagi saat masuk, dan itu penurunan keamanan yang
# tidak diputuskan siapa pun.
#
# Pada 14 September 2026 ketiganya kebetulan memang sudah kosong, jadi tidak
# ada yang hilang. Jebakannya tetap dipasangi penjaga sekarang, bukan nanti
# sesudah TOTP dinyalakan.
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
        """Mengembalikan kolom faktor kedua DAN kode pemulihannya.

        Kode pemulihan ikut, dan itu bukan kelebihan kehati hatian. Mematikan
        TOTP memang menghapus seluruh kode pemulihan, dan itu perilaku yang
        benar. Tetapi ujinya menjalankan hal itu pada akun sungguhan, jadi
        tanpa baris ini akun pemiliknya berakhir dalam keadaan ganjil:
        rahasia TOTP-nya kembali, sedangkan kode pemulihan yang sudah ia catat
        di tempat aman tidak berlaku lagi, tanpa satu pun pemberitahuan.
        """
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
            # Sesi sebelumnya mungkin mati sebelum sempat mengembalikan.
            # Kalau titipannya masih ada, itu yang benar, bukan yang ada di
            # basis data sekarang.
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


# --------------------------------------------------- server admin sungguhan ---
#
# Dipakai uji peramban yang perlu halaman admin BESERTA API-nya, bukan situs
# statis. Ditaruh di sini, bukan di salah satu berkas uji, sebab dua berkas
# sudah memakainya dan fixture yang tinggal di satu berkas uji tidak pernah
# terlihat berkas lain.

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
    """API dan halaman admin di http://localhost:<porta>.

    Ber-scope MODUL, bukan sesi, dan itu bukan pemborosan. Dengan satu server
    dipakai bersama seluruh berkas uji peramban, berkas yang jalan belakangan
    gagal seluruhnya sementara berkas yang sama lolos kalau dijalankan
    sendirian. Servernya melayani berkas pertama dengan baik lalu berhenti
    menjawab; `Page.goto` pun habis waktu tiga puluh detik. Sebabnya belum
    saya temukan, dan memberi tiap berkas server sendiri menutup gejalanya
    dengan ongkos beberapa detik.

    Namanya WAJIB localhost, bukan 127.0.0.1. WebAuthn menuntut rp_id berupa
    nama domain, dan alamat IP bukan nama domain, jadi seluruh uji passkey
    lewat peramban hanya mungkin di alamat bernama. WEBAUTHN_ASAL harus
    menyebut porta acaknya juga, sebab asal dibandingkan lengkap dengan
    portanya.

    Dijalankan sebagai subproses lewat `backend/jalan.py`, bukan di dalam
    utas, sebab berkas itulah yang tahu cara menghindari ProactorEventLoop
    yang ditolak psycopg di Windows.
    """
    if not _ada_basis_data():
        pytest.skip("tidak ada basis data. cd infrastructure && docker compose up -d")

    porta = _porta_bebas()
    asal = f"http://localhost:{porta}"

    lingkungan = dict(os.environ)
    lingkungan["WEBAUTHN_RP_ID"] = "localhost"
    lingkungan["WEBAUTHN_ASAL"] = f'["{asal}"]'
    # Tanpa HTTPS, cookie ber-Secure tidak pernah tersimpan, dan sesi yang
    # tidak tersimpan terlihat persis seperti masuk yang gagal.
    lingkungan["COOKIE_AMAN"] = "false"

    proses = subprocess.Popen(
        [sys.executable, str(AKAR / "backend" / "jalan.py"), "--port", str(porta)],
        cwd=str(AKAR), env=lingkungan,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    import urllib.error
    import urllib.request

    batas = time.time() + TENGGAT_SERVER_DETIK
    hidup = False
    while time.time() < batas:
        if proses.poll() is not None:
            pytest.skip("server berhenti sendiri: " + proses.stdout.read()[-800:])
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
    """Satu konteks baru dengan authenticator maya Chrome sudah terpasang.

    Memakai fixture `peramban` yang sudah ada, bukan membuka Playwright kedua.
    Versi pertama membuka instans sendiri, dan akibatnya seluruh uji peramban
    lama gagal saat dijalankan bersama sama: "It looks like you are using
    Playwright Sync API inside the asyncio loop". Satu proses hanya boleh
    memegang satu Playwright sinkron.

    Ia membuat pasangan kunci sungguhan dan menandatangani sungguhan; yang
    tidak sungguhan cuma sensornya. Tanda tangannya tetap diverifikasi
    pustaka `webauthn` yang sama dengan yang dipakai produksi.
    """
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()

    cdp = konteks.new_cdp_session(tab)
    cdp.send("WebAuthn.enable")
    hasil = cdp.send("WebAuthn.addVirtualAuthenticator", {
        "options": {
            # "internal" adalah sensor yang menempel pada perangkatnya, yaitu
            # yang orang sebut sidik jari. Itu yang dituntut halaman admin
            # lewat AuthenticatorAttachment.PLATFORM.
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
    """Masuk dengan sandi ke halaman admin, lalu menunggu dashboardnya siap."""
    tab.goto(f"{asal}/admin", wait_until="domcontentloaded")
    tab.wait_for_selector("#tombol-masuk")
    tab.fill("#email", EMAIL_UJI)
    tab.fill("#sandi", SANDI_UJI)
    tab.click("#tombol-masuk")
    tab.wait_for_selector("#layar-daftar:not(.sembunyi)", timeout=15000)
