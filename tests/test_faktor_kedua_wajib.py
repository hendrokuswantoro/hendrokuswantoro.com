from __future__ import annotations

import pytest

try:
    from backend.api import tergantung
    from backend.core import keamanan
    from backend.core.konfigurasi import pengaturan

    ADA_BACKEND = True
except ModuleNotFoundError:  # pragma: no cover
    ADA_BACKEND = False

pytestmark = pytest.mark.skipif(
    not ADA_BACKEND,
    reason="backend belum terpasang. Jalankan: pip install -r backend/requirements.txt",
)


@pytest.fixture(autouse=True)
def rahasia_jwt(monkeypatch):
    if not ADA_BACKEND:
        return
    monkeypatch.setenv("JWT_SECRET", "rahasia-uji-yang-panjangnya-lebih-dari-tigapuluh-dua")
    pengaturan.cache_clear()
    yield
    pengaturan.cache_clear()


def test_token_membawa_sesi_dan_kekuatannya():
    token, _ = keamanan.buat_access_token("abc", "admin", "sesi-1", True)
    muatan = keamanan.baca_access_token(token)
    assert muatan["sid"] == "sesi-1"
    assert muatan["f2"] is True


def test_token_tanpa_faktor_kedua_menandainya_begitu():
    token, _ = keamanan.buat_access_token("abc", "admin")
    muatan = keamanan.baca_access_token(token)
    assert muatan["f2"] is False
    assert muatan["sid"] is None


async def _kuat(pengguna: dict) -> dict:
    return await tergantung.butuh_admin_kuat(pengguna)


def test_sesi_lewat_faktor_kedua_boleh_menulis(monkeypatch):
    import asyncio

    monkeypatch.setenv("FAKTOR_KEDUA_WAJIB", "true")
    pengaturan.cache_clear()

    pengguna = {"id": "a", "peran": "admin", "faktor_kedua": True}
    assert asyncio.run(_kuat(pengguna)) is pengguna


def test_sesi_yang_cuma_lewat_sandi_ditolak_menulis(monkeypatch):
    import asyncio

    from fastapi import HTTPException

    monkeypatch.setenv("FAKTOR_KEDUA_WAJIB", "true")
    pengaturan.cache_clear()

    pengguna = {"id": "a", "peran": "admin", "faktor_kedua": False}
    with pytest.raises(HTTPException) as galat:
        asyncio.run(_kuat(pengguna))

    assert galat.value.status_code == 403
    assert "faktor kedua" in galat.value.detail
    assert "halaman keamanan" in galat.value.detail.lower()


def test_bisa_dimatikan_untuk_pemulihan(monkeypatch):
    import asyncio

    monkeypatch.setenv("FAKTOR_KEDUA_WAJIB", "false")
    pengaturan.cache_clear()

    pengguna = {"id": "a", "peran": "admin", "faktor_kedua": False}
    assert asyncio.run(_kuat(pengguna)) is pengguna


def test_bawaannya_menyala():
    from backend.core.konfigurasi import Pengaturan

    assert Pengaturan.model_fields["faktor_kedua_wajib"].default is True


def test_jalur_tulis_memakai_penjaga_yang_kuat():
    from konftes import AKAR

    for nama in ("admin.py", "berkas.py"):
        isi = (AKAR / "backend" / "api" / "v1" / nama).read_text(encoding="utf-8")
        assert "butuh_admin_kuat" in isi, f"{nama} tidak memakai penjaga yang kuat"
        assert "dependencies=[Depends(butuh_admin_kuat)]" in isi, (
            f"{nama} memasang penjaganya per rute, bukan untuk seluruh router. "
            "Satu rute yang lupa sudah cukup membuka semuanya."
        )


def test_halaman_keamanan_tidak_mengunci_pemilik_di_luar():
    from konftes import AKAR

    isi = (AKAR / "backend" / "api" / "v1" / "keamanan.py").read_text(encoding="utf-8")
    for fungsi in ("totp_mulai", "totp_aktifkan", "wajah_daftar"):
        potong = isi[isi.index(f"async def {fungsi}("):]
        potong = potong[:potong.index(")", potong.index("Depends("))]
        assert "butuh_admin_kuat" not in potong, (
            f"{fungsi} memakai penjaga yang kuat, jadi faktor kedua tidak akan "
            "pernah bisa dipasang oleh yang belum punya"
        )
    assert "butuh_admin_pendaftar" in isi


def _klien_dan_token(monkeypatch):
    import os

    import psycopg
    from fastapi.testclient import TestClient

    dsn = os.environ.get("DSN", "")
    if not dsn:
        pytest.skip("tidak ada basis data")
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            pass
    except Exception:
        pytest.skip("tidak ada basis data")

    import asyncio
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    from backend.main import aplikasi

    klien = TestClient(aplikasi)
    klien.__enter__()
    jawaban = klien.post(
        "/api/v1/auth/login",
        json={"email": "kuswantoro.hendro01@gmail.com", "sandi": "sandi-uji-lokal-panjang"},
    )
    assert jawaban.status_code == 200, jawaban.text
    isi = jawaban.json()
    if isi["tahap"] != "selesai":
        klien.__exit__(None, None, None)
        pytest.skip("akun uji sudah punya faktor kedua, jadi sesi lemah tidak bisa dibuat")
    return klien, {"Authorization": f"Bearer {isi['akses']}"}


def test_sesi_lemah_ditolak_menulis_lewat_api(monkeypatch):
    klien, kepala = _klien_dan_token(monkeypatch)
    try:
        monkeypatch.setenv("FAKTOR_KEDUA_WAJIB", "true")
        pengaturan.cache_clear()

        for metode, jalur in (
            ("get", "/api/v1/admin/blog"),
            ("post", "/api/v1/admin/blog"),
            ("get", "/api/v1/admin/berkas"),
        ):
            jawaban = getattr(klien, metode)(jalur, headers=kepala, **(
                {"json": {}} if metode == "post" else {}
            ))
            assert jawaban.status_code == 403, f"{metode.upper()} {jalur}: {jawaban.status_code}"
            assert "faktor kedua" in jawaban.text

        assert klien.get("/api/v1/keamanan", headers=kepala).status_code == 200
    finally:
        pengaturan.cache_clear()
        klien.__exit__(None, None, None)


def test_keadaan_keamanan_menyebutkan_sesinya_lemah(monkeypatch):
    klien, kepala = _klien_dan_token(monkeypatch)
    try:
        keadaan = klien.get("/api/v1/keamanan", headers=kepala).json()
        assert keadaan["sesi_kuat"] is False
        assert "faktor_kedua_wajib" in keadaan
        assert "pencabutan_segera_siap" in keadaan
    finally:
        klien.__exit__(None, None, None)


def test_rahasia_lama_masih_diterima_selama_rotasi(monkeypatch):
    lama = "rahasia-lama-yang-panjangnya-lebih-dari-tigapuluh-dua-huruf"
    baru = "rahasia-baru-yang-panjangnya-juga-lebih-dari-tigapuluh-dua"

    monkeypatch.setenv("JWT_SECRET", lama)
    monkeypatch.delenv("JWT_SECRET_LAMA", raising=False)
    pengaturan.cache_clear()
    token, _ = keamanan.buat_access_token("abc", "admin", "sesi-1", True)

    monkeypatch.setenv("JWT_SECRET", baru)
    monkeypatch.setenv("JWT_SECRET_LAMA", lama)
    pengaturan.cache_clear()

    muatan = keamanan.baca_access_token(token)
    assert muatan is not None, "token lama ditolak, padahal rotasinya belum selesai"
    assert muatan["sub"] == "abc"

    token_baru, _ = keamanan.buat_access_token("abc", "admin", "sesi-2", True)
    monkeypatch.delenv("JWT_SECRET_LAMA")
    pengaturan.cache_clear()
    assert keamanan.baca_access_token(token_baru) is not None


def test_rahasia_lama_berhenti_berlaku_setelah_dikosongkan(monkeypatch):
    lama = "rahasia-lama-yang-panjangnya-lebih-dari-tigapuluh-dua-huruf"
    baru = "rahasia-baru-yang-panjangnya-juga-lebih-dari-tigapuluh-dua"

    monkeypatch.setenv("JWT_SECRET", lama)
    pengaturan.cache_clear()
    token, _ = keamanan.buat_access_token("abc", "admin")

    monkeypatch.setenv("JWT_SECRET", baru)
    monkeypatch.delenv("JWT_SECRET_LAMA", raising=False)
    pengaturan.cache_clear()
    assert keamanan.baca_access_token(token) is None


def test_rahasia_lama_tidak_pernah_dipakai_menandatangani():
    from konftes import AKAR

    isi = (AKAR / "backend" / "core" / "keamanan.py").read_text(encoding="utf-8")
    for baris in isi.splitlines():
        if "jwt.encode" in baris or "jwt_rahasia_lama" in baris:
            assert not ("jwt.encode" in baris and "lama" in baris), baris
    assert "jwt.encode(muatan, atur.jwt_rahasia," in isi
