"""Kesehatan sistem. Tipis, tetapi tetap lewat lapisannya sendiri supaya
router tidak pernah memanggil repositori langsung."""

from __future__ import annotations

from backend.repositori import kesehatan as repo


async def basis_data_sehat() -> bool:
    return await repo.sehat()
