"""Enkripsi cadangan. Bab 15.18.

Enkripsi adalah tempat paling mudah membuat sesuatu yang *terlihat* bekerja.
Berkas yang keluar tampak acak, dan selesai. Yang tidak terlihat: apakah ia
benar benar bisa dibuka kembali, apakah kunci yang salah benar benar ditolak,
dan apakah berkas yang berubah satu bit ketahuan atau justru terbuka jadi
sampah yang dikira data.

Tidak butuh basis data. Yang diuji fungsinya, bukan alurnya; alur cadangan
yang utuh diuji di CI dengan `cadangan.py uji-pulih`, yang benar benar
memulihkan ke basis data sementara lalu menghitung barisnya.
"""

from __future__ import annotations

import base64
import gzip
import subprocess
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))

pytest.importorskip("cryptography")

from backend.db import enkripsi  # noqa: E402

ISI = b"-- pg_dump\nCREATE TABLE contoh (id int);\n" * 200


@pytest.fixture
def kunci() -> bytes:
    return base64.b64decode(enkripsi.buat_kunci())


# ------------------------------------------------------------------ kunci ---


def test_kunci_baru_panjangnya_benar():
    mentah = base64.b64decode(enkripsi.buat_kunci())
    assert len(mentah) == enkripsi.PANJANG_KUNCI


def test_dua_kunci_tidak_pernah_sama():
    """Kunci yang bisa ditebak sama saja dengan tidak ada kunci."""
    assert len({enkripsi.buat_kunci() for _ in range(20)}) == 20


def test_kunci_yang_salah_bentuk_ditolak_dengan_jelas(monkeypatch):
    for buruk in ("bukan base64 sama sekali!!", base64.b64encode(b"terlalu pendek").decode()):
        monkeypatch.setenv(enkripsi.NAMA_ENV, buruk)
        with pytest.raises(enkripsi.KunciTidakAda):
            enkripsi.kunci_dari_env(wajib=True)


def test_tanpa_kunci_boleh_diam_kalau_memang_tidak_wajib(monkeypatch):
    """Cadangan lokal tetap dibuat walau kuncinya belum disiapkan. Cadangan
    yang tidak jadi dibuat lebih buruk daripada cadangan yang belum
    terenkripsi di mesin sendiri."""
    monkeypatch.delenv(enkripsi.NAMA_ENV, raising=False)
    assert enkripsi.kunci_dari_env(wajib=False) is None
    with pytest.raises(enkripsi.KunciTidakAda):
        enkripsi.kunci_dari_env(wajib=True)


# --------------------------------------------------------------- bolak balik ---


def test_dikunci_lalu_dibuka_menghasilkan_isi_yang_sama(kunci):
    assert enkripsi.buka(enkripsi.kunci(ISI, kunci), kunci) == ISI


def test_isinya_tidak_lagi_terbaca(kunci):
    hasil = enkripsi.kunci(ISI, kunci)
    assert b"CREATE TABLE" not in hasil
    assert b"pg_dump" not in hasil


def test_dua_kali_mengunci_menghasilkan_berkas_berbeda(kunci):
    """Nonce acak. Tanpa itu, dua cadangan dengan isi sama menghasilkan
    berkas yang sama persis, dan siapa pun yang menyimpannya tahu bahwa
    isinya tidak berubah di antara keduanya."""
    a, b = enkripsi.kunci(ISI, kunci), enkripsi.kunci(ISI, kunci)
    assert a != b
    assert enkripsi.buka(a, kunci) == enkripsi.buka(b, kunci) == ISI


def test_gzip_masih_bisa_dipadatkan_sebelum_dikunci(kunci):
    """Urutannya penting: padatkan dulu, baru kunci. Keluaran AES tidak bisa
    dipadatkan sama sekali, jadi urutan sebaliknya membuang seluruh gunanya
    gzip."""
    padat = gzip.compress(ISI, 6)
    assert len(padat) < len(ISI) / 4
    terkunci = enkripsi.kunci(padat, kunci)
    assert gzip.decompress(enkripsi.buka(terkunci, kunci)) == ISI


# ---------------------------------------------------- yang harus ditolak ---


def test_kunci_yang_salah_ditolak(kunci):
    lain = base64.b64decode(enkripsi.buat_kunci())
    with pytest.raises(enkripsi.TidakBisaDibuka):
        enkripsi.buka(enkripsi.kunci(ISI, kunci), lain)


@pytest.mark.parametrize("posisi", [10, 40, -20, -1])
def test_satu_bit_yang_berubah_ketahuan(kunci, posisi):
    """Ini yang membedakan GCM dari mode yang sekadar menyandi. Cadangan yang
    rusak di tengah jalan harus gagal dibuka, bukan terbuka jadi sampah yang
    dikira data lalu dipulihkan ke basis data sungguhan."""
    rusak = bytearray(enkripsi.kunci(ISI, kunci))
    rusak[posisi] ^= 0x01
    with pytest.raises(enkripsi.TidakBisaDibuka):
        enkripsi.buka(bytes(rusak), kunci)


def test_penanda_yang_diganti_ketahuan(kunci):
    """Penanda ikut diautentikasi, bukan sekadar ditempel di depan."""
    hasil = bytearray(enkripsi.kunci(ISI, kunci))
    hasil[0:7] = b"HKCAD9\n"
    with pytest.raises(enkripsi.TidakBisaDibuka):
        enkripsi.buka(bytes(hasil), kunci)


def test_berkas_polos_tidak_dikira_terenkripsi(kunci):
    with pytest.raises(enkripsi.TidakBisaDibuka):
        enkripsi.buka(gzip.compress(ISI), kunci)


def test_berkas_terpotong_ditolak(kunci):
    hasil = enkripsi.kunci(ISI, kunci)
    for potong in (8, 20, len(hasil) - 1):
        with pytest.raises(enkripsi.TidakBisaDibuka):
            enkripsi.buka(hasil[:potong], kunci)


def test_isi_yang_kelewat_besar_ditolak_bukan_dimakan(kunci, monkeypatch):
    """Seluruh isinya masuk memori sekali jalan. Batasnya disebut terus
    terang dan ditegakkan, bukan ditemukan saat mesinnya kehabisan memori."""
    monkeypatch.setattr(enkripsi, "BATAS_BITA", 1000)
    with pytest.raises(ValueError):
        enkripsi.kunci(b"x" * 1001, kunci)


# ------------------------------------------------------------ pengenalan ---


def test_terenkripsi_mengenali_dari_penanda_bukan_dari_nama(kunci):
    assert enkripsi.terenkripsi(enkripsi.kunci(ISI, kunci))
    assert not enkripsi.terenkripsi(gzip.compress(ISI))
    assert not enkripsi.terenkripsi(b"")


# ------------------------------------------------------------- perintah ---


def test_perintah_kunci_mencetak_baris_yang_siap_disalin():
    hasil = subprocess.run(
        [sys.executable, str(AKAR / "backend" / "db" / "enkripsi.py"), "kunci"],
        capture_output=True, text=True,
    )
    assert hasil.returncode == 0
    baris = hasil.stdout.splitlines()[0]
    nama, _, nilai = baris.partition("=")
    assert nama == enkripsi.NAMA_ENV
    assert len(base64.b64decode(nilai)) == enkripsi.PANJANG_KUNCI


def test_kunci_tidak_pernah_ada_di_dalam_kode():
    """Bab 15.11. Kunci bawaan adalah kunci yang sudah bocor."""
    isi = (AKAR / "backend" / "db" / "enkripsi.py").read_text(encoding="utf-8")
    assert "os.environ" in isi
    for baris in isi.splitlines():
        bersih = baris.strip()
        if bersih.startswith("#") or "NAMA_ENV" in bersih:
            continue
        assert "CADANGAN_KUNCI=" not in bersih, baris
