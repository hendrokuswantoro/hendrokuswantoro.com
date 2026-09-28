from __future__ import annotations

import datetime as dt
import os
import re
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

KEPALA = (AKAR / "_headers").read_text(encoding="utf-8")
NGINX = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
KEAMANAN_TXT = (AKAR / ".well-known" / "security.txt").read_text(encoding="utf-8")


def _nilai(nama: str) -> str:
    for baris in KEPALA.splitlines():
        if baris.strip().startswith(nama + ":"):
            return baris.split(":", 1)[1].strip()
    raise AssertionError(f"_headers tidak menyebut {nama}")


@pytest.mark.parametrize("nama, nilai", [
    ("Cross-Origin-Opener-Policy", "same-origin"),
    ("Cross-Origin-Resource-Policy", "same-origin"),
    ("X-Permitted-Cross-Domain-Policies", "none"),
])
def test_isolasi_asal_terpasang_di_kedua_tempat(nama, nilai):
    assert _nilai(nama) == nilai
    blok_nginx = NGINX.count(f'add_header {nama} "{nilai}" always;')
    blok_nosniff = NGINX.count('add_header X-Content-Type-Options "nosniff" always;')
    assert blok_nginx == blok_nosniff, f"{nama} tidak ada di setiap blok nginx yang memasang header"


def test_fitur_peramban_yang_tidak_dipakai_ditolak():
    kebijakan = dict(
        bagian.split("=", 1) for bagian in (b.strip() for b in _nilai("Permissions-Policy").split(","))
    )
    for fitur in ("camera", "microphone", "geolocation", "usb", "serial", "hid", "payment",
                  "display-capture", "browsing-topics"):
        assert kebijakan.get(fitur) == "()", f"{fitur} tidak ditolak"
    assert kebijakan.get("fullscreen") == "(self)", "peta butuh layar penuh"


def test_csp_menolak_bingkai_dari_mana_pun():
    csp = _nilai("Content-Security-Policy")
    assert "frame-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-inline'" not in csp and "'unsafe-eval'" not in csp


def test_security_txt_mengikuti_rfc_9116():
    medan = dict(b.split(": ", 1) for b in KEAMANAN_TXT.strip().splitlines())
    assert medan["Contact"].startswith("mailto:")
    assert medan["Canonical"] == "https://www.hendrokuswantoro.com/.well-known/security.txt"
    habis = dt.datetime.fromisoformat(medan["Expires"].replace("Z", "+00:00"))
    sekarang = dt.datetime.now(dt.timezone.utc)
    assert habis > sekarang, "security.txt sudah kedaluwarsa, perbarui Expires"
    assert habis - sekarang <= dt.timedelta(days=366), "RFC 9116 meminta Expires kurang dari setahun"


def test_security_txt_ikut_terbit():
    assert ".well-known/security.txt" in (AKAR / "tools" / "bangun_situs.sh").read_text(encoding="utf-8")
    assert ".well-known/security.txt" in (AKAR / "tools" / "build_dist.py").read_text(encoding="utf-8")


psycopg = pytest.importorskip("psycopg")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from backend.core import surat  # noqa: E402
from backend.layanan import autentikasi  # noqa: E402
from konftes import EMAIL_UJI as EMAIL  # noqa: E402
from konftes import SANDI_UJI as SANDI  # noqa: E402
from konftes import ada_basis_data  # noqa: E402
from konftes import loop_untuk_psycopg as _loop_untuk_psycopg  # noqa: E402

DSN = os.environ.get("DSN", "")
butuh_db = pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data")

NAMA_COOKIE = "hk_refresh"
JALUR_COOKIE = "/api/v1/auth"


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


@pytest.fixture(autouse=True)
def bersihkan():
    if not ada_basis_data(DSN):
        yield
        return
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT now()")
        sejak = k.fetchone()[0]
    yield
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "UPDATE sesi SET dicabut_pada = now() WHERE dibuat_pada >= %s AND dicabut_pada IS NULL",
            (sejak,),
        )
        k.execute("DELETE FROM gagal_masuk WHERE pada >= %s", (sejak,))
        k.execute("DELETE FROM peristiwa_keamanan WHERE pada >= %s", (sejak,))
        s.commit()


def _masuk(klien) -> tuple[dict, str]:
    klien.cookies.clear()
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return {"Authorization": f"Bearer {j.json()['akses']}"}, j.cookies.get(NAMA_COOKIE)


def _perpanjang(klien, cookie: str):
    klien.cookies.clear()
    klien.cookies.set(NAMA_COOKIE, cookie, path=JALUR_COOKIE)
    return klien.post("/api/v1/auth/refresh")


def _hidup(cookie: str) -> bool:
    from backend.core import keamanan

    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "SELECT 1 FROM sesi WHERE token_hash = %s AND dicabut_pada IS NULL",
            (keamanan.ringkas(cookie),),
        )
        return k.fetchone() is not None


@butuh_db
def test_token_lama_yang_dipakai_lagi_mencabut_seluruh_sesi(klien, monkeypatch):
    monkeypatch.setattr(autentikasi, "TENGGANG_PUTAR_DETIK", 0)
    _, lain = _masuk(klien)
    _, lama = _masuk(klien)
    j = _perpanjang(klien, lama)
    assert j.status_code == 200, j.text
    baru = j.cookies.get(NAMA_COOKIE)

    ulang = _perpanjang(klien, lama)
    assert ulang.status_code == 401
    assert not _hidup(baru), "token pengganti pencuri tetap hidup"
    assert not _hidup(lain), "perangkat lain tetap hidup setelah pencurian terdeteksi"


@butuh_db
def test_dua_tab_yang_berebut_memperpanjang_tidak_dianggap_pencuri(klien):
    _, lain = _masuk(klien)
    _, lama = _masuk(klien)
    j = _perpanjang(klien, lama)
    assert j.status_code == 200
    baru = j.cookies.get(NAMA_COOKIE)
    assert _perpanjang(klien, lama).status_code == 401
    assert _hidup(baru) and _hidup(lain), "tab kedua dalam masa tenggang mengeluarkan semuanya"


@butuh_db
def test_perangkat_yang_dikeluarkan_tidak_memicu_pencabutan_massal(klien, monkeypatch):
    monkeypatch.setattr(autentikasi, "TENGGANG_PUTAR_DETIK", 0)
    _, dikeluarkan = _masuk(klien)
    kepala, sini = _masuk(klien)
    klien.cookies.clear()
    klien.cookies.set(NAMA_COOKIE, sini, path=JALUR_COOKIE)
    assert klien.post("/api/v1/auth/sesi/cabut-lain", headers=kepala).status_code == 200
    assert _perpanjang(klien, dikeluarkan).status_code == 401
    assert _hidup(sini), "perangkat yang dikeluarkan mengeluarkan pemiliknya sendiri"


@butuh_db
def test_sesi_punya_umur_mutlak(klien):
    from backend.core import keamanan

    _, cookie = _masuk(klien)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "UPDATE sesi SET awal = now() - interval '40 days' WHERE token_hash = %s",
            (keamanan.ringkas(cookie),),
        )
        s.commit()
    j = _perpanjang(klien, cookie)
    assert j.status_code == 401
    assert "terlalu lama" in j.text


@butuh_db
def test_putaran_mewarisi_awal_dan_tidak_melewati_batas(klien):
    from backend.core import keamanan

    _, cookie = _masuk(klien)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "UPDATE sesi SET awal = now() - interval '25 days' WHERE token_hash = %s",
            (keamanan.ringkas(cookie),),
        )
        s.commit()
    j = _perpanjang(klien, cookie)
    assert j.status_code == 200
    baru = j.cookies.get(NAMA_COOKIE)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "SELECT awal, kadaluarsa FROM sesi WHERE token_hash = %s", (keamanan.ringkas(baru),)
        )
        awal, kadaluarsa = k.fetchone()
    assert dt.datetime.now(dt.timezone.utc) - awal > dt.timedelta(days=24)
    assert kadaluarsa <= awal + dt.timedelta(days=30, seconds=5)


@butuh_db
@pytest.mark.parametrize("jalur", ["/api/v1/keamanan", "/api/v1/auth/sesi"])
def test_jawaban_peka_tidak_boleh_disimpan(klien, jalur):
    kepala, _ = _masuk(klien)
    j = klien.get(jalur, headers=kepala)
    assert j.headers.get("cache-control") == "no-store"


@butuh_db
def test_jawaban_masuk_tidak_boleh_disimpan(klien):
    klien.cookies.clear()
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.headers.get("cache-control") == "no-store"


@butuh_db
def test_isi_publik_tetap_boleh_disimpan(klien):
    j = klien.get("/api/v1/blog")
    assert j.headers.get("cache-control") != "no-store"


@butuh_db
def test_tebakan_sandi_berulang_dikabarkan_sekali(klien, monkeypatch):
    from backend.core import konfigurasi

    monkeypatch.setenv("SMTP_HOST", "")
    konfigurasi.pengaturan.cache_clear()
    maks = konfigurasi.pengaturan().masuk_gagal_maks
    sebelum = set(surat.KOTAK.glob("*.eml")) if surat.KOTAK.exists() else set()
    for _ in range(maks + 2):
        klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-sekali-bukan-ini"})
    baru = [
        p for p in surat.KOTAK.glob("*.eml")
        if p not in sebelum and "berulang kali" in p.read_text(encoding="utf-8", errors="ignore")
    ]
    assert len(baru) == 1, f"kabar tebakan sandi terkirim {len(baru)} kali"
    konfigurasi.pengaturan.cache_clear()


def test_kabar_tebakan_tidak_membawa_sandinya():
    kode = (AKAR / "backend" / "layanan" / "kabar.py").read_text(encoding="utf-8")
    potong = kode[kode.index("async def kabari_tebakan"):kode.index("async def kabari_perubahan_keamanan")]
    assert not re.search(r"\bsandi\b\s*[,)]", potong), "isi surat tebakan menyebut sandi yang diketik"
