"""Unggah, sisipkan, terbitkan, hapus. Lewat API sungguhan dan basis data.

Dilewati kalau tidak ada basis data. Yang diuji di sini bukan lagi pembacaan
kepala berkas, melainkan apa yang terjadi di antara lapisan: berkas yang
tertulis ke cakram, baris yang tertulis ke basis data, dan yang tidak boleh
terjadi kalau salah satunya gagal.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()


def _loop_untuk_psycopg() -> None:
    """psycopg menolak ProactorEventLoop, yang jadi bawaan Windows. Disetel di
    dalam fixture, bukan saat modul diimpor: pytest mengimpor seluruh modul
    uji saat mengoleksi, dan menyetelnya lebih awal ikut meracuni proses yang
    sedang menjalankan uji Playwright."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


pytest.importorskip("fastapi")
pytest.importorskip("httpx")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

from test_berkas import gif, jpeg, mp4, png  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not bisa_terhubung(), reason="tidak ada basis data")


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


@pytest.fixture
def bersih(klien, kepala):
    """Menghapus tiap berkas yang dibuat uji ini, lewat API-nya sendiri."""
    dibuat: list[str] = []
    yield dibuat
    for nama in dibuat:
        klien.delete(f"/api/v1/admin/berkas/{nama}", headers=kepala)


def unggah(klien, kepala, data: bytes, nama: str, tipe: str = "application/octet-stream"):
    return klien.post(
        "/api/v1/admin/berkas",
        headers=kepala,
        files={"berkas": (nama, data, tipe)},
    )


# ------------------------------------------------------------------ alur ---


def test_foto_masuk_lalu_muncul_di_daftar(klien, kepala, bersih):
    j = unggah(klien, kepala, png(1600, 900), "pemandangan.png")
    assert j.status_code == 201, j.text
    hasil = j.json()
    bersih.append(hasil["nama"])

    assert hasil["jenis"] == "gambar"
    assert hasil["tipe_mime"] == "image/png"
    assert (hasil["lebar"], hasil["tinggi"]) == (1600, 900)
    assert hasil["alamat"] == f"/unggahan/{hasil['nama']}"
    assert hasil["nama_asal"] == "pemandangan.png"
    assert hasil["sudah_ada"] is False

    daftar = klien.get("/api/v1/admin/berkas", headers=kepala).json()
    assert any(b["nama"] == hasil["nama"] for b in daftar["isi"])


def test_berkas_benar_benar_bisa_diambil_dari_alamatnya(klien, kepala, bersih):
    j = unggah(klien, kepala, png(64, 48), "kecil.png")
    hasil = j.json()
    bersih.append(hasil["nama"])

    ambil = klien.get(hasil["alamat"])
    assert ambil.status_code == 200
    assert ambil.headers["content-type"] == "image/png"
    # nosniff dipasang aplikasi sendiri, bukan diserahkan ke nginx: jalur ini
    # juga hidup saat dikembangkan tanpa nginx sama sekali.
    assert ambil.headers["x-content-type-options"] == "nosniff"
    assert "immutable" in ambil.headers["cache-control"]


def test_ukuran_gambar_ikut_ke_dalam_nama_berkasnya(klien, kepala, bersih):
    """Supaya pembangkit halaman tahu lebar dan tingginya tanpa membuka
    berkasnya dan tanpa bertanya ke basis data."""
    j = unggah(klien, kepala, jpeg(800, 450), "foto.jpg")
    hasil = j.json()
    bersih.append(hasil["nama"])
    assert hasil["nama"].endswith("-800x450.jpg")

    sys.path.insert(0, str(AKAR / "tools"))
    import markah

    assert markah.ukuran(hasil["alamat"]) == (800, 450)


def test_markah_yang_dijawab_memang_diterima_pengurainya(klien, kepala, bersih):
    """Jawaban unggahan membawa baris markah siap tempel. Kalau baris itu
    ditolak pengurai, tombol Sisipkan adalah tombol yang menghasilkan galat."""
    sys.path.insert(0, str(AKAR / "tools"))
    import markah

    for data, nama in ((png(10, 10), "a.png"), (mp4(), "a.mp4")):
        hasil = unggah(klien, kepala, data, nama).json()
        bersih.append(hasil["nama"])
        blok = markah.blok(hasil["markah"])
        assert len(blok) == 1
        assert blok[0].alamat == hasil["alamat"]


def test_video_tidak_diukur(klien, kepala, bersih):
    """Mengukurnya menuntut ffmpeg, dan menebaknya berarti menuliskan angka
    yang tidak pernah diukur."""
    hasil = unggah(klien, kepala, mp4(), "jalan.mp4").json()
    bersih.append(hasil["nama"])
    assert hasil["jenis"] == "video"
    assert hasil["lebar"] is None and hasil["tinggi"] is None


def test_berkas_yang_sama_tidak_digandakan(klien, kepala, bersih):
    """Satu foto yang dipakai di tiga tulisan tetap satu berkas di cakram."""
    data = gif(120, 90)
    satu = unggah(klien, kepala, data, "sama.gif").json()
    bersih.append(satu["nama"])

    dua = unggah(klien, kepala, data, "nama-lain.gif").json()
    assert dua["nama"] == satu["nama"]
    assert dua["sudah_ada"] is True


# ---------------------------------------------------------------- tolakan ---


def test_html_bernama_foto_png_tetap_ditolak(klien, kepala):
    """Nama dan Content-Type keduanya datang dari pengirim. Berkas yang lolos
    akan disajikan lagi dari alamat situs ini."""
    j = unggah(klien, kepala, b"<html><script>alert(1)</script>", "foto.png", "image/png")
    assert j.status_code == 415
    assert "bukan foto atau video" in j.text


def test_nama_kiriman_yang_menjelajah_folder_tidak_membentuk_jalur(klien, kepala, bersih):
    """Namanya dicatat apa adanya untuk dilihat orang, dan nama di cakram
    tetap buatan server sendiri."""
    j = unggah(klien, kepala, png(20, 20), "../../etc/passwd.png")
    assert j.status_code == 201
    hasil = j.json()
    bersih.append(hasil["nama"])

    assert ".." not in hasil["nama"]
    assert "/" not in hasil["nama"]
    assert hasil["nama_asal"] == "passwd.png"


# ---------------------------------------------------------------- hapus ---


def test_berkas_yang_masih_dipakai_tulisan_tidak_bisa_dihapus(klien, kepala, bersih):
    """Menghapusnya adalah kegagalan yang tidak bersuara: tulisannya tetap
    terbit, hanya gambarnya jadi kotak kosong, dan yang menyadarinya
    pembaca."""
    hasil = unggah(klien, kepala, png(400, 300), "dipakai.png").json()
    bersih.append(hasil["nama"])

    slug = "uji-berkas-dipakai"
    tulisan = {
        "slug": slug,
        "tanggal": "2026-01-02",
        "judul_en": "With a picture", "judul_id": "Dengan gambar",
        "ringkas_en": "Short.", "ringkas_id": "Pendek.",
        "keterangan_en": "Short.", "keterangan_id": "Pendek.",
        "lede_en": "Lede.", "lede_id": "Lede.",
        "isi_en": f"A paragraph.\n\n![A picture]({hasil['alamat']})",
        "isi_id": f"Satu paragraf.\n\n![Sebuah gambar]({hasil['alamat']})",
        "tag_en": "How I work", "tag_id": "Cara kerja",
        "baca_en": "1 min read", "baca_id": "1 menit baca",
    }
    buat = klien.post("/api/v1/admin/blog", headers=kepala, json=tulisan)
    assert buat.status_code == 201, buat.text

    try:
        tolak = klien.delete(f"/api/v1/admin/berkas/{hasil['nama']}", headers=kepala)
        assert tolak.status_code == 409
        assert slug in tolak.text
    finally:
        klien.delete(f"/api/v1/admin/blog/{slug}", headers=kepala)


def test_hapus_membuang_barisnya_dan_berkasnya_sekaligus(klien, kepala):
    hasil = unggah(klien, kepala, png(30, 30), "sekali-pakai.png").json()

    from backend.layanan import berkas as layanan

    jalur = layanan.jalur(hasil["nama"])
    assert jalur.exists()

    buang = klien.delete(f"/api/v1/admin/berkas/{hasil['nama']}", headers=kepala)
    assert buang.status_code == 204
    assert not jalur.exists()
    assert klien.get(hasil["alamat"]).status_code == 404


def test_hapus_berkas_yang_tidak_ada_menjawab_404(klien, kepala):
    j = klien.delete("/api/v1/admin/berkas/tidak-pernah-ada.webp", headers=kepala)
    assert j.status_code == 404


# ------------------------------------------------------------- pratinjau ---


def test_pratinjau_memakai_pembangkit_yang_sama_dengan_situsnya(klien, kepala, bersih):
    hasil = unggah(klien, kepala, png(1200, 800), "pratinjau.png").json()
    bersih.append(hasil["nama"])

    j = klien.post(
        "/api/v1/admin/pratinjau",
        headers=kepala,
        json={
            "isi_en": f"## Head\n\n- one\n- two\n\n![A picture]({hasil['alamat']})",
            "isi_id": f"## Judul\n\n- satu\n- dua\n\n![Sebuah gambar]({hasil['alamat']})",
        },
    )
    assert j.status_code == 200, j.text
    html = j.json()["html"]

    assert "<h2 " in html
    assert '<ul class="tulisan__daftar">' in html
    assert 'width="1200" height="800"' in html
    assert 'data-ind-alt="Sebuah gambar"' in html


def test_pratinjau_menolak_dengan_alasan_yang_sama_dengan_simpan(klien, kepala):
    """Pratinjau yang menerima apa yang Simpan tolak adalah pratinjau yang
    berbohong."""
    jahat = "![peta](https://contoh.example/a.png)"
    j = klien.post("/api/v1/admin/pratinjau", headers=kepala,
                   json={"isi_en": jahat, "isi_id": jahat})
    assert j.status_code == 422
    assert "diunggah ke situs ini" in j.text


def test_pratinjau_menghitung_kata_tanpa_tanda_markahnya(klien, kepala):
    j = klien.post(
        "/api/v1/admin/pratinjau",
        headers=kepala,
        json={"isi_en": "**Dua** kata.", "isi_id": "**Dua** kata."},
    )
    assert j.json()["kata_en"] == 2


def test_systemexit_dari_pembangkit_tidak_menjatuhkan_pekerjanya(klien, kepala):
    """badan() adalah alat baris perintah yang berhenti dengan SystemExit
    ketika dua bahasanya tidak sebangun. SystemExit bukan turunan Exception:
    kalau ia naik dari dalam sebuah permintaan, yang berhenti bukan
    permintaannya melainkan pekerjanya."""
    j = klien.post(
        "/api/v1/admin/pratinjau",
        headers=kepala,
        json={"isi_en": "Satu.\n\nDua.", "isi_id": "Satu."},
    )
    assert j.status_code == 422
    assert "blok" in j.text
    # Dan prosesnya masih melayani permintaan berikutnya.
    assert klien.get("/api/v1/admin/berkas", headers=kepala).status_code == 200
