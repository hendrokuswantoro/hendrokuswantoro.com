"""Halaman keamanan akun: verifikasi email, TOTP, kode pemulihan, jejak.

Semua yang di sini menuntut sesi admin yang sudah lengkap. Menyalakan atau
mematikan faktor kedua adalah perubahan pada jalan masuk itu sendiri, dan
perubahan semacam itu tidak boleh bisa dilakukan oleh tiket yang baru
melewati faktor pertama.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.api.tergantung import alamat_teringkas, butuh_admin
from backend.core import rahasia, surat
from backend.core.konfigurasi import pengaturan
from backend.layanan import keamanan as lapis

rute = APIRouter(prefix="/keamanan", tags=["keamanan"])


def _asal(permintaan: Request) -> str:
    """Alamat situs untuk ditaruh di dalam surat.

    Diambil dari daftar asal yang diizinkan, BUKAN dari header Origin
    permintaannya. Header itu datang dari peramban, jadi memercayainya berarti
    membiarkan penyerang memilih sendiri alamat tautan verifikasi yang
    dikirimkan ke kotak surat pemilik akun.
    """
    izin = pengaturan().asal_diizinkan
    return izin[-1] if izin else "https://www.hendrokuswantoro.com"


@rute.get("", summary="Keadaan keamanan akun")
async def keadaan(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    baris = await lapis.keadaan_akun(pengguna["id"])
    if not baris:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
    return {
        "email": baris["email"],
        "email_terverifikasi": baris["email_terverifikasi_pada"] is not None,
        "email_terverifikasi_pada": baris["email_terverifikasi_pada"],
        "totp_terpasang": baris["totp_terpasang"],
        "totp_aktif": baris["totp_aktif_pada"] is not None,
        "punya_sandi": baris["punya_sandi"],
        "passkey": baris["passkey"],
        "pemulihan_sisa": baris["pemulihan_sisa"],
        # Dua keadaan lingkungan yang jujur disebut, bukan disembunyikan.
        # Tombol yang selalu ada lalu selalu gagal lebih buruk daripada
        # tombol yang menjelaskan kenapa ia belum bisa dipakai.
        "surat_siap": surat.siap(),
        "kunci_kolom_siap": rahasia.siap(),
    }


# ------------------------------------------------------- verifikasi email ---


@rute.post("/email/kirim", summary="Kirim ulang tautan verifikasi email")
async def kirim_verifikasi(
    permintaan: Request,
    pengguna: Annotated[dict, Depends(butuh_admin)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    if not penuh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
    try:
        hasil = await lapis.kirim_verifikasi_email(penuh, _asal(permintaan), alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(ditolak)
        ) from ditolak
    return {"terkirim": hasil.terkirim, "catatan": hasil.catatan}


class Tautan(BaseModel):
    token: str = Field(min_length=10, max_length=200)


@rute.post("/email/konfirmasi", summary="Buka tautan verifikasi email")
async def konfirmasi(
    isian: Tautan,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    """Sengaja TIDAK menuntut sesi.

    Tautan verifikasi dibuka dari kotak surat, sering di perangkat lain yang
    belum pernah masuk. Menuntut sesi di sini berarti menuntut orang masuk
    lebih dulu untuk membuktikan email yang justru dipakai memulihkan akses.

    Yang menjaganya token itu sendiri: 32 bita dari `secrets`, sekali pakai,
    hidup 24 jam, dan yang tersimpan hanya sha256-nya.
    """
    try:
        pengguna = await lapis.selesaikan_verifikasi_email(isian.token, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    return {"email": pengguna["email"], "terverifikasi": True}


# ------------------------------------------------------------------ TOTP ---


@rute.post("/totp/mulai", summary="Buat rahasia TOTP baru")
async def totp_mulai(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    if not penuh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
    try:
        return await lapis.mulai_totp(penuh)
    except lapis.BelumSiap as belum:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(belum)
        ) from belum


class KodeTotp(BaseModel):
    kode: str = Field(min_length=6, max_length=10)


@rute.post("/totp/aktifkan", summary="Aktifkan TOTP dan cetak kode pemulihan")
async def totp_aktifkan(
    isian: KodeTotp,
    pengguna: Annotated[dict, Depends(butuh_admin)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    try:
        kode = await lapis.aktifkan_totp(penuh, isian.kode, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    return {
        "aktif": True,
        "kode_pemulihan": kode,
        "catatan": (
            "Delapan kode ini ditampilkan sekali saja. Yang tersimpan di server "
            "hanya sidiknya, jadi tidak ada siapa pun yang bisa menunjukkannya lagi, "
            "termasuk saya. Simpan di tempat yang bukan ponsel yang sama."
        ),
    }


@rute.post("/totp/matikan", summary="Matikan TOTP")
async def totp_matikan(
    isian: KodeTotp,
    pengguna: Annotated[dict, Depends(butuh_admin)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    try:
        await lapis.matikan_totp(penuh, isian.kode, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    return {"aktif": False}


# --------------------------------------------------------------- peristiwa --


@rute.get("/peristiwa", summary="Aktivitas keamanan terakhir")
async def peristiwa(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return {"peristiwa": await lapis.jejak(pengguna["id"])}
