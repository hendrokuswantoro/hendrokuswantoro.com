from __future__ import annotations

import datetime as dt
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat

RP_ID = "testserver"
ASAL = "http://testserver"

os.environ["WEBAUTHN_RP_ID"] = RP_ID
os.environ["WEBAUTHN_ASAL"] = f'["{ASAL}"]'

muat()

pytest.importorskip("fastapi")
pytest.importorskip("webauthn")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient

from otentikator import Otentikator, tantangan_dari

DSN = os.environ.get("DSN", "")
from konftes import EMAIL_UJI as EMAIL
from konftes import SANDI_UJI as SANDI


from konftes import loop_untuk_psycopg as _loop_untuk_psycopg


from konftes import ada_basis_data


pytestmark = pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data")


def _sejak() -> object:
    try:
        with psycopg.connect(DSN, connect_timeout=3) as s, s.cursor() as k:
            k.execute("SELECT now()")
            return k.fetchone()[0]
    except Exception:
        return None


SEJAK = _sejak()


@pytest.fixture(autouse=True)
def bersihkan():
    yield
    with psycopg.connect(DSN) as s, s.cursor() as k:
        if SEJAK is None:
            k.execute("DELETE FROM kredensial")
        else:
            k.execute("DELETE FROM kredensial WHERE dibuat_pada >= %s", (SEJAK,))
        k.execute("DELETE FROM tantangan")
        k.execute("DELETE FROM gagal_masuk")
        s.commit()


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.core.konfigurasi import pengaturan

    pengaturan.cache_clear()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c
    pengaturan.cache_clear()


@pytest.fixture
def masuk(klien):
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    return {"Authorization": f"Bearer {j.json()['akses']}"}


@pytest.fixture
def perangkat():
    return Otentikator(RP_ID)


def daftarkan(klien, kepala, perangkat, nama="Laptop uji") -> dict:
    mulai = klien.post("/api/v1/auth/passkey/daftar/mulai", headers=kepala)
    assert mulai.status_code == 200, mulai.text
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    selesai = klien.post(
        "/api/v1/auth/passkey/daftar/selesai",
        headers=kepala,
        json={"nama": nama, "jawaban": perangkat.daftar(tantangan, ASAL)},
    )
    assert selesai.status_code == 201, selesai.text
    return selesai.json()


def masuk_dengan(klien, perangkat, **kwargs):
    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    assert mulai.status_code == 200, mulai.text
    tantangan = tantangan_dari(mulai.json()["pilihan"])
    return klien.post(
        "/api/v1/auth/passkey/masuk/selesai",
        json={"jawaban": perangkat.masuk(tantangan, ASAL, **kwargs)},
    )


def test_daftar_lalu_masuk(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat)
    assert hasil["nama"] == "Laptop uji"

    j = masuk_dengan(klien, perangkat)
    assert j.status_code == 200, j.text
    assert j.json()["peran"] == "admin"


def test_masuk_passkey_memberi_sesi_yang_sama_dengan_sandi(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    j = masuk_dengan(klien, perangkat)

    assert "hk_refresh" not in j.text, "refresh token bocor ke badan jawaban"
    kue = j.headers.get("set-cookie", "").lower()
    assert "httponly" in kue and "samesite=strict" in kue

    assert klien.post("/api/v1/auth/refresh").status_code == 200


def test_kunci_publik_yang_tersimpan_memang_kunci_publik(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT kunci_publik FROM kredensial")
        tersimpan = bytes(k.fetchone()[0])

    rahasia = perangkat.kunci.private_numbers().private_value.to_bytes(32, "big")
    assert rahasia not in tersimpan, "kunci privat ikut tersimpan"
    assert len(tersimpan) < 200, "yang tersimpan bukan kunci publik COSE"


def test_penghitung_ikut_naik(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    masuk_dengan(klien, perangkat)
    masuk_dengan(klien, perangkat)

    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT penghitung, dipakai_pada FROM kredensial")
        penghitung, dipakai = k.fetchone()
    assert penghitung == 2
    assert dipakai is not None


def test_tantangan_hanya_boleh_sekali(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)

    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    pertama = klien.post("/api/v1/auth/passkey/masuk/selesai",
                         json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert pertama.status_code == 200

    kedua = klien.post("/api/v1/auth/passkey/masuk/selesai",
                       json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert kedua.status_code == 401, "tantangan bekas pakai diterima lagi"


def test_tantangan_kedaluwarsa_ditolak(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)

    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    sekarang = dt.datetime.now(dt.timezone.utc)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "UPDATE tantangan SET dibuat_pada = %s, kadaluarsa = %s WHERE nilai = %s",
            (sekarang - dt.timedelta(minutes=10), sekarang - dt.timedelta(minutes=1), tantangan),
        )
        s.commit()

    j = klien.post("/api/v1/auth/passkey/masuk/selesai",
                   json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert j.status_code == 401


def test_tantangan_karangan_sendiri_ditolak(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    j = klien.post("/api/v1/auth/passkey/masuk/selesai",
                   json={"jawaban": perangkat.masuk(b"tantangan-karangan-sendiri-32-bita!!", ASAL)})
    assert j.status_code == 401


def test_tanda_tangan_dari_kunci_lain_ditolak(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    j = masuk_dengan(klien, perangkat, tanda_tangan_palsu=True)
    assert j.status_code == 401


def test_asal_yang_salah_ditolak(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)

    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    j = klien.post(
        "/api/v1/auth/passkey/masuk/selesai",
        json={"jawaban": perangkat.masuk(tantangan, "https://hendrokuswantoro.com.jahat.id")},
    )
    assert j.status_code == 401, "tanda tangan untuk alamat lain diterima"


def test_penghitung_yang_mundur_ditolak(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    assert masuk_dengan(klien, perangkat).status_code == 200

    perangkat.mundurkan_penghitung(0)
    j = masuk_dengan(klien, perangkat, naikkan=0)
    assert j.status_code == 401, "kredensial yang penghitungnya mundur diterima"


def test_kredensial_tidak_dikenal_ditolak(klien, masuk):
    asing = Otentikator(RP_ID)
    j = masuk_dengan(klien, asing)
    assert j.status_code == 401


def test_mendaftar_menuntut_sudah_masuk(klien, perangkat):
    assert klien.post("/api/v1/auth/passkey/daftar/mulai").status_code == 401
    assert klien.post(
        "/api/v1/auth/passkey/daftar/selesai",
        json={"nama": "x", "jawaban": perangkat.daftar(b"a" * 32, ASAL)},
    ).status_code == 401


def test_tantangan_daftar_tidak_bisa_dipakai_untuk_masuk(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)

    mulai = klien.post("/api/v1/auth/passkey/daftar/mulai", headers=masuk)
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    j = klien.post("/api/v1/auth/passkey/masuk/selesai",
                   json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert j.status_code == 401


def test_jawaban_yang_bukan_webauthn_ditolak_tanpa_500(klien, masuk):
    for badan in ({}, {"id": "bukan-base64url-!!"}, {"response": {}}):
        j = klien.post("/api/v1/auth/passkey/masuk/selesai", json={"jawaban": badan})
        assert j.status_code in (401, 422), f"{badan} menjawab {j.status_code}"


def test_daftar_dan_cabut(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat)

    daftar = klien.get("/api/v1/auth/passkey", headers=masuk)
    assert daftar.status_code == 200
    nama = [k["nama"] for k in daftar.json()["daftar"]]
    assert "Laptop uji" in nama, f"kunci yang baru didaftarkan tidak ada di daftar: {nama}"

    assert klien.delete(f"/api/v1/auth/passkey/{hasil['id']}", headers=masuk).status_code == 204
    sesudah = [k["nama"] for k in klien.get("/api/v1/auth/passkey", headers=masuk).json()["daftar"]]
    assert "Laptop uji" not in sesudah, f"kunci yang dicabut masih terdaftar: {sesudah}"

    assert masuk_dengan(klien, perangkat).status_code == 401, "kunci yang dicabut masih bisa masuk"


def test_mencabut_kunci_orang_lain_menjawab_404(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat)

    from backend.core import keamanan

    token, _ = keamanan.buat_access_token("00000000-0000-0000-0000-000000000009", "admin")
    j = klien.delete(f"/api/v1/auth/passkey/{hasil['id']}",
                     headers={"Authorization": f"Bearer {token}"})
    assert j.status_code == 404


def test_perangkat_yang_sama_tidak_ditawarkan_dua_kali(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    mulai = klien.post("/api/v1/auth/passkey/daftar/mulai", headers=masuk)
    import json

    pilihan = json.loads(mulai.json()["pilihan"])
    terdaftar = klien.get("/api/v1/auth/passkey", headers=masuk).json()["daftar"]
    assert len(pilihan.get("excludeCredentials") or []) == len(terdaftar), (
        f"{len(terdaftar)} kunci terdaftar tetapi "
        f"{len(pilihan.get('excludeCredentials') or [])} yang dikecualikan"
    )
    assert terdaftar, "tidak ada kunci terdaftar, jadi ujinya tidak menjaga apa apa"


def test_nama_kosong_diberi_nama_bawaan(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat, nama="   ")
    assert hasil["nama"] == "Perangkat tanpa nama"


def test_tanpa_konfigurasi_menjawab_503_bukan_menebak(klien):
    from backend.core.konfigurasi import pengaturan

    asli = os.environ.get("WEBAUTHN_RP_ID")
    os.environ["WEBAUTHN_RP_ID"] = ""
    pengaturan.cache_clear()
    try:
        assert klien.post("/api/v1/auth/passkey/masuk/mulai").status_code == 503
        assert klien.get("/api/v1/auth/passkey/siap").json()["siap"] is False
    finally:
        if asli is not None:
            os.environ["WEBAUTHN_RP_ID"] = asli
        pengaturan.cache_clear()


def buka_dengan(klien, kepala, perangkat):
    mulai = klien.post("/api/v1/auth/passkey/buka/mulai", headers=kepala)
    assert mulai.status_code == 200, mulai.text
    tantangan = tantangan_dari(mulai.json()["pilihan"])
    return klien.post(
        "/api/v1/auth/passkey/buka/selesai",
        headers=kepala,
        json={"jawaban": perangkat.masuk(tantangan, ASAL)},
    )


def test_kunci_layar_dibuka_dengan_sidik_jari(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    j = buka_dengan(klien, masuk, perangkat)
    assert j.status_code == 200, j.text
    assert j.json() == {"terbuka": True}


def test_membuka_kunci_menuntut_sudah_masuk(klien):
    assert klien.post("/api/v1/auth/passkey/buka/mulai").status_code == 401
    kosong = {"jawaban": {}}
    assert klien.post("/api/v1/auth/passkey/buka/selesai", json=kosong).status_code == 401


def test_membuka_kunci_tanpa_sidik_jari_ditolak_dengan_alasan(klien, masuk):
    j = klien.post("/api/v1/auth/passkey/buka/mulai", headers=masuk)
    assert j.status_code == 400
    assert "belum ada" in j.text


def test_tantangan_buka_tidak_bisa_dipakai_untuk_masuk(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    mulai = klien.post("/api/v1/auth/passkey/buka/mulai", headers=masuk)
    tantangan = tantangan_dari(mulai.json()["pilihan"])
    j = klien.post("/api/v1/auth/passkey/masuk/selesai",
                   json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert j.status_code == 401, "tantangan kunci layar menerbitkan sesi baru"


def test_tantangan_masuk_tidak_bisa_dipakai_membuka(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    tantangan = tantangan_dari(mulai.json()["pilihan"])
    j = klien.post("/api/v1/auth/passkey/buka/selesai", headers=masuk,
                   json={"jawaban": perangkat.masuk(tantangan, ASAL)})
    assert j.status_code == 401


def test_tantangan_buka_hanya_sekali(klien, masuk, perangkat):
    daftarkan(klien, masuk, perangkat)
    mulai = klien.post("/api/v1/auth/passkey/buka/mulai", headers=masuk)
    tantangan = tantangan_dari(mulai.json()["pilihan"])
    pertama = {"jawaban": perangkat.masuk(tantangan, ASAL)}
    j = klien.post("/api/v1/auth/passkey/buka/selesai", headers=masuk, json=pertama)
    assert j.status_code == 200
    ulang = {"jawaban": perangkat.masuk(tantangan, ASAL)}
    j = klien.post("/api/v1/auth/passkey/buka/selesai", headers=masuk, json=ulang)
    assert j.status_code == 401
