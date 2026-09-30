from __future__ import annotations

import re
import sys

from konftes import AKAR

sys.path.insert(0, str(AKAR))

from backend.core.csp_admin import hash_sebaris, kebijakan

NGINX = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
MAIN = (AKAR / "backend" / "main.py").read_text(encoding="utf-8")
VPS = (AKAR / ".github" / "workflows" / "vps.yml").read_text(encoding="utf-8")
UNIT = (AKAR / "infrastructure" / "systemd" / "hk-api.service").read_text(encoding="utf-8")


def _blok(awalan: str) -> str:
    tanda = re.search(r"^ *" + re.escape(awalan) + r" *\{$", NGINX, re.M)
    assert tanda, awalan
    return NGINX[tanda.start():NGINX.index("\n    }", tanda.start())]


def test_kebijakan_bawaan_nginx_sama_dengan_milik_aplikasi():
    bawaan = re.search(r'map \$upstream_http_x_hk_csp \$csp_admin \{\s*""\s*"([^"]+)";', NGINX)
    assert bawaan, "nginx tidak punya kebijakan bawaan untuk /admin"
    assert bawaan.group(1) == kebijakan(""), "kebijakan dashboard HTML di nginx dan di aplikasi berpisah"


def test_hanya_skrip_sebaris_yang_diberi_hash():
    html = (
        '<script src="/_next/a.js" async=""></script>'
        "<script>self.__next_f=[]</script>"
        "<script>self.__next_f=[]</script>"
        '<script type="module">x()</script>'
    )
    hasil = hash_sebaris(html)
    assert len(hasil) == 2, hasil
    csp = kebijakan(html)
    assert all(h in csp for h in hasil)
    assert "'unsafe-inline'" not in csp and "'unsafe-eval'" not in csp


def test_nginx_memakai_kebijakan_dari_aplikasi_dan_tidak_membocorkan_tajuknya():
    blok = _blok("location ^~ /admin")
    assert "add_header Content-Security-Policy $csp_admin always;" in blok
    assert "proxy_hide_header X-HK-CSP;" in blok
    assert 'X-HK-CSP' in MAIN and "kebijakan_admin(" in MAIN


def test_berkas_next_disajikan_nginx_dengan_tajuk_keamanan():
    blok = _blok("location ^~ /_next/")
    assert "alias /srv/hendrokuswantoro/app/next/out/_next/;" in blok
    assert "immutable" in blok
    for tajuk in ("X-Content-Type-Options", "Strict-Transport-Security", "Content-Security-Policy"):
        assert f"add_header {tajuk}" in blok, tajuk


def test_vps_menyalakan_dashboard_next_dan_deploy_membangunnya():
    assert "ADMIN_NEXT=1" in (AKAR / ".env.example").read_text(encoding="utf-8")
    assert "EnvironmentFile=/etc/hendrokuswantoro/env" in UNIT
    assert "npm run build" in VPS and "out/admin/index.html" in VPS
    assert VPS.index("npm run build") < VPS.index("rsync"), "next/out dikirim sebelum dibangun"
    assert "--exclude 'next/.next'" in VPS


def test_masuk_ulang_dari_sesi_lemah_tidak_menawarkan_wajah():
    halaman = (AKAR / "next" / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")
    masuk = (AKAR / "next" / "components" / "admin" / "MasukView.tsx").read_text(encoding="utf-8")
    spanduk = halaman[halaman.index("<strong>Akses kamu terbatas.</strong>"):]
    spanduk = spanduk[:spanduk.index("Masuk ulang")]
    assert "setUlangKuat(true)" in spanduk, (
        "tombol Masuk ulang dipakai untuk membuka kunci, jadi wajah yang memberi sesi lemah tidak boleh ditawarkan"
    )
    assert "hanyaKuat={ulangKuat}" in halaman
    assert 'hasil.cara.filter((c) => c !== "wajah")' in masuk


def test_dashboard_tidak_mengaku_tulisan_sudah_ada_di_situs():
    next_ = (AKAR / "next" / "components" / "admin" / "PenyuntingTulisan.tsx").read_text(encoding="utf-8")
    html = (AKAR / "backend" / "admin" / "dasbor-penyunting.js").read_text(encoding="utf-8")
    for isi in (next_, html):
        assert "Tulisan sudah terbit." not in isi, "menandai terbit tidak membuatnya tampil di situs"
        assert "tools/terbitkan.cmd" in isi
    skrip = (AKAR / "tools" / "terbitkan.sh").read_text(encoding="utf-8")
    assert "git pull --ff-only" in skrip and "--sumber api" in skrip
    assert 'git commit --quiet -m "tulisan: terbitkan dari dashboard' in skrip and '-- "$@"' in skrip, (
        "commit penerbit hanya boleh membawa berkas tulisan, bukan perubahan lain di laptop"
    )
