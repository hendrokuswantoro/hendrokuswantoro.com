from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.layanan import proyek as layanan
from backend.skema.proyek import DaftarProyek, Kategori, Proyek

rute = APIRouter(prefix="/projects", tags=["proyek"])


@rute.get("", response_model=DaftarProyek, summary="Daftar proyek")
async def daftar(
    batas: int = Query(20, ge=1, le=100),
    lewati: int = Query(0, ge=0),
    kategori: Kategori | None = Query(None),
) -> DaftarProyek:
    return await layanan.daftar(batas, lewati, kategori)


@rute.get("/{slug}", response_model=Proyek, summary="Satu proyek")
async def satu(slug: str) -> Proyek:
    hasil = await layanan.satu(slug)
    if hasil is None:
        raise HTTPException(status_code=404, detail="proyek tidak ada")
    return hasil
