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
