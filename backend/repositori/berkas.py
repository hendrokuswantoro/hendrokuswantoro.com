"""SQL untuk catatan foto dan video yang diunggah.

Berkasnya sendiri tidak lewat sini. Yang menulis dan menghapusnya di cakram
`layanan/berkas.py`; yang di sini hanya catatannya.
"""

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
    """Berkas dengan isi yang sama persis, kalau sudah pernah diunggah.

    Dipakai supaya satu foto yang dipakai di tiga tulisan tetap satu berkas
    di cakram, dan supaya mengunggah ulang berkas yang sama tidak diam diam
    meninggalkan salinan yatim yang tidak pernah ada yang menghapusnya.
    """
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
    """Jumlah berkas, total bitanya, dan berapa yang masuk hari ini.

    Ketiganya dibaca dalam satu kueri. Tiga kueri berurutan bisa menjawab tiga
    keadaan yang berbeda kalau ada unggahan lain yang masuk di antaranya, dan
    batas yang dihitung dari keadaan yang tidak pernah ada bersamaan adalah
    batas yang salah.
    """
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
    """Slug tulisan mana saja yang masih menyebut alamat ini.

    Dipanggil sebelum menghapus. Menghapus berkas yang masih dipakai adalah
    kegagalan yang diam: tulisannya tetap terbit, hanya gambarnya jadi kotak
    kosong, dan yang menyadarinya pembaca, bukan penulisnya.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT slug FROM blog_posts "
            "WHERE position(%s in isi_en) > 0 OR position(%s in isi_id) > 0 "
            "ORDER BY slug",
            (alamat, alamat),
        )
        return [b["slug"] for b in await k.fetchall()]
