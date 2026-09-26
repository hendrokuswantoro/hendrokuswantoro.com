from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse

LANGKAH = 30
ANGKA = 6
TOLERANSI = 1
PANJANG_RAHASIA = 20


def rahasia_baru() -> str:
    return base64.b32encode(secrets.token_bytes(PANJANG_RAHASIA)).decode("ascii").rstrip("=")


def _mentah(rahasia: str) -> bytes:
    padat = rahasia.strip().replace(" ", "").upper()
    padat += "=" * (-len(padat) % 8)
    return base64.b32decode(padat, casefold=True)


def kode_pada(rahasia: str, langkah: int) -> str:
    pesan = struct.pack(">Q", langkah)
    sidik = hmac.new(_mentah(rahasia), pesan, hashlib.sha1).digest()
    geser = sidik[-1] & 0x0F
    potong = struct.unpack(">I", sidik[geser:geser + 4])[0] & 0x7FFFFFFF
    return str(potong % (10 ** ANGKA)).zfill(ANGKA)


def kode_sekarang(rahasia: str, saat: float | None = None) -> str:
    return kode_pada(rahasia, int((saat if saat is not None else time.time()) // LANGKAH))


def cocok(rahasia: str, kode: str, saat: float | None = None) -> int | None:
    bersih = "".join(ch for ch in (kode or "") if ch.isdigit())
    if len(bersih) != ANGKA:
        return None

    sekarang = int((saat if saat is not None else time.time()) // LANGKAH)
    for geser in range(-TOLERANSI, TOLERANSI + 1):
        langkah = sekarang + geser
        if hmac.compare_digest(kode_pada(rahasia, langkah), bersih):
            return langkah
    return None


def alamat_otpauth(rahasia: str, email: str, penerbit: str = "hendrokuswantoro.com") -> str:
    label = urllib.parse.quote(f"{penerbit}:{email}", safe="")
    tanya = urllib.parse.urlencode({
        "secret": rahasia,
        "issuer": penerbit,
        "algorithm": "SHA1",
        "digits": ANGKA,
        "period": LANGKAH,
    })
    return f"otpauth://totp/{label}?{tanya}"


JUMLAH_PEMULIHAN = 8
ABJAD = "ABCDEFGHJKMNPQRSTVWXYZ23456789"
PANJANG_BAGIAN = 5


def kode_pemulihan_baru() -> str:
    bagian = [
        "".join(secrets.choice(ABJAD) for _ in range(PANJANG_BAGIAN))
        for _ in range(2)
    ]
    return "-".join(bagian)


def normalkan_pemulihan(kode: str) -> str:
    return "".join(ch for ch in (kode or "").upper() if ch in ABJAD)


def qr_svg(isi: str, ukuran: int = 8) -> str:
    import qrcode

    q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(isi)
    q.make(fit=True)
    matriks = q.get_matrix()
    sisi = len(matriks)

    kotak: list[str] = []
    for y, baris in enumerate(matriks):
        x = 0
        while x < sisi:
            if not baris[x]:
                x += 1
                continue
            mulai = x
            while x < sisi and baris[x]:
                x += 1
            kotak.append(f'<rect x="{mulai}" y="{y}" width="{x - mulai}" height="1"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sisi} {sisi}" '
        f'width="{sisi * ukuran}" height="{sisi * ukuran}" '
        f'shape-rendering="crispEdges" role="img" '
        f'aria-label="Kode QR untuk aplikasi authenticator">'
        f'<rect width="{sisi}" height="{sisi}" fill="#ffffff"/>'
        f'<g fill="#000000">{"".join(kotak)}</g></svg>'
    )
