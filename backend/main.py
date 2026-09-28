from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager, suppress

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import pathlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request

from backend.api.v1 import (admin, auth, berkas, keamanan, kesehatan, passkey,
                            peta, proyek, tulisan)
from backend.core import basis_data
from backend.core.catat import CatatPermintaan, pasang
from backend.core.csp_admin import kebijakan as kebijakan_admin
from backend.core.konfigurasi import pengaturan
from backend.core.laju import BatasiLaju
from backend.core.tanpa_simpan import TanpaSimpan
from backend.layanan import pembersihan


@asynccontextmanager
async def daur(app: FastAPI):
    atur = pengaturan()
    tugas = None
    if atur.siap:
        await basis_data.buka()
        tugas = asyncio.create_task(pembersihan.ulangi())
    pasang().info("mulai", extra={"tambahan": {"basis_data": atur.siap}})
    yield
    if tugas is not None:
        tugas.cancel()
        with suppress(asyncio.CancelledError):
            await tugas
    await basis_data.tutup()


def buat() -> FastAPI:
    atur = pengaturan()

    dokumen = os.environ.get("DOKUMEN_API") == "1"

    app = FastAPI(
        title="hendrokuswantoro.com",
        version="1.0.0",
        summary="API isi dan spasial untuk situs pribadi Hendro Kuswantoro",
        lifespan=daur,
        docs_url="/docs" if dokumen else None,
        redoc_url="/redoc" if dokumen else None,
        openapi_url="/openapi.json" if dokumen else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=atur.asal_diizinkan,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(BatasiLaju)
    app.add_middleware(TanpaSimpan)
    app.add_middleware(CatatPermintaan)

    app.include_router(kesehatan.rute)
    for bagian in (tulisan.rute, proyek.rute, peta.rute, auth.rute,
                   passkey.rute, keamanan.rute, admin.rute, berkas.rute):
        app.include_router(bagian, prefix="/api/v1")

    class Unggahan(StaticFiles):
        def file_response(self, *a, **k):  # type: ignore[override]
            jawaban = super().file_response(*a, **k)
            jawaban.headers["X-Content-Type-Options"] = "nosniff"
            jawaban.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return jawaban

    from backend.layanan.berkas import folder as folder_unggahan

    app.mount("/unggahan", Unggahan(directory=folder_unggahan()), name="unggahan")

    NEXT_ADMIN = pathlib.Path(__file__).resolve().parent.parent / "next" / "out"
    HTML_ADMIN = pathlib.Path(__file__).resolve().parent / "admin" / "index.html"

    pakai_next = os.environ.get("ADMIN_NEXT") == "1" and (NEXT_ADMIN / "admin" / "index.html").exists()

    if pakai_next:
        app.mount("/_next", StaticFiles(directory=NEXT_ADMIN / "_next"), name="next")

    @app.get("/admin", include_in_schema=False)
    async def dashboard() -> FileResponse:
        kepala = {"X-Robots-Tag": "noindex, nofollow"}
        if pakai_next:
            berkas = NEXT_ADMIN / "admin" / "index.html"
            kepala["X-HK-CSP"] = kebijakan_admin(berkas.read_text(encoding="utf-8"))
        else:
            berkas = HTML_ADMIN
        return FileResponse(berkas, headers=kepala)

    HURUF = HTML_ADMIN.parent.parent.parent / "assets" / "fonts"
    ASET_ADMIN = {
        "dasbor.css": (HTML_ADMIN.parent / "dasbor.css", "text/css; charset=utf-8"),
        "dasbor-inti.js": (HTML_ADMIN.parent / "dasbor-inti.js", "application/javascript; charset=utf-8"),
        "dasbor-panel.js": (HTML_ADMIN.parent / "dasbor-panel.js", "application/javascript; charset=utf-8"),
        "dasbor-penyunting.js": (
            HTML_ADMIN.parent / "dasbor-penyunting.js", "application/javascript; charset=utf-8"
        ),
        "dasbor.js": (HTML_ADMIN.parent / "dasbor.js", "application/javascript; charset=utf-8"),
        "poppins-400.woff2": (HURUF / "poppins-v24-400-latin.woff2", "font/woff2"),
        "poppins-600.woff2": (HURUF / "poppins-v24-600-latin.woff2", "font/woff2"),
        "poppins-700.woff2": (HURUF / "poppins-v24-700-latin.woff2", "font/woff2"),
    }

    @app.get("/admin/{nama}", include_in_schema=False)
    async def aset_dashboard(nama: str):
        pilihan = ASET_ADMIN.get(nama)
        if pilihan is None or not pilihan[0].is_file():
            raise HTTPException(status_code=404, detail="tidak ada")
        berkas, tipe = pilihan
        return FileResponse(
            berkas,
            media_type=tipe,
            headers={
                "X-Robots-Tag": "noindex, nofollow",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-cache",
            },
        )

    @app.exception_handler(Exception)
    async def galat_tak_terduga(permintaan: Request, galat: Exception):
        pasang().error(
            "galat tak terduga",
            extra={"tambahan": {"jalur": permintaan.url.path, "jenis": type(galat).__name__}},
        )
        return JSONResponse({"galat": "kesalahan di server"}, status_code=500)

    return app


aplikasi = buat()
