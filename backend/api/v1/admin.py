"""Jalur admin. Seluruhnya di belakang butuh_admin.

Bab 15.9: otorisasi diverifikasi di backend, tanpa pengecualian. Tidak ada
satu pun rute di berkas ini yang bisa dicapai tanpa token beperan admin.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.tergantung import butuh_admin, butuh_admin_kuat
from backend.layanan import pratinjau as layanan_pratinjau
from backend.layanan import tulis as layanan
from backend.skema.tulis import PANJANG_ISI, TulisanMasuk, TulisanUbah

# butuh_admin_kuat, bukan butuh_admin: seluruh rute di berkas ini mengubah
# isi situs, dan permukaan itu menuntut sesi yang lahir lewat faktor kedua.
# Halaman keamanan sengaja TIDAK memakainya, supaya faktor keduanya masih bisa
# dipasang oleh orang yang belum punya.
rute = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(butuh_admin_kuat)]
)


class UbahStatus(BaseModel):
    status: Literal["draf", "terbit", "arsip"]


class Pratinjau(BaseModel):
    """Dua bahasa sekaligus, sebab yang diperiksa justru kesebangunannya."""

    isi_en: str = Field(default="", max_length=PANJANG_ISI)
    isi_id: str = Field(default="", max_length=PANJANG_ISI)


def _ke_http(galat: Exception) -> HTTPException:
    if isinstance(galat, layanan.TidakAda):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tulisan tidak ada")
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(galat))


@rute.get("/blog", summary="Semua tulisan, termasuk draf")
async def daftar() -> dict:
    isi = await layanan.daftar_semua()
    return {"jumlah": len(isi), "isi": isi}


@rute.get("/blog/{slug}", summary="Satu tulisan, termasuk draf")
async def satu(slug: str) -> dict:
    try:
        return await layanan.satu(slug)
    except layanan.TidakAda as galat:
        raise _ke_http(galat) from galat


@rute.post("/blog", status_code=status.HTTP_201_CREATED, summary="Tulisan baru, status draf")
async def buat(
    masuk: TulisanMasuk,
    pengguna: Annotated[dict, Depends(butuh_admin_kuat)],
) -> dict:
    try:
        return await layanan.buat(masuk.model_dump(), pengguna["id"])
    except (layanan.Ditolak, layanan.TidakAda) as galat:
        raise _ke_http(galat) from galat


@rute.patch("/blog/{slug}", summary="Sunting sebagian")
async def ubah(slug: str, perubahan: TulisanUbah) -> dict:
    try:
        return await layanan.ubah(slug, perubahan.model_dump(exclude_none=True))
    except (layanan.Ditolak, layanan.TidakAda) as galat:
        raise _ke_http(galat) from galat


@rute.post("/blog/{slug}/status", summary="Ubah status terbit")
async def ubah_status(slug: str, permintaan: UbahStatus) -> dict:
    try:
        return await layanan.ubah_status(slug, permintaan.status)
    except (layanan.Ditolak, layanan.TidakAda) as galat:
        raise _ke_http(galat) from galat


@rute.post("/pratinjau", summary="Markah jadi HTML, dengan pembangkit situsnya sendiri")
async def pratinjau(permintaan: Pratinjau) -> dict:
    """Menjawab 200 dengan HTML-nya, atau 422 dengan alasan yang sama persis
    dengan alasan yang akan dipakai Simpan menolaknya.

    Satu pengurai untuk pratinjau dan penyimpanan, bukan dua. Dua pengurai
    untuk satu bahasa markah akan berpisah, dan yang berpisah diam diam
    membuat layar pratinjau berbohong.
    """
    try:
        return layanan_pratinjau.bangun(permintaan.isi_en, permintaan.isi_id)
    except layanan_pratinjau.Ditolak as galat:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(galat)
        ) from galat


@rute.delete("/blog/{slug}", status_code=status.HTTP_204_NO_CONTENT, summary="Hapus tulisan")
async def hapus(slug: str) -> None:
    try:
        await layanan.hapus(slug)
    except layanan.TidakAda as galat:
        raise _ke_http(galat) from galat
