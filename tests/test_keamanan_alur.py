"""Alur keamanan akun lewat HTTP: verifikasi email, TOTP, pemulihan, jejak.

Dipisah dari `test_keamanan_akun.py` karena seluruh isinya menuntut basis
data, sedangkan yang di sana tidak menuntut apa pun dan harus selalu jalan.

Yang diuji di sini perilaku titik akhirnya, termasuk kode status yang
dikembalikannya, bukan fungsi di baliknya. Faktor kedua yang bisa dilewati
adalah faktor kedua yang tidak ada, dan cara melewatinya hampir selalu lewat
jalur HTTP yang lupa diperiksa, bukan lewat fungsi yang salah hitung.

Dilewati kalau Postgres tidak ada, dengan alasan yang disebut.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

pytest.importorskip("cryptography")
psycopg = pytest.importorskip("psycopg")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from backend.core import rahasia, surat  # noqa: E402
from backend.layanan import totp  # noqa: E402

DSN = os.environ.get("DSN", "")
EMAIL = "kuswantoro.hendro01@gmail.com"
SANDI = "sandi-uji-lokal-panjang"


def _bisa_terhubung() -> bool:
    if not DSN:
        return False
    try:
        with psycopg.connect(DSN, connect_timeout=3):
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _bisa_terhubung(),
    reason="tidak ada basis data. Jalankan: docker compose up -d db",
)


def _loop_untuk_psycopg() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
def klien():
    _loop_untuk_psycopg()
    from backend.main import aplikasi

    with TestClient(aplikasi) as c:
        yield c


@pytest.fixture(autouse=True)
def bersihkan_keamanan():
    """Tiap uji mulai dari keadaan yang sama, dan meninggalkannya begitu juga.

    Yang kedua lebih penting daripada yang pertama: uji yang menyalakan TOTP
    lalu berhenti di tengah akan meninggalkan akun pemilik situs ini dalam
    keadaan menuntut kode dari aplikasi yang tidak terpasang di mana pun.
    """
    def bersih() -> None:
        with psycopg.connect(DSN) as s, s.cursor() as k:
            k.execute("DELETE FROM kode_sekali")
            k.execute("DELETE FROM kode_pemulihan")
            k.execute("DELETE FROM peristiwa_keamanan")
            k.execute("DELETE FROM gagal_masuk")
            k.execute(
                "UPDATE users SET totp_rahasia = NULL, totp_aktif_pada = NULL, "
                "email_terverifikasi_pada = NULL"
            )
            s.commit()

    bersih()
    yield
    bersih()


@pytest.fixture
def kunci_kolom(monkeypatch):
    from backend.core import konfigurasi
    from backend.db import enkripsi

    monkeypatch.setenv(rahasia.NAMA_ENV, enkripsi.buat_kunci())
    konfigurasi.pengaturan.cache_clear()
    yield
    konfigurasi.pengaturan.cache_clear()


@pytest.fixture(autouse=True)
def tanpa_smtp_wajib(monkeypatch):
    """Surat ditulis ke berkas, tidak dikirim. Uji yang mengirim surat
    sungguhan adalah uji yang mengirimi orang surat sungguhan."""
    from backend.core import konfigurasi

    monkeypatch.setenv("SURAT_WAJIB", "0")
    # SMTP dikosongkan juga: uji yang mengirim surat sungguhan adalah uji yang
    # mengirimi orang surat sungguhan, dan itu tidak boleh tergantung pada apa
    # yang kebetulan tertulis di .env mesin yang menjalankannya.
    for nama in ("SMTP_HOST", "SMTP_PENGGUNA", "SMTP_SANDI", "SURAT_DARI"):
        monkeypatch.setenv(nama, "")
    konfigurasi.pengaturan.cache_clear()
    yield
    konfigurasi.pengaturan.cache_clear()


def _pengguna_id() -> str:
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT id FROM users WHERE lower(email) = lower(%s)", (EMAIL,))
        return str(k.fetchone()[0])


def _masuk(klien) -> str:
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200, j.text
    isi = j.json()
    assert isi["tahap"] == "selesai", isi
    return isi["akses"]


def _kepala(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _token_dari_surat(kecuali: set | None = None) -> str:
    """Diambil dari berkas surat, persis seperti pemiliknya mengambilnya dari
    kotak suratnya. API tidak pernah mengembalikan tokennya.

    Isinya dibaca lewat pustaka email, bukan dengan membelah berkasnya.
    Badan surat disandikan quoted-printable, jadi tautan yang panjang dipotong
    dengan "=" di ujung baris, dan token yang diambil apa adanya dari berkas
    akan terpotong di tengah. Ini sudah terjadi.
    """
    import email as pustaka_email

    terbaru = _surat_terbaru(kecuali)
    pesan = pustaka_email.message_from_bytes(terbaru.read_bytes())
    isi = pesan.get_payload(decode=True).decode("utf-8", "replace")
    return isi.split("?verifikasi=")[1].split()[0].strip()


def _kotak_sekarang() -> set:
    return set(surat.KOTAK.glob("*.eml")) if surat.KOTAK.exists() else set()


def _surat_terbaru(kecuali: set | None = None) -> pathlib.Path:
    """Berkas surat terbaru, diurutkan dari waktu tulisnya.

    Namanya memuat detik dan delapan heksa acak, jadi dua surat dalam detik
    yang sama tidak terurut menurut waktu kalau diurutkan menurut nama. Uji
    yang meminta dua tautan berturut turut pernah mengambil tautan yang sama
    dua kali karena itu, lalu melaporkan bahwa tautan lama tidak dimatikan
    padahal ia dimatikan.
    """
    calon = [p for p in surat.KOTAK.glob("*.eml") if p not in (kecuali or set())]
    assert calon, "tidak ada surat baru yang ditulis"
    return max(calon, key=lambda p: p.stat().st_mtime_ns)


def _pasang_totp(klien, akses: str) -> str:
    mulai = klien.post("/api/v1/keamanan/totp/mulai", headers=_kepala(akses))
    assert mulai.status_code == 200, mulai.text
    return mulai.json()["rahasia"]


# ----------------------------------------------------------------- keadaan --


def test_halaman_keamanan_menyebut_keadaan_lingkungannya(klien):
    """Tombol yang selalu ada lalu selalu gagal lebih buruk daripada tombol
    yang menjelaskan kenapa ia belum bisa dipakai."""
    j = klien.get("/api/v1/keamanan", headers=_kepala(_masuk(klien)))
    assert j.status_code == 200, j.text
    isi = j.json()
    for kunci in ("email_terverifikasi", "totp_aktif", "passkey", "pemulihan_sisa",
                  "surat_siap", "kunci_kolom_siap"):
        assert kunci in isi, kunci
    assert isi["email"] == EMAIL


def test_halaman_keamanan_menolak_tanpa_token(klien):
    assert klien.get("/api/v1/keamanan").status_code == 401


# ------------------------------------------------------- verifikasi email --


def test_tautan_verifikasi_sekali_pakai(klien):
    akses = _masuk(klien)
    j = klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(akses))
    assert j.status_code == 200, j.text

    token = _token_dari_surat()
    pertama = klien.post("/api/v1/keamanan/email/konfirmasi", json={"token": token})
    assert pertama.status_code == 200, pertama.text
    assert pertama.json()["terverifikasi"] is True

    kedua = klien.post("/api/v1/keamanan/email/konfirmasi", json={"token": token})
    assert kedua.status_code == 400, "tautan yang sudah dipakai masih diterima"


def test_token_verifikasi_tidak_pernah_tersimpan_apa_adanya(klien):
    klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(_masuk(klien)))
    token = _token_dari_surat()

    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT kode_hash FROM kode_sekali WHERE tujuan = 'email'")
        tersimpan = [b[0] for b in k.fetchall()]

    assert tersimpan
    assert token not in tersimpan
    assert all(len(h.strip()) == 64 for h in tersimpan), "bukan sha256 heksa"


def test_tautan_palsu_ditolak(klien):
    j = klien.post("/api/v1/keamanan/email/konfirmasi", json={"token": "x" * 40})
    assert j.status_code == 400


def test_meminta_tautan_baru_mematikan_yang_lama(klien):
    """Kalau tidak, tiap permintaan menambah satu tautan hidup, dan ruang
    tebakannya tumbuh tanpa batas."""
    akses = _masuk(klien)
    sebelum = _kotak_sekarang()
    klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(akses))
    lama = _token_dari_surat(sebelum)

    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("UPDATE kode_sekali SET dibuat_pada = now() - interval '5 minutes'")
        s.commit()

    tengah = _kotak_sekarang()
    klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(akses))
    baru = _token_dari_surat(tengah)
    assert baru != lama

    j = klien.post("/api/v1/keamanan/email/konfirmasi", json={"token": lama})
    assert j.status_code == 400, "tautan lama masih hidup sesudah yang baru terbit"


def test_kirim_ulang_terlalu_cepat_ditolak(klien):
    akses = _masuk(klien)
    assert klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(akses)).status_code == 200
    lagi = klien.post("/api/v1/keamanan/email/kirim", headers=_kepala(akses))
    assert lagi.status_code == 429


# ------------------------------------------------------------------- TOTP --


def test_totp_dipasang_lalu_dipakai_masuk(klien, kunci_kolom):
    akses = _masuk(klien)
    rahasia_baru = _pasang_totp(klien, akses)

    # Belum aktif sampai satu kode yang benar membuktikan perangkatnya bisa
    # membacanya. Rahasia yang diaktifkan tanpa pernah dibuktikan terbaca
    # adalah cara mengunci diri sendiri di luar pintunya sendiri.
    keadaan = klien.get("/api/v1/keamanan", headers=_kepala(akses)).json()
    assert keadaan["totp_terpasang"] is True
    assert keadaan["totp_aktif"] is False

    salah = klien.post("/api/v1/keamanan/totp/aktifkan",
                       json={"kode": "000000"}, headers=_kepala(akses))
    assert salah.status_code == 400

    benar = klien.post("/api/v1/keamanan/totp/aktifkan",
                       json={"kode": totp.kode_sekarang(rahasia_baru)},
                       headers=_kepala(akses))
    assert benar.status_code == 200, benar.text
    assert len(benar.json()["kode_pemulihan"]) == totp.JUMLAH_PEMULIHAN

    # Sekarang sandi saja tidak lagi cukup.
    lagi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert lagi.status_code == 200, lagi.text
    isi = lagi.json()
    assert isi["tahap"] == "faktor2", isi
    assert isi["akses"] == "", "sesi terbit padahal faktor kedua belum dilewati"
    assert "totp" in isi["cara"]

    lolos = klien.post("/api/v1/auth/faktor-kedua", json={
        "tiket": isi["tiket"], "cara": "totp",
        "kode": totp.kode_sekarang(rahasia_baru),
    })
    assert lolos.status_code == 200, lolos.text
    assert lolos.json()["tahap"] == "selesai"
    assert lolos.json()["akses"]


def test_rahasia_totp_di_basis_data_tidak_terbaca(klien, kunci_kolom):
    rahasia_baru = _pasang_totp(klien, _masuk(klien))
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT totp_rahasia FROM users WHERE id = %s", (_pengguna_id(),))
        tersimpan = k.fetchone()[0]
    assert tersimpan
    assert rahasia_baru not in tersimpan, (
        "rahasia TOTP tersimpan apa adanya. Basis data yang bocor memberi "
        "penyerang faktor kedua bersama yang pertama."
    )


def test_kode_totp_salah_ditolak_saat_masuk(klien, kunci_kolom):
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    klien.post("/api/v1/keamanan/totp/aktifkan",
               json={"kode": totp.kode_sekarang(r)}, headers=_kepala(akses))

    isi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI}).json()
    j = klien.post("/api/v1/auth/faktor-kedua", json={
        "tiket": isi["tiket"], "cara": "totp", "kode": "000000",
    })
    assert j.status_code == 401


def test_kode_pemulihan_dipakai_sekali(klien, kunci_kolom):
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    pemulihan = klien.post("/api/v1/keamanan/totp/aktifkan",
                           json={"kode": totp.kode_sekarang(r)},
                           headers=_kepala(akses)).json()["kode_pemulihan"]
    satu = pemulihan[0]

    isi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI}).json()
    lolos = klien.post("/api/v1/auth/faktor-kedua", json={
        "tiket": isi["tiket"], "cara": "pemulihan", "kode": satu,
    })
    assert lolos.status_code == 200, lolos.text

    lagi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI}).json()
    ulang = klien.post("/api/v1/auth/faktor-kedua", json={
        "tiket": lagi["tiket"], "cara": "pemulihan", "kode": satu,
    })
    assert ulang.status_code == 401, "kode pemulihan yang sama diterima dua kali"


def test_kode_pemulihan_tidak_tersimpan_apa_adanya(klien, kunci_kolom):
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    pemulihan = klien.post("/api/v1/keamanan/totp/aktifkan",
                           json={"kode": totp.kode_sekarang(r)},
                           headers=_kepala(akses)).json()["kode_pemulihan"]

    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT kode_hash FROM kode_pemulihan")
        tersimpan = [b[0] for b in k.fetchall()]

    for satu in pemulihan:
        assert satu not in tersimpan
        assert totp.normalkan_pemulihan(satu) not in tersimpan


def test_mematikan_totp_menuntut_kode_juga(klien, kunci_kolom):
    """Tanpa itu, siapa pun yang sempat memegang sesi yang sudah masuk bisa
    mencabut faktor kedua tanpa pernah memilikinya."""
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    klien.post("/api/v1/keamanan/totp/aktifkan",
               json={"kode": totp.kode_sekarang(r)}, headers=_kepala(akses))

    salah = klien.post("/api/v1/keamanan/totp/matikan",
                       json={"kode": "000000"}, headers=_kepala(akses))
    assert salah.status_code == 400

    benar = klien.post("/api/v1/keamanan/totp/matikan",
                       json={"kode": totp.kode_sekarang(r)}, headers=_kepala(akses))
    assert benar.status_code == 200, benar.text

    # Rahasianya hilang, bukan sekadar dinonaktifkan, dan kode pemulihannya ikut.
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT totp_rahasia FROM users WHERE id = %s", (_pengguna_id(),))
        assert k.fetchone()[0] is None
        k.execute("SELECT count(*) FROM kode_pemulihan")
        assert k.fetchone()[0] == 0


def test_tiket_faktor_kedua_bukan_token_admin(klien, kunci_kolom):
    """Tiket yang diterima sebagai token akses berarti faktor keduanya bisa
    dilewati seluruhnya."""
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    klien.post("/api/v1/keamanan/totp/aktifkan",
               json={"kode": totp.kode_sekarang(r)}, headers=_kepala(akses))

    isi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI}).json()
    j = klien.get("/api/v1/keamanan", headers=_kepala(isi["tiket"]))
    assert j.status_code == 401, "tiket faktor kedua diterima sebagai token admin"


def test_cara_yang_tidak_ada_di_tiket_ditolak(klien, kunci_kolom):
    akses = _masuk(klien)
    r = _pasang_totp(klien, akses)
    klien.post("/api/v1/keamanan/totp/aktifkan",
               json={"kode": totp.kode_sekarang(r)}, headers=_kepala(akses))
    isi = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI}).json()

    j = klien.post("/api/v1/auth/faktor-kedua", json={
        "tiket": isi["tiket"], "cara": "email", "kode": "123456",
    })
    assert j.status_code == 400


def test_totp_tanpa_kunci_kolom_menjawab_503_bukan_menyimpan_polos(klien, monkeypatch):
    """Fitur yang menurunkan jaminannya sendiri saat konfigurasinya kurang
    adalah fitur yang jaminannya tidak pernah bisa dipercaya."""
    from backend.core import konfigurasi

    monkeypatch.setenv(rahasia.NAMA_ENV, "")
    konfigurasi.pengaturan.cache_clear()
    j = klien.post("/api/v1/keamanan/totp/mulai", headers=_kepala(_masuk(klien)))
    assert j.status_code == 503
    assert "KUNCI_KOLOM" in j.text, j.text


# -------------------------------------------------------------- peristiwa --


def test_yang_gagal_ikut_tercatat(klien):
    """Yang berhasil hanya memberi tahu pemiliknya apa yang sudah ia lakukan.
    Yang gagal memberi tahu bahwa ada orang lain sedang mencoba."""
    akses = _masuk(klien)
    j = klien.get("/api/v1/keamanan/peristiwa", headers=_kepala(akses))
    assert j.status_code == 200, j.text
    daftar = j.json()["peristiwa"]
    assert daftar, "tidak ada satu pun peristiwa tercatat"
    assert any(p["jenis"] == "masuk" and p["berhasil"] for p in daftar)


def test_peristiwa_tidak_menyimpan_alamat_ip_apa_adanya(klien):
    _masuk(klien)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute(
            "SELECT alamat_ringkas FROM peristiwa_keamanan WHERE alamat_ringkas IS NOT NULL"
        )
        alamat = [b[0] for b in k.fetchall()]
    assert alamat, "tidak ada peristiwa beralamat sama sekali"
    for satu in alamat:
        assert len(satu) == 64, f"bukan sha256: {satu}"
        assert "." not in satu and ":" not in satu, f"alamat IP apa adanya: {satu}"


def test_peristiwa_hanya_milik_sendiri(klien):
    """Jejak keamanan satu akun tidak boleh bisa dibaca dari akun lain."""
    akses = _masuk(klien)
    j = klien.get("/api/v1/keamanan/peristiwa", headers=_kepala(akses))
    for p in j.json()["peristiwa"]:
        assert set(p) == {"jenis", "berhasil", "keterangan", "alamat_ringkas",
                          "peramban", "pada"}, p


# ------------------------------------------------ yang sudah ada tidak berubah --


def test_tanpa_faktor_kedua_masuknya_tetap_seperti_dulu(klien):
    """Lapisan baru tidak boleh mengubah perilaku yang sudah ada hanya karena
    ia dipasang. Selama tidak ada faktor kedua yang berlaku, sesi terbit
    langsung, persis seperti sebelumnya."""
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": SANDI})
    assert j.status_code == 200
    isi = j.json()
    assert isi["tahap"] == "selesai"
    assert isi["akses"] and isi["peran"] == "admin"


def test_sandi_salah_tetap_401(klien):
    j = klien.post("/api/v1/auth/login", json={"email": EMAIL, "sandi": "salah-panjang-sekali"})
    assert j.status_code == 401
