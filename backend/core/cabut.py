from __future__ import annotations

from backend.core.konfigurasi import pengaturan

_redis = None
_gagal = False


async def _klien():
    global _redis, _gagal
    if _gagal:
        return None
    if _redis is None:
        atur = pengaturan()
        if not atur.redis_url:
            return None
        import redis.asyncio as redis_async

        _redis = redis_async.from_url(atur.redis_url, socket_connect_timeout=2)
    return _redis


def siap() -> bool:
    return bool(pengaturan().redis_url)


def _kunci(sesi_id: str) -> str:
    return f"cabut:{sesi_id}"


def _umur_detik() -> int:
    return pengaturan().akses_umur_menit * 60 + 60


async def catat(sesi_id: list[str]) -> None:
    if not sesi_id:
        return
    r = await _klien()
    if r is None:
        return
    try:
        pipa = r.pipeline()
        for satu in sesi_id:
            pipa.set(_kunci(str(satu)), "1", ex=_umur_detik())
        await pipa.execute()
    except Exception:
        return


async def sudah_dicabut(sesi_id: str | None) -> bool:
    if not sesi_id:
        return False
    r = await _klien()
    if r is None:
        return False
    try:
        return await r.exists(_kunci(str(sesi_id))) == 1
    except Exception:
        return False
