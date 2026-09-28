from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.api.tergantung import (
    alamat_teringkas,
    butuh_admin,
    butuh_admin_kuat,
    butuh_admin_pendaftar,
)
from backend.core import cabut as daftar_cabut
from backend.core import rahasia, surat
from backend.layanan import wajah as wajah_modul
from backend.core.konfigurasi import pengaturan
from backend.layanan import kabar
from backend.layanan import keamanan as lapis

rute = APIRouter(prefix="/keamanan", tags=["keamanan"])


def _asal(permintaan: Request) -> str:
    for asal in pengaturan().asal_diizinkan:
        if asal.startswith("https://") and "localhost" not in asal and "127.0.0.1" not in asal:
            return asal
    return "https://www.hendrokuswantoro.com"


async def _pengguna_penuh(pengguna: dict) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    if not penuh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
    return penuh


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
        "wajah_terdaftar": baris["wajah_didaftar_pada"] is not None,
        "kabar_masuk": baris["kabar_masuk"],
        "kabar_perubahan": baris["kabar_perubahan"],
        "mode_ketat": baris["mode_ketat"],
        "surat_siap": surat.siap(),
        "kunci_kolom_siap": rahasia.siap(),
        "wajah_siap": wajah_modul.siap(),
        "faktor_kedua_wajib": pengaturan().faktor_kedua_wajib,
        "sesi_kuat": bool(pengguna.get("faktor_kedua")),
        "pencabutan_segera_siap": daftar_cabut.siap(),
    }


@rute.post("/email/kirim", summary="Kirim ulang tautan verifikasi email")
async def kirim_verifikasi(
    permintaan: Request,
    pengguna: Annotated[dict, Depends(butuh_admin)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await _pengguna_penuh(pengguna)
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
    try:
        pengguna = await lapis.selesaikan_verifikasi_email(isian.token, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    return {"email": pengguna["email"], "terverifikasi": True}


@rute.post("/totp/mulai", summary="Buat rahasia TOTP baru")
async def totp_mulai(pengguna: Annotated[dict, Depends(butuh_admin_pendaftar)]) -> dict:
    penuh = await _pengguna_penuh(pengguna)
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
    pengguna: Annotated[dict, Depends(butuh_admin_pendaftar)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    try:
        kode = await lapis.aktifkan_totp(penuh, isian.kode, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    await kabar.kabari_perubahan_keamanan(penuh, "authenticator dinyalakan")
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
    pengguna: Annotated[dict, Depends(butuh_admin_kuat)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    try:
        await lapis.matikan_totp(penuh, isian.kode, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak

    await kabar.kabari_perubahan_keamanan(penuh, "authenticator dimatikan")
    return {"aktif": False}


@rute.get("/peristiwa", summary="Aktivitas keamanan terakhir")
async def peristiwa(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return {"peristiwa": await lapis.jejak(pengguna["id"])}


class BingkaiWajah(BaseModel):
    bingkai: list[str] = Field(min_length=2, max_length=5)


@rute.post("/wajah/daftar", summary="Daftarkan wajah sebagai faktor kedua")
async def wajah_daftar(
    isian: BingkaiWajah,
    pengguna: Annotated[dict, Depends(butuh_admin_pendaftar)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await _pengguna_penuh(pengguna)
    try:
        hasil = await lapis.daftarkan_wajah(penuh, isian.bingkai, alamat)
    except lapis.BelumSiap as belum:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(belum)
        ) from belum
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    await kabar.kabari_perubahan_keamanan(penuh, "wajah didaftarkan")
    return hasil


@rute.post("/wajah/hapus", summary="Hapus wajah yang terdaftar")
async def wajah_hapus(
    pengguna: Annotated[dict, Depends(butuh_admin_kuat)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    penuh = await lapis.pengguna(pengguna["id"])
    await lapis.hapus_wajah(penuh, alamat)
    await kabar.kabari_perubahan_keamanan(penuh, "wajah dihapus")
    return {"terdaftar": False}


class Setelan(BaseModel):
    kabar_masuk: bool | None = None
    kabar_perubahan: bool | None = None
    mode_ketat: bool | None = None


@rute.patch("/setelan", summary="Ubah notifikasi keamanan dan mode ketat")
async def ubah_setelan(
    isian: Setelan,
    pengguna: Annotated[dict, Depends(butuh_admin_kuat)],
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    perubahan = isian.model_dump(exclude_none=True)
    try:
        ringkasan = await lapis.ubah_setelan(pengguna["id"], perubahan, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    if ringkasan:
        penuh = await _pengguna_penuh(pengguna)
        await kabar.kabari_perubahan_keamanan(penuh, ", ".join(ringkasan), paksa=True)
    return await lapis.setelan(pengguna["id"])
