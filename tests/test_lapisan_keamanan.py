from __future__ import annotations

import asyncio
import contextlib
import re
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))

NGINX = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(encoding="utf-8")
ALUR = {p.name: p.read_text(encoding="utf-8") for p in (AKAR / ".github" / "workflows").glob("*.yml")}
CI = ALUR["ci.yml"]


def test_pembatas_laju_menjawab_429_bukan_503():
    assert "limit_req_status 429;" in NGINX and "limit_conn_status 429;" in NGINX, (
        "503 membuat pemantau dan pemindai mengira servernya rusak"
    )


def test_host_yang_diteruskan_ke_aplikasi_ditulis_tetap():
    assert "proxy_set_header Host $host;" not in NGINX
    assert NGINX.count("proxy_set_header Host $server_name;") == NGINX.count("proxy_pass http://hk_api;")


def test_dashboard_terisolasi_dari_asal_lain():
    blok = NGINX[NGINX.index("location ^~ /admin {"):]
    blok = blok[:blok.index("\n    }")]
    assert 'add_header Cross-Origin-Embedder-Policy "require-corp" always;' in blok


@pytest.mark.parametrize("nama", sorted(ALUR))
def test_action_dikunci_ke_commit_bukan_ke_tag(nama):
    for pakai in re.findall(r"uses:\s*(\S+)", ALUR[nama]):
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", pakai), (
            f"{nama}: {pakai} memakai tag yang bisa dipindah pemiliknya ke kode lain"
        )


def test_dependabot_menjaga_ketiga_ekosistem():
    isi = (AKAR / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    for ekosistem in ("github-actions", "pip", "npm"):
        assert f"package-ecosystem: {ekosistem}" in isi, ekosistem


def test_ci_memindai_rahasia_dan_celah_kode():
    assert "zricethezav/gitleaks:v8.30.1" in CI and "--config /repo/.gitleaks.toml" in CI
    assert "fetch-depth: 0" in CI[CI.index("name: Security Scan"):CI.index("name: No secret anywhere")]
    assert "bandit -r backend tools -q -lll" in CI
    aturan = (AKAR / ".gitleaks.toml").read_text(encoding="utf-8")
    assert "useDefault = true" in aturan
    assert "'''^[A-Z][A-Z0-9_]*=$'''" in aturan, "pengecualian gitleaks melebar melampaui baris kosong"


def test_tiruan_produksi_tidak_membaca_env_asli():
    tumpukan = (AKAR / "infrastructure" / "uji-keamanan" / "compose.yml").read_text(encoding="utf-8")
    assert "/srv/hendrokuswantoro/app/.env:ro" in tumpukan, "tiruan bisa membaca SMTP asli dan mengirim surat sungguhan"
    assert "../..:/srv/hendrokuswantoro/app:ro" in tumpukan
    alat = (AKAR / "tools" / "uji_keamanan.sh").read_text(encoding="utf-8")
    assert "down -v" in alat and "trap bersihkan EXIT" in alat
    assert "zap-api-scan.py" in alat and "Bearer" in alat, "pemindaian API tidak masuk sebagai admin"


class _Kursor:
    def __init__(self, catat):
        self.catat = catat
        self.rowcount = 1

    async def execute(self, sql, param=None):
        self.catat.append((sql, param))

    async def fetchone(self):
        return {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Sesi:
    def __init__(self, catat):
        self.catat = catat

    def cursor(self):
        return _Kursor(self.catat)


def _palsu(catat):
    @contextlib.asynccontextmanager
    async def koneksi():
        yield _Sesi(catat)
    return koneksi


JAHAT = "judul_en = 'x', status = 'terbit' --"


def test_nama_kolom_jahat_tidak_pernah_sampai_ke_sql_tulisan(monkeypatch):
    pytest.importorskip("psycopg")
    from backend.repositori import tulis

    catat = []
    monkeypatch.setattr(tulis, "koneksi", _palsu(catat))
    asyncio.run(tulis.ubah("slug", {JAHAT: "a", "judul_en": "Judul"}))
    sql, param = catat[0]
    assert JAHAT not in sql and "status" not in sql.split("WHERE")[0]
    assert "judul_en = %s" in sql and param == ["Judul", "slug"]

    catat.clear()
    assert asyncio.run(tulis.ubah("slug", {JAHAT: "a"})) is None
    assert not catat, "permintaan tanpa kolom sah tetap menyentuh basis data"


def test_nama_kolom_jahat_tidak_pernah_sampai_ke_sql_setelan(monkeypatch):
    pytest.importorskip("psycopg")
    from backend.repositori import keamanan

    catat = []
    monkeypatch.setattr(keamanan, "koneksi", _palsu(catat))
    asyncio.run(keamanan.simpan_setelan("id", {JAHAT: True, "kabar_masuk": False}))
    sql, param = catat[0]
    assert JAHAT not in sql and "kabar_masuk = %s" in sql
    assert param == (False, "id")


def test_ci_menjalankan_linter_keamanan_workflow_shell_dan_nginx():
    assert "zizmor==1.30.1" in CI and "zizmor --offline .github/workflows" in CI
    assert "shellcheck -S style" in CI
    assert "gixy-ng==0.2.55" in CI and "gixy -ll" in CI
    aturan = (AKAR / ".github" / "zizmor.yml").read_text(encoding="utf-8")
    assert set(re.findall(r"^\s+- (\S+)$", aturan, re.M)) == {"kesehatan.yml", "vps.yml"}, (
        "pengecualian zizmor melebar ke workflow yang tidak dijaga syarat workflow_run"
    )


@pytest.mark.parametrize("nama", sorted(ALUR))
def test_checkout_tidak_meninggalkan_token_di_folder_kerja(nama):
    isi = ALUR[nama]
    for awal in [m.start() for m in re.finditer(r"uses: actions/checkout@", isi)]:
        blok = isi[awal:isi.find("\n      - ", awal + 1)]
        assert "persist-credentials: false" in blok, f"{nama}: checkout menyimpan token di .git/config"


@pytest.mark.parametrize("nama", sorted(ALUR))
def test_nilai_dari_luar_tidak_disisipkan_ke_skrip_shell(nama):
    for blok in re.findall(r"run: \|\n((?:\s{10,}.*\n|\n)+)", ALUR[nama]):
        for ungkapan in re.findall(r"\$\{\{\s*([^}]+?)\s*\}\}", blok):
            assert not ungkapan.startswith(("vars.", "steps.", "github.event", "inputs.")), (
                f"{nama}: {ungkapan} disisipkan ke shell; lewatkan melalui env"
            )


@pytest.mark.parametrize("nama", ["kesehatan.yml", "vps.yml"])
def test_workflow_run_hanya_dari_push_ke_repositori_ini(nama):
    isi = ALUR[nama]
    assert "branches: [main]" in isi[isi.index("workflow_run:"):isi.index("permissions:")]
    assert isi.count("github.event.workflow_run.event == 'push'") >= 1
    assert isi.count("github.event.workflow_run.head_repository.full_name == github.repository") >= 1


def test_deploy_mengirim_commit_yang_diuji_ci():
    vps = ALUR["vps.yml"]
    assert "ref: ${{ github.event.workflow_run.head_sha || github.sha }}" in vps, (
        "pada workflow_run, checkout bawaan mengambil ujung main, bukan commit yang baru lolos CI"
    )


def test_izin_menulis_isu_hanya_untuk_job_yang_membutuhkannya():
    isi = ALUR["kesehatan.yml"]
    atas = isi[isi.index("permissions:"):isi.index("jobs:")]
    assert "issues: write" not in atas


def test_dependabot_menunggu_rilis_baru_mengendap():
    isi = (AKAR / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    assert isi.count("package-ecosystem:") == isi.count("default-days: 7"), (
        "paket yang baru dirilis, termasuk yang dibajak, langsung diusulkan"
    )


def test_nginx_tidak_menyebut_versinya_dan_membatasi_sandi_tls():
    atas = NGINX[:NGINX.index("server {")]
    assert "server_tokens off;" in atas
    assert re.search(r"^ssl_ciphers (ECDHE-[A-Z0-9-]+:)*ECDHE-[A-Z0-9-]+;$", atas, re.M)
    assert "CBC" not in atas and "SHA256:AES" not in atas


def test_nginx_tidak_mengirim_cache_control_dua_kali():
    assert not re.search(r"^\s*expires ", NGINX, re.M), (
        "expires menambah Cache-Control kedua di samping add_header"
    )


def test_nama_tanpa_www_mengirim_hsts():
    blok = NGINX[NGINX.index("server_name hendrokuswantoro.com;"):]
    blok = blok[:blok.index("\n}")]
    assert 'add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;' in blok


def test_halaman_html_divalidasi_ulang():
    assert "add_header Cache-Control $cache_halaman always;" in NGINX
    assert '    default       "public, max-age=0, must-revalidate";' in NGINX
    assert "location ~* \.html$" not in NGINX, "blok ini tidak pernah tercapai dan membuang header keamanan"


def test_tiruan_produksi_tidak_berjalan_sebagai_root():
    isi = (AKAR / "infrastructure" / "uji-keamanan" / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"^USER (?!root)\w+$", isi, re.M)
