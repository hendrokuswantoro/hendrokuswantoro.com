from __future__ import annotations

import struct

TANDA_PNG = b"\x89PNG\r\n\x1a\n"


def adalah_webp(data: bytes) -> bool:
    return data.startswith(b"RIFF") and data[8:12] == b"WEBP"

BISA_DIBUANG = ("image/jpeg", "image/png", "image/webp")


class TidakBisa(Exception):
    pass


def buang(tipe: str, data: bytes) -> bytes:
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
            raise TidakBisa("susunan JPEG tidak seperti yang dikenali")

        tanda = data[i + 1]

        if tanda == 0xDA:
            keluar.append(data[i:])
            break

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


_PNG_DIBUANG = {b"eXIf", b"tEXt", b"iTXt", b"zTXt", b"tIME"}


def _png(data: bytes) -> bytes:
    if not data.startswith(TANDA_PNG):
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


def _webp(data: bytes) -> bytes:
    if not adalah_webp(data):
        raise TidakBisa("bukan WebP")

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
        habis = i + 8 + panjang + (panjang & 1)
        if habis > batas:
            raise TidakBisa("kotak WebP melewati ujung berkasnya")

        if jenis in (b"EXIF", b"XMP "):
            i = habis
            continue

        if jenis == b"VP8X":
            isi = bytearray(data[i + 8:habis])
            isi[0] &= ~0b00001100 & 0xFF
            keluar.append(data[i:i + 8] + bytes(isi))
        else:
            keluar.append(data[i:habis])

        i = habis

    badan = b"".join(keluar)
    return b"RIFF" + struct.pack("<I", len(badan) + 4) + b"WEBP" + badan
