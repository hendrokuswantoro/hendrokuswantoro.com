from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from backend.api.tergantung import alamat_teringkas, butuh_admin
from backend.core import keamanan as inti
from backend.core.konfigurasi import pengaturan
from backend.layanan import autentikasi as layanan
from backend.layanan import kabar
from backend.layanan import keamanan as lapis

rute = APIRouter(prefix="/auth", tags=["auth"])

NAMA_COOKIE = "hk_refresh"


class Kredensial(BaseModel):
    email: EmailStr
    sandi: str = Field(min_length=8, max_length=200)


class JawabanMasuk(BaseModel):
    tahap: str = "selesai"
    akses: str = ""
    umur_detik: int = 0
    nama: str = ""
    peran: str = ""
    tiket: str = ""
    cara: list[str] = []


def pasang_cookie(jawaban: Response, hasil: layanan.Masuk) -> None:
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
    permintaan: Request,
    jawaban: Response,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> JawabanMasuk:
    _wajib_siap()
    try:
        pengguna = await layanan.periksa_sandi(kredensial.email, kredensial.sandi, alamat)
    except layanan.Ditolak as ditolak:
        kode = status.HTTP_429_TOO_MANY_REQUESTS if ditolak.terkunci else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=kode, detail=str(ditolak)) from ditolak

    peramban = permintaan.headers.get("user-agent", "")

    cara = await lapis.faktor_kedua_yang_berlaku(pengguna)

    if cara == ["passkey"] and pengaturan().faktor_kedua_wajib:
        await lapis.catat_peristiwa(
            str(pengguna["id"]), "sandi_benar", False, "akun memakai passkey",
            alamat, permintaan.headers.get("user-agent", ""),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="akun ini memakai passkey. Masuk dengan tombol passkey.",
        )
    cara = [c for c in cara if c != "passkey"]
    if cara:
        tiket, umur = inti.buat_tiket_faktor_kedua(str(pengguna["id"]), cara)
        await lapis.catat_peristiwa(
            str(pengguna["id"]), "sandi_benar", True, "menunggu faktor kedua", alamat, peramban
        )
        if cara == ["email"]:
            try:
                await lapis.kirim_otp_masuk(pengguna, alamat)
            except lapis.Ditolak:
                pass
        return JawabanMasuk(tahap="faktor2", tiket=tiket, umur_detik=umur, cara=cara)

    await kabar.kabari_masuk(pengguna, "sandi", alamat, peramban)

    hasil = await layanan.terbitkan(pengguna, faktor_kedua=False)
    pasang_cookie(jawaban, hasil)
    await lapis.catat_peristiwa(str(pengguna["id"]), "masuk", True, "sandi", alamat, peramban)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


class FaktorKedua(BaseModel):
    tiket: str
    cara: str = Field(pattern="^(totp|email|pemulihan|wajah)$")
    kode: str = Field(default="", max_length=40)
    tantangan: str = Field(default="", max_length=64)
    bingkai: list[str] = Field(default_factory=list, max_length=5)


@rute.post("/faktor-kedua", response_model=JawabanMasuk, summary="Selesaikan faktor kedua")
async def faktor_kedua(
    isian: FaktorKedua,
    permintaan: Request,
    jawaban: Response,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> JawabanMasuk:
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="tiket tidak berlaku atau sudah kedaluwarsa, ulangi dari awal",
        )

    pengguna_id = muatan["sub"]
    if isian.cara not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cara tidak tersedia")

    try:
        if isian.cara == "wajah":
            if not isian.tantangan or not isian.bingkai:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="butuh tantangan dan bingkai",
                )
            lolos = await lapis.periksa_wajah(
                pengguna_id, isian.tantangan, isian.bingkai, alamat
            )
        elif not isian.kode:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="kode kosong")
        elif isian.cara == "totp":
            lolos = await lapis.periksa_totp(pengguna_id, isian.kode, alamat)
        elif isian.cara == "email":
            lolos = await lapis.periksa_otp_masuk(pengguna_id, isian.kode, alamat)
        else:
            lolos = await lapis.periksa_pemulihan(pengguna_id, isian.kode, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(ditolak)
        ) from ditolak

    if not lolos:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="kode salah")

    pengguna = await lapis.pengguna(pengguna_id)
    if not pengguna:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="kode salah")

    await kabar.kabari_masuk(
        pengguna, isian.cara, alamat, permintaan.headers.get("user-agent", "")
    )

    hasil = await layanan.terbitkan(pengguna, faktor_kedua=(isian.cara != "wajah"))
    pasang_cookie(jawaban, hasil)
    await lapis.catat_peristiwa(
        pengguna_id, "masuk", True, isian.cara, alamat, permintaan.headers.get("user-agent", "")
    )
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


class MintaKode(BaseModel):
    tiket: str


@rute.post("/faktor-kedua/tantangan-wajah", summary="Minta urutan gerakan untuk verifikasi wajah")
async def tantangan_wajah(isian: MintaKode) -> dict:
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None or "wajah" not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")
    try:
        return await lapis.tantangan_wajah(muatan["sub"])
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak


@rute.post("/faktor-kedua/kirim-ulang", summary="Kirim ulang kode ke email")
async def kirim_ulang(
    isian: MintaKode,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None or "email" not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")

    pengguna = await lapis.pengguna(muatan["sub"])
    if not pengguna:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")
    try:
        hasil = await lapis.kirim_otp_masuk(pengguna, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(ditolak)
        ) from ditolak
    return {"terkirim": hasil.terkirim, "catatan": hasil.catatan}


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

    pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


@rute.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Keluar")
async def logout(permintaan: Request, jawaban: Response) -> None:
    token = permintaan.cookies.get(NAMA_COOKIE)
    if token:
        await layanan.keluar(token)
    jawaban.delete_cookie(NAMA_COOKIE, path="/api/v1/auth")


@rute.get("/sesi", summary="Perangkat yang sedang masuk")
async def sesi(
    permintaan: Request, pengguna: Annotated[dict, Depends(butuh_admin)]
) -> dict:
    daftar = await layanan.sesi_saya(pengguna["id"], permintaan.cookies.get(NAMA_COOKIE))
    return {"sesi": daftar, "jumlah": len(daftar)}


@rute.post("/sesi/cabut-lain", summary="Keluarkan perangkat lain, sisakan yang ini")
async def cabut_lain(
    permintaan: Request, pengguna: Annotated[dict, Depends(butuh_admin)]
) -> dict:
    jumlah = await layanan.keluar_dari_yang_lain(
        pengguna["id"], permintaan.cookies.get(NAMA_COOKIE)
    )
    return {"sesi_dicabut": jumlah}
