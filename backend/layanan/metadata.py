"""Membuang metadata dari foto, termasuk koordinat tempat pemotretannya.

Kenapa ini ada. Foto dari ponsel membawa EXIF, dan EXIF bisa memuat lintang
dan bujur tempat ia diambil, merek dan nomor seri kameranya, serta waktu
pengambilannya sampai ke detik. Kalau fotonya terbit apa adanya, seluruh
keterangan itu ikut terbit, dan yang paling merugikan biasanya yang pertama:
alamat rumah, sekolah anak, atau tempat kerja, dibaca siapa saja yang mengunduh
gambarnya.

**Yang dikerjakan berkas ini hanya membuang, tidak pernah menulis ulang
gambarnya.** Potongan bita yang memuat metadata dilewati, sisanya disalin apa
adanya. Tidak ada penyandian ulang, jadi tidak ada penurunan mutu dan tidak
ada pengurai gambar yang dijalankan terhadap berkas dari luar.

**Yang TIDAK bisa dikerjakan, dan disebut terus terang.** GIF dan AVIF tidak
didukung. Metadata di GIF duduk di blok ekstensi yang bercampur dengan data
gambarnya, dan di AVIF ia di dalam pohon kotak ISO-BMFF yang menuntut pengurai
utuh. Membuang setengah lalu mengaku sudah bersih adalah kebohongan yang lebih
berbahaya daripada tidak membuang sama sekali, sebab ia membuat orang berhenti
hati hati. Jadi keduanya DITOLAK ketika pembuangan diminta, bukan diterima diam
diam.
"""

from __future__ import annotations

import struct

# Jenis yang metadatanya benar benar bisa dibuang di sini.
BISA_DIBUANG = ("image/jpeg", "image/png", "image/webp")


class TidakBisa(Exception):
    """Jenis berkas yang pembuangan metadatanya tidak didukung."""


def buang(tipe: str, data: bytes) -> bytes:
    """Bita yang sama, dikurangi metadatanya."""
    if tipe == "image/jpeg":
        return _jpeg(data)
    if tipe == "image/png":
        return _png(data)
    if tipe == "image/webp":
        return _webp(data)
    raise TidakBisa(
        f"metadata {tipe} belum bisa dibuang di sini. Yang bisa: "
        + ", ".join(BISA_DIBUANG)
    )


# ------------------------------------------------------------------- JPEG ---

# APP1 memuat EXIF dan XMP, APP2 profil warna ICC, APP13 blok IPTC milik
# Photoshop. COM komentar bebas. Semuanya dibuang.
#
# APP0 ditahan: ia JFIF, yang memuat kerapatan piksel, dan sebagian pembaca
# lama menuntutnya ada.
_JPEG_DIBUANG = {0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9,
                 0xEA, 0xEB, 0xEC, 0xED, 0xEE, 0xEF, 0xFE}


def _jpeg(data: bytes) -> bytes:
    if not data.startswith(b"\xff\xd8"):
        raise TidakBisa("bukan JPEG")

    keluar = [data[:2]]
    i = 2
    batas = len(data)

    while i + 3 < batas:
        if data[i] != 0xFF:
            # Bita yang bukan penanda berarti susunannya tidak seperti yang
            # dikira. Yang benar adalah berhenti dan mengadu, bukan menebak.
            raise TidakBisa("susunan JPEG tidak seperti yang dikenali")

        tanda = data[i + 1]

        # SOS: sesudah ini badan gambarnya, dan tidak ada metadata lagi.
        if tanda == 0xDA:
            keluar.append(data[i:])
            break

        # Penanda tanpa badan.
        if tanda in (0x01, 0xD8) or 0xD0 <= tanda <= 0xD7:
            keluar.append(data[i:i + 2])
            i += 2
            continue

        panjang = int.from_bytes(data[i + 2:i + 4], "big")
        if panjang < 2:
            raise TidakBisa("panjang segmen JPEG tidak masuk akal")

        if tanda not in _JPEG_DIBUANG:
            keluar.append(data[i:i + 2 + panjang])
        i += 2 + panjang
    else:
        keluar.append(data[i:])

    return b"".join(keluar)


# -------------------------------------------------------------------- PNG ---

# Kotak yang memuat teks, waktu, dan EXIF. Semuanya ancillary, artinya
# pembaca gambar memang boleh mengabaikannya, jadi membuangnya tidak pernah
# merusak gambarnya.
_PNG_DIBUANG = {b"eXIf", b"tEXt", b"iTXt", b"zTXt", b"tIME"}


def _png(data: bytes) -> bytes:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise TidakBisa("bukan PNG")

    keluar = [data[:8]]
    i = 8
    batas = len(data)

    while i + 8 <= batas:
        panjang = int.from_bytes(data[i:i + 4], "big")
        jenis = data[i + 4:i + 8]
        habis = i + 12 + panjang
        if habis > batas:
            raise TidakBisa("kotak PNG melewati ujung berkasnya")

        if jenis not in _PNG_DIBUANG:
            keluar.append(data[i:habis])

        i = habis
        if jenis == b"IEND":
            break

    return b"".join(keluar)


# ------------------------------------------------------------------- WebP ---


def _webp(data: bytes) -> bytes:
    if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"):
        raise TidakBisa("bukan WebP")

    # Bentuk sederhana, VP8 atau VP8L tanpa pembungkus VP8X, tidak punya
    # tempat untuk menyimpan EXIF sama sekali.
    if data[12:16] in (b"VP8 ", b"VP8L"):
        return data

    if data[12:16] != b"VP8X":
        raise TidakBisa("bentuk WebP tidak dikenali")

    keluar = []
    i = 12
    batas = len(data)

    while i + 8 <= batas:
        jenis = data[i:i + 4]
        panjang = int.from_bytes(data[i + 4:i + 8], "little")
        # Kotak RIFF selalu genap; yang ganjil diberi satu bita penyangga.
        habis = i + 8 + panjang + (panjang & 1)
        if habis > batas:
            raise TidakBisa("kotak WebP melewati ujung berkasnya")

        if jenis in (b"EXIF", b"XMP "):
            i = habis
            continue

        if jenis == b"VP8X":
            # Dua bit penanda di bita pertama mengumumkan ada EXIF dan XMP.
            # Kalau kotaknya dibuang tetapi bitnya dibiarkan menyala, sebagian
            # pembaca mencarinya lalu menganggap berkasnya rusak.
            isi = bytearray(data[i + 8:habis])
            isi[0] &= ~0b00001100 & 0xFF
            keluar.append(data[i:i + 8] + bytes(isi))
        else:
            keluar.append(data[i:habis])

        i = habis

    badan = b"".join(keluar)
    return b"RIFF" + struct.pack("<I", len(badan) + 4) + b"WEBP" + badan
