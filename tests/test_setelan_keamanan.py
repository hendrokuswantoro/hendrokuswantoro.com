from __future__ import annotations

import asyncio
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat

muat()

pytest.importorskip("fastapi")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient

from backend.core import surat
from backend.layanan import keamanan as lapis
from konftes import EMAIL_UJI as EMAIL
from konftes import SANDI_UJI as SANDI
from konftes import ada_basis_data
from konftes import loop_untuk_psycopg as _loop_untuk_psycopg

DSN = os.environ.get("DSN", "")
butuh_db = pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data")


def _cara(monkeypatch, **isi) -> list[str]:
    keadaan = {
        "totp_aktif_pada": None, "passkey": 0, "wajah_didaftar_pada": None,
        "pemulihan_sisa": 0, "email_terverifikasi_pada": None, "mode_ketat": False,
        **isi,
    }

    async def baca(_):
        return keadaan

    monkeypatch.setattr(lapis.repo, "keadaan", baca)
    monkeypatch.setattr(lapis.wajah_modul, "siap", lambda: True)
    return asyncio.run(lapis.faktor_kedua_yang_berlaku({"id": "x"}))


def test_mode_ketat_menutup_wajah(monkeypatch):
    biasa = _cara(monkeypatch, totp_aktif_pada=1, wajah_didaftar_pada=1)
    ketat = _cara(monkeypatch, totp_aktif_pada=1, wajah_didaftar_pada=1, mode_ketat=True)
    assert "wajah" in biasa
    assert "wajah" not in ketat and "totp" in ketat


def test_mode_ketat_tidak_menutup_satu_satunya_pintu(monkeypatch):
    assert _cara(monkeypatch, wajah_didaftar_pada=1, mode_ketat=True) == ["wajah"]


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


@pytest.fixture(autouse=True)
def setelan_bawaan():
    def pulihkan() -> None:
        if not ada_basis_data(DSN):
            return
        with psycopg.connect(DSN) as s, s.cursor() as k:
            k.execute(
                "UPDATE users SET kabar_masuk = true, kabar_perubahan = true, "
                "mode_ketat = false WHERE lower(email) = lower(%s)",
                (EMAIL,),
            )
            s.commit()

    pulihkan()
    yield
    pulihkan()


def _kepala(klien) -> dict:
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return {"Authorization": f"Bearer {j.json()['akses']}"}


def _surat() -> set:
    return set(surat.KOTAK.glob("*.eml")) if surat.KOTAK.exists() else set()


def _isi(berkas) -> str:
    import email as pustaka_email

    pesan = pustaka_email.message_from_bytes(berkas.read_bytes())
    return pesan.get_payload(decode=True).decode("utf-8", "replace")


@butuh_db
def test_keadaan_menyebut_setelan_bawaan(klien):
    isi = klien.get("/api/v1/keamanan", headers=_kepala(klien)).json()
    assert (isi["kabar_masuk"], isi["kabar_perubahan"], isi["mode_ketat"]) == (True, True, False)


@butuh_db
def test_setelan_menuntut_sudah_masuk(klien):
    j = klien.patch("/api/v1/keamanan/setelan", json={"kabar_masuk": False})
    assert j.status_code == 401


@butuh_db
def test_mematikan_kabar_tersimpan_dan_tetap_dikabarkan(klien):
    kepala = _kepala(klien)
    klien.patch("/api/v1/keamanan/setelan", json={"kabar_perubahan": False}, headers=kepala)

    sebelum = _surat()
    j = klien.patch("/api/v1/keamanan/setelan", json={"kabar_masuk": False}, headers=kepala)
    assert j.status_code == 200, j.text
    assert j.json()["kabar_masuk"] is False

    baru = _surat() - sebelum
    assert len(baru) == 1, "mematikan notifikasi harus selalu dikabarkan"
    assert "kabar masuk dari perangkat baru dimatikan" in _isi(baru.pop())


@butuh_db
def test_kabar_perubahan_mati_berarti_tidak_ada_surat(klien):
    kepala = _kepala(klien)
    klien.patch("/api/v1/keamanan/setelan", json={"kabar_perubahan": False}, headers=kepala)
    sebelum = _surat()
    assert klien.post("/api/v1/keamanan/wajah/hapus", headers=kepala).status_code == 200
    assert _surat() == sebelum


@butuh_db
def test_kabar_perubahan_hidup_mengirim_surat(klien):
    kepala = _kepala(klien)
    sebelum = _surat()
    assert klien.post("/api/v1/keamanan/wajah/hapus", headers=kepala).status_code == 200
    baru = _surat() - sebelum
    assert len(baru) == 1 and "wajah dihapus" in _isi(baru.pop())


@butuh_db
def test_mode_ketat_butuh_authenticator_atau_sidik_jari(klien):
    kepala = _kepala(klien)
    j = klien.patch("/api/v1/keamanan/setelan", json={"mode_ketat": True}, headers=kepala)
    assert j.status_code == 400
    assert "authenticator" in j.text


@butuh_db
def test_setelan_yang_tidak_berubah_tidak_dikabarkan(klien):
    kepala = _kepala(klien)
    sebelum = _surat()
    j = klien.patch("/api/v1/keamanan/setelan", json={"kabar_masuk": True}, headers=kepala)
    assert j.status_code == 200
    assert _surat() == sebelum


@butuh_db
def test_perubahan_setelan_tercatat_di_aktivitas(klien):
    kepala = _kepala(klien)
    klien.patch("/api/v1/keamanan/setelan", json={"kabar_masuk": False}, headers=kepala)
    jejak = klien.get("/api/v1/keamanan/peristiwa", headers=kepala).json()["peristiwa"]
    assert any(p["jenis"] == "setelan_kabar" for p in jejak)
