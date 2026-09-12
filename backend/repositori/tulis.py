"""SQL untuk menulis tulisan. Terpisah dari repositori baca.

Yang membaca dipakai pengunjung, yang menulis hanya dipakai admin. Memisahkan
berkasnya membuat jelas mana kueri yang pernah tersentuh permintaan publik
dan mana yang tidak.
"""

from __future__ import annotations

from typing import Any

from backend.core.basis_data import koneksi

KOLOM_TULIS = (
    "judul_en", "judul_id", "ringkas_en", "ringkas_id",
    "keterangan_en", "keterangan_id", "lede_en", "lede_id",
    "isi_en", "isi_id", "tag_en", "tag_id", "baca_en", "baca_id",
)


async def ada(slug: str) -> bool:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("SELECT 1 AS ada FROM blog_posts WHERE slug = %s", (slug,))
        return await k.fetchone() is not None


async def buat(nilai: dict[str, Any], penulis_id: str) -> dict[str, Any]:
    kolom = ["slug", "terbit_pada", *KOLOM_TULIS, "penulis_id", "status"]
    isi = [nilai["slug"], nilai["tanggal"], *[nilai[k] for k in KOLOM_TULIS],
           penulis_id, "draf"]
    tanda = ", ".join(["%s"] * len(kolom))

    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"INSERT INTO blog_posts ({', '.join(kolom)}) VALUES ({tanda}) "
            "RETURNING slug, status, terbit_pada, dibuat_pada",
            isi,
        )
        return await k.fetchone()


async def ubah(slug: str, nilai: dict[str, Any]) -> dict[str, Any] | None:
    """Hanya kolom yang disebut yang diubah.

    Nama kolomnya tidak pernah datang dari pemanggil: yang boleh diubah
    disaring lebih dulu terhadap daftar tetap di berkas ini. Nama kolom
    dinamis dari luar adalah injeksi SQL yang menunggu giliran.
    """
    boleh = {*KOLOM_TULIS, "terbit_pada"}
    bagian = {k: v for k, v in nilai.items() if k in boleh}
    if not bagian:
        return None

    setel = ", ".join(f"{k} = %s" for k in bagian)
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"UPDATE blog_posts SET {setel} WHERE slug = %s "
            "RETURNING slug, status, terbit_pada, diubah_pada",
            [*bagian.values(), slug],
        )
        return await k.fetchone()


async def ubah_status(slug: str, status: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE blog_posts SET status = %s::status_terbit WHERE slug = %s "
            "RETURNING slug, status, terbit_pada",
            (status, slug),
        )
        return await k.fetchone()


async def hapus(slug: str) -> bool:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM blog_posts WHERE slug = %s", (slug,))
        return k.rowcount > 0


async def daftar_semua() -> list[dict[str, Any]]:
    """Termasuk draf dan arsip. Hanya untuk admin."""
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT slug, status, terbit_pada, judul_en, judul_id, diubah_pada "
            "FROM blog_posts ORDER BY coalesce(terbit_pada, '9999-12-31') DESC, slug"
        )
        return await k.fetchall()
