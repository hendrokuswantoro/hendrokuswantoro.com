"""Basis data: skema, batasan, dan isinya.

Dilewati kalau tidak ada basis data yang bisa dihubungi, supaya rangkaian uji
tetap bisa dijalankan tanpa Docker. Di CI basis datanya disediakan sebagai
service container, jadi di sana uji ini benar benar berjalan.

Yang diuji bukan "barisnya ada", melainkan **basis datanya menolak yang harus
ditolak**. Batasan yang tidak pernah diuji adalah batasan yang mungkin saja
tidak pernah menyala.
"""

from __future__ import annotations

import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

from isi import SumberBerkas  # noqa: E402
from muat_env import muat  # noqa: E402

muat()

psycopg = pytest.importorskip("psycopg", reason="psycopg belum terpasang")

DSN = os.environ.get("DSN", "")


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not bisa_terhubung(),
    reason="tidak ada basis data. Jalankan: cd infrastructure && docker compose up -d",
)


@pytest.fixture(scope="module")
def sambung():
    with psycopg.connect(DSN) as s:
        yield s


def test_postgis_hidup(sambung):
    with sambung.cursor() as k:
        k.execute("SELECT postgis_version()")
        assert k.fetchone()[0], "ekstensi PostGIS tidak aktif"


def test_migrasi_tercatat(sambung):
    with sambung.cursor() as k:
        k.execute("SELECT count(*) FROM skema_migrasi")
        assert k.fetchone()[0] >= 1, "tidak ada migrasi yang tercatat"


def test_indeks_spasial_ada(sambung):
    """Tanpa GIST, tiap kueri spasial memindai seluruh tabel."""
    with sambung.cursor() as k:
        k.execute(
            "SELECT tablename FROM pg_indexes "
            "WHERE indexdef ILIKE '%USING gist%' AND schemaname = 'public'"
        )
        tabel = {r[0] for r in k.fetchall()}
    assert {"projects", "spatial_layers"} <= tabel, f"indeks GIST kurang, ada di {tabel}"


def test_isi_basis_data_sama_dengan_content(sambung):
    """Basis data yang isinya berbeda dari situs yang terbit adalah jenis
    kesalahan yang paling lama tidak ketahuan."""
    sumber = SumberBerkas(AKAR / "content")
    with sambung.cursor() as k:
        k.execute("SELECT slug FROM blog_posts ORDER BY slug")
        tulisan_db = [r[0] for r in k.fetchall()]
        k.execute("SELECT slug FROM projects ORDER BY slug")
        proyek_db = [r[0] for r in k.fetchall()]

    assert tulisan_db == sorted(t.slug for t in sumber.tulisan())
    assert proyek_db == sorted(p.slug for p in sumber.proyek())


def test_geojson_keluar_dari_postgis(sambung):
    with sambung.cursor() as k:
        k.execute(
            "SELECT slug, ST_AsGeoJSON(geom)::json FROM projects ORDER BY urut LIMIT 1"
        )
        slug, geo = k.fetchone()
    assert geo["type"] == "Point"
    bujur, lintang = geo["coordinates"]
    assert 94 <= bujur <= 142 and -12 <= lintang <= 7, f"{slug} di luar Indonesia"


def test_kueri_jarak_memakai_geography(sambung):
    """Jarak dalam derajat tidak ada artinya. Uji ini memastikan jalur meter
    benar benar bekerja, bukan sekadar tidak melempar galat."""
    with sambung.cursor() as k:
        k.execute(
            """
            SELECT count(*) FROM projects
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(110.3671, -7.7828), 4326)::geography,
                50000)
            """
        )
        dekat = k.fetchone()[0]
    assert dekat >= 1, "tidak ada proyek dalam 50 km dari Yogyakarta, itu mustahil"


def test_titik_di_luar_indonesia_ditolak(sambung):
    with pytest.raises(psycopg.errors.CheckViolation):
        with sambung.transaction(), sambung.cursor() as k:
            k.execute(
                "INSERT INTO projects (slug,urut,judul_en,judul_id,ringkas_en,"
                "ringkas_id,peran_en,peran_id,badge_en,badge_id,kategori,"
                "jenis_peta,teknologi,gambar,gambar_alt_en,gambar_alt_id,geom) "
                "VALUES ('uji-paris',900,'a','a','a','a','a','a','a','a',"
                "'{app}','app','{x}','/a','a','a',"
                "ST_SetSRID(ST_MakePoint(2.35,48.85),4326))"
            )


def test_terbit_tanpa_tanggal_ditolak(sambung):
    """Merusak urutan umpan RSS tanpa galat apa pun, kalau dibiarkan lolos."""
    with pytest.raises(psycopg.errors.CheckViolation):
        with sambung.transaction(), sambung.cursor() as k:
            k.execute(
                "INSERT INTO blog_posts (slug,judul_en,judul_id,ringkas_en,"
                "ringkas_id,keterangan_en,keterangan_id,lede_en,lede_id,"
                "isi_en,isi_id,tag_en,tag_id,baca_en,baca_id,status) "
                "VALUES ('uji-tanpa-tanggal','a','a','a','a','a','a','a','a',"
                "'a','a','a','a','a','a','terbit')"
            )


def test_slug_aneh_ditolak(sambung):
    with pytest.raises(psycopg.errors.CheckViolation):
        with sambung.transaction(), sambung.cursor() as k:
            k.execute(
                "INSERT INTO blog_posts (slug,judul_en,judul_id,ringkas_en,"
                "ringkas_id,keterangan_en,keterangan_id,lede_en,lede_id,"
                "isi_en,isi_id,tag_en,tag_id,baca_en,baca_id) "
                "VALUES ('Judul Dengan Spasi','a','a','a','a','a','a','a','a',"
                "'a','a','a','a','a','a')"
            )


def test_urut_proyek_tidak_boleh_kembar(sambung):
    with pytest.raises(psycopg.errors.UniqueViolation):
        with sambung.transaction(), sambung.cursor() as k:
            k.execute(
                "INSERT INTO projects (slug,urut,judul_en,judul_id,ringkas_en,"
                "ringkas_id,peran_en,peran_id,badge_en,badge_id,kategori,"
                "jenis_peta,teknologi,gambar,gambar_alt_en,gambar_alt_id,geom) "
                "VALUES ('uji-urut-kembar',1,'a','a','a','a','a','a','a','a',"
                "'{app}','app','{x}','/a','a','a',"
                "ST_SetSRID(ST_MakePoint(110.0,-7.0),4326))"
            )


def test_pemuat_bisa_dijalankan_berulang(sambung):
    """Menjalankan pemuat dua kali tidak boleh menggandakan isinya."""
    import subprocess

    with sambung.cursor() as k:
        k.execute("SELECT count(*) FROM projects")
        sebelum = k.fetchone()[0]

    hasil = subprocess.run(
        [sys.executable, "backend/db/muat_awal.py"],
        cwd=AKAR, capture_output=True, text=True,
    )
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr

    with psycopg.connect(DSN) as lagi, lagi.cursor() as k:
        k.execute("SELECT count(*) FROM projects")
        sesudah = k.fetchone()[0]
    assert sesudah == sebelum, f"pemuat menggandakan isi: {sebelum} jadi {sesudah}"
