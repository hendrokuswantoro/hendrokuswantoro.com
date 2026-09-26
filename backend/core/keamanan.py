from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend.core.konfigurasi import pengaturan

_hasher = PasswordHasher()

ALGORITMA = "HS256"
PENERBIT = "hendrokuswantoro.com"
UNTUK = "hendrokuswantoro.com/admin"


HASH_UMPAN = _hasher.hash(secrets.token_urlsafe(32))


def hash_sandi(sandi: str) -> str:
    return _hasher.hash(sandi)


def sandi_cocok(sandi: str, hash_tersimpan: str) -> bool:
    try:
        return _hasher.verify(hash_tersimpan, sandi)
    except (VerifyMismatchError, VerificationError, InvalidHashError, TypeError):
        return False


def perlu_dihash_ulang(hash_tersimpan: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hash_tersimpan)
    except InvalidHashError:
        return True


def ringkas(nilai: str) -> str:
    return hashlib.sha256(nilai.encode("utf-8")).hexdigest()


def refresh_token_baru() -> str:
    return secrets.token_urlsafe(48)


def buat_access_token(
    pengguna_id: str,
    peran: str,
    sesi_id: str | None = None,
    faktor_kedua: bool = False,
) -> tuple[str, int]:
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
    atur = pengaturan()

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
