from __future__ import annotations

import os
import re
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat

muat()


from konftes import loop_untuk_psycopg as _loop_untuk_psycopg


pytest.importorskip("fastapi", reason="backend belum terpasang")
pytest.importorskip("httpx", reason="httpx belum terpasang")

from fastapi.testclient import TestClient

DSN = os.environ.get("DSN", "")


from konftes import ada_basis_data


ADA_DB = ada_basis_data(DSN)


@pytest.fixture(scope="module")
def klien():
    if not ADA_DB:
        pytest.skip("tidak ada basis data. cd infrastructure && docker compose up -d")

    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


butuh_db = pytest.mark.skipif(
    not ADA_DB, reason="tidak ada basis data. cd infrastructure && docker compose up -d"
)


@butuh_db
def test_kesehatan(klien):
    j = klien.get("/health")
    assert j.status_code == 200
    isi = j.json()
    assert isi["status"] == "sehat"
    assert isi["basis_data"] is True


@butuh_db
def test_daftar_tulisan_dua_bahasa(klien):
    isi = klien.get("/api/v1/blog?batas=2").json()
    assert isi["jumlah"] >= 3
    assert len(isi["isi"]) == 2
    for t in isi["isi"]:
        for bagian in ("judul", "ringkas", "tag", "baca"):
            assert t[bagian]["en"] and t[bagian]["id"], f"{t['slug']}: {bagian} tidak lengkap"


@butuh_db
def test_tulisan_terbaru_lebih_dulu(klien):
    tanggal = [t["tanggal"] for t in klien.get("/api/v1/blog").json()["isi"]]
    assert tanggal == sorted(tanggal, reverse=True)


@butuh_db
def test_satu_tulisan_membawa_isinya(klien):
    isi = klien.get("/api/v1/blog/kapan-peta-diam").json()
    assert isi["slug"] == "kapan-peta-diam"
    assert isi["isi_en"].startswith("## ")
    assert isi["isi_id"].startswith("## ")


@butuh_db
def test_tulisan_tidak_ada_menjawab_404(klien):
    assert klien.get("/api/v1/blog/tidak-pernah-ditulis").status_code == 404


@butuh_db
def test_saring_proyek_per_kategori(klien):
    isi = klien.get("/api/v1/projects?kategori=analysis").json()
    assert isi["jumlah"] >= 1
    for p in isi["isi"]:
        assert "analysis" in p["kategori"]


@butuh_db
def test_kategori_ngawur_ditolak_422(klien):
    assert klien.get("/api/v1/projects?kategori=bukan-kategori").status_code == 422


@butuh_db
def test_batas_di_luar_jangkauan_ditolak(klien):
    assert klien.get("/api/v1/blog?batas=0").status_code == 422
    assert klien.get("/api/v1/blog?batas=1000").status_code == 422


@butuh_db
def test_geojson_bentuknya_benar(klien):
    isi = klien.get("/api/v1/maps/projects-spatial").json()
    assert isi["type"] == "FeatureCollection"
    assert len(isi["features"]) == 7
    for f in isi["features"]:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] == "Point"
        bujur, lintang = f["geometry"]["coordinates"]
        assert 94 <= bujur <= 142, f"{f['properties']['slug']}: bujur di luar Indonesia"
        assert -12 <= lintang <= 7, f"{f['properties']['slug']}: lintang di luar Indonesia"


@butuh_db
def test_nearby_jaraknya_meter(klien):
    isi = klien.get(
        "/api/v1/maps/nearby?lng=110.3671&lat=-7.7828&radius_m=60000"
    ).json()
    assert isi["jumlah"] >= 1
    dekat = {p["slug"]: p["jarak_m"] for p in isi["isi"]}
    assert "parking" in dekat
    assert dekat["parking"] < 5000, f"jarak parking {dekat['parking']} tidak masuk akal"
    assert isi["isi"] == sorted(isi["isi"], key=lambda p: p["jarak_m"])


@butuh_db
def test_koordinat_di_luar_indonesia_ditolak(klien):
    assert klien.get("/api/v1/maps/nearby?lng=2.35&lat=48.85").status_code == 422


@butuh_db
def test_openapi_terbit():
    from backend.main import aplikasi

    jalur = aplikasi.openapi()["paths"]
    for wajib in ("/health", "/api/v1/blog", "/api/v1/maps/projects-spatial"):
        assert wajib in jalur, f"{wajib} tidak terdokumentasi"


def test_openapi_tertutup_kecuali_diminta(klien, monkeypatch):
    for jalur in ("/openapi.json", "/docs", "/redoc"):
        assert klien.get(jalur).status_code == 404, f"{jalur} terbuka"


SQL = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|TRUNCATE)\s", re.I)


def test_sql_hanya_ada_di_lapisan_repositori():
    bocor = []
    for berkas in (AKAR / "backend").rglob("*.py"):
        bagian = set(berkas.relative_to(AKAR / "backend").parts)
        if bagian & {"repositori", "db"}:
            continue
        isi = berkas.read_text(encoding="utf-8")
        baris_kode = [b for b in isi.splitlines() if not b.strip().startswith("#")]
        if SQL.search("\n".join(baris_kode)):
            bocor.append(berkas.relative_to(AKAR).as_posix())
    assert not bocor, f"SQL bocor keluar dari lapisan repositori: {bocor}"


def test_router_tidak_memanggil_repositori_langsung():
    bocor = []
    for berkas in (AKAR / "backend" / "api").rglob("*.py"):
        isi = berkas.read_text(encoding="utf-8")
        if re.search(r"from backend\.repositori", isi):
            bocor.append(berkas.relative_to(AKAR).as_posix())
    assert not bocor, f"router melompati lapisan layanan: {bocor}"


def test_aplikasi_tidak_pernah_mengubah_susunan_basis_data():
    import re

    larangan = re.compile(
        r"\b(CREATE|DROP|ALTER|TRUNCATE|GRANT|REVOKE)\s+"
        r"(TABLE|INDEX|SCHEMA|ROLE|DATABASE|VIEW|SEQUENCE|EXTENSION)\b",
        re.IGNORECASE,
    )
    for berkas in sorted((AKAR / "backend").rglob("*.py")):
        if "__pycache__" in berkas.parts:
            continue
        if berkas.name == "migrasi.py" or "db" in berkas.parts:
            continue
        isi = berkas.read_text(encoding="utf-8")
        cocok = larangan.search(isi)
        assert cocok is None, (
            f"{berkas.relative_to(AKAR)} memuat DDL: {cocok.group(0)!r}. "
            "Aplikasi berjalan tanpa hak itu, jadi ia akan gagal di produksi."
        )


def test_berkas_hak_terkecil_ada_dan_tidak_memuat_sandi():
    berkas = AKAR / "infrastructure" / "postgres" / "hak_terkecil.sql"
    assert berkas.exists(), "infrastructure/postgres/hak_terkecil.sql hilang"

    isi = berkas.read_text(encoding="utf-8")
    assert "sandi_app" in isi
    assert "PASSWORD '" not in isi, "ada sandi tertulis di berkas yang masuk git"

    for jahat in ("GRANT ALL", "SUPERUSER", "CREATEDB", "CREATEROLE"):
        assert jahat not in isi, f"hak_terkecil.sql memberi {jahat}"
