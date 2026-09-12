"""Satu satunya lapisan yang tahu SQL untuk tulisan.

Bab 15.4 memisahkan Router, Service, dan Repository. Pemisahan itu baru ada
artinya kalau SQL tidak pernah bocor ke luar berkas ini: begitu satu kueri
ditulis di lapisan layanan, seluruh pemisahannya jadi hiasan.

Semua kueri memakai parameter, tanpa pengecualian. Bab 15.11.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from backend.core.basis_data import koneksi

KOLOM = """
    slug, terbit_pada,
    judul_en, judul_id, ringkas_en, ringkas_id,
    tag_en, tag_id, baca_en, baca_id
"""

KOLOM_PENUH = KOLOM + """,
    keterangan_en, keterangan_id, lede_en, lede_id, isi_en, isi_id
"""


async def jumlah_terbit() -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("SELECT count(*) AS n FROM blog_posts WHERE status = 'terbit'")
        return (await k.fetchone())["n"]


async def daftar(batas: int, lewati: int) -> list[dict[str, Any]]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"""
            SELECT {KOLOM}
            FROM blog_posts
            WHERE status = 'terbit'
            ORDER BY terbit_pada DESC, slug
            LIMIT %s OFFSET %s
            """,
            (batas, lewati),
        )
        return await k.fetchall()


async def satu(slug: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"SELECT {KOLOM_PENUH} FROM blog_posts WHERE slug = %s AND status = 'terbit'",
            (slug,),
        )
        return await k.fetchone()


async def terbaru() -> dt.date | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT max(terbit_pada) AS t FROM blog_posts WHERE status = 'terbit'"
        )
        return (await k.fetchone())["t"]
