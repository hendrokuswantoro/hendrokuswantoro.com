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
import errno
import pathlib
import socket
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
        uvicorn.run(
            "backend.main:aplikasi",
            host=pilihan.host, port=pilihan.port, reload=True,
            reload_dirs=[str(AKAR / "backend")],
        )
        return 0

    atur = uvicorn.Config(
        "backend.main:aplikasi",
        host=pilihan.host, port=pilihan.port,
        loop="none",
        access_log=False,
    )

    soket = _soket_loopback(pilihan.host, pilihan.port)
    return 0 if asyncio.run(uvicorn.Server(atur).serve(sockets=soket)) is None else 1


def _soket_loopback(inang: str, porta: int) -> list[socket.socket] | None:
    if inang not in ("127.0.0.1", "localhost", "::1", "[::1]"):
        return None

    dibuka: list[socket.socket] = []
    for keluarga, alamat in ((socket.AF_INET, ("127.0.0.1", porta)),
                             (socket.AF_INET6, ("::1", porta))):
        try:
            s = socket.socket(keluarga, socket.SOCK_STREAM)
            if sys.platform == "win32":
                s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(alamat)
            s.listen(128)
            s.set_inheritable(True)
            dibuka.append(s)
        except OSError as galat:
            if galat.errno == errno.EADDRINUSE or getattr(galat, "winerror", None) == 10048:
                for lain in dibuka:
                    lain.close()
                raise SystemExit(
                    f"jalan.py: porta {porta} sudah dipakai. Dashboard mungkin sudah menyala; "
                    f"buka http://localhost:{porta}/admin"
                ) from galat

    if not dibuka:
        return None
    print(f"jalan.py: mendengarkan {len(dibuka)} loopback di porta {porta}")
    return dibuka


if __name__ == "__main__":
    raise SystemExit(main())
