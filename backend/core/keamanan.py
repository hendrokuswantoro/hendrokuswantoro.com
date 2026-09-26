"""Sandi, token, dan ringkasan. Bab 15.8, 15.10, 15.11.

Tidak ada satu pun protokol kriptografi buatan sendiri di sini, sesuai
larangan di bab 15.8. Yang dipakai Argon2id lewat argon2-cffi dan JWT lewat
pyjwt, keduanya pustaka yang sudah ditelaah orang banyak.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend.core.konfigurasi import pengaturan

# Parameter bawaan argon2-cffi mengikuti RFC 9106. Tidak diturunkan.
_hasher = PasswordHasher()

ALGORITMA = "HS256"
PENERBIT = "hendrokuswantoro.com"
UNTUK = "hendrokuswantoro.com/admin"


# Hash sungguhan dari nilai acak, dihitung sekali saat modul dimuat.
# Dipakai saat penggunanya tidak ada, supaya lama jawabannya sama persis
# dengan saat penggunanya ada tetapi sandinya salah. Selisih waktu saja
# sudah membocorkan email mana yang terdaftar.
HASH_UMPAN = _hasher.hash(secrets.token_urlsafe(32))


def hash_sandi(sandi: str) -> str:
    return _hasher.hash(sandi)


def sandi_cocok(sandi: str, hash_tersimpan: str) -> bool:
    try:
        return _hasher.verify(hash_tersimpan, sandi)
    except (VerifyMismatchError, VerificationError, InvalidHashError, TypeError):
        return False


def perlu_dihash_ulang(hash_tersimpan: str) -> bool:
    """Parameter Argon2 naik seiring waktu. Hash lama diperbarui diam diam
    saat pemiliknya masuk, bukan dibiarkan selamanya pakai parameter lama."""
    try:
        return _hasher.check_needs_rehash(hash_tersimpan)
    except InvalidHashError:
        return True


def ringkas(nilai: str) -> str:
    """SHA-256, dipakai untuk refresh token dan alamat IP.

    Refresh token tidak pernah disimpan apa adanya: basis data yang bocor
    tidak boleh memberi siapa pun kunci masuk.
    """
    return hashlib.sha256(nilai.encode("utf-8")).hexdigest()


def refresh_token_baru() -> str:
    return secrets.token_urlsafe(48)


def buat_access_token(
    pengguna_id: str,
    peran: str,
    sesi_id: str | None = None,
    faktor_kedua: bool = False,
) -> tuple[str, int]:
    """Umurnya pendek dengan sengaja. Bab 15.10.

    Umur pendek dulu satu satunya pembatas kerusakan kalau token ini bocor,
    sebab JWT diperiksa dengan tanda tangannya sendiri dan tidak pernah
    ditanyakan ke basis data. Sejak 19 September 2026 ada yang kedua: `sid`
    membawa id sesinya, dan tiap permintaan memeriksanya terhadap daftar
    cabut di Redis. Lihat backend/core/cabut.py.

    `f2` mencatat apakah sesi ini lahir lewat faktor kedua. Ia dibawa di
    dalam token, bukan disimpulkan ulang tiap permintaan, sebab yang benar
    adalah keadaan saat orangnya masuk: menyalakan TOTP sesudah masuk tidak
    boleh diam diam menguatkan sesi yang sudah terbit.
    """
    atur = pengaturan()
    sekarang = dt.datetime.now(dt.timezone.utc)
    umur = atur.akses_umur_menit

    muatan = {
        "sub": pengguna_id,
        "peran": peran,
        "sid": str(sesi_id) if sesi_id else None,
        "f2": bool(faktor_kedua),
        "iss": PENERBIT,
        "aud": UNTUK,
        "iat": sekarang,
        "exp": sekarang + dt.timedelta(minutes=umur),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(muatan, atur.jwt_rahasia, algorithm=ALGORITMA), umur * 60


def baca_access_token(token: str) -> dict | None:
    """Signature, issuer, audience, dan kedaluwarsa semuanya diperiksa.

    Melewatkan salah satunya adalah cacat yang klasik: token sah dari sistem
    lain, atau token kedaluwarsa, diterima seolah masih berlaku.
    """
    atur = pengaturan()

    # Rahasia yang sedang berlaku lebih dulu, lalu yang lama kalau memang
    # sedang ada rotasi berjalan. Urutannya begitu supaya keadaan biasa, yaitu
    # tanpa rotasi, tidak membayar satu percobaan tambahan.
    #
    # Yang lama HANYA dipakai memeriksa. Tidak ada satu pun jalur yang
    # menandatangani dengannya, jadi rotasi selalu bergerak satu arah.
    for rahasia in (atur.jwt_rahasia, atur.jwt_rahasia_lama):
        if not rahasia:
            continue
        try:
            return jwt.decode(
                token,
                rahasia,
                algorithms=[ALGORITMA],
                audience=UNTUK,
                issuer=PENERBIT,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except jwt.PyJWTError:
            continue
    return None


# ------------------------------------------------- tiket faktor kedua ---

# Antara "sandinya benar" dan "sesinya terbit" ada satu keadaan yang harus
# dibawa entah di mana: penggunanya sudah membuktikan faktor pertama dan belum
# membuktikan yang kedua.
#
# Cara yang buruk dan biasa: menerbitkan sesi lalu menandainya "belum lengkap".
# Sesi itu sudah berupa kunci; apa pun yang lupa memeriksa tandanya akan
# menerimanya. Cara yang dipakai di sini: tiket terpisah, umurnya lima menit,
# dan satu satunya pintu yang menerimanya adalah pintu faktor kedua.
#
# Tiketnya JWT yang sama algoritmanya, hanya audiensnya berbeda. Audiens yang
# berbeda berarti `baca_access_token` menolaknya, dan `baca_tiket` menolak
# access token: keduanya tidak bisa tertukar, dan itu diperiksa pustakanya
# sendiri, bukan oleh satu baris if yang bisa terlupa.

UNTUK_TIKET = "hk-faktor-kedua"
TIKET_UMUR_MENIT = 5


def buat_tiket_faktor_kedua(pengguna_id: str, cara: list[str]) -> tuple[str, int]:
    atur = pengaturan()
    sekarang = dt.datetime.now(dt.timezone.utc)
    muatan = {
        "sub": pengguna_id,
        "cara": cara,
        "iss": PENERBIT,
        "aud": UNTUK_TIKET,
        "iat": sekarang,
        "exp": sekarang + dt.timedelta(minutes=TIKET_UMUR_MENIT),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(muatan, atur.jwt_rahasia, algorithm=ALGORITMA), TIKET_UMUR_MENIT * 60


def baca_tiket_faktor_kedua(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            pengaturan().jwt_rahasia,
            algorithms=[ALGORITMA],
            audience=UNTUK_TIKET,
            issuer=PENERBIT,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        return None
