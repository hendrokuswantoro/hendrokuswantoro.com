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

    # Dokumentasi interaktif tertutup kecuali diminta.
    #
    # /docs, /redoc, dan /openapi.json menyerahkan seluruh permukaan API kepada
    # siapa pun yang membukanya, termasuk nama tiap titik akhir admin dan
    # bentuk persis badan permintaannya. Itu bukan kerentanan dengan
    # sendirinya, dan bukan pula rahasia yang menjaga apa apa; yang menjaga
    # tetap token. Tetapi ia memberi peta lengkap secara cuma cuma kepada
    # orang yang tidak punya urusan di sana, dan tidak ada gunanya bagi
    # pengunjung situs.
    #
    # Di mesin pengembangan ia sangat berguna, jadi ia dinyalakan dengan
    # sengaja lewat DOKUMEN_API=1, bukan dimatikan dengan sengaja. Yang
    # bawaannya terbuka akan tetap terbuka di produksi pada hari ada yang
    # lupa mematikannya.
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
    for bagian in (tulisan.rute, proyek.rute, peta.rute, auth.rute,
                   passkey.rute, keamanan.rute, admin.rute, berkas.rute):
        app.include_router(bagian, prefix="/api/v1")

    # --- berkas yang diunggah ------------------------------------------------
    #
    # Dilayani sebagai berkas statis, bukan lewat rute yang membaca basis
    # data. Gambar di dalam tulisan diminta puluhan kali per halaman, dan
    # tiap permintaan yang melewati kolam koneksi demi mengirim bita yang
    # sudah ada di cakram adalah koneksi yang direbut dari permintaan yang
    # benar benar butuh basis data.
    #
    # Dua tajuk dipasang sendiri di sini dan tidak diserahkan ke nginx, sebab
    # jalur ini juga hidup saat dikembangkan tanpa nginx sama sekali:
    #
    #   X-Content-Type-Options: nosniff
    #       Berkasnya sudah dipastikan gambar atau video dari bita pertamanya,
    #       jadi Content-Type di sini benar. nosniff yang menjaga peramban
    #       tidak menebak yang lain kalau suatu hari pemeriksaan itu bocor.
    #   Cache-Control: immutable
    #       Namanya acak dan tidak pernah dipakai ulang untuk isi yang
    #       berbeda, jadi janji itu memang bisa dipenuhi. Berkas yang diganti
    #       isinya akan mendapat nama baru, bukan alamat yang sama.
    class Unggahan(StaticFiles):
        def file_response(self, *a, **k):  # type: ignore[override]
            jawaban = super().file_response(*a, **k)
            jawaban.headers["X-Content-Type-Options"] = "nosniff"
            jawaban.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return jawaban

    # Foldernya dibuat kalau belum ada. StaticFiles menolak berdiri di atas
    # folder yang tidak ada, dan kegagalannya terjadi saat aplikasi dibangun,
    # yaitu jauh dari orang yang lupa membuat foldernya.
    from backend.layanan.berkas import folder as folder_unggahan

    app.mount("/unggahan", Unggahan(directory=folder_unggahan()), name="unggahan")

    # --- permukaan menulis ---------------------------------------------------
    #
    # Ada dua, dan keduanya memakai API yang sama persis.
    #
    #   backend/admin/index.html  HTML biasa, tanpa langkah build
    #   next/out/admin/           versi Next.js, hasil `npm run build`
    #
    # Yang disajikan ditentukan ADMIN_NEXT. Bawaannya yang HTML, sebab ia
    # tidak menuntut apa apa: satu berkas, tidak ada Node, tidak ada langkah
    # build yang bisa lupa dijalankan. Versi Next.js dinyalakan dengan sengaja,
    # dan kalau hasil buildnya belum ada, yang HTML tetap keluar, bukan 404.
    #
    # Keduanya tidak diindeks: robots.txt situs tidak menyebutnya, dan
    # jawabannya membawa X-Robots-Tag. Yang menjaganya tetap token, bukan itu.
    NEXT_ADMIN = pathlib.Path(__file__).resolve().parent.parent / "next" / "out"
    HTML_ADMIN = pathlib.Path(__file__).resolve().parent / "admin" / "index.html"

    pakai_next = os.environ.get("ADMIN_NEXT") == "1" and (NEXT_ADMIN / "admin" / "index.html").exists()

    if pakai_next:
        # Aset Next diminta dari /_next/..., jadi jalurnya harus persis itu.
        app.mount("/_next", StaticFiles(directory=NEXT_ADMIN / "_next"), name="next")

    @app.get("/admin", include_in_schema=False)
    async def dashboard() -> FileResponse:
        berkas = (NEXT_ADMIN / "admin" / "index.html") if pakai_next else HTML_ADMIN
        return FileResponse(berkas, headers={"X-Robots-Tag": "noindex, nofollow"})

    # Gaya dan skrip dashboard HTML, sebagai berkas terpisah.
    #
    # Sampai 19 September 2026 keduanya sebaris di dalam index.html, dan
    # akibatnya dashboard mati total di balik nginx: CSP produksi untuk /admin
    # memakai script-src 'self' ditambah satu hash sha256 milik skrip tema di
    # situs publik, jadi skrip 44 KB di dalam halaman ini ditolak seluruhnya.
    # Gagalnya sunyi, tombol Masuk diam, dan jejaknya hanya di konsol.
    #
    # Dilayani dari sini, bukan dari StaticFiles yang dipasang di /admin,
    # sebab /admin sendiri harus tetap menjawab dokumen HTML-nya. Daftarnya
    # tertutup: dua nama, dipetakan tangan, jadi tidak ada satu pun jalur yang
    # datang dari pemanggil.
    #
    # Tiga huruf Poppins ikut di daftar yang sama sejak 26 September 2026,
    # diambil dari assets/fonts milik situs. Di balik nginx /assets memang
    # sudah ada, tetapi backend yang dijalankan sendiri saat mengembangkan
    # tidak menyajikannya, dan dashboard yang hurufnya berganti tergantung
    # cara menjalankannya tampak seperti dua aplikasi.
    HURUF = HTML_ADMIN.parent.parent.parent / "assets" / "fonts"
    ASET_ADMIN = {
        "dasbor.css": (HTML_ADMIN.parent / "dasbor.css", "text/css; charset=utf-8"),
        "dasbor.js": (HTML_ADMIN.parent / "dasbor.js", "application/javascript; charset=utf-8"),
        "poppins-400.woff2": (HURUF / "poppins-v24-400-latin.woff2", "font/woff2"),
        "poppins-600.woff2": (HURUF / "poppins-v24-600-latin.woff2", "font/woff2"),
        "poppins-700.woff2": (HURUF / "poppins-v24-700-latin.woff2", "font/woff2"),
    }

    @app.get("/admin/{nama}", include_in_schema=False)
    async def aset_dashboard(nama: str):
        pilihan = ASET_ADMIN.get(nama)
        # Berkas yang tidak ada di cakram dijawab 404, bukan 500. Mesin yang
        # hanya membawa backend tanpa assets/ tetap punya dashboard yang
        # jalan, dengan huruf sistem.
        if pilihan is None or not pilihan[0].is_file():
            raise HTTPException(status_code=404, detail="tidak ada")
        berkas, tipe = pilihan
        return FileResponse(
            berkas,
            media_type=tipe,
            headers={
                "X-Robots-Tag": "noindex, nofollow",
                "X-Content-Type-Options": "nosniff",
                # Tidak immutable: nama berkasnya tetap, jadi janji itu tidak
                # bisa dipenuhi. Yang dipakai revalidasi, yang murah untuk
                # halaman yang cuma dibuka pemiliknya.
                "Cache-Control": "no-cache",
            },
        )

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
