"""Sesi yang dicabut mematikan token aksesnya sekarang, bukan lima belas
menit lagi.

Access token adalah JWT: ia diperiksa dengan tanda tangannya sendiri dan tidak
pernah ditanyakan ke basis data. Itu yang membuatnya murah, dan itu juga yang
membuatnya tidak bisa dicabut. Sampai 19 September 2026, menekan "keluar" atau
"keluarkan perangkat lain" hanya mematikan refresh token-nya; token akses yang
sudah terbit tetap sah sampai umurnya habis.

Lima belas menit terdengar pendek sampai diingat kapan tombolnya ditekan.
"Keluarkan perangkat lain" ditekan justru ketika pemiliknya curiga ada orang
lain di dalam akunnya.

Yang menutupnya daftar cabut di Redis, dan uji di berkas ini yang
membuktikannya. **Tanpa Redis ujinya dilewati, bukan dipalsukan**: tanpa Redis
pemendekan itu memang tidak berlaku, dan halaman keamanan mengatakannya.
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
pytest.importorskip("httpx")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def _ada_basis_data() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


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
    pytest.mark.skipif(not _ada_basis_data(), reason="tidak ada basis data"),
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


# ------------------------------------------------------------------ keluar ---


def test_token_akses_mati_seketika_sesudah_keluar(klien):
    akses = _masuk(klien)

    # Masih hidup sebelum keluar.
    assert klien.get("/api/v1/keamanan", headers=_kepala(akses)).status_code == 200

    assert klien.post("/api/v1/auth/logout").status_code == 204

    # Dan mati sesudahnya, memakai token yang sama persis. Tanpa daftar cabut,
    # baris ini menjawab 200 sampai lima belas menit berikutnya.
    jawaban = klien.get("/api/v1/keamanan", headers=_kepala(akses))
    assert jawaban.status_code == 401, (
        "token akses masih berlaku sesudah keluar, jadi pencabutannya tertunda"
    )
    assert "dicabut" in jawaban.text


def test_token_akses_mati_sesudah_keluarkan_yang_lain(klien):
    """Tombol yang ditekan orang saat sedang curiga. Ia menjanjikan perangkat
    lain keluar sekarang, dan janji itu harus benar sekarang.

    Dua sesi dibuat lewat satu klien, bukan dua. Dua TestClient bersarang
    membuat dua gelung peristiwa, dan kolam psycopg yang lahir di gelung
    pertama menolak dipakai dari gelung kedua dengan galat yang tidak menyebut
    sebabnya: "attached to a different loop". Yang dibutuhkan uji ini cuma dua
    sesi, dan masuk dua kali sudah memberi dua sesi; cookie-nya tertimpa yang
    kedua, dan itu justru yang menjadikan sesi kedua "perangkat ini".
    """
    korban = _masuk(klien)      # sesi pertama, akan dikeluarkan
    penghuni = _masuk(klien)    # sesi kedua, cookie-nya yang sekarang dipegang

    keluar = klien.post("/api/v1/auth/sesi/cabut-lain", headers=_kepala(penghuni))
    assert keluar.status_code == 200, keluar.text
    assert keluar.json()["sesi_dicabut"] >= 1

    # Yang disisakan tetap hidup.
    assert klien.get("/api/v1/keamanan", headers=_kepala(penghuni)).status_code == 200

    # Yang dikeluarkan mati sekarang, bukan lima belas menit lagi.
    jawaban = klien.get("/api/v1/keamanan", headers=_kepala(korban))
    assert jawaban.status_code == 401, (
        "perangkat lain masih bisa memakai tokennya sesudah dikeluarkan"
    )


def test_memutar_refresh_mematikan_token_lama(klien):
    """Refresh berputar: yang lama mati sebelum yang baru terbit. Tokennya
    ikut, kalau tidak, sesi lama yang sudah diputar tetap bisa dipakai."""
    lama = _masuk(klien)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 200, putar.text

    assert klien.get("/api/v1/keamanan", headers=_kepala(lama)).status_code == 401
    baru = putar.json()["akses"]
    assert klien.get("/api/v1/keamanan", headers=_kepala(baru)).status_code == 200


def test_kekuatan_sesi_ikut_berputar(klien):
    """Sesi yang lahir lewat sandi saja tetap lemah sesudah diputar, dan yang
    lahir lewat faktor kedua tetap kuat. Tanpa ini, tombol Simpan berubah
    perilakunya sendiri lima belas menit kemudian."""
    _masuk(klien)
    putar = klien.post("/api/v1/auth/refresh")
    assert putar.status_code == 200

    keadaan = klien.get(
        "/api/v1/keamanan", headers=_kepala(putar.json()["akses"])
    ).json()
    assert keadaan["sesi_kuat"] is False


def test_halaman_keamanan_mengaku_pencabutannya_bekerja(klien):
    """Kalau Redis ada, ia harus mengatakan ya. Kalau tidak ada, uji ini
    memang dilewati, dan yang dikatakan halamannya tidak."""
    akses = _masuk(klien)
    keadaan = klien.get("/api/v1/keamanan", headers=_kepala(akses)).json()
    assert keadaan["pencabutan_segera_siap"] is True
