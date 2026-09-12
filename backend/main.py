"""API hendrokuswantoro.com.

    uvicorn backend.main:aplikasi --reload --port 8000

Dokumentasi OpenAPI otomatis ada di /docs.

Lapisannya, dari luar ke dalam:

    Router (backend/api)      HTTP, kode status, parameter
      -> Schema (backend/skema)    validasi masuk dan keluar, Pydantic
      -> Service (backend/layanan) aturan bisnis, tidak tahu SQL
      -> Repository (backend/repositori)  satu satunya yang tahu SQL
      -> PostgreSQL + PostGIS

Pemisahan itu baru ada artinya kalau ditegakkan. Ada uji yang menolak kalau
SQL muncul di luar lapisan repositori.
"""

from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

# psycopg menolak ProactorEventLoop, yang jadi bawaan Windows sejak 3.8, dan
# gagalnya berbentuk PoolTimeout yang tidak menyebut sebabnya sama sekali.
# Hanya berlaku di mesin pengembangan: di Linux, tempat ini benar benar jalan,
# baris ini tidak melakukan apa apa.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from backend.api.v1 import kesehatan, peta, proyek, tulisan
from backend.core import basis_data
from backend.core.catat import CatatPermintaan, pasang
from backend.core.konfigurasi import pengaturan
from backend.core.laju import BatasiLaju


@asynccontextmanager
async def daur(app: FastAPI):
    atur = pengaturan()
    if atur.siap:
        await basis_data.buka()
    pasang().info("mulai", extra={"tambahan": {"basis_data": atur.siap}})
    yield
    await basis_data.tutup()


def buat() -> FastAPI:
    atur = pengaturan()

    app = FastAPI(
        title="hendrokuswantoro.com",
        version="1.0.0",
        summary="API isi dan spasial untuk situs pribadi Hendro Kuswantoro",
        lifespan=daur,
    )

    # bab 15.11: CORS disebut satu satu, tidak pernah '*'
    app.add_middleware(
        CORSMiddleware,
        allow_origins=atur.asal_diizinkan,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(BatasiLaju)
    app.add_middleware(CatatPermintaan)

    app.include_router(kesehatan.rute)
    for bagian in (tulisan.rute, proyek.rute, peta.rute):
        app.include_router(bagian, prefix="/api/v1")

    @app.exception_handler(Exception)
    async def galat_tak_terduga(permintaan: Request, galat: Exception):
        """Bab 15.11: galat tidak pernah membocorkan isi dalamnya ke pemanggil.

        Yang dikirim keluar hanya kalimat umum. Rinciannya masuk log, tempat
        yang memang untuk itu.
        """
        pasang().error(
            "galat tak terduga",
            extra={"tambahan": {"jalur": permintaan.url.path, "jenis": type(galat).__name__}},
        )
        return JSONResponse({"galat": "kesalahan di server"}, status_code=500)

    return app


aplikasi = buat()
