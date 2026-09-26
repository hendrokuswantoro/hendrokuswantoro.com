from __future__ import annotations

import struct
import zlib

import pytest

try:
    from backend.layanan import metadata

    ADA_BACKEND = True
except ModuleNotFoundError:  # pragma: no cover
    ADA_BACKEND = False
    metadata = None  # type: ignore[assignment]

pytestmark = pytest.mark.skipif(
    not ADA_BACKEND,
    reason="backend belum terpasang. Jalankan: pip install -r backend/requirements.txt",
)

JEJAK = b"KOORDINAT-RAHASIA-7.7956S-110.3695E"


def jpeg_ber_exif() -> bytes:
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x02\x00\x00\x01\x00\x01\x00\x00"
    muatan = b"Exif\x00\x00" + JEJAK + b"\x00" * 8
    app1 = b"\xff\xe1" + struct.pack(">H", len(muatan) + 2) + muatan
    komentar = b"\xff\xfe" + struct.pack(">H", len(JEJAK) + 2) + JEJAK
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 17, 8, 90, 160, 3) + b"\x00" * 9
    sos = b"\xff\xda" + struct.pack(">H", 12) + b"\x00" * 10 + b"badan-gambar"
    return b"\xff\xd8" + app0 + app1 + komentar + sof + sos + b"\xff\xd9"


def _kotak(nama: bytes, isi: bytes) -> bytes:
    return (struct.pack(">I", len(isi)) + nama + isi
            + struct.pack(">I", zlib.crc32(nama + isi) & 0xFFFFFFFF))


def png_ber_exif() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + _kotak(b"IHDR", struct.pack(">IIBBBBB", 160, 90, 8, 2, 0, 0, 0))
        + _kotak(b"eXIf", JEJAK)
        + _kotak(b"tEXt", b"Comment\x00" + JEJAK)
        + _kotak(b"IDAT", zlib.compress(b"\x00" * 30))
        + _kotak(b"IEND", b"")
    )


def _riff(potongan: list[tuple[bytes, bytes]]) -> bytes:
    badan = b""
    for nama, isi in potongan:
        badan += nama + struct.pack("<I", len(isi)) + isi
        if len(isi) & 1:
            badan += b"\x00"
    return b"RIFF" + struct.pack("<I", len(badan) + 4) + b"WEBP" + badan


def webp_ber_exif() -> bytes:
    vp8x = bytes([0b00001100, 0, 0, 0]) + (159).to_bytes(3, "little") + (89).to_bytes(3, "little")
    return _riff([
        (b"VP8X", vp8x),
        (b"VP8 ", b"badan-gambar-webp"),
        (b"EXIF", JEJAK),
        (b"XMP ", b"<x:xmpmeta>" + JEJAK + b"</x:xmpmeta>"),
    ])


def webp_polos() -> bytes:
    return _riff([(b"VP8L", b"\x2f" + b"\x00" * 12)])


@pytest.mark.parametrize("tipe,bikin", [
    ("image/jpeg", jpeg_ber_exif),
    ("image/png", png_ber_exif),
    ("image/webp", webp_ber_exif),
])
def test_koordinatnya_benar_benar_hilang(tipe, bikin):
    asli = bikin()
    assert JEJAK in asli, "contohnya sendiri tidak memuat jejaknya"

    bersih = metadata.buang(tipe, asli)
    assert JEJAK not in bersih, f"{tipe}: koordinatnya masih ada sesudah dibuang"
    assert len(bersih) < len(asli)


def test_gambarnya_tetap_utuh_sesudah_dibuang():
    bersih = metadata.buang("image/jpeg", jpeg_ber_exif())
    assert bersih.startswith(b"\xff\xd8")
    assert bersih.endswith(b"\xff\xd9")
    assert b"badan-gambar" in bersih
    assert b"JFIF" in bersih, "APP0 ikut terbuang, padahal ia bukan metadata pribadi"
    layanan = pytest.importorskip("backend.layanan.berkas")
    assert layanan.ukuran("image/jpeg", bersih) == (160, 90)


def test_png_tetap_terbaca_ukurannya():
    layanan = pytest.importorskip("backend.layanan.berkas")

    bersih = metadata.buang("image/png", png_ber_exif())
    assert layanan.ukuran("image/png", bersih) == (160, 90)
    assert bersih.endswith(_kotak(b"IEND", b""))


def test_webp_menurunkan_penanda_exif_yang_kotaknya_sudah_dibuang():
    bersih = metadata.buang("image/webp", webp_ber_exif())
    tempat = bersih.index(b"VP8X") + 8
    penanda = bersih[tempat]
    assert not penanda & 0b00001000, "penanda EXIF masih menyala"
    assert not penanda & 0b00000100, "penanda XMP masih menyala"


def test_webp_sederhana_dibiarkan_apa_adanya():
    asli = webp_polos()
    assert metadata.buang("image/webp", asli) == asli


@pytest.mark.parametrize("tipe", ["image/gif", "image/avif", "video/mp4"])
def test_yang_belum_didukung_menolak_dengan_terus_terang(tipe):
    with pytest.raises(metadata.TidakBisa) as galat:
        metadata.buang(tipe, b"apa saja")
    assert "belum bisa" in str(galat.value)


def test_berkas_yang_rusak_ditolak_bukan_ditebak():
    with pytest.raises(metadata.TidakBisa):
        metadata.buang("image/jpeg", b"\xff\xd8" + b"bukan penanda")
    with pytest.raises(metadata.TidakBisa):
        metadata.buang("image/png", b"bukan png sama sekali")


def test_daftar_yang_bisa_dibuang_disebut_di_satu_tempat():
    assert set(metadata.BISA_DIBUANG) == {"image/jpeg", "image/png", "image/webp"}
