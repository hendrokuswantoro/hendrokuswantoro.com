"""Autentikasi dan otorisasi. Bab 15.8 sampai 15.11.

Yang diuji bukan "bisa masuk", melainkan **yang seharusnya ditolak benar
benar ditolak**: token bekas pakai, sesi yang sudah dicabut, token tanpa
peran admin, dan tebakan sandi berulang.

Dilewati kalau tidak ada basis data.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

from backend.core import keamanan  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not bisa_terhubung(), reason="tidak ada basis data")


@pytest.fixture(autouse=True)
def bersihkan_kunci():
    """Uji penguncian meninggalkan catatan gagal. Dibersihkan supaya uji
    berikutnya tidak ikut terkunci."""
    yield
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("DELETE FROM gagal_masuk")
        s.commit()


@pytest.fixture
def klien():
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


def masuk(klien) -> str:
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return j.json()["akses"]


# ----------------------------------------------------------------- sandi ---


def test_sandi_disimpan_sebagai_argon2id():
    """Bab 15.8. Sandi apa adanya di basis data adalah kebocoran yang sudah
    terjadi, tinggal menunggu ketahuan."""
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT sandi_hash FROM users WHERE lower(email)=lower(%s)", (EMAIL,))
        h = k.fetchone()[0]
    assert h.startswith("$argon2id$"), "sandi tidak di-hash dengan Argon2id"
    assert SANDI not in h


def test_hash_yang_sama_tidak_pernah_sama_dua_kali():
    """Garam acak. Tanpa itu, dua orang bersandi sama punya hash sama."""
    assert keamanan.hash_sandi("kata-sandi-uji") != keamanan.hash_sandi("kata-sandi-uji")


def test_verifikasi_sandi():
    h = keamanan.hash_sandi("benar-sekali-panjang")
    assert keamanan.sandi_cocok("benar-sekali-panjang", h)
    assert not keamanan.sandi_cocok("salah", h)
    assert not keamanan.sandi_cocok("benar-sekali-panjang", "bukan-hash")


# ----------------------------------------------------------------- token ---


def test_token_memeriksa_penerbit_dan_audience():
    """Melewatkan salah satunya berarti token sah dari sistem lain diterima."""
    import jwt

    from backend.core.konfigurasi import pengaturan

    token, _ = keamanan.buat_access_token("00000000-0000-0000-0000-000000000001", "admin")
    assert keamanan.baca_access_token(token) is not None

    palsu = jwt.encode(
        {"sub": "x", "iss": "situs-lain", "aud": "situs-lain",
         "iat": 0, "exp": 9_999_999_999},
        pengaturan().jwt_rahasia, algorithm="HS256",
    )
    assert keamanan.baca_access_token(palsu) is None, "penerbit asing diterima"


def test_token_kedaluwarsa_ditolak():
    import datetime as dt

    import jwt

    from backend.core.konfigurasi import pengaturan

    lampau = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
    token = jwt.encode(
        {"sub": "x", "peran": "admin", "iss": keamanan.PENERBIT, "aud": keamanan.UNTUK,
         "iat": lampau, "exp": lampau},
        pengaturan().jwt_rahasia, algorithm="HS256",
    )
    assert keamanan.baca_access_token(token) is None


def test_token_dengan_rahasia_lain_ditolak():
    import jwt

    token = jwt.encode(
        {"sub": "x", "peran": "admin", "iss": keamanan.PENERBIT, "aud": keamanan.UNTUK,
         "iat": 0, "exp": 9_999_999_999},
        "rahasia-yang-bukan-punya-kita", algorithm="HS256",
    )
    assert keamanan.baca_access_token(token) is None


# ------------------------------------------------------------------ alur ---


def test_masuk_dan_identitas(klien):
    akses = masuk(klien)
    j = klien.get("/api/v1/auth/saya", headers={"Authorization": f"Bearer {akses}"})
    assert j.status_code == 200
    assert j.json()["peran"] == "admin"


def test_refresh_ada_di_cookie_httponly(klien):
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert "hk_refresh" not in j.text, "refresh token bocor ke badan jawaban"
    kue = j.headers.get("set-cookie", "").lower()
    assert "httponly" in kue, "cookie refresh bisa dibaca JavaScript"
    assert "samesite=strict" in kue


def test_refresh_diputar_dan_yang_lama_mati(klien):
    """Bab 15.10. Token yang sudah diputar lalu muncul lagi berarti
    salinannya ada di tangan orang lain."""
    masuk(klien)
    lama = klien.cookies.get("hk_refresh")

    j = klien.post("/api/v1/auth/refresh")
    assert j.status_code == 200
    baru = klien.cookies.get("hk_refresh")
    assert baru != lama, "refresh token tidak diputar"

    klien.cookies.set("hk_refresh", lama)
    assert klien.post("/api/v1/auth/refresh").status_code == 401


def test_keluar_mencabut_sesi(klien):
    masuk(klien)
    assert klien.post("/api/v1/auth/logout").status_code == 204
    assert klien.post("/api/v1/auth/refresh").status_code == 401


def test_tanpa_token_401_bukan_403(klien):
    """401 berarti belum masuk, 403 berarti sudah masuk tetapi tidak boleh.
    Menukar keduanya membuat pesan galat menyesatkan."""
    j = klien.get("/api/v1/auth/saya")
    assert j.status_code == 401
    assert "bearer" in j.headers.get("www-authenticate", "").lower()


def test_peran_bukan_admin_ditolak_403(klien):
    """Bab 15.9: token yang sah belum tentu token yang berhak."""
    token, _ = keamanan.buat_access_token("00000000-0000-0000-0000-000000000002", "visitor")
    j = klien.get("/api/v1/auth/saya", headers={"Authorization": f"Bearer {token}"})
    assert j.status_code == 403


def test_sandi_salah_dan_email_asing_dijawab_sama(klien):
    """Jawaban yang berbeda memberi tahu penebak bahwa emailnya benar ada."""
    a = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-sekali-panjang"})
    b = klien.post("/api/v1/auth/login",
                   json={"email": "bukan-siapa-siapa@contoh.id", "sandi": "salah-sekali-panjang"})
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"]


def test_terkunci_sesudah_lima_gagal(klien):
    for _ in range(5):
        klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-salah-salah"})
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-salah-salah"})
    assert j.status_code == 429, "tebak sandi berulang tidak dibatasi"


def test_alamat_ip_tidak_disimpan_apa_adanya(klien):
    klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-lagi-panjang"})
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT alamat_hash FROM gagal_masuk ORDER BY pada DESC LIMIT 1")
        baris = k.fetchone()
    assert baris, "percobaan gagal tidak tercatat"
    assert len(baris[0]) == 64, "alamat tidak diringkas"
    assert "." not in baris[0] and ":" not in baris[0], "alamat IP tersimpan apa adanya"


def test_sandi_terlalu_pendek_ditolak_422(klien):
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "pendek"})
    assert j.status_code == 422
