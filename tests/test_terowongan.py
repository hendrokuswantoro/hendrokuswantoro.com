from __future__ import annotations

import re
import sys
import time

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))

jwt = pytest.importorskip("jwt")
pytest.importorskip("starlette")
pytest.importorskip("httpx")

from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.core import konfigurasi, terowongan

NGINX = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
INANG = "admin.hendrokuswantoro.com"
TIM = "hendro"
AUD = "a" * 64
KUNCI = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KUNCI_LAIN = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(aud: str = AUD, tim: str = TIM, kunci=KUNCI, umur: int = 300) -> str:
    kini = int(time.time())
    muatan = {"aud": [aud], "iss": f"https://{tim}.cloudflareaccess.com", "iat": kini,
              "exp": kini + umur, "email": "kuswantoro.hendro01@gmail.com"}
    return jwt.encode(muatan, kunci, algorithm="RS256")


class _Kunci:
    key = KUNCI.public_key()


class _Klien:
    def get_signing_key_from_jwt(self, _token):
        return _Kunci()


def _aplikasi():
    async def admin(permintaan):
        return JSONResponse({"klien": permintaan.client.host},
                            headers={"X-HK-CSP": "default-src 'self'; script-src 'sha256-abc'"})

    async def api(permintaan):
        return JSONResponse({"klien": permintaan.client.host})

    async def lain(_permintaan):
        return JSONResponse({"isi": "rahasia"})

    rute = [Route("/admin", admin), Route("/api/v1/blog", api), Route("/docs", lain)]
    return terowongan.Terowongan(Starlette(routes=rute))


@pytest.fixture
def klien(monkeypatch):
    monkeypatch.setenv("TEROWONGAN_HOST", INANG)
    monkeypatch.setenv("ACCESS_TIM", TIM)
    monkeypatch.setenv("ACCESS_AUD", AUD)
    monkeypatch.setattr(terowongan, "_kunci", lambda _tim: _Klien())
    konfigurasi.pengaturan.cache_clear()
    yield TestClient(_aplikasi(), base_url=f"https://{INANG}", client=("127.0.0.1", 50000))
    konfigurasi.pengaturan.cache_clear()


def _dari_terowongan(**tambahan):
    kepala = {"cf-ray": "8a1b2c3d4e5f6a7b-SIN", "cf-connecting-ip": "203.0.113.9"}
    kepala.update(tambahan)
    return kepala


def test_tanpa_token_access_ditolak(klien):
    jawaban = klien.get("/admin", headers=_dari_terowongan())
    assert jawaban.status_code == 403
    assert jawaban.headers["strict-transport-security"].startswith("max-age=63072000")


@pytest.mark.parametrize("salah", [
    token(aud="b" * 64), token(tim="orang-lain"), token(kunci=KUNCI_LAIN), token(umur=-60), "bukan.jwt.sama-sekali",
], ids=["aud-lain", "tim-lain", "kunci-lain", "kedaluwarsa", "bukan-jwt"])
def test_token_access_yang_salah_ditolak(klien, salah):
    kepala = _dari_terowongan(**{"cf-access-jwt-assertion": salah})
    assert klien.get("/admin", headers=kepala).status_code == 403


def test_token_access_sah_diterima_dengan_header_keamanan(klien):
    jawaban = klien.get("/admin", headers=_dari_terowongan(**{"cf-access-jwt-assertion": token()}))
    assert jawaban.status_code == 200
    kepala = jawaban.headers
    assert kepala["content-security-policy"] == "default-src 'self'; script-src 'sha256-abc'"
    assert "x-hk-csp" not in kepala
    assert kepala["x-frame-options"] == "DENY"
    assert kepala["cross-origin-embedder-policy"] == "require-corp"
    assert "camera=(self)" in kepala["permissions-policy"]
    assert kepala["x-robots-tag"] == "noindex, nofollow"


def test_alamat_pembaca_dibaca_dari_cloudflare(klien):
    jawaban = klien.get("/api/v1/blog", headers=_dari_terowongan(**{"cf-access-jwt-assertion": token()}))
    assert jawaban.json()["klien"] == "203.0.113.9"
    assert jawaban.headers["content-security-policy"] == terowongan.CSP_API


def test_alamat_karangan_tidak_dipercaya(klien):
    kepala = _dari_terowongan(**{"cf-access-jwt-assertion": token(), "cf-connecting-ip": "bukan-alamat"})
    assert klien.get("/api/v1/blog", headers=kepala).json()["klien"] == "127.0.0.1"


def test_jalur_di_luar_dashboard_tidak_dibuka_lewat_terowongan(klien):
    jawaban = klien.get("/docs", headers=_dari_terowongan(**{"cf-access-jwt-assertion": token()}))
    assert jawaban.status_code == 404
    assert "rahasia" not in jawaban.text


def test_nama_host_localhost_dengan_penanda_cloudflare_tetap_dijaga(klien):
    jawaban = klien.get("http://localhost:8000/admin", headers={"cf-ray": "8a1b2c3d4e5f6a7b-SIN"})
    assert jawaban.status_code == 403


def test_nama_host_terowongan_tanpa_penanda_tetap_dijaga(klien):
    assert klien.get("/admin").status_code == 403


def test_localhost_biasa_tidak_berubah(klien):
    jawaban = klien.get("http://localhost:8000/admin")
    assert jawaban.status_code == 200
    assert "strict-transport-security" not in jawaban.headers
    assert jawaban.json()["klien"] == "127.0.0.1"


def test_terowongan_setengah_jadi_menolak_bukan_membuka(klien, monkeypatch):
    monkeypatch.setenv("ACCESS_AUD", "")
    konfigurasi.pengaturan.cache_clear()
    jawaban = klien.get("/admin", headers=_dari_terowongan(**{"cf-access-jwt-assertion": token()}))
    assert jawaban.status_code == 503
    assert "ACCESS_AUD" in jawaban.json()["detail"]


def _nginx(nama: str, blok: str) -> str:
    cocok = re.search(rf'add_header {nama} "([^"]*)" always;', blok)
    assert cocok, nama
    return cocok.group(1)


def test_header_terowongan_sama_dengan_nginx():
    admin = NGINX[NGINX.index("location ^~ /admin {"):]
    admin = admin[:admin.index("\n    }")]
    kita = terowongan.kepala_untuk("/admin")
    for nama in ("X-Content-Type-Options", "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
                 "Cross-Origin-Embedder-Policy", "X-Permitted-Cross-Domain-Policies", "X-Frame-Options",
                 "Referrer-Policy", "Strict-Transport-Security", "X-Robots-Tag", "Permissions-Policy"):
        assert kita[nama] == _nginx(nama, admin), nama
    bawaan = re.search(r'map \$upstream_http_x_hk_csp \$csp_admin \{\n\s+""\s+"([^"]*)";', NGINX)
    assert kita["Content-Security-Policy"] == bawaan.group(1)

    nxt = NGINX[NGINX.index("location ^~ /_next/ {"):]
    nxt = nxt[:nxt.index("\n    }")]
    kita = terowongan.kepala_untuk("/_next/static/a.js")
    for nama in ("Permissions-Policy", "X-Robots-Tag", "Content-Security-Policy"):
        assert kita[nama] == _nginx(nama, nxt), nama


def test_aplikasi_memasang_terowongan_paling_luar():
    isi = (AKAR / "backend" / "main.py").read_text(encoding="utf-8")
    urutan = re.findall(r"app\.add_middleware\((\w+)", isi)
    assert urutan[-1] == "Terowongan", "alamat pembaca harus diganti sebelum pembatas laju dan catatan membacanya"


def test_nginx_tidak_meneruskan_header_cloudflare_ke_aplikasi(monkeypatch):
    for nama in ("CF-Ray", "CF-Connecting-IP", "Cf-Access-Jwt-Assertion"):
        assert NGINX.count(f'proxy_set_header {nama} "";') == NGINX.count("proxy_pass http://hk_api;"), (
            f"{nama} yang lolos dari nginx membuat aplikasi di VPS mengira dirinya di balik terowongan, "
            "dan tanpa TEROWONGAN_HOST seluruh permintaannya dijawab 503"
        )

    for nama in ("TEROWONGAN_HOST", "ACCESS_TIM", "ACCESS_AUD"):
        monkeypatch.setenv(nama, "")
    konfigurasi.pengaturan.cache_clear()
    try:
        vps = TestClient(_aplikasi(), base_url="https://www.hendrokuswantoro.com")
        assert vps.get("/api/v1/blog").status_code == 200
        assert vps.get("/api/v1/blog", headers={"cf-ray": "8a1b2c3d4e5f6a7b-SIN"}).status_code == 503
    finally:
        konfigurasi.pengaturan.cache_clear()
