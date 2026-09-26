from __future__ import annotations

from typing import Any

from backend.repositori import tulis as repo


class Ditolak(Exception):
    pass


class TidakAda(Exception):
    pass


STATUS_SAH = {"draf", "terbit", "arsip"}


async def buat(nilai: dict[str, Any], penulis_id: str) -> dict[str, Any]:
    if await repo.ada(nilai["slug"]):
        raise Ditolak(f"slug {nilai['slug']} sudah dipakai tulisan lain")
    return await repo.buat(nilai, penulis_id)


async def ubah(slug: str, nilai: dict[str, Any]) -> dict[str, Any]:
    if not await repo.ada(slug):
        raise TidakAda(slug)

    if "tanggal" in nilai:
        nilai = {**nilai, "terbit_pada": nilai.pop("tanggal")}

    hasil = await repo.ubah(slug, nilai)
    if hasil is None:
        raise Ditolak("tidak ada kolom yang bisa diubah")
    return hasil


async def ubah_status(slug: str, status: str) -> dict[str, Any]:
    if status not in STATUS_SAH:
        raise Ditolak(f"status {status} tidak dikenal")
    if not await repo.ada(slug):
        raise TidakAda(slug)

    hasil = await repo.ubah_status(slug, status)
    if hasil is None:
        raise TidakAda(slug)
    return hasil


async def hapus(slug: str) -> None:
    if not await repo.hapus(slug):
        raise TidakAda(slug)


async def satu(slug: str) -> dict[str, Any]:
    baris = await repo.satu(slug)
    if baris is None:
        raise TidakAda(slug)
    return baris


async def daftar_semua() -> list[dict[str, Any]]:
    return await repo.daftar_semua()
