from __future__ import annotations

import hashlib
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.konfigurasi import pengaturan

_GARAM = secrets.token_bytes(16)

_redis = None


async def klien():
    global _redis
    if _redis is None:
        atur = pengaturan()
        if not atur.redis_url:
            return None
        import redis.asyncio as redis_async

        _redis = redis_async.from_url(atur.redis_url, socket_connect_timeout=2)
    return _redis


def _kunci(alamat: str) -> str:
    ringkas = hashlib.sha256(_GARAM + alamat.encode("utf-8")).hexdigest()[:32]
    return f"laju:{ringkas}"


class BatasiLaju(BaseHTTPMiddleware):
    async def dispatch(self, permintaan: Request, lanjut):
        atur = pengaturan()
        alamat = permintaan.client.host if permintaan.client else ""

        if not alamat:
            return await lanjut(permintaan)

        r = await klien()
        if r is None:
            return await lanjut(permintaan)

        kunci = _kunci(alamat)
        try:
            jumlah = await r.incr(kunci)
            if jumlah == 1:
                await r.expire(kunci, atur.laju_jendela_detik)
        except Exception:
            return await lanjut(permintaan)

        if jumlah > atur.laju_jumlah:
            return JSONResponse(
                {"galat": "terlalu banyak permintaan"},
                status_code=429,
                headers={"Retry-After": str(atur.laju_jendela_detik)},
            )
        return await lanjut(permintaan)
