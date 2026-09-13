"""API: bentuk jawabannya, kode statusnya, dan lapisan yang menopangnya.

Dilewati kalau tidak ada basis data, sama seperti test_basis_data.py.

Uji terakhir di berkas ini tidak menyentuh HTTP sama sekali. Ia menegakkan
pemisahan lapisan yang diminta bab 15.4, sebab pemisahan yang hanya ditulis
di dokumen akan runtuh pada hari pertama seseorang menulis satu kueri di
tempat yang salah karena sedang buru buru.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()


def _loop_untuk_psycopg() -> None:
    """psycopg menolak ProactorEventLoop, yang jadi bawaan Windows.

    Disetel di dalam fixture, bukan saat modul diimpor. pytest mengimpor
    seluruh modul uji saat mengoleksi, bahkan yang tidak akan dijalankan,
    jadi menyetelnya di tingkat modul ikut meracuni proses yang sedang
    menjalankan uji Playwright: Playwright justru menuntut ProactorEventLoop
    untuk menjalankan subproses, dan gagalnya berbunyi NotImplementedError
    yang tidak menyebut sebabnya.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


pytest.importorskip("fastapi", reason="backend belum terpasang")
pytest.importorskip("httpx", reason="httpx belum terpasang")

from fastapi.testclient import TestClient  # noqa: E402

DSN = os.environ.get("DSN", "")


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        import psycopg

        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


ADA_DB = bisa_terhubung()


@pytest.fixture(scope="module")
def klien():
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
    """Validasi Pydantic, bukan 500 dari basis data."""
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
        # urutan sumbu RFC 7946: bujur dulu. Tertukar berarti Indonesia
        # digambar di Somalia, dan tidak ada galat yang menyebutnya
        assert 94 <= bujur <= 142, f"{f['properties']['slug']}: bujur di luar Indonesia"
        assert -12 <= lintang <= 7, f"{f['properties']['slug']}: lintang di luar Indonesia"


@butuh_db
def test_nearby_jaraknya_meter(klien):
    """Jarak dalam derajat tidak ada artinya. Parkir ada di tengah Yogyakarta,
    jadi jaraknya dari Tugu wajib di bawah 5 km, bukan angka tanpa satuan."""
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
    """Bab 15.22 menuntut dokumentasi API. FastAPI membuatnya, tetapi hanya
    kalau tiap rute benar benar punya response_model.

    Dibaca dari aplikasinya langsung, bukan lewat HTTP. Sejak penyisiran
    keamanan 13 September 2026, /openapi.json tertutup kecuali DOKUMEN_API=1,
    jadi mengambilnya lewat HTTP akan menguji setelan itu, bukan kelengkapan
    dokumentasinya.
    """
    from backend.main import aplikasi

    jalur = aplikasi.openapi()["paths"]
    for wajib in ("/health", "/api/v1/blog", "/api/v1/maps/projects-spatial"):
        assert wajib in jalur, f"{wajib} tidak terdokumentasi"


def test_openapi_tertutup_kecuali_diminta(klien, monkeypatch):
    """Peta lengkap permukaan API, termasuk tiap titik akhir admin, tidak
    diberikan cuma cuma kepada siapa pun yang membukanya."""
    for jalur in ("/openapi.json", "/docs", "/redoc"):
        assert klien.get(jalur).status_code == 404, f"{jalur} terbuka"


# --------------------------------------------------------------- lapisan ---

SQL = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|TRUNCATE)\s", re.I)


def test_sql_hanya_ada_di_lapisan_repositori():
    """Bab 15.4. Begitu satu kueri ditulis di lapisan layanan atau di router,
    seluruh pemisahannya jadi hiasan."""
    bocor = []
    for berkas in (AKAR / "backend").rglob("*.py"):
        bagian = set(berkas.relative_to(AKAR / "backend").parts)
        if bagian & {"repositori", "db"}:
            continue
        isi = berkas.read_text(encoding="utf-8")
        # abaikan docstring dan komentar yang menyebut SQL sebagai kata biasa
        baris_kode = [b for b in isi.splitlines() if not b.strip().startswith("#")]
        if SQL.search("\n".join(baris_kode)):
            bocor.append(berkas.relative_to(AKAR).as_posix())
    assert not bocor, f"SQL bocor keluar dari lapisan repositori: {bocor}"


def test_router_tidak_memanggil_repositori_langsung():
    """Router berbicara ke layanan, layanan berbicara ke repositori."""
    bocor = []
    for berkas in (AKAR / "backend" / "api").rglob("*.py"):
        isi = berkas.read_text(encoding="utf-8")
        if re.search(r"from backend\.repositori", isi):
            bocor.append(berkas.relative_to(AKAR).as_posix())
    assert not bocor, f"router melompati lapisan layanan: {bocor}"
