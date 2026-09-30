from __future__ import annotations

import configparser
import os
import re
import subprocess

import pytest

from konftes import AKAR

INFRA = AKAR / "infrastructure"
NGINX = (INFRA / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
KEPALA = (AKAR / "_headers").read_text(encoding="utf-8")


def tanpa_komentar(teks: str, tanda: str = "#") -> str:
    return "\n".join(
        b for b in teks.splitlines() if not b.strip().startswith(tanda)
    )


NGINX_KODE = tanpa_komentar(NGINX)

UNIT = sorted((INFRA / "systemd").glob("*"))
SKRIP = sorted(INFRA.glob("*.sh"))


def _dari_headers(nama: str) -> str:
    for baris in KEPALA.splitlines():
        if baris.strip().lower().startswith(nama.lower() + ":"):
            return baris.split(":", 1)[1].strip()
    raise AssertionError(f"_headers tidak menyebut {nama}")


def _dari_nginx(nama: str) -> str:
    cocok = re.search(rf'add_header\s+{nama}\s+"(.*?)"\s+always;', NGINX, re.DOTALL)
    assert cocok, f"nginx tidak menyebut {nama}"
    return cocok.group(1)


@pytest.mark.parametrize("header", [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "X-Permitted-Cross-Domain-Policies",
])
def test_header_nginx_sama_dengan_cloudflare(header):
    assert _dari_nginx(header) == _dari_headers(header), (
        f"{header} berbeda antara nginx dan _headers"
    )


def test_hash_skrip_sebaris_ikut_ke_nginx():
    hash_headers = set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", KEPALA))
    hash_nginx = set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", NGINX))
    assert hash_headers == hash_nginx, "hash CSP tidak sama di kedua tempat"


def test_setiap_add_header_memakai_always():
    for baris in NGINX.splitlines():
        b = baris.strip()
        if b.startswith("add_header ") and not b.startswith("add_header Cache-Control"):
            assert b.endswith("always;"), b


def test_location_api_tidak_memasang_add_header_sendiri():
    blok = re.findall(r"location\s+[^{]*/api/[^{]*\{(.*?)\n    \}", NGINX_KODE, re.DOTALL)
    assert blok, "tidak menemukan blok location /api/"
    for isi in blok:
        assert "add_header" not in isi, (
            "add_header di dalam location /api/ akan menghapus header keamanan induknya"
        )


def test_api_lewat_soket_unix_bukan_porta():
    assert "unix:/run/hk-api/api.sock" in NGINX
    assert not re.search(r"proxy_pass\s+http://127\.0\.0\.1:\d+", NGINX)


def test_jalur_masuk_dibatasi_lebih_ketat_daripada_jalur_biasa():
    zona = dict(re.findall(r"limit_req_zone\s+\S+\s+zone=(\w+):\S+\s+rate=(\S+);", NGINX))
    assert zona.get("umum", "").endswith("r/s"), zona
    assert zona.get("masuk", "").endswith("r/m"), zona
    assert "location /api/v1/auth/" in NGINX
    assert "zone=masuk" in NGINX


def test_alamat_html_lama_tetap_hidup():
    assert r"location ~ ^(/[A-Za-z0-9][A-Za-z0-9/_-]*)\.html$ {" in NGINX, (
        "tidak ada pengalihan dari alamat .html yang lama, atau polanya kembali "
        "menerima garis miring terbalik yang membuatnya pengalih ke situs lain"
    )
    assert "return 308" in NGINX


def test_versi_nginx_tidak_diumumkan():
    assert "server_tokens off;" in NGINX


def _baca_unit(berkas):
    p = configparser.ConfigParser(strict=False, allow_no_value=True, interpolation=None)
    p.optionxform = str
    p.read_string(berkas.read_text(encoding="utf-8"))
    return p


@pytest.mark.parametrize("berkas", UNIT, ids=lambda p: p.name)
def test_unit_terbaca_sebagai_ini(berkas):
    p = _baca_unit(berkas)
    assert "Unit" in p, f"{berkas.name} tanpa bagian [Unit]"
    assert p["Unit"].get("Description"), f"{berkas.name} tanpa Description"


def test_layanan_api_tidak_berjalan_sebagai_root():
    p = _baca_unit(INFRA / "systemd" / "hk-api.service")
    assert p["Service"]["User"] == "hk"
    assert p["Service"]["Group"] == "hk"


@pytest.mark.parametrize("kunci", [
    "NoNewPrivileges", "PrivateTmp", "ProtectSystem", "ProtectHome",
    "RestrictSUIDSGID", "LockPersonality", "CapabilityBoundingSet",
])
def test_pengerasan_api_masih_ada(kunci):
    p = _baca_unit(INFRA / "systemd" / "hk-api.service")
    assert kunci in p["Service"], f"pengerasan {kunci} hilang dari hk-api.service"


def test_rahasia_datang_dari_berkas_bukan_dari_unit():
    for nama in ("hk-api.service", "hk-cadangan.service"):
        isi = (INFRA / "systemd" / nama).read_text(encoding="utf-8")
        assert "EnvironmentFile=" in isi, nama
        baris_env = [b for b in isi.splitlines() if b.startswith("Environment=")]
        assert not baris_env, f"{nama} menaruh nilai langsung di unit: {baris_env}"


def test_cadangan_menguji_pemulihan_tiap_kali_dijalankan():
    isi = (INFRA / "systemd" / "hk-cadangan.service").read_text(encoding="utf-8")
    langkah = [b for b in isi.splitlines() if b.startswith("ExecStart=")]
    assert len(langkah) == 3, langkah
    assert "cadangan.py buat" in langkah[0]
    assert "cadangan.py uji-pulih" in langkah[1], "pemulihan tidak pernah diuji"
    assert "kirim.sh" in langkah[2]


def test_kegagalan_cadangan_memberitahu_seseorang():
    isi = (INFRA / "systemd" / "hk-cadangan.service").read_text(encoding="utf-8")
    assert "OnFailure=" in isi, (
        "kegagalan cadangan hanya duduk di journal sampai ada yang membukanya"
    )
    assert (INFRA / "systemd" / "hk-cadangan-gagal@.service").exists()


def test_timer_mengejar_jadwal_yang_terlewat():
    p = _baca_unit(INFRA / "systemd" / "hk-cadangan.timer")
    assert p["Timer"]["Persistent"] == "true", (
        "tanpa Persistent, cadangan yang terlewat karena mesinnya mati "
        "dilewati diam diam sampai besok malam"
    )
    assert p["Timer"]["OnCalendar"]
    assert not p["Timer"]["OnCalendar"].endswith("00:00:00"), (
        "jam bulat adalah saat seluruh dunia menjalankan tugas terjadwalnya"
    )


def test_folder_cadangan_satu_satunya_yang_boleh_ditulis():
    p = _baca_unit(INFRA / "systemd" / "hk-cadangan.service")
    assert p["Service"]["ProtectSystem"] == "strict"
    assert p["Service"]["ReadWritePaths"].endswith("/cadangan")
    assert p["Service"]["UMask"] == "0077", "cadangan berisi salinan penuh basis data"


@pytest.mark.parametrize("berkas", SKRIP, ids=lambda p: p.name)
def test_skrip_tidak_punya_galat_sintaks(berkas):
    hasil = subprocess.run(["sh", "-n", str(berkas)], capture_output=True, text=True)
    assert hasil.returncode == 0, hasil.stderr


@pytest.mark.parametrize("berkas", SKRIP, ids=lambda p: p.name)
def test_skrip_berhenti_saat_gagal(berkas):
    isi = berkas.read_text(encoding="utf-8")
    assert re.search(r"^set -eu?", isi, re.M), f"{berkas.name} tidak memakai set -e"


def test_pengirim_menolak_berkas_yang_tidak_terenkripsi():
    isi = (INFRA / "kirim.sh").read_text(encoding="utf-8")
    assert "HKCAD1" in isi, "pengirim tidak memeriksa penanda enkripsi"
    assert "hk-*.sql.gz.enc" in isi
    assert "head -c 6" in isi


def test_pengirim_punya_retensi():
    isi = (INFRA / "kirim.sh").read_text(encoding="utf-8")
    assert "rclone delete" in isi and "--min-age" in isi, (
        "cadangan yang menumpuk selamanya adalah tagihan yang tumbuh selamanya"
    )


CURIGA = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*=\s*['\"]?[A-Za-z0-9/+_-]{12,}"
)


@pytest.mark.parametrize("berkas", [*SKRIP, *UNIT, INFRA / "nginx" / "hendrokuswantoro.conf",
                                    INFRA / "docker-compose.yml",
                                    AKAR / ".github" / "workflows" / "vps.yml"],
                         ids=lambda p: p.name)
def test_tidak_ada_rahasia_tertulis(berkas):
    for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), 1):
        bersih = baris.strip()
        if bersih.startswith("#") or bersih.startswith(";"):
            continue
        if "${" in bersih:
            continue
        assert not CURIGA.search(bersih), f"{berkas.name}:{nomor} {bersih[:70]}"


VPS = (AKAR / ".github" / "workflows" / "vps.yml").read_text(encoding="utf-8")


def test_deploy_mati_sampai_dinyalakan():
    assert "vars.VPS_AKTIF == '1'" in VPS


def test_deploy_tidak_pernah_mengirim_commit_yang_ci_nya_merah():
    assert "github.event.workflow_run.conclusion == 'success'" in VPS


def test_deploy_menyematkan_kunci_host():
    assert "secrets.VPS_KUNCI_HOST" in VPS
    assert "StrictHostKeyChecking yes" in VPS
    assert "ssh-keyscan" not in VPS, "kunci yang dipindai saat deploy dipercaya tanpa diperiksa"
    assert "StrictHostKeyChecking=no" not in tanpa_komentar(VPS)


def test_deploy_memigrasi_sebelum_menyalakan_ulang():
    urut_migrasi = VPS.index("migrasi.py")
    urut_restart = VPS.index("systemctl restart hk-api")
    assert urut_migrasi < urut_restart, (
        "kode baru sempat berjalan di atas skema lama"
    )


def test_deploy_memeriksa_hasilnya():
    assert "/health" in VPS, "deploy tidak pernah memastikan layanannya bangun lagi"


def test_deploy_tidak_pernah_menyalin_env_atau_cadangan():
    for larangan in ("--exclude '.env'", "--exclude 'cadangan'", "--exclude '/unggahan'"):
        assert larangan in VPS, larangan


def test_hanya_satu_deploy_berjalan_sekaligus():
    assert "concurrency:" in VPS and "group: vps" in VPS


def _jalankan_kirim(folder, *arg):
    return subprocess.run(
        ["sh", str(INFRA / "kirim.sh"), "--coba", *arg],
        capture_output=True, text=True,
        env={**os.environ, "CADANGAN_FOLDER": str(folder),
             "CADANGAN_TUJUAN": "palsu:bucket"},
    )


def test_pengirim_menolak_berkas_polos_yang_namanya_enc(tmp_path):
    (tmp_path / "hk-2026-01-01-0000.sql.gz.enc").write_bytes(b"ini gzip biasa, bukan HKCAD1")
    hasil = _jalankan_kirim(tmp_path)
    assert hasil.returncode != 0, hasil.stdout
    assert "TOLAK" in hasil.stderr


def test_pengirim_menerima_berkas_terenkripsi_walau_jalurnya_berspasi(tmp_path):
    folder = tmp_path / "ada spasi di sini"
    folder.mkdir()
    (folder / "hk-2026-01-01-0000.sql.gz.enc").write_bytes(b"HKCAD1\n" + b"x" * 64)

    hasil = _jalankan_kirim(folder)
    assert hasil.returncode == 0, hasil.stderr
    assert "akan dikirim" in hasil.stdout


def test_pengirim_diam_kalau_tujuannya_belum_diisi(tmp_path):
    hasil = subprocess.run(
        ["sh", str(INFRA / "kirim.sh"), "--coba"],
        capture_output=True, text=True,
        env={**{k: v for k, v in os.environ.items() if k != "CADANGAN_TUJUAN"},
             "CADANGAN_FOLDER": str(tmp_path)},
    )
    assert hasil.returncode == 0
    assert "belum diisi" in hasil.stderr


import sys

sys.path.insert(0, str(AKAR / "tools"))


def test_seluruh_alur_kerja_lolos_pemeriksanya():
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    hasil = subprocess.run(
        [sys.executable, str(AKAR / "tools" / "periksa_alur.py")],
        capture_output=True, text=True, cwd=AKAR,
    )
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr


def test_pemeriksa_menangkap_baris_yang_dulu_lolos():
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    from periksa_alur import periksa_garis_miring

    asli = (
        r"for jalur in / /about /project /blog/ \n                       "
        r"/blog/kapan-peta-diam \n                       /robots.txt; do"
    )
    assert "\\" in asli, "ujinya sendiri kehilangan garis miringnya"
    assert periksa_garis_miring("uji", asli), (
        "pemeriksanya meloloskan baris yang justru jadi alasan ia dibuat"
    )


def test_pemeriksa_tidak_menghukum_printf():
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    from periksa_alur import periksa_garis_miring

    wajar = r"""printf '%s\n' "$KUNCI" > ~/.ssh/deploy"""
    assert "\\" in wajar
    assert not periksa_garis_miring("uji", wajar), (
        "printf memang tempat garis miring n berarti baris baru"
    )


def test_pemeriksa_tidak_menghukum_komentar():
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    from periksa_alur import periksa_garis_miring

    catatan = r'# dulu baris ini memuat "\n" harfiah, dan itu sebabnya gagal'
    assert "\\" in catatan
    assert not periksa_garis_miring("uji", catatan)


def test_tidak_ada_lagi_garis_miring_n_di_kesehatan():
    teks = (AKAR / ".github" / "workflows" / "kesehatan.yml").read_text(encoding="utf-8")
    baris_daftar = [
        b for b in teks.splitlines()
        if "for jalur in" in b or ("while" in b and "jalur" in b)
    ]
    assert baris_daftar, "daftar jalur yang diperiksa hilang sama sekali"
    for b in baris_daftar:
        assert "\\" not in b, f"garis miring kembali ke daftar jalur: {b.strip()}"


def test_alamat_kanonik_ikut_diperiksa_kesehatan():
    teks = (AKAR / ".github" / "workflows" / "kesehatan.yml").read_text(encoding="utf-8")
    assert "canonical" in teks, "tidak ada langkah yang memeriksa alamat kanonik"
    assert "getent hosts" in teks or "nslookup" in teks or "dig " in teks, (
        "langkah kanoniknya tidak pernah benar benar menanyakan DNS"
    )


def test_blok_assets_tidak_kehilangan_header_keamanan():
    blok = re.search(
        r"location /assets/ \{(.*?)\n    \}", NGINX, re.S
    )
    assert blok, "blok location /assets/ tidak ditemukan"
    isi = blok.group(1)

    for arahan in (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Strict-Transport-Security",
        "Content-Security-Policy",
    ):
        assert arahan in isi, (
            f"blok /assets/ memasang add_header tetapi tidak mengulang {arahan}, "
            "jadi berkasnya dikirim tanpa header itu"
        )


def _csp_dari_blok(awalan: str) -> str:
    tanda = re.search(r"^ *" + re.escape(awalan) + r" *\{$", NGINX, re.M)
    assert tanda, f"{awalan} tidak ada di konfigurasi nginx"
    blok = NGINX[tanda.start():NGINX.index("\n    }", tanda.start())]
    if "add_header Content-Security-Policy $csp_admin always;" in blok:
        cocok = re.search(r'map \$upstream_http_x_hk_csp \$csp_admin \{\s*""\s*"([^"]+)";', NGINX)
    else:
        cocok = re.search(r'add_header Content-Security-Policy "([^"]+)"', blok)
    assert cocok, f"{awalan} tidak memasang CSP"
    return cocok.group(1)


def _arahan(csp: str) -> dict[str, set[str]]:
    hasil = {}
    for bagian in csp.split(";"):
        potong = bagian.split()
        if potong:
            hasil[potong[0]] = set(potong[1:])
    return hasil


def test_csp_situs_seragam_antar_bloknya():
    situs = {_csp_dari_blok("location /assets/"), _dari_nginx("Content-Security-Policy")}
    assert len(situs) == 1, "CSP di nginx tidak seragam antar blok situs"


def test_csp_dashboard_lebih_ketat_daripada_situs_publiknya():
    dasbor = _arahan(_csp_dari_blok("location ^~ /admin"))
    situs = _arahan(_dari_nginx("Content-Security-Policy"))

    assert "'unsafe-inline'" not in dasbor.get("style-src", set())
    assert not any(s.startswith("'sha256-") for s in dasbor.get("script-src", set())), (
        "masih ada hash skrip sebaris di CSP dashboard"
    )

    for nama, sumber in dasbor.items():
        assert sumber <= situs.get(nama, sumber), (
            f"{nama} di dashboard lebih longgar daripada di situs: "
            f"{sorted(sumber - situs.get(nama, set()))}"
        )

    for luar in ("mapbox", "openfreemap", "arcgisonline", "amazonaws"):
        assert luar not in " ".join(str(s) for s in dasbor.values()), (
            f"dashboard tidak memuat peta, jadi {luar} tidak perlu ada di CSP-nya"
        )


def test_langkah_peramban_di_ci_menyebut_penandanya():
    alur = (AKAR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    perintah = [
        b.strip() for b in alur.splitlines()
        if "pytest" in b and ("test_peramban" in b or "test_performa" in b)
    ]
    assert len(perintah) == 2, f"harusnya dua langkah peramban, ketemu {len(perintah)}"
    for b in perintah:
        assert "-m peramban" in b, (
            f"langkah ini tidak akan mengumpulkan satu uji pun: {b}"
        )


def test_pytest_ini_memang_mengecualikan_peramban():
    ini = (AKAR / "pytest.ini").read_text(encoding="utf-8")
    assert 'not peramban' in ini


def test_kamera_hanya_dibuka_di_halaman_admin():
    assert 'camera=()' in _dari_nginx("Permissions-Policy"), (
        "kamera terbuka untuk seluruh situs"
    )

    blok = re.search(r"location \^~ /admin \{(.*?)\n    \}", NGINX, re.S)
    assert blok, "blok location ^~ /admin tidak ditemukan"
    isi = blok.group(1)
    assert "camera=(self)" in isi, "halaman admin tidak diizinkan memakai kamera"


def test_blok_admin_tidak_kehilangan_header_lain():
    blok = re.search(r"location \^~ /admin \{(.*?)\n    \}", NGINX, re.S)
    isi = blok.group(1)
    for arahan in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy",
                   "Strict-Transport-Security", "Content-Security-Policy",
                   "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy"):
        assert arahan in isi, f"blok /admin kehilangan {arahan}"
