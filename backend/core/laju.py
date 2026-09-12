"""Pembatas laju per IP, memakai Redis. Bab 15.11.

Alamat IP tidak pernah disimpan apa adanya. Yang jadi kunci adalah ringkasan
SHA-256 dari alamat itu ditambah garam acak per proses, jadi isi Redis tidak
bisa dibaca balik jadi daftar pengunjung. Pola yang sama dipakai proyek
Parkir Jogja, dengan alasan yang sama.

Kalau Redis tidak ada, permintaan diteruskan. Pembatas laju yang mematikan
situs saat cache-nya mati adalah kerugian yang lebih besar daripada yang
dicegahnya.
"""

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
            # alamat tidak diketahui tetap diizinkan: menolaknya akan
            # memblokir pengguna sah di belakang perantara
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
            # Redis mati bukan alasan menutup situs
            return await lanjut(permintaan)

        if jumlah > atur.laju_jumlah:
            return JSONResponse(
                {"galat": "terlalu banyak permintaan"},
                status_code=429,
                headers={"Retry-After": str(atur.laju_jendela_detik)},
            )
        return await lanjut(permintaan)
