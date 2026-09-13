"""Nginx, systemd, pengiriman cadangan, dan alur deploy. Bab 12, 14, 15, 18.

Tidak ada VPS di mesin ini, dan berpura pura ada akan menghasilkan uji yang
membuktikan hal yang salah. Yang bisa dibuktikan tanpa server justru yang
paling sering rusak diam diam, dan itu yang diuji di sini:

1. Header keamanan di nginx sama persis dengan yang dikirim Cloudflare.
   Situs yang aturannya berbeda tergantung siapa yang menyajikannya adalah
   dua situs yang berbeda, dan yang satunya tidak pernah diuji.
2. Berkas unit systemd punya bagian dan kunci yang benar, dan pengerasannya
   masih ada. Baris NoNewPrivileges yang terhapus tidak menimbulkan galat
   apa pun; layanannya tetap menyala, hanya tidak lagi terkurung.
3. Skrip pengirim menolak berkas yang tidak terenkripsi.
4. Tidak ada satu pun rahasia tertulis di berkas infrastruktur.

Susunan nginx-nya sendiri diuji nginx sungguhan lewat
`sh infrastructure/periksa_nginx.sh`, yang menjalankannya di dalam kontainer.
Itu dipanggil CI, bukan dari sini, sebab ia menuntut Docker.
"""

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
    """Komentar boleh menyebut aturan yang justru dilarang, untuk menjelaskan
    kenapa ia dilarang. Uji yang menghukum penjelasan semacam itu akan
    membuat orang menghapus penjelasannya, bukan memperbaiki kodenya."""
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


# ----------------------------------------------------------------- nginx ---


@pytest.mark.parametrize("header", [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "Strict-Transport-Security",
    "Content-Security-Policy",
])
def test_header_nginx_sama_dengan_cloudflare(header):
    assert _dari_nginx(header) == _dari_headers(header), (
        f"{header} berbeda antara nginx dan _headers"
    )


def test_hash_skrip_sebaris_ikut_ke_nginx():
    """Kalau skrip temanya berubah dan hanya _headers yang diperbarui, temanya
    akan bekerja di Cloudflare dan diam diam ditolak di VPS."""
    hash_headers = set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", KEPALA))
    hash_nginx = set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", NGINX))
    assert hash_headers == hash_nginx, "hash CSP tidak sama di kedua tempat"


def test_setiap_add_header_memakai_always():
    """Tanpa `always`, nginx melewatkan header pada jawaban 4xx dan 5xx. Halaman
    404 tanpa CSP adalah halaman yang aturannya paling longgar di seluruh
    situs, dan itu halaman yang paling mudah dipancing untuk muncul."""
    for baris in NGINX.splitlines():
        b = baris.strip()
        if b.startswith("add_header ") and not b.startswith("add_header Cache-Control"):
            assert b.endswith("always;"), b


def test_location_api_tidak_memasang_add_header_sendiri():
    """Jebakan nginx yang paling sering memakan korban: satu add_header di
    dalam location MENGHAPUS seluruh add_header milik blok server. Menambahkan
    satu header di /api/ berarti membuang enam header keamanan dari seluruh
    jawaban API tanpa satu pun peringatan."""
    blok = re.findall(r"location\s+[^{]*/api/[^{]*\{(.*?)\n    \}", NGINX_KODE, re.DOTALL)
    assert blok, "tidak menemukan blok location /api/"
    for isi in blok:
        assert "add_header" not in isi, (
            "add_header di dalam location /api/ akan menghapus header keamanan induknya"
        )


def test_api_lewat_soket_unix_bukan_porta():
    """Porta di localhost bisa dihubungi proses mana pun di mesin itu."""
    assert "unix:/run/hk-api/api.sock" in NGINX
    assert not re.search(r"proxy_pass\s+http://127\.0\.0\.1:\d+", NGINX)


def test_jalur_masuk_dibatasi_lebih_ketat_daripada_jalur_biasa():
    zona = dict(re.findall(r"limit_req_zone\s+\S+\s+zone=(\w+):\S+\s+rate=(\S+);", NGINX))
    assert zona.get("umum", "").endswith("r/s"), zona
    assert zona.get("masuk", "").endswith("r/m"), zona
    assert "location /api/v1/auth/" in NGINX
    assert "zone=masuk" in NGINX


def test_alamat_html_lama_tetap_hidup():
    """Tautan yang sudah beredar tidak boleh mati hanya karena situsnya
    berpindah dari Cloudflare ke VPS."""
    assert re.search(r"location\s+~\s+\^\(/\.\+\)\\\.html\$", NGINX), (
        "tidak ada pengalihan dari alamat .html yang lama"
    )
    assert "return 308" in NGINX


def test_versi_nginx_tidak_diumumkan():
    assert "server_tokens off;" in NGINX


def test_http_hanya_untuk_dialihkan_dan_acme():
    blok = re.search(r"listen 80;(.*?)\n\}", NGINX, re.DOTALL)
    assert blok, "tidak ada blok HTTP"
    assert "acme-challenge" in blok.group(1)
    assert "return 308 https://" in blok.group(1)


# --------------------------------------------------------------- systemd ---


def _baca_unit(berkas):
    # interpolation=None: systemd memakai %i dan %n sebagai penanda templat,
    # dan configparser bawaan mengira % miliknya lalu menolak seluruh berkas.
    p = configparser.ConfigParser(strict=False, allow_no_value=True, interpolation=None)
    # Nama kunci systemd peka huruf besar kecil; configparser memaksanya jadi
    # huruf kecil kalau tidak dicegah.
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
    """Baris yang terhapus di sini tidak menimbulkan galat apa pun. Layanannya
    tetap menyala, hanya tidak lagi terkurung, dan tidak ada yang tahu sampai
    ada yang memanfaatkannya."""
    p = _baca_unit(INFRA / "systemd" / "hk-api.service")
    assert kunci in p["Service"], f"pengerasan {kunci} hilang dari hk-api.service"


def test_rahasia_datang_dari_berkas_bukan_dari_unit():
    """Berkas unit bisa dibaca siapa saja di mesin itu. EnvironmentFile
    dimiliki root dengan izin 0640."""
    for nama in ("hk-api.service", "hk-cadangan.service"):
        isi = (INFRA / "systemd" / nama).read_text(encoding="utf-8")
        assert "EnvironmentFile=" in isi, nama
        baris_env = [b for b in isi.splitlines() if b.startswith("Environment=")]
        assert not baris_env, f"{nama} menaruh nilai langsung di unit: {baris_env}"


def test_cadangan_menguji_pemulihan_tiap_kali_dijalankan():
    """Cadangan yang belum pernah dipulihkan belum terbukti apa apa, dan
    pemulihan pertama tidak boleh dicoba pada hari datanya benar benar
    hilang."""
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


# ---------------------------------------------------------------- skrip ---


@pytest.mark.parametrize("berkas", SKRIP, ids=lambda p: p.name)
def test_skrip_tidak_punya_galat_sintaks(berkas):
    hasil = subprocess.run(["sh", "-n", str(berkas)], capture_output=True, text=True)
    assert hasil.returncode == 0, hasil.stderr


@pytest.mark.parametrize("berkas", SKRIP, ids=lambda p: p.name)
def test_skrip_berhenti_saat_gagal(berkas):
    """Tanpa `set -e`, skrip pemasangan yang gagal di tengah tetap berjalan
    sampai akhir lalu melaporkan berhasil."""
    isi = berkas.read_text(encoding="utf-8")
    assert re.search(r"^set -eu?", isi, re.M), f"{berkas.name} tidak memakai set -e"


def test_pengirim_menolak_berkas_yang_tidak_terenkripsi():
    isi = (INFRA / "kirim.sh").read_text(encoding="utf-8")
    assert "HKCAD1" in isi, "pengirim tidak memeriksa penanda enkripsi"
    assert "hk-*.sql.gz.enc" in isi
    # Dibaca dari isinya, bukan dari namanya: nama berkas bisa diganti siapa saja.
    assert "head -c 6" in isi


def test_pengirim_punya_retensi():
    isi = (INFRA / "kirim.sh").read_text(encoding="utf-8")
    assert "rclone delete" in isi and "--min-age" in isi, (
        "cadangan yang menumpuk selamanya adalah tagihan yang tumbuh selamanya"
    )


# -------------------------------------------------------------- rahasia ---

CURIGA = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key)\s*=\s*['\"]?[A-Za-z0-9/+_-]{12,}"
)


@pytest.mark.parametrize("berkas", [*SKRIP, *UNIT, INFRA / "nginx" / "hendrokuswantoro.conf",
                                    INFRA / "docker-compose.yml",
                                    AKAR / ".github" / "workflows" / "vps.yml"],
                         ids=lambda p: p.name)
def test_tidak_ada_rahasia_tertulis(berkas):
    """Bab 15.11. Rahasia yang pernah masuk git tetap ada di git selamanya,
    bahkan sesudah baris itu dihapus di commit berikutnya."""
    for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), 1):
        bersih = baris.strip()
        if bersih.startswith("#") or bersih.startswith(";"):
            continue
        # ${VAR} dan ${{ secrets.X }} justru cara yang benar
        if "${" in bersih:
            continue
        assert not CURIGA.search(bersih), f"{berkas.name}:{nomor} {bersih[:70]}"


# -------------------------------------------------------------- deploy ---

VPS = (AKAR / ".github" / "workflows" / "vps.yml").read_text(encoding="utf-8")


def test_deploy_mati_sampai_dinyalakan():
    """Alur kerja yang mencoba menghubungi VPS yang belum ada akan gagal tiap
    push, dan lampu merah yang selalu menyala adalah lampu merah yang berhenti
    dibaca."""
    assert "vars.VPS_AKTIF == '1'" in VPS


def test_deploy_tidak_pernah_mengirim_commit_yang_ci_nya_merah():
    assert "github.event.workflow_run.conclusion == 'success'" in VPS


def test_deploy_menyematkan_kunci_host():
    """StrictHostKeyChecking=no berarti menerima siapa pun yang kebetulan
    menjawab di alamat itu."""
    assert "ssh-keyscan" in VPS
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
    for larangan in ("--exclude '.env'", "--exclude 'cadangan'"):
        assert larangan in VPS, larangan


def test_hanya_satu_deploy_berjalan_sekaligus():
    assert "concurrency:" in VPS and "group: vps" in VPS


# --------------------------------------------- pengirim, benar benar dijalankan ---
#
# Dua uji di bawah menjalankan kirim.sh sungguhan dengan --coba, yang tidak
# menghubungi siapa pun. Keduanya ada karena membaca skripnya saja tidak cukup:
# percobaan pertama skrip ini menolak berkas yang sah, gara gara spasi di nama
# folder memecah jalurnya jadi dua kata. Tidak ada pembacaan kode yang akan
# menemukan itu.


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
    """Folder berspasi bukan kasus buatan: repositori ini sendiri tinggal di
    "D:/Projects/personal web"."""
    folder = tmp_path / "ada spasi di sini"
    folder.mkdir()
    (folder / "hk-2026-01-01-0000.sql.gz.enc").write_bytes(b"HKCAD1\n" + b"x" * 64)

    hasil = _jalankan_kirim(folder)
    assert hasil.returncode == 0, hasil.stderr
    assert "akan dikirim" in hasil.stdout


def test_pengirim_diam_kalau_tujuannya_belum_diisi(tmp_path):
    """Tujuan yang belum diisi bukan kegagalan: ia berarti pengiriman keluar
    memang belum dinyalakan, dan menggagalkan unit cadangan karenanya akan
    membuat cadangan lokalnya ikut dilaporkan gagal tiap malam."""
    hasil = subprocess.run(
        ["sh", str(INFRA / "kirim.sh"), "--coba"],
        capture_output=True, text=True,
        env={**{k: v for k, v in os.environ.items() if k != "CADANGAN_TUJUAN"},
             "CADANGAN_FOLDER": str(tmp_path)},
    )
    assert hasil.returncode == 0
    assert "belum diisi" in hasil.stderr


# ------------------------------------------------------- alur kerja sendiri ---

# Alur kerja GitHub Actions tidak pernah diperiksa sebelum dijalankan di sana,
# dan satu kekeliruan di dalamnya membuat pemeriksaan kesehatan gagal tiap
# malam selama berhari hari sambil membuka isu otomatis yang menyatakan
# situsnya mati. Situsnya sehat sepanjang waktu itu.
#
# Rangkaian uji di bawah ikut menguji pemeriksanya sendiri: ia diberi kembali
# baris yang dulu lolos, dan kalau pemeriksanya meloloskannya lagi, ujinya
# gagal. Pemeriksa yang tidak pernah dibuktikan bisa menangkap apa pun adalah
# pemeriksa yang belum tentu menangkap apa pun.

import sys  # noqa: E402

sys.path.insert(0, str(AKAR / "tools"))


def test_seluruh_alur_kerja_lolos_pemeriksanya():
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    hasil = subprocess.run(
        [sys.executable, str(AKAR / "tools" / "periksa_alur.py")],
        capture_output=True, text=True, cwd=AKAR,
    )
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr


def test_pemeriksa_menangkap_baris_yang_dulu_lolos():
    """Baris aslinya, apa adanya, dari kesehatan.yml sebelum diperbaiki."""
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    from periksa_alur import periksa_garis_miring

    # Rangkaian mentah: di sini \n wajib dua karakter, bukan baris baru.
    # Kalau ia sampai jadi baris baru, ujinya akan lolos tanpa menguji apa pun.
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
    """Komentar yang menjelaskan kekeliruan itu wajib boleh menyebutnya."""
    pytest.importorskip("yaml", reason="pyyaml belum terpasang")
    from periksa_alur import periksa_garis_miring

    catatan = r'# dulu baris ini memuat "\n" harfiah, dan itu sebabnya gagal'
    assert "\\" in catatan
    assert not periksa_garis_miring("uji", catatan)


def test_tidak_ada_lagi_garis_miring_n_di_kesehatan():
    """Langsung ke berkasnya, bukan lewat pemeriksanya: kalau suatu saat
    pemeriksanya rusak, uji ini masih berdiri."""
    teks = (AKAR / ".github" / "workflows" / "kesehatan.yml").read_text(encoding="utf-8")
    baris_daftar = [
        b for b in teks.splitlines()
        if "for jalur in" in b or ("while" in b and "jalur" in b)
    ]
    assert baris_daftar, "daftar jalur yang diperiksa hilang sama sekali"
    for b in baris_daftar:
        assert "\\" not in b, f"garis miring kembali ke daftar jalur: {b.strip()}"


def test_alamat_kanonik_ikut_diperiksa_kesehatan():
    """Alamat yang situs ini sebut tentang dirinya sendiri wajib eksis. Pada
    13 September 2026 www.hendrokuswantoro.com belum terdaftar sama sekali,
    sementara seluruh rel=canonical, sitemap, dan umpan RSS menunjuk ke sana,
    dan tidak ada satu pun pemeriksaan yang menyadarinya."""
    teks = (AKAR / ".github" / "workflows" / "kesehatan.yml").read_text(encoding="utf-8")
    assert "canonical" in teks, "tidak ada langkah yang memeriksa alamat kanonik"
    assert "getent hosts" in teks or "nslookup" in teks or "dig " in teks, (
        "langkah kanoniknya tidak pernah benar benar menanyakan DNS"
    )


def test_blok_assets_tidak_kehilangan_header_keamanan():
    """Satu add_header di dalam location menghapus seluruh add_header induknya.

    Blok /assets/ memasang Cache-Control, jadi sampai 13 September 2026 setiap
    berkas JavaScript, SVG, dan font di situs ini dikirim nginx tanpa nosniff,
    tanpa HSTS, dan tanpa CSP, sementara Cloudflare mengirim semuanya karena
    _headers menumpuk aturan alih alih menggantinya. Dua penyaji dengan aturan
    berbeda, dan yang diuji hanya salah satunya.
    """
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


def test_csp_di_blok_assets_sama_dengan_yang_di_server():
    """Dua CSP yang berbeda di satu berkas adalah satu yang sudah tertinggal."""
    semua = re.findall(r'add_header Content-Security-Policy "([^"]+)"', NGINX)
    assert len(semua) >= 2, "CSP hanya tertulis sekali, blok /assets/ belum punya"
    assert len(set(semua)) == 1, "CSP di nginx tidak seragam antar blok"


def test_langkah_peramban_di_ci_menyebut_penandanya():
    """pytest.ini memasang addopts `-m "not peramban"` supaya putaran biasa
    tidak menyalakan Chromium. Tanpa `-m peramban` di CI, pytest tidak
    mengumpulkan satu uji pun dan keluar dengan kode 5, yang berarti "tidak ada
    uji" dan bukan "ada uji yang gagal". Selama berhari hari tidak satu pun uji
    peramban berjalan di CI, dan halaman Actions hanya berbunyi "Process
    completed with exit code 5".
    """
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
    """Uji di atas hanya masuk akal selama pengecualiannya masih ada. Kalau
    suatu saat addopts-nya dicabut, uji ini yang memberi tahu, bukan kegagalan
    membingungkan di CI."""
    ini = (AKAR / "pytest.ini").read_text(encoding="utf-8")
    assert 'not peramban' in ini
