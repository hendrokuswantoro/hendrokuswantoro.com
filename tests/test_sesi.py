from __future__ import annotations

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
from konftes import EMAIL_UJI as EMAIL  # noqa: E402
from konftes import SANDI_UJI as SANDI  # noqa: E402


from konftes import loop_untuk_psycopg as _loop_untuk_psycopg  # noqa: E402


from konftes import ada_basis_data  # noqa: E402


pytestmark = pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data")


@pytest.fixture(autouse=True)
def bersihkan():
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
    klien.cookies.clear()
    kepala = _masuk(klien)
    cookie = klien.cookies.get(NAMA_COOKIE)
    assert cookie, "masuk tidak memasang cookie refresh"
    return kepala, cookie


def _pakai(klien, cookie: str | None) -> None:
    klien.cookies.clear()
    if cookie:
        klien.cookies.set(NAMA_COOKIE, cookie, path=JALUR_COOKIE)


def test_menuntut_sudah_masuk(klien):
    assert klien.get("/api/v1/auth/sesi").status_code in (401, 403)


def test_sesi_sendiri_muncul_dan_ditandai(klien):
    kepala = _masuk(klien)
    isi = klien.get("/api/v1/auth/sesi", headers=kepala).json()

    assert isi["jumlah"] >= 1
    assert isi["jumlah"] == len(isi["sesi"])
    ini = [s for s in isi["sesi"] if s["perangkat_ini"]]
    assert len(ini) == 1, f"perangkat ini harus tepat satu, dapat {len(ini)}"


def test_sidik_token_tidak_pernah_ikut_keluar(klien):
    kepala = _masuk(klien)
    isi = klien.get("/api/v1/auth/sesi", headers=kepala).json()

    for satu in isi["sesi"]:
        assert set(satu) == {"id", "dibuat_pada", "kadaluarsa", "perangkat_ini"}, (
            f"jawabannya membawa medan yang tidak diminta: {sorted(satu)}"
        )
    teks = klien.get("/api/v1/auth/sesi", headers=kepala).text
    assert "token_hash" not in teks


def test_tanpa_nama_perangkat_dan_tanpa_alamat(klien):
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

    _pakai(klien, cookie_b)
    assert klien.post("/api/v1/auth/logout").status_code == 204

    _pakai(klien, cookie_a)
    sesudah = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"]
    assert sesudah == sebelum, "sesi yang sudah keluar masih terdaftar"
    assert kepala_b


def test_cabut_lain_menyisakan_perangkat_ini(klien):
    kepala_a, cookie_a = _perangkat_baru(klien)
    _kepala_b, cookie_b = _perangkat_baru(klien)

    _pakai(klien, cookie_a)
    assert klien.get("/api/v1/auth/sesi", headers=kepala_a).json()["jumlah"] >= 2

    jawab = klien.post("/api/v1/auth/sesi/cabut-lain", headers=kepala_a)
    assert jawab.status_code == 200, jawab.text
    assert jawab.json()["sesi_dicabut"] >= 1

    isi = klien.get("/api/v1/auth/sesi", headers=kepala_a).json()
    assert isi["jumlah"] == 1
    assert isi["sesi"][0]["perangkat_ini"] is True

    _pakai(klien, cookie_b)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 401, (
        f"sesi lain masih bisa diperpanjang: {putar.status_code}"
    )


def test_cabut_lain_menuntut_sudah_masuk(klien):
    assert klien.post("/api/v1/auth/sesi/cabut-lain").status_code in (401, 403)
