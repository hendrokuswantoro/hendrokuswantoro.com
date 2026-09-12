"""Masuk, perpanjang, keluar.

Refresh token hidup di cookie HttpOnly Secure SameSite=Strict, bukan di
badan jawaban. Bab 15.10. Token yang bisa dibaca JavaScript adalah token
yang bisa diambil satu XSS.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from backend.api.tergantung import alamat_teringkas, butuh_admin
from backend.core.konfigurasi import pengaturan
from backend.layanan import autentikasi as layanan

rute = APIRouter(prefix="/auth", tags=["auth"])

NAMA_COOKIE = "hk_refresh"


class Kredensial(BaseModel):
    email: EmailStr
    sandi: str = Field(min_length=8, max_length=200)


class JawabanMasuk(BaseModel):
    akses: str
    umur_detik: int
    nama: str
    peran: str


def _pasang_cookie(jawaban: Response, hasil: layanan.Masuk) -> None:
    atur = pengaturan()
    jawaban.set_cookie(
        NAMA_COOKIE,
        hasil.refresh,
        httponly=True,
        secure=atur.cookie_aman,
        samesite="strict",
        expires=hasil.refresh_kadaluarsa,
        path="/api/v1/auth",
    )


def _wajib_siap() -> None:
    if not pengaturan().auth_siap:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="autentikasi belum dikonfigurasi",
        )


@rute.post("/login", response_model=JawabanMasuk, summary="Masuk sebagai admin")
async def login(
    kredensial: Kredensial,
    jawaban: Response,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> JawabanMasuk:
    _wajib_siap()
    try:
        hasil = await layanan.masuk(kredensial.email, kredensial.sandi, alamat)
    except layanan.Ditolak as ditolak:
        # 429 kalau terkunci, 401 kalau salah. Keduanya tidak pernah
        # menyebut apakah emailnya terdaftar.
        kode = status.HTTP_429_TOO_MANY_REQUESTS if ditolak.terkunci else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=kode, detail=str(ditolak)) from ditolak

    _pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


@rute.post("/refresh", response_model=JawabanMasuk, summary="Putar refresh token")
async def refresh(permintaan: Request, jawaban: Response) -> JawabanMasuk:
    _wajib_siap()
    token = permintaan.cookies.get(NAMA_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tidak ada sesi")
    try:
        hasil = await layanan.perpanjang(token)
    except layanan.Ditolak as ditolak:
        jawaban.delete_cookie(NAMA_COOKIE, path="/api/v1/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ditolak)
        ) from ditolak

    _pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


@rute.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Keluar")
async def logout(permintaan: Request, jawaban: Response) -> None:
    token = permintaan.cookies.get(NAMA_COOKIE)
    if token:
        await layanan.keluar(token)
    jawaban.delete_cookie(NAMA_COOKIE, path="/api/v1/auth")


@rute.post("/logout-semua", summary="Keluar dari semua perangkat")
async def logout_semua(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    jumlah = await layanan.keluar_semua(pengguna["id"])
    return {"sesi_dicabut": jumlah}


@rute.get("/saya", summary="Siapa yang sedang masuk")
async def saya(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return pengguna
