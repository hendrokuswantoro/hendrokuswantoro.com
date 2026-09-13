"""Aturan menulis, menyunting, dan menerbitkan.

Satu aturan yang ditegakkan di sini dan tidak di mana pun lagi: tulisan hanya
boleh berpindah ke status terbit kalau tanggalnya sudah ada. Basis data juga
menahannya lewat CHECK, tetapi kalau yang menahan cuma basis data, yang
sampai ke penulis adalah 500 tanpa penjelasan, bukan kalimat yang bisa
ditindaklanjuti.
"""

from __future__ import annotations

from typing import Any

from backend.repositori import tulis as repo


class Ditolak(Exception):
    """Permintaan tulis yang tidak sah, dengan alasan yang bisa dibaca."""


class TidakAda(Exception):
    """Slug yang diminta tidak ada."""


STATUS_SAH = {"draf", "terbit", "arsip"}


async def buat(nilai: dict[str, Any], penulis_id: str) -> dict[str, Any]:
    if await repo.ada(nilai["slug"]):
        raise Ditolak(f"slug {nilai['slug']} sudah dipakai tulisan lain")
    return await repo.buat(nilai, penulis_id)


async def ubah(slug: str, nilai: dict[str, Any]) -> dict[str, Any]:
    if not await repo.ada(slug):
        raise TidakAda(slug)

    # nama kolom di basis data berbeda dari nama di skema masuk
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
    """Dipakai penyunting untuk membuka tulisan, termasuk yang masih draf.

    Sampai hari ini penyunting membuka tulisan lewat jalur publik
    /api/v1/blog/{slug}, yang hanya menjawab kalau statusnya sudah terbit.
    Akibatnya draf yang baru dibuat tidak pernah bisa dibuka lagi, dan
    satu satunya jalan keluar adalah menerbitkannya lebih dulu, yaitu
    persis kebalikan dari gunanya draf.
    """
    baris = await repo.satu(slug)
    if baris is None:
        raise TidakAda(slug)
    return baris


async def daftar_semua() -> list[dict[str, Any]]:
    return await repo.daftar_semua()
