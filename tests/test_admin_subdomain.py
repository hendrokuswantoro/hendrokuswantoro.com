from __future__ import annotations

import ipaddress
import re
import sys

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

import ip_cloudflare  # noqa: E402

INFRA = AKAR / "infrastructure"
NGINX = (INFRA / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
PASANG = (INFRA / "pasang.sh").read_text(encoding="utf-8")
ADMIN = "admin.hendrokuswantoro.com"


def _server(nama: str) -> str:
    for blok in re.split(r"\n(?=server \{)", NGINX):
        if re.search(rf"server_name {re.escape(nama)};", blok):
            return blok
    raise AssertionError(f"tidak ada server untuk {nama}")


def test_alamat_asli_hanya_dipercaya_dari_cloudflare():
    assert ip_cloudflare.nginx_baru(ip_cloudflare.baca()) == NGINX, (
        "set_real_ip_from di nginx tertinggal dari cloudflare-ip.txt, jalankan python tools/ip_cloudflare.py"
    )
    assert "real_ip_header CF-Connecting-IP;" in NGINX
    assert "real_ip_header X-Forwarded-For" not in NGINX, "X-Forwarded-For bisa dikarang pengirimnya"
    assert "real_ip_recursive" not in NGINX


def test_daftar_cloudflare_bukan_jaringan_yang_terlalu_lebar():
    daftar = ip_cloudflare.baca()
    assert len(daftar) >= 10
    for teks in daftar:
        jaringan = ipaddress.ip_network(teks)
        assert not jaringan.is_private, teks
        batas = 12 if jaringan.version == 4 else 29
        assert jaringan.prefixlen >= batas, f"{teks} terlalu lebar untuk dipercaya"


def test_firewall_hanya_membuka_443_untuk_cloudflare():
    assert "ufw default deny incoming" in PASANG
    assert "infrastructure/cloudflare-ip.txt" in PASANG
    assert 'ufw allow proto tcp from "$jaringan" to any port 443' in PASANG
    for terbuka in ("ufw allow 80/tcp", "ufw allow 443/tcp", "ufw allow http", "ufw allow https"):
        assert terbuka not in PASANG, f"{terbuka} membuka VPS untuk siapa pun, melewati Cloudflare"


def test_tidak_ada_http_dan_nama_asing_ditolak_sejak_jabat_tangan():
    assert "listen 80" not in NGINX and "listen [::]:80" not in NGINX
    bawaan = _server("_")
    assert "default_server" in bawaan and "ssl_reject_handshake on;" in bawaan
    assert "letsencrypt" not in NGINX and "certbot" not in PASANG


def test_sertifikat_origin_dipakai_di_setiap_server():
    for nama in ("hendrokuswantoro.com", "www.hendrokuswantoro.com", ADMIN):
        blok = _server(nama)
        assert "ssl_certificate     /etc/ssl/hendrokuswantoro/origin.pem;" in blok, nama
        assert "ssl_certificate_key /etc/ssl/hendrokuswantoro/origin.key;" in blok, nama
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in NGINX


def test_dashboard_dan_api_hanya_tinggal_di_subdomain_admin():
    www = _server("www.hendrokuswantoro.com")
    for jalur in ("/api/", "/admin", "/unggahan/", "/_next/"):
        assert f"{jalur} {{" not in www and f"{jalur}{{" not in www, f"www masih menyajikan {jalur}"
    assert "proxy_pass" not in www

    admin = _server(ADMIN)
    for awalan in ("location ^~ /admin {", "location /api/ {", "location /api/v1/auth/ {",
                   "location = /api/v1/admin/berkas {", "location /unggahan/ {", "location ^~ /_next/ {"):
        assert awalan in admin, awalan
    assert re.search(r"location / \{\s*return 308 https://www\.hendrokuswantoro\.com\$request_uri;", admin)


def test_subdomain_admin_tidak_diindeks_dan_api_tidak_boleh_memuat_apa_pun():
    admin = _server(ADMIN)
    kepala = admin[:admin.index("\n    location ")]
    assert 'add_header X-Robots-Tag "noindex, nofollow" always;' in kepala
    assert "Strict-Transport-Security" in kepala
    csp = re.search(r'add_header Content-Security-Policy "([^"]+)" always;', kepala).group(1)
    assert csp.startswith("default-src 'none';")
    assert "script-src" not in csp


def test_cookie_sesi_hanya_milik_nama_admin():
    from fastapi import Response

    import datetime as dt

    from backend.api.v1 import auth
    from backend.layanan.autentikasi import Masuk

    jawaban = Response()
    hasil = Masuk(
        akses="a", umur_detik=900, refresh="RAHASIA",
        refresh_kadaluarsa=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1),
        nama="Hendro", peran="admin",
    )
    auth.pasang_cookie(jawaban, hasil)

    cookie = jawaban.headers["set-cookie"].lower()
    assert "domain=" not in cookie, "cookie dengan Domain ikut terkirim ke seluruh subdomain"
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api/v1/auth" in cookie


def test_passkey_produksi_terikat_ke_nama_admin():
    contoh = (AKAR / ".env.example").read_text(encoding="utf-8")
    assert f"# Produksi : WEBAUTHN_RP_ID={ADMIN}" in contoh
    assert f"WEBAUTHN_RP_ID={ADMIN}" in PASANG
    assert f'WEBAUTHN_ASAL=["https://{ADMIN}"]' in PASANG
