"""Titik akhir spasial. Fase 3.

Jalur datanya: PostGIS -> FastAPI -> GeoJSON -> MapLibre.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.layanan import proyek as layanan
from backend.skema.proyek import KumpulanFitur

rute = APIRouter(prefix="/maps", tags=["peta"])


@rute.get(
    "/projects-spatial",
    response_model=KumpulanFitur,
    summary="Lokasi proyek sebagai GeoJSON FeatureCollection",
)
async def projects_spatial() -> KumpulanFitur:
    """Titik ini tempat menggantungkan penanda di peta, **bukan** koordinat
    survei dan bukan batas wilayah kajian."""
    return await layanan.geojson()


@rute.get("/nearby", summary="Proyek dalam radius tertentu, jarak dalam meter")
async def dekat(
    lng: float = Query(..., ge=94, le=142, description="bujur, derajat"),
    lat: float = Query(..., ge=-12, le=7, description="lintang, derajat"),
    radius_m: int = Query(50000, ge=100, le=2_000_000),
    batas: int = Query(10, ge=1, le=50),
) -> dict:
    hasil = await layanan.dekat(lng, lat, radius_m, batas)
    return {"jumlah": len(hasil), "radius_m": radius_m, "isi": hasil}
