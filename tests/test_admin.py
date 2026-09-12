"""Jalur tulis admin, dan sumber isi dari API.

Fase 5 dan 6. Dilewati kalau tidak ada basis data.

Uji terakhir di berkas ini yang paling berarti: HTML yang dibangkitkan dari
API harus sama persis dengan yang dibangkitkan dari berkas. Itu bukti bahwa
SumberIsi benar benar antarmuka, bukan sekadar dua kelas yang kebetulan
punya nama metode sama.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
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


pytest.importorskip("fastapi")
pytest.importorskip("httpx")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"
SLUG = "uji-otomatis-jangan-dipakai"


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not bisa_terhubung(), reason="tidak ada basis data")


def contoh(**ganti) -> dict:
    dasar = {
        "slug": SLUG,
        "tanggal": "2026-01-02",
        "judul_en": "Written by a test",
        "judul_id": "Ditulis oleh uji",
        "ringkas_en": "A post that exists only while this test runs.",
        "ringkas_id": "Tulisan yang hanya ada selama uji ini berjalan.",
        "keterangan_en": "Temporary.",
        "keterangan_id": "Sementara.",
        "lede_en": "Nothing here survives the test.",
        "lede_id": "Tidak ada di sini yang bertahan sesudah uji.",
        "isi_en": "## One\n\nA paragraph.\n\n> A quote.",
        "isi_id": "## Satu\n\nSatu paragraf.\n\n> Satu kutipan.",
        "tag_en": "How I work",
        "tag_id": "Cara kerja",
        "baca_en": "1 min read",
        "baca_id": "1 menit baca",
    }
    dasar.update(ganti)
    return dasar


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


@pytest.fixture
def kepala(klien) -> dict:
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return {"Authorization": f"Bearer {j.json()['akses']}"}


@pytest.fixture(autouse=True)
def bersihkan():
    yield
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("DELETE FROM blog_posts WHERE slug LIKE 'uji-%%'")
        k.execute("DELETE FROM gagal_masuk")
        s.commit()


# ------------------------------------------------------------- otorisasi ---


@pytest.mark.parametrize("metode,jalur", [
    ("get", "/api/v1/admin/blog"),
    ("post", "/api/v1/admin/blog"),
    ("patch", f"/api/v1/admin/blog/{SLUG}"),
    ("delete", f"/api/v1/admin/blog/{SLUG}"),
])
def test_semua_jalur_admin_tertutup_tanpa_token(klien, metode, jalur):
    """Bab 15.9. Satu rute yang lupa dijaga sudah cukup untuk membuka semuanya."""
    kirim = {"json": {}} if metode in ("post", "patch") else {}
    j = getattr(klien, metode)(jalur, **kirim)
    assert j.status_code == 401, f"{metode.upper()} {jalur} terbuka tanpa token"


# ------------------------------------------------------------------ alur ---


def test_tulisan_baru_mulai_sebagai_draf(klien, kepala):
    j = klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    assert j.status_code == 201, j.text
    assert j.json()["status"] == "draf"

    # draf tidak boleh terlihat di jalur publik
    assert klien.get(f"/api/v1/blog/{SLUG}").status_code == 404


def test_terbit_lalu_terlihat_publik(klien, kepala):
    klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    j = klien.post(f"/api/v1/admin/blog/{SLUG}/status", headers=kepala,
                   json={"status": "terbit"})
    assert j.status_code == 200
    assert klien.get(f"/api/v1/blog/{SLUG}").status_code == 200


def test_arsip_menghilang_lagi(klien, kepala):
    klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    klien.post(f"/api/v1/admin/blog/{SLUG}/status", headers=kepala, json={"status": "terbit"})
    klien.post(f"/api/v1/admin/blog/{SLUG}/status", headers=kepala, json={"status": "arsip"})
    assert klien.get(f"/api/v1/blog/{SLUG}").status_code == 404


def test_slug_kembar_ditolak_409(klien, kepala):
    klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    j = klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    assert j.status_code == 409


def test_sunting_sebagian(klien, kepala):
    klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    j = klien.patch(f"/api/v1/admin/blog/{SLUG}", headers=kepala,
                    json={"judul_en": "Judul baru"})
    assert j.status_code == 200

    klien.post(f"/api/v1/admin/blog/{SLUG}/status", headers=kepala, json={"status": "terbit"})
    isi = klien.get(f"/api/v1/blog/{SLUG}").json()
    assert isi["judul"]["en"] == "Judul baru"
    assert isi["judul"]["id"] == "Ditulis oleh uji", "kolom lain ikut berubah"


def test_sunting_kosong_ditolak(klien, kepala):
    klien.post("/api/v1/admin/blog", headers=kepala, json=contoh())
    assert klien.patch(f"/api/v1/admin/blog/{SLUG}", headers=kepala, json={}).status_code == 422


def test_slug_tidak_ada_menjawab_404(klien, kepala):
    j = klien.patch("/api/v1/admin/blog/tidak-pernah-ada", headers=kepala,
                    json={"judul_en": "x"})
    assert j.status_code == 404


# ---------------------------------------------------------- yang ditolak ---


def test_dua_bahasa_tidak_sebangun_ditolak(klien, kepala):
    """Aturan yang sama dengan yang dijaga pembangkit situs statis: satu
    bahasa kehilangan satu paragraf adalah kegagalan yang diam."""
    j = klien.post("/api/v1/admin/blog", headers=kepala,
                   json=contoh(isi_id="## Satu\n\nSatu paragraf."))
    assert j.status_code == 422
    assert "blok" in j.text


def test_markah_tidak_didukung_ditolak(klien, kepala):
    j = klien.post("/api/v1/admin/blog", headers=kepala,
                   json=contoh(isi_en="- daftar", isi_id="- daftar"))
    assert j.status_code == 422
    assert "baris 1" in j.text


def test_slug_berspasi_ditolak(klien, kepala):
    j = klien.post("/api/v1/admin/blog", headers=kepala, json=contoh(slug="uji ada spasi"))
    assert j.status_code == 422


def test_terlalu_panjang_ditolak_sebelum_sampai_basis_data(klien, kepala):
    """Kalau yang menolak cuma PostgreSQL, yang sampai ke penulis adalah 500
    tanpa penjelasan."""
    j = klien.post("/api/v1/admin/blog", headers=kepala, json=contoh(judul_en="x" * 400))
    assert j.status_code == 422


# --------------------------------------------------------------- fase 6 ---


def test_sumber_api_sama_dengan_sumber_berkas():
    """Antarmuka SumberIsi dipenuhi dua implementasi yang hasilnya identik."""
    from isi import SumberApi, SumberBerkas

    api = SumberApi("http://127.0.0.1:8000")
    try:
        dari_api = api.tulisan()
    except Exception:
        pytest.skip("API tidak berjalan di 127.0.0.1:8000")

    dari_berkas = SumberBerkas(AKAR / "content").tulisan()

    assert [t.slug for t in dari_api] == [t.slug for t in dari_berkas]
    for a, b in zip(dari_api, dari_berkas):
        assert a.judul == b.judul, f"{a.slug}: judul berbeda"
        assert a.isi_en == b.isi_en, f"{a.slug}: isi Inggris berbeda"
        assert a.isi_id == b.isi_id, f"{a.slug}: isi Indonesia berbeda"


def test_bangkitan_dari_api_sama_persis_dengan_yang_ter_commit():
    """Bukti paling keras bahwa Fase 0 tidak terbuang: pembangkit yang sama,
    sumber yang berbeda, keluaran yang sama sampai ke byte."""
    hasil = subprocess.run(
        [sys.executable, "tools/bangun_tulisan.py", "--sumber", "api", "--periksa"],
        cwd=AKAR, capture_output=True, text=True,
    )
    if "URLError" in hasil.stderr or "tidak dapat" in hasil.stderr:
        pytest.skip("API tidak berjalan di 127.0.0.1:8000")
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr
