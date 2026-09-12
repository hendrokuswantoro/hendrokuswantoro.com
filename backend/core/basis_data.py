"""Satu kolam koneksi untuk seluruh proses.

Membuka koneksi per permintaan adalah cara paling gampang membuat API yang
cepat jadi lambat: sambungan TCP plus autentikasi tiap kali, dan basis data
kehabisan slot begitu ada sedikit lalu lintas.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from backend.core.konfigurasi import pengaturan

_kolam: AsyncConnectionPool | None = None


async def buka() -> None:
    global _kolam
    if _kolam is not None:
        return
    atur = pengaturan()
    _kolam = AsyncConnectionPool(
        atur.dsn,
        min_size=atur.kolam_min,
        max_size=atur.kolam_maks,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    await _kolam.open(wait=True, timeout=10)


async def tutup() -> None:
    global _kolam
    if _kolam is not None:
        await _kolam.close()
        _kolam = None


@asynccontextmanager
async def koneksi():
    if _kolam is None:
        raise RuntimeError("kolam basis data belum dibuka")
    async with _kolam.connection() as sambung:
        yield sambung
