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

    soket = _soket_loopback(pilihan.host, pilihan.port)
    return 0 if asyncio.run(uvicorn.Server(atur).serve(sockets=soket)) is None else 1


def _soket_loopback(inang: str, porta: int) -> list[socket.socket] | None:
    """Mendengarkan di KEDUA loopback, IPv4 dan IPv6, bukan salah satu.

    Kenapa ini ada, dan ongkosnya sudah dibayar sekali.

    Di Windows, `localhost` menunjuk `::1` lebih dulu, baru `127.0.0.1`.
    Server yang hanya mengikat 127.0.0.1 tetap bisa dibuka lewat localhost,
    tetapi tiap permintaan menunggu percobaan IPv6 gagal dulu. Terukur di
    mesin ini:

        http://127.0.0.1:PORT/health      16 ms
        http://localhost:PORT/health    2050 ms

    Dua detik, pada setiap permintaan, termasuk yang tidak menyentuh basis
    data sama sekali. Dan ini bukan soal kenyamanan: WebAuthn MENUNTUT nama
    domain, jadi halaman admin hanya bisa dibuka lewat `localhost`, tepat di
    jalur yang lambat itu. Sebuah dashboard yang memuat tujuh permintaan
    berarti empat belas detik menunggu, dan itu yang membuat alur masuk
    passkey tampak menggantung tanpa sebab.

    Mengikat `::1` saja menukar masalahnya, bukan menyelesaikannya: yang
    membuka 127.0.0.1 lalu yang menunggu dua detik. Jadi keduanya dibuka.

    Hanya berlaku untuk alamat loopback. Host lain diserahkan apa adanya ke
    uvicorn, sebab mengikat lebih banyak daripada yang diminta pada alamat
    yang menghadap jaringan adalah keputusan keamanan, bukan penyetelan
    kecepatan.
    """
    if inang not in ("127.0.0.1", "localhost", "::1", "[::1]"):
        return None

    dibuka: list[socket.socket] = []
    for keluarga, alamat in ((socket.AF_INET, ("127.0.0.1", porta)),
                             (socket.AF_INET6, ("::1", porta))):
        try:
            s = socket.socket(keluarga, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(alamat)
            s.listen(128)
            s.set_inheritable(True)
            dibuka.append(s)
        except OSError:
            # Satu tumpukan yang tidak tersedia bukan alasan gagal jalan.
            pass

    if not dibuka:
        return None
    print(f"jalan.py: mendengarkan {len(dibuka)} loopback di porta {porta}")
    return dibuka


if __name__ == "__main__":
    raise SystemExit(main())
