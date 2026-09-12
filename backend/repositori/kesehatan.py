"""Satu kueri, sependek mungkin, untuk membuktikan basis datanya menjawab.

Ada di lapisan repositori karena isinya SQL, dan aturannya tanpa pengecualian:
SQL hanya hidup di sini. Daftar pengecualian selalu bertambah.
"""

from __future__ import annotations

from backend.core.basis_data import koneksi


async def sehat() -> bool:
    try:
        async with koneksi() as s, s.cursor() as k:
            await k.execute("SELECT 1 AS satu")
            return (await k.fetchone())["satu"] == 1
    except Exception:
        return False
