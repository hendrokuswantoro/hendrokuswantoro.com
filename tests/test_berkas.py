"""Unggahan foto dan video: yang diterima, dan terutama yang ditolak.

Satu kalimat menjelaskan hampir seluruh berkas ini: **jenis berkas ditentukan
dari isinya, bukan dari yang dikatakan pengirimnya.** Nama berkas dan header
Content-Type keduanya datang dari pengirim, jadi keduanya bisa berbunyi apa
saja. Berkas HTML bernama "foto.jpg" yang diterima lalu disajikan lagi dari
alamat situs ini adalah skrip milik pengirimnya yang jalan di atas asal situs
ini.

Berkas contoh di bawah dibuat dari bita, bukan diambil dari cakram dan bukan
dibangkitkan pustaka gambar. Alasannya dua: ujinya jalan di CI tanpa berkas
tambahan apa pun, dan yang diuji memang pembacaan kepala berkasnya, jadi
kepala berkas yang ditulis tangan justru lebih tepat sasaran daripada foto
sungguhan yang isinya tidak diketahui ujinya.
"""

from __future__ import annotations

import io
import struct

import pytest

# Seluruh berkas ini menuntut backend terpasang, sebab yang diuji memang
# lapisan layanannya. Penjaganya di tingkat modul, bukan per uji, dan itu
# beda dari test_passkey_alamat.py yang sebagian ujinya cuma membaca HTML.
try:  # noqa: SIM105
    from backend.layanan import berkas as layanan

    ADA_BACKEND = True
except ModuleNotFoundError:  # pragma: no cover
    ADA_BACKEND = False
    layanan = None  # type: ignore[assignment]

pytestmark = pytest.mark.skipif(
    not ADA_BACKEND,
    reason="backend belum terpasang. Jalankan: pip install -r backend/requirements.txt",
)


# ------------------------------------------------------------ berkas contoh ---


def png(lebar: int, tinggi: int) -> bytes:
    """Kepala PNG yang sah sampai akhir IHDR. Sesudahnya tidak dibaca."""
    ihdr = struct.pack(">II", lebar, tinggi) + b"\x08\x06\x00\x00\x00"
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", len(ihdr))
        + b"IHDR"
        + ihdr
        + b"\x00\x00\x00\x00"
    )


def gif(lebar: int, tinggi: int) -> bytes:
    return b"GIF89a" + struct.pack("<HH", lebar, tinggi) + b"\xf7\x00\x00"


def jpeg(lebar: int, tinggi: int, sisipan: bytes = b"") -> bytes:
    """SOI, lalu segmen tambahan kalau diminta, lalu SOF0.

    `sisipan` dipakai menguji bahwa ukurannya tetap ketemu walau ada komentar
    atau thumbnail EXIF panjang sebelum SOF, yaitu susunan yang sebenarnya
    keluar dari kamera.
    """
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 17, 8, tinggi, lebar, 3) + b"\x00" * 9
    return b"\xff\xd8" + sisipan + sof + b"\xff\xd9"


def komentar_jpeg(panjang: int) -> bytes:
    return b"\xff\xfe" + struct.pack(">H", panjang + 2) + b"x" * panjang


def webp_vp8l(lebar: int, tinggi: int) -> bytes:
    angka = (lebar - 1) | ((tinggi - 1) << 14)
    isi = b"VP8L" + struct.pack("<I", 20) + b"\x2f" + struct.pack("<I", angka)
    return b"RIFF" + struct.pack("<I", len(isi) + 4) + b"WEBP" + isi + b"\x00" * 8


def webp_vp8x(lebar: int, tinggi: int) -> bytes:
    isi = (
        b"VP8X"
        + struct.pack("<I", 10)
        + b"\x10\x00\x00\x00"
        + (lebar - 1).to_bytes(3, "little")
        + (tinggi - 1).to_bytes(3, "little")
    )
    return b"RIFF" + struct.pack("<I", len(isi) + 4) + b"WEBP" + isi + b"\x00" * 8


def mp4() -> bytes:
    return b"\x00\x00\x00\x18ftypisom" + b"\x00" * 16


def webm() -> bytes:
    return b"\x1a\x45\xdf\xa3" + b"\x00" * 32


# ------------------------------------------------------------- mengenalinya ---


@pytest.mark.parametrize("data,jenis,tipe", [
    (png(2, 3), "gambar", "image/png"),
    (gif(4, 5), "gambar", "image/gif"),
    (jpeg(6, 7), "gambar", "image/jpeg"),
    (webp_vp8l(8, 9), "gambar", "image/webp"),
    (webp_vp8x(10, 11), "gambar", "image/webp"),
    (mp4(), "video", "video/mp4"),
    (webm(), "video", "video/webm"),
])
def test_jenis_dibaca_dari_bita_pertamanya(data, jenis, tipe):
    assert layanan.kenali(data) == (jenis, tipe)


@pytest.mark.parametrize("data", [
    b"<!doctype html><script>alert(1)</script>",
    b"#!/bin/sh\nrm -rf /",
    b"GIF87",                      # terpotong, bukan GIF
    b"%PDF-1.7\n",
    b"",
])
def test_yang_bukan_foto_atau_video_ditolak(data):
    """Termasuk yang hampir benar. Berkas yang lolos jadi berkas yang
    disajikan lagi dari alamat situs ini."""
    with pytest.raises(layanan.Ditolak):
        layanan.kenali(data)


def test_nama_dan_tipe_kiriman_tidak_dipakai_memutuskan_apa_apa():
    """Isinya HTML, namanya foto.png, Content-Type-nya image/png. Yang
    menentukan tetap isinya."""
    with pytest.raises(layanan.Ditolak):
        layanan.kenali(b"<html><body>bukan gambar</body></html>")


# ------------------------------------------------------------- ukurannya ---


@pytest.mark.parametrize("tipe,data,ukur", [
    ("image/png", png(1600, 900), (1600, 900)),
    ("image/gif", gif(320, 240), (320, 240)),
    ("image/jpeg", jpeg(4032, 3024), (4032, 3024)),
    ("image/jpeg", jpeg(800, 600, komentar_jpeg(5000)), (800, 600)),
    ("image/webp", webp_vp8l(1024, 768), (1024, 768)),
    ("image/webp", webp_vp8x(3840, 2160), (3840, 2160)),
])
def test_ukuran_gambar_dibaca_dari_kepalanya(tipe, data, ukur):
    assert layanan.ukuran(tipe, data) == ukur


def test_gambar_yang_ukurannya_tidak_terbaca_ditolak():
    """Gambar tanpa ukuran membuat tulisan di bawahnya melompat saat
    gambarnya tiba, tepat ketika ada yang sedang membacanya."""
    with pytest.raises(layanan.Ditolak):
        layanan.ukuran("image/jpeg", b"\xff\xd8\xff\xd9")


# --------------------------------------------------------------- namanya ---


def test_nama_di_cakram_tidak_pernah_datang_dari_pengirimnya():
    nama = layanan.nama_baru("gambar", "image/webp", (800, 450))
    assert nama.endswith("-800x450.webp")
    assert len(nama) > len("-800x450.webp")
    # Dua unggahan tidak pernah bertabrakan namanya.
    assert nama != layanan.nama_baru("gambar", "image/webp", (800, 450))


def test_nama_video_tanpa_ukuran():
    """Video tidak diukur. Mengukurnya menuntut ffmpeg, dan menebaknya berarti
    menuliskan angka yang tidak pernah diukur."""
    nama = layanan.nama_baru("video", "video/mp4", None)
    assert nama.endswith(".mp4")
    assert "x" not in nama.rsplit(".", 1)[0]


@pytest.mark.parametrize("jahat", [
    "../rahasia.webp",
    "..\\rahasia.webp",
    "/etc/passwd",
    ".tersembunyi",
    "",
])
def test_jalur_menolak_nama_yang_keluar_dari_foldernya(jahat):
    with pytest.raises(layanan.Ditolak):
        layanan.jalur(jahat)


@pytest.mark.parametrize("masuk,keluar", [
    ("C:\\Users\\Hendro\\foto.jpg", "foto.jpg"),
    ("../../etc/passwd", "passwd"),
    ("baris\nkedua.png", "bariskedua.png"),
    ("", "tanpa-nama"),
])
def test_nama_asal_dibersihkan_walau_tidak_dipakai_membentuk_jalur(masuk, keluar):
    """Ia muncul lagi di daftar berkas dan di log, dan di keduanya nama yang
    memuat baris baru bisa merusak bacaan."""
    assert layanan._rapikan_nama(masuk) == keluar


# -------------------------------------------------------------- batasnya ---


def test_berkas_yang_melewati_batas_ditolak_di_tengah_pembacaan(monkeypatch):
    """Ditolak sebelum seluruhnya masuk ke memori proses ini.

    Membaca dulu lalu menolak belakangan berarti berkas satu gigabita tetap
    sempat masuk, dan penolakan sesudah itu tidak menolong siapa pun.
    """
    monkeypatch.setattr(layanan, "batas", lambda jenis: 1024)
    besar = png(10, 10) + b"\x00" * (4096 - len(png(10, 10)))

    with pytest.raises(layanan.Ditolak) as galat:
        layanan._baca(io.BytesIO(besar))
    assert "batas" in str(galat.value)


def test_batas_gambar_dan_video_berbeda():
    """Foto dan video memang beda ukuran, jadi batasnya tidak satu angka."""
    assert layanan.batas("video") > layanan.batas("gambar")


def test_berkas_kosong_ditolak():
    with pytest.raises(layanan.Ditolak):
        layanan._baca(io.BytesIO(b""))
