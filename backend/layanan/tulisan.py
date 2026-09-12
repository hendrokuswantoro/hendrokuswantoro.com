"""Aturan bisnis untuk tulisan. Lapisan ini tidak tahu SQL dan tidak tahu HTTP.

Yang dikerjakan di sini cuma satu hal yang tidak layak ada di repositori
maupun di router: mengubah baris basis data yang datar jadi bentuk
berpasangan dua bahasa yang dipakai seluruh situs.
"""

from __future__ import annotations

from typing import Any

from backend.repositori import tulisan as repo
from backend.skema.tulisan import DaftarTulisan, TulisanPenuh, TulisanRingkas
from backend.skema.umum import Teks


def _teks(baris: dict[str, Any], nama: str) -> Teks:
    return Teks(en=baris[f"{nama}_en"], id=baris[f"{nama}_id"])


def _ringkas(baris: dict[str, Any]) -> TulisanRingkas:
    return TulisanRingkas(
        slug=baris["slug"],
        tanggal=baris["terbit_pada"],
        judul=_teks(baris, "judul"),
        ringkas=_teks(baris, "ringkas"),
        tag=_teks(baris, "tag"),
        baca=_teks(baris, "baca"),
    )


async def daftar(batas: int, lewati: int) -> DaftarTulisan:
    baris = await repo.daftar(batas, lewati)
    return DaftarTulisan(
        jumlah=await repo.jumlah_terbit(),
        batas=batas,
        lewati=lewati,
        isi=[_ringkas(b) for b in baris],
    )


async def satu(slug: str) -> TulisanPenuh | None:
    baris = await repo.satu(slug)
    if baris is None:
        return None
    return TulisanPenuh(
        **_ringkas(baris).model_dump(),
        keterangan=_teks(baris, "keterangan"),
        lede=_teks(baris, "lede"),
        isi_en=baris["isi_en"],
        isi_id=baris["isi_id"],
    )
