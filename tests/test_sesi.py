"""Daftar perangkat yang sedang masuk, dan cara mengusirnya.

Panel ini menjawab satu pertanyaan yang tidak bisa dijawab dari mana pun
sebelumnya: **ada berapa sesi yang hidup di akun saya sekarang.** Selama
jawabannya tidak bisa dilihat, sesi curian bisa hidup berbulan bulan tanpa
seorang pun tahu, sebab sesi yang dipakai orang lain tidak menimbulkan apa
apa di layar pemiliknya.

Dua hal yang dijaga di sini, dan yang kedua lebih mudah dilanggar:

1. **Daftarnya benar.** Sesi yang dicabut dan yang kedaluwarsa tidak ikut,
   dan sesi perangkat yang sedang dipakai ditandai.
2. **Sidik tokennya tidak pernah keluar.** Yang dikirim ke peramban cuma
   penanda "perangkat ini", bukan sidik yang dipakai membandingkannya. Sidik
   yang sampai ke halaman adalah sidik yang bisa dibaca siapa pun yang
   membuka halaman itu.

Ada juga yang sengaja TIDAK ada di jawabannya: nama perangkat dan alamat IP.
Keduanya memang tidak pernah disimpan, dan menambahkannya berarti mulai
mencatat tempat pemiliknya berada. Itu keputusan tersendiri, bukan sesuatu
yang boleh menyelinap masuk lewat sebuah panel.

Dilewati kalau tidak ada basis data.
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

pytest.importorskip("fastapi")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def _loop_untuk_psycopg() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _bisa_terhubung(), reason="tidak ada basis data")


@pytest.fixture(autouse=True)
def bersihkan():
    """Sesi milik uji ini dicabut, bukan dihapus, dan hanya yang lahir di sini.

    Dicabut supaya jalurnya sama dengan yang dilalui sesi sungguhan. Dibatasi
    waktu supaya sesi pemiliknya yang sedang hidup di peramban tidak ikut
    diputus oleh sebuah uji.
    """
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT now()")
        sejak = k.fetchone()[0]
    yield
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "UPDATE sesi SET dicabut_pada = now() "
            "WHERE dibuat_pada >= %s AND dicabut_pada IS NULL",
            (sejak,),
        )
        # Dibatasi waktu, sama seperti baris di atasnya. Menghapus seluruh
        # isinya akan membuka kunci akun yang memang sedang terkunci karena
        # percobaan masuk yang gagal, di mesin siapa pun yang menjalankan ini.
        k.execute("DELETE FROM gagal_masuk WHERE pada >= %s", (sejak,))
        s.commit()


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


NAMA_COOKIE = "hk_refresh"
JALUR_COOKIE = "/api/v1/auth"


def _masuk(klien) -> dict:
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return {"Authorization": f"Bearer {j.json()['akses']}"}


def _perangkat_baru(klien) -> tuple[dict, str]:
    """Satu sesi lagi, seolah dari perangkat lain.

    Dua perangkat ditiru dengan menukar cookie, bukan dengan membuka
    `TestClient` kedua di dalam yang pertama. Versi pertama uji ini melakukan
    yang kedua dan pecah saat dibongkar, dengan `RuntimeError: got Future
    attached to a different loop`: tiap TestClient menjalankan portalnya
    sendiri, dan yang di dalam menutup lebih dulu daripada yang di luar.
    Titik akhirnya sendiri baik baik saja, yang keliru cara mengujinya.
    """
    klien.cookies.clear()
    kepala = _masuk(klien)
    cookie = klien.cookies.get(NAMA_COOKIE)
    assert cookie, "masuk tidak memasang cookie refresh"
    return kepala, cookie


def _pakai(klien, cookie: str | None) -> None:
    klien.cookies.clear()
    if cookie:
        klien.cookies.set(NAMA_COOKIE, cookie, path=JALUR_COOKIE)


# ------------------------------------------------------------------ daftar ---


def test_menuntut_sudah_masuk(klien):
    """Daftar perangkat adalah keterangan tentang akun, bukan halaman umum."""
    assert klien.get("/api/v1/auth/sesi").status_code in (401, 403)


def test_sesi_sendiri_muncul_dan_ditandai(klien):
    kepala = _masuk(klien)
    isi = klien.get("/api/v1/auth/sesi", headers=kepala).json()

    assert isi["jumlah"] >= 1
    assert isi["jumlah"] == len(isi["sesi"])
    ini = [s for s in isi["sesi"] if s["perangkat_ini"]]
    assert len(ini) == 1, f"perangkat ini harus tepat satu, dapat {len(ini)}"


def test_sidik_token_tidak_pernah_ikut_keluar(klien):
    """Yang dikirim penanda, bukan bahan untuk membuat penanda itu."""
    kepala = _masuk(klien)
    isi = klien.get("/api/v1/auth/sesi", headers=kepala).json()

    for satu in isi["sesi"]:
        assert set(satu) == {"id", "dibuat_pada", "kadaluarsa", "perangkat_ini"}, (
            f"jawabannya membawa medan yang tidak diminta: {sorted(satu)}"
        )
    teks = klien.get("/api/v1/auth/sesi", headers=kepala).text
    assert "token_hash" not in teks


def test_tanpa_nama_perangkat_dan_tanpa_alamat(klien):
    """Kalau suatu saat seseorang menambahkannya, uji ini yang harus dibuka
    lebih dulu, bersama keputusan sadar untuk mulai menyimpannya."""
    kepala = _masuk(klien)
    teks = klien.get("/api/v1/auth/sesi", headers=kepala).text.lower()
    for kata in ("user_agent", "useragent", "alamat", "ip_", "peramban"):
        assert kata not in teks, f"jawabannya menyebut {kata}"


def test_sesi_yang_dicabut_tidak_ikut(klien):
    kepala_a, cookie_a = _perangkat_baru(klien)
    sebelum = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"]

    kepala_b, cookie_b = _perangkat_baru(klien)
    tengah = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"]
    assert tengah == sebelum + 1, "sesi kedua tidak terlihat"

    # Keluar dari perangkat kedua lewat jalur biasa, bukan lewat SQL.
    _pakai(klien, cookie_b)
    assert klien.post("/api/v1/auth/logout").status_code == 204

    _pakai(klien, cookie_a)
    sesudah = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"]
    assert sesudah == sebelum, "sesi yang sudah keluar masih terdaftar"
    assert kepala_b  # dipakai supaya niatnya jelas: dua sesi, bukan satu


# ------------------------------------------------------------- cabut lain ---


def test_cabut_lain_menyisakan_perangkat_ini(klien):
    """Ini inti panelnya. Tombol yang ikut mengeluarkan pemiliknya akan ragu
    ragu ditekan, padahal justru saat curiga ia harus ditekan cepat."""
    kepala_a, cookie_a = _perangkat_baru(klien)
    _kepala_b, cookie_b = _perangkat_baru(klien)

    _pakai(klien, cookie_a)
    assert klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"] >= 2

    jawab = klien.post("/api/v1/auth/sesi/cabut-lain", headers=kepala_a)
    assert jawab.status_code == 200, jawab.text
    assert jawab.json()["sesi_dicabut"] >= 1

    # Yang di sini masih hidup, dan tinggal sendirian.
    isi = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()
    assert isi["jumlah"] == 1
    assert isi["sesi"][0]["perangkat_ini"] is True

    # Yang di sana sudah tidak bisa memperpanjang.
    _pakai(klien, cookie_b)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 401, (
        f"sesi lain masih bisa diperpanjang: {putar.status_code}"
    )


def test_cabut_lain_menuntut_sudah_masuk(klien):
    assert klien.post("/api/v1/auth/sesi/cabut-lain").status_code in (401, 403)
