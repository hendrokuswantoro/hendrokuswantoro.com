"""Menjalankan API.

    python backend/jalan.py
    python backend/jalan.py --reload

Kenapa tidak langsung `uvicorn backend.main:aplikasi`: di Windows uvicorn
membuat `ProactorEventLoop` secara eksplisit, dan psycopg menolak bekerja di
atasnya. Gagalnya berbentuk `PoolTimeout: pool initialization incomplete`
yang tidak menyebut sebabnya sama sekali, jadi mudah disalahkan ke basis
datanya, bukan ke event loop-nya.

Berkas ini membuat loop-nya sendiri lebih dulu lalu menyuruh uvicorn memakai
yang sudah ada (`loop="none"`). Di Linux, tempat ini benar benar berjalan
nanti, tidak ada bedanya dengan memanggil uvicorn langsung.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--host", default="127.0.0.1")
    alasan.add_argument("--port", type=int, default=8000)
    alasan.add_argument("--reload", action="store_true")
    pilihan = alasan.parse_args()

    if pilihan.reload:
        # jalur reload memakai subproses, dan di jalur itu uvicorn sendiri
        # sudah memilih SelectorEventLoop
        uvicorn.run(
            "backend.main:aplikasi",
            host=pilihan.host, port=pilihan.port, reload=True,
            reload_dirs=[str(AKAR / "backend")],
        )
        return 0

    atur = uvicorn.Config(
        "backend.main:aplikasi",
        host=pilihan.host, port=pilihan.port,
        loop="none",          # pakai loop yang sudah dibuat di atas
        access_log=False,     # kami mencatat sendiri, terstruktur, di core/catat.py
    )
    return 0 if asyncio.run(uvicorn.Server(atur).serve()) is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
