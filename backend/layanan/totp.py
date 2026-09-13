"""TOTP, RFC 6238, dan kode pemulihannya.

Ini bukan protokol buatan sendiri. TOTP adalah standar terbuka yang sudah
dipakai Google Authenticator, Aegis, 1Password, dan Authy sejak 2011, dan
seluruh isinya cuma HMAC-SHA1 atas nomor jendela waktu. Menuliskannya di sini
lebih jujur daripada menarik satu pustaka baru untuk tiga puluh baris yang
bisa dibaca langsung, dan keenam vektor uji resmi RFC 6238 ada di
`tests/test_keamanan_akun.py` sebagai buktinya.

Yang sengaja tidak dikarang sendiri: penyandian rahasianya. Itu AES-256-GCM
dari `backend/core/rahasia.py`, yang meminjam implementasi yang sudah dipakai
cadangan.

Tiga hal yang sering salah pada TOTP dan ditangani di sini:

1. **Jendela ketetanggaan.** Jam perangkat tidak pernah persis sama dengan jam
   server. Satu langkah ke belakang dan satu ke depan diterima, jadi selisih
   sampai tiga puluh detik ke arah mana pun tetap masuk. Lebih lebar dari itu
   memperbesar ruang tebakan tanpa menolong siapa pun.
2. **Perbandingan yang bocor lewat waktu.** Dibandingkan dengan
   `secrets.compare_digest`, bukan `==`.
3. **Kode yang sama dipakai dua kali.** Kode yang sudah berhasil dipakai
   ditolak sampai jendelanya lewat. Tanpa itu, kode yang terlihat sekilas oleh
   orang lain masih berlaku sampai tiga puluh detik.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse

LANGKAH = 30          # detik per kode, sebagaimana bawaan seluruh aplikasi
ANGKA = 6
TOLERANSI = 1         # satu langkah ke belakang dan satu ke depan
PANJANG_RAHASIA = 20  # 160 bit, sebagaimana disarankan RFC 4226


def rahasia_baru() -> str:
    """Base32 tanpa padding, bentuk yang dibaca aplikasi authenticator."""
    return base64.b32encode(secrets.token_bytes(PANJANG_RAHASIA)).decode("ascii").rstrip("=")


def _mentah(rahasia: str) -> bytes:
    padat = rahasia.strip().replace(" ", "").upper()
    padat += "=" * (-len(padat) % 8)
    return base64.b32decode(padat, casefold=True)


def kode_pada(rahasia: str, langkah: int) -> str:
    """Satu kode untuk satu nomor jendela. RFC 6238 bagian 4."""
    pesan = struct.pack(">Q", langkah)
    sidik = hmac.new(_mentah(rahasia), pesan, hashlib.sha1).digest()
    geser = sidik[-1] & 0x0F
    potong = struct.unpack(">I", sidik[geser:geser + 4])[0] & 0x7FFFFFFF
    return str(potong % (10 ** ANGKA)).zfill(ANGKA)


def kode_sekarang(rahasia: str, saat: float | None = None) -> str:
    return kode_pada(rahasia, int((saat if saat is not None else time.time()) // LANGKAH))


def cocok(rahasia: str, kode: str, saat: float | None = None) -> int | None:
    """Nomor jendela yang cocok, atau None.

    Nomornya dikembalikan, bukan True, supaya pemanggilnya bisa menyimpan
    jendela terakhir yang terpakai dan menolak kode yang sama dipakai lagi.
    """
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
    """URI otpauth:// yang dibaca aplikasi authenticator dari kode QR.

    Perhatikan labelnya memuat penerbit DAN emailnya, dipisah titik dua. Itu
    bukan hiasan: tanpa penerbit di label, daftar di aplikasi penggunanya
    hanya berisi alamat email tanpa keterangan situs mana.
    """
    label = urllib.parse.quote(f"{penerbit}:{email}", safe="")
    tanya = urllib.parse.urlencode({
        "secret": rahasia,
        "issuer": penerbit,
        "algorithm": "SHA1",
        "digits": ANGKA,
        "period": LANGKAH,
    })
    return f"otpauth://totp/{label}?{tanya}"


# ------------------------------------------------------------- pemulihan ---

JUMLAH_PEMULIHAN = 8
# Tanpa huruf yang bisa tertukar saat disalin dari kertas: I, L, O, U, 0, 1.
ABJAD = "ABCDEFGHJKMNPQRSTVWXYZ23456789"
PANJANG_BAGIAN = 5


def kode_pemulihan_baru() -> str:
    """Bentuknya XXXXX-XXXXX. Sekitar 49 bit, jauh di atas yang bisa ditebak
    lewat jaringan, dan masih bisa ditulis tangan tanpa salah."""
    bagian = [
        "".join(secrets.choice(ABJAD) for _ in range(PANJANG_BAGIAN))
        for _ in range(2)
    ]
    return "-".join(bagian)


def normalkan_pemulihan(kode: str) -> str:
    """Orang mengetik ulang kode ini dari kertas. Huruf kecil, spasi, dan
    tanda hubung yang lupa ditulis tidak boleh jadi alasan gagal."""
    return "".join(ch for ch in (kode or "").upper() if ch in ABJAD)


# --------------------------------------------------------------- kode QR ---


def qr_svg(isi: str, ukuran: int = 8) -> str:
    """Kode QR sebagai SVG, digambar di sini, bukan diminta ke layanan luar.

    Seluruh layanan "buat QR gratis" bekerja dengan cara yang sama: alamat
    otpauth-nya dikirim ke server mereka. Alamat itu MEMUAT rahasia TOTP-nya.
    Mengirimnya ke pihak ketiga berarti menyerahkan faktor kedua kepada orang
    yang tidak pernah diminta menjaganya, dan itu tetap benar walaupun mereka
    berjanji tidak menyimpannya.

    CSP situs ini juga menolaknya, dan itu memang gunanya CSP.

    Yang dipakai pustaka `qrcode` untuk bagian yang sulit, yaitu penyandian
    dan koreksi galatnya. Yang ditulis di sini cuma mengubah matriks hitam
    putihnya jadi SVG: lima belas baris, dan hasilnya tidak menuntut satu pun
    permintaan jaringan.
    """
    import qrcode

    q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(isi)
    q.make(fit=True)
    matriks = q.get_matrix()
    sisi = len(matriks)

    # Modul yang bersebelahan digabung jadi satu <rect> memanjang. Satu rect
    # per modul menghasilkan SVG 51 KB untuk kode yang isinya seratus bita;
    # digabung begini jadi sekitar seperlimanya, dan gambarnya sama persis.
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
