from __future__ import annotations

from typing import Any

from backend.core.basis_data import koneksi

KOLOM = (
    "id, nama, nama_asal, jenis, tipe_mime, bita, lebar, tinggi, "
    "sidik, dibuat_pada"
)


async def simpan(nilai: dict[str, Any], pengunggah_id: str | None) -> dict[str, Any]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "INSERT INTO berkas "
            "(nama, nama_asal, jenis, tipe_mime, bita, lebar, tinggi, sidik, pengunggah_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            f"RETURNING {KOLOM}",
            (
                nilai["nama"], nilai["nama_asal"], nilai["jenis"], nilai["tipe_mime"],
                nilai["bita"], nilai.get("lebar"), nilai.get("tinggi"), nilai["sidik"],
                pengunggah_id,
            ),
        )
        return await k.fetchone()


async def lewat_sidik(sidik: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(f"SELECT {KOLOM} FROM berkas WHERE sidik = %s", (sidik,))
        return await k.fetchone()


async def satu(nama: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(f"SELECT {KOLOM} FROM berkas WHERE nama = %s", (nama,))
        return await k.fetchone()


async def daftar(batas: int, lewati: int) -> list[dict[str, Any]]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"SELECT {KOLOM} FROM berkas ORDER BY dibuat_pada DESC, nama "
            "LIMIT %s OFFSET %s",
            (batas, lewati),
        )
        return await k.fetchall()


async def jumlah() -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("SELECT count(*) AS n FROM berkas")
        return (await k.fetchone())["n"]


async def pemakaian() -> dict[str, int]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT count(*) AS jumlah, "
            "       coalesce(sum(bita), 0) AS bita, "
            "       count(*) FILTER (WHERE dibuat_pada > now() - interval '1 day') "
            "           AS hari_ini "
            "FROM berkas"
        )
        baris = await k.fetchone()
        return {
            "jumlah": baris["jumlah"],
            "bita": int(baris["bita"]),
            "hari_ini": baris["hari_ini"],
        }


async def hapus(nama: str) -> bool:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM berkas WHERE nama = %s", (nama,))
        return k.rowcount > 0


async def dipakai_tulisan(alamat: str) -> list[str]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT slug FROM blog_posts "
            "WHERE position(%s in isi_en) > 0 OR position(%s in isi_id) > 0 "
            "ORDER BY slug",
            (alamat, alamat),
        )
        return [b["slug"] for b in await k.fetchall()]
