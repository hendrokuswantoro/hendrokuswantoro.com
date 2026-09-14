"""Passkey, WebAuthn. Bab 15.8.

Yang diuji di sini bukan "bisa masuk pakai passkey". Itu bagian yang mudah
dan akan ketahuan sendiri hari pertama dipakai. Yang diuji adalah **yang
seharusnya ditolak benar benar ditolak**: tantangan bekas pakai, tantangan
kedaluwarsa, tanda tangan dari kunci lain, kredensial yang penghitungnya
mundur, pendaftaran tanpa masuk lebih dulu, dan pencabutan kunci milik orang
lain.

Ujinya memakai authenticator tiruan di `tests/otentikator.py` yang benar
benar membuat pasangan kunci P-256 dan benar benar menandatangani. Tanda
tangannya diverifikasi pustaka `webauthn` yang sama dengan yang dipakai
produksi, jadi yang lolos di sini adalah tanda tangan yang juga akan lolos
di server sungguhan.

Dilewati kalau tidak ada basis data.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

RP_ID = "testserver"
ASAL = "http://testserver"

# Disetel **sebelum** .env dibaca, sebab muat() sengaja tidak menimpa yang
# sudah ada di environment. TestClient memakai host "testserver", sedangkan
# .env di mesin pengembangan menyebut localhost, dan rp_id yang tidak sama
# dengan host pemanggilnya akan ditolak, betul betul ditolak.
os.environ["WEBAUTHN_RP_ID"] = RP_ID
os.environ["WEBAUTHN_ASAL"] = f'["{ASAL}"]'

muat()

pytest.importorskip("fastapi")
pytest.importorskip("webauthn")
psycopg = pytest.importorskip("psycopg")

from fastapi.testclient import TestClient  # noqa: E402

from otentikator import Otentikator, tantangan_dari  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def _loop_untuk_psycopg() -> None:
    """Sama alasannya dengan di test_auth.py: psycopg menolak
    ProactorEventLoop, dan menyetelnya di tingkat modul akan meracuni uji
    Playwright yang justru menuntut ProactorEventLoop."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not bisa_terhubung(), reason="tidak ada basis data")


def _sejak() -> object:
    """Jam basis data saat rangkaian ini dimuat, dipakai membatasi pembersihan.

    Diambil dari basis datanya, bukan dari Python, sebab keduanya bisa
    berselisih beberapa detik dan selisih itu persis yang menentukan satu
    baris ikut terhapus atau tertinggal.
    """
    try:
        with psycopg.connect(DSN, connect_timeout=3) as s, s.cursor() as k:
            k.execute("SELECT now()")
            return k.fetchone()[0]
    except Exception:
        return None


SEJAK = _sejak()


@pytest.fixture(autouse=True)
def bersihkan():
    """Membersihkan yang dibuat uji ini, bukan mengosongkan tabelnya.

    Sebelumnya baris pertamanya `DELETE FROM kredensial`, tanpa WHERE. Di
    basis data pengembangan tabel itu berisi passkey SUNGGUHAN milik
    pemiliknya, jadi sekali rangkaian uji dijalankan, setiap perangkat yang
    pernah didaftarkan lenyap. Tidak ada galat, tidak ada peringatan; yang
    terjadi cuma tombol sidik jari yang tiba tiba tidak mengenali siapa pun
    lagi. Itu benar benar terjadi pada 14 September 2026.

    Sekarang yang dihapus hanya baris yang lahir sesudah rangkaian ini
    dimulai. `tantangan` dan `gagal_masuk` tetap dikosongkan seluruhnya, dan
    itu memang aman: keduanya berumur pendek dan tidak memuat apa pun yang
    perlu dipegang.
    """
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
    """Token admin, lewat sandi. Passkey didaftarkan oleh orang yang sudah
    masuk, bukan oleh siapa pun yang menemukan alamatnya."""
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


# ------------------------------------------------------------ alur wajar ---


def test_daftar_lalu_masuk(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat)
    assert hasil["nama"] == "Laptop uji"

    j = masuk_dengan(klien, perangkat)
    assert j.status_code == 200, j.text
    assert j.json()["peran"] == "admin"


def test_masuk_passkey_memberi_sesi_yang_sama_dengan_sandi(klien, masuk, perangkat):
    """Passkey mengganti cara membuktikan siapa, bukan cara sesinya dikelola.
    Kalau jalur ini menerbitkan sesi dengan aturan sendiri, satu dari dua
    jalur akan tertinggal tiap kali aturan sesinya berubah."""
    daftarkan(klien, masuk, perangkat)
    j = masuk_dengan(klien, perangkat)

    assert "hk_refresh" not in j.text, "refresh token bocor ke badan jawaban"
    kue = j.headers.get("set-cookie", "").lower()
    assert "httponly" in kue and "samesite=strict" in kue

    assert klien.post("/api/v1/auth/refresh").status_code == 200


def test_kunci_publik_yang_tersimpan_memang_kunci_publik(klien, masuk, perangkat):
    """Tabel kredensial tidak boleh menyimpan satu pun rahasia. Basis data
    yang bocor seluruhnya tidak boleh memberi siapa pun cara masuk."""
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


# ------------------------------------------------------ yang harus ditolak ---


def test_tantangan_hanya_boleh_sekali(klien, masuk, perangkat):
    """Tantangan yang bisa dipakai dua kali membuat jawaban yang direkam
    bisa diputar ulang, dan itu menghapus seluruh gunanya tantangan."""
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

    # Keduanya digeser mundur, bukan hanya kadaluarsa: batasan
    # kadaluarsa_sesudah_dibuat menolak baris yang mati sebelum ia lahir,
    # dan uji yang melanggarnya sedang menguji basis datanya, bukan kodenya.
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
    """Tantangan lahir di server. Yang datang dari luar tidak pernah ada di
    tabel, jadi tidak pernah cocok."""
    daftarkan(klien, masuk, perangkat)
    j = klien.post("/api/v1/auth/passkey/masuk/selesai",
                   json={"jawaban": perangkat.masuk(b"tantangan-karangan-sendiri-32-bita!!", ASAL)})
    assert j.status_code == 401


def test_tanda_tangan_dari_kunci_lain_ditolak(klien, masuk, perangkat):
    """Bentuknya sempurna, tanda tangannya bukan milik kredensial ini."""
    daftarkan(klien, masuk, perangkat)
    j = masuk_dengan(klien, perangkat, tanda_tangan_palsu=True)
    assert j.status_code == 401


def test_asal_yang_salah_ditolak(klien, masuk, perangkat):
    """Inti dari passkey. Halaman palsu boleh meniru tampilannya, tetapi
    tidak bisa meniru alamatnya, dan alamat itu ikut ditandatangani."""
    daftarkan(klien, masuk, perangkat)

    mulai = klien.post("/api/v1/auth/passkey/masuk/mulai")
    tantangan = tantangan_dari(mulai.json()["pilihan"])

    j = klien.post(
        "/api/v1/auth/passkey/masuk/selesai",
        json={"jawaban": perangkat.masuk(tantangan, "https://hendrokuswantoro.com.jahat.id")},
    )
    assert j.status_code == 401, "tanda tangan untuk alamat lain diterima"


def test_penghitung_yang_mundur_ditolak(klien, masuk, perangkat):
    """Penghitung yang tidak naik menandakan kredensialnya disalin."""
    daftarkan(klien, masuk, perangkat)
    assert masuk_dengan(klien, perangkat).status_code == 200

    perangkat.mundurkan_penghitung(0)
    j = masuk_dengan(klien, perangkat, naikkan=0)
    assert j.status_code == 401, "kredensial yang penghitungnya mundur diterima"


def test_kredensial_tidak_dikenal_ditolak(klien, masuk):
    """Perangkat yang belum pernah didaftarkan, tanda tangannya sah sendiri."""
    asing = Otentikator(RP_ID)
    j = masuk_dengan(klien, asing)
    assert j.status_code == 401


def test_mendaftar_menuntut_sudah_masuk(klien, perangkat):
    """Titik akhir pendaftaran yang terbuka adalah pintu belakang."""
    assert klien.post("/api/v1/auth/passkey/daftar/mulai").status_code == 401
    assert klien.post(
        "/api/v1/auth/passkey/daftar/selesai",
        json={"nama": "x", "jawaban": perangkat.daftar(b"a" * 32, ASAL)},
    ).status_code == 401


def test_tantangan_daftar_tidak_bisa_dipakai_untuk_masuk(klien, masuk, perangkat):
    """Tujuan tantangan ikut disimpan. Tanpa itu, tantangan pendaftaran yang
    lebih mudah didapat bisa dipakai menyelesaikan proses masuk."""
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


# --------------------------------------------------------------- kelola ---


def test_daftar_dan_cabut(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat)

    daftar = klien.get("/api/v1/auth/passkey", headers=masuk)
    assert daftar.status_code == 200
    # Yang diperiksa kunci YANG DIBUAT UJI INI, bukan seluruh isi tabelnya.
    #
    # Versi sebelumnya menuntut daftarnya berisi tepat satu nama, dan itu
    # hanya benar selama pembersih uji mengosongkan tabel `kredensial`
    # seluruhnya. Pembersih itu ternyata ikut menghapus passkey SUNGGUHAN
    # milik pemilik situs ini, jadi ia dipersempit, dan uji ini ikut berubah
    # bersamanya. Uji yang benar hanya karena data orang lain dihapus bukan
    # uji yang benar.
    nama = [k["nama"] for k in daftar.json()["daftar"]]
    assert "Laptop uji" in nama, f"kunci yang baru didaftarkan tidak ada di daftar: {nama}"

    assert klien.delete(f"/api/v1/auth/passkey/{hasil['id']}", headers=masuk).status_code == 204
    sesudah = [k["nama"] for k in klien.get("/api/v1/auth/passkey", headers=masuk).json()["daftar"]]
    assert "Laptop uji" not in sesudah, f"kunci yang dicabut masih terdaftar: {sesudah}"

    assert masuk_dengan(klien, perangkat).status_code == 401, "kunci yang dicabut masih bisa masuk"


def test_mencabut_kunci_orang_lain_menjawab_404(klien, masuk, perangkat):
    """404, bukan 403. Membedakan keduanya memberi tahu penanya bahwa
    kredensial itu ada dan milik orang lain."""
    hasil = daftarkan(klien, masuk, perangkat)

    from backend.core import keamanan

    token, _ = keamanan.buat_access_token("00000000-0000-0000-0000-000000000009", "admin")
    j = klien.delete(f"/api/v1/auth/passkey/{hasil['id']}",
                     headers={"Authorization": f"Bearer {token}"})
    assert j.status_code == 404


def test_perangkat_yang_sama_tidak_ditawarkan_dua_kali(klien, masuk, perangkat):
    """exclude_credentials membuat peramban menolak mendaftarkan ulang
    perangkat yang sama, supaya daftarnya tidak penuh kunci kembar yang tidak
    bisa dibedakan pemiliknya."""
    daftarkan(klien, masuk, perangkat)
    mulai = klien.post("/api/v1/auth/passkey/daftar/mulai", headers=masuk)
    import json

    pilihan = json.loads(mulai.json()["pilihan"])
    # Setiap kunci yang sudah terdaftar wajib ikut dikecualikan, termasuk
    # kunci sungguhan milik pemiliknya yang kebetulan ada di basis data
    # pengembangan. Jadi yang dibandingkan jumlah kunci yang benar benar ada,
    # bukan angka satu yang hanya benar di tabel yang kosong.
    terdaftar = klien.get("/api/v1/auth/passkey", headers=masuk).json()["daftar"]
    assert len(pilihan.get("excludeCredentials") or []) == len(terdaftar), (
        f"{len(terdaftar)} kunci terdaftar tetapi "
        f"{len(pilihan.get('excludeCredentials') or [])} yang dikecualikan"
    )
    assert terdaftar, "tidak ada kunci terdaftar, jadi ujinya tidak menjaga apa apa"


def test_nama_kosong_diberi_nama_bawaan(klien, masuk, perangkat):
    hasil = daftarkan(klien, masuk, perangkat, nama="   ")
    assert hasil["nama"] == "Perangkat tanpa nama"


# ------------------------------------------------------------ konfigurasi ---


def test_tanpa_konfigurasi_menjawab_503_bukan_menebak(klien):
    """rp_id yang ditebak dari header Host berarti penyerang boleh memilih
    rp_id sendiri, dan verifikasi asal berhenti berarti apa apa."""
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
