from __future__ import annotations

from fastapi import APIRouter, Response

from backend.core import laju
from backend.layanan import kesehatan as layanan

rute = APIRouter(tags=["kesehatan"])


@rute.get("/health", summary="Kesehatan proses, basis data, dan cache")
async def kesehatan(jawaban: Response) -> dict:
    db = await layanan.basis_data_sehat()

    cache = None
    r = await laju.klien()
    if r is not None:
        try:
            cache = bool(await r.ping())
        except Exception:
            cache = False

    sehat = db
    jawaban.status_code = 200 if sehat else 503
    return {
        "status": "sehat" if sehat else "sakit",
        "basis_data": db,
        "cache": cache,
    }
