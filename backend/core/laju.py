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


AWALAN_MASUK = "/api/v1/auth/"


def _kunci(alamat: str, golongan: str = "laju") -> str:
    ringkas = hashlib.sha256(_GARAM + alamat.encode("utf-8")).hexdigest()[:32]
    return f"{golongan}:{ringkas}"


async def _hitung(r, kunci: str, jendela: int) -> int:
    jumlah = await r.incr(kunci)
    if jumlah == 1:
        await r.expire(kunci, jendela)
    return jumlah


def _terlalu_banyak(jendela: int) -> JSONResponse:
    return JSONResponse(
        {"galat": "terlalu banyak permintaan"},
        status_code=429,
        headers={"Retry-After": str(jendela)},
    )


class BatasiLaju(BaseHTTPMiddleware):
    async def dispatch(self, permintaan: Request, lanjut):
        atur = pengaturan()
        alamat = permintaan.client.host if permintaan.client else ""

        if not alamat:
            return await lanjut(permintaan)

        r = await klien()
        if r is None:
            return await lanjut(permintaan)

        jendela = atur.laju_jendela_detik
        masuk = permintaan.url.path.startswith(AWALAN_MASUK)
        try:
            jumlah = await _hitung(r, _kunci(alamat), jendela)
            jumlah_masuk = await _hitung(r, _kunci(alamat, "laju-masuk"), jendela) if masuk else 0
        except Exception:
            return await lanjut(permintaan)

        if jumlah > atur.laju_jumlah or jumlah_masuk > atur.laju_masuk_jumlah:
            return _terlalu_banyak(jendela)
        return await lanjut(permintaan)
