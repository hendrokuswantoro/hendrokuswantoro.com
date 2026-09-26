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
pytest.importorskip("httpx")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

DSN = os.environ.get("DSN", "")
from konftes import EMAIL_UJI as EMAIL  # noqa: E402
from konftes import SANDI_UJI as SANDI  # noqa: E402


from konftes import ada_basis_data  # noqa: E402


def _ada_redis() -> bool:
    alamat = os.environ.get("REDIS_URL", "")
    if not alamat:
        return False
    try:
        import redis

        redis.from_url(alamat, socket_connect_timeout=2).ping()
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data"),
    pytest.mark.skipif(
        not _ada_redis(),
        reason="tidak ada Redis, jadi pencabutan segera memang tidak berlaku",
    ),
]


@pytest.fixture
def klien():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


def _masuk(klien) -> str:
    jawaban = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert jawaban.status_code == 200, jawaban.text
    isi = jawaban.json()
    if isi["tahap"] != "selesai":
        pytest.skip("akun uji punya faktor kedua, alur ini butuh sesi satu langkah")
    return isi["akses"]


def _kepala(akses: str) -> dict:
    return {"Authorization": f"Bearer {akses}"}


def test_token_akses_mati_seketika_sesudah_keluar(klien):
    akses = _masuk(klien)

    assert klien.get("/api/v1/keamanan", headers=_kepala(akses)).status_code == 200

    assert klien.post("/api/v1/auth/logout").status_code == 204

    jawaban = klien.get("/api/v1/keamanan", headers=_kepala(akses))
    assert jawaban.status_code == 401, (
        "token akses masih berlaku sesudah keluar, jadi pencabutannya tertunda"
    )
    assert "dicabut" in jawaban.text


def test_token_akses_mati_sesudah_keluarkan_yang_lain(klien):
    korban = _masuk(klien)
    penghuni = _masuk(klien)

    keluar = klien.post("/api/v1/auth/sesi/cabut-lain", headers=_kepala(penghuni))
    assert keluar.status_code == 200, keluar.text
    assert keluar.json()["sesi_dicabut"] >= 1

    assert klien.get("/api/v1/keamanan", headers=_kepala(penghuni)).status_code == 200

    jawaban = klien.get("/api/v1/keamanan", headers=_kepala(korban))
    assert jawaban.status_code == 401, (
        "perangkat lain masih bisa memakai tokennya sesudah dikeluarkan"
    )


def test_memutar_refresh_mematikan_token_lama(klien):
    lama = _masuk(klien)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 200, putar.text

    assert klien.get("/api/v1/keamanan", headers=_kepala(lama)).status_code == 401
    baru = putar.json()["akses"]
    assert klien.get("/api/v1/keamanan", headers=_kepala(baru)).status_code == 200


def test_kekuatan_sesi_ikut_berputar(klien):
    _masuk(klien)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 200

    keadaan = klien.get(
        "/api/v1/keamanan", headers=_kepala(putar.json()["akses"])
    ).json()
    assert keadaan["sesi_kuat"] is False


def test_halaman_keamanan_mengaku_pencabutannya_bekerja(klien):
    akses = _masuk(klien)
    keadaan = klien.get("/api/v1/keamanan", headers=_kepala(akses)).json()
    assert keadaan["pencabutan_segera_siap"] is True
