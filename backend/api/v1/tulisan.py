from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.layanan import tulisan as layanan
from backend.skema.tulisan import DaftarTulisan, TulisanPenuh

rute = APIRouter(prefix="/blog", tags=["blog"])


@rute.get("", response_model=DaftarTulisan, summary="Daftar tulisan terbit")
async def daftar(
    batas: int = Query(20, ge=1, le=100),
    lewati: int = Query(0, ge=0),
) -> DaftarTulisan:
    return await layanan.daftar(batas, lewati)


@rute.get("/{slug}", response_model=TulisanPenuh, summary="Satu tulisan")
async def satu(slug: str) -> TulisanPenuh:
    hasil = await layanan.satu(slug)
    if hasil is None:
        raise HTTPException(status_code=404, detail="tulisan tidak ada")
    return hasil
