"""SQL untuk passkey dan tantangannya.

Tidak ada satu pun keputusan di berkas ini, hanya baca dan tulis. Aturan
siapa boleh apa dan tantangan mana yang masih berlaku ada di
`layanan/passkey.py`.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from backend.core.basis_data import koneksi


# ------------------------------------------------------------- tantangan ---


async def simpan_tantangan(
    tujuan: str, nilai: bytes, kadaluarsa: dt.datetime, pengguna_id: str | None = None
) -> str:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "INSERT INTO tantangan (tujuan, pengguna_id, nilai, kadaluarsa) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (tujuan, pengguna_id, nilai, kadaluarsa),
        )
        return str((await k.fetchone())["id"])


async def pakai_tantangan(tujuan: str, nilai: bytes) -> dict[str, Any] | None:
    """Menandai terpakai dan mengembalikan barisnya, dalam satu pernyataan.

    Satu pernyataan dengan sengaja. Membaca dulu lalu menandai belakangan
    membuka celah antara keduanya: dua permintaan yang datang bersamaan
    dengan tantangan sama akan sama sama lolos. UPDATE ... RETURNING menutup
    itu tanpa kunci tambahan, karena baris yang sudah terisi `dipakai_pada`
    tidak lagi cocok dengan syaratnya.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            UPDATE tantangan SET dipakai_pada = now()
            WHERE nilai = %s AND tujuan = %s
              AND dipakai_pada IS NULL AND kadaluarsa > now()
            RETURNING id, tujuan, pengguna_id
            """,
            (nilai, tujuan),
        )
        return await k.fetchone()


async def bersihkan_tantangan() -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM tantangan WHERE kadaluarsa < now() - interval '1 day'")
        return k.rowcount


# ------------------------------------------------------------ kredensial ---


async def simpan(
    pengguna_id: str,
    kredensial_id: bytes,
    kunci_publik: bytes,
    penghitung: int,
    jenis_perangkat: str,
    tercadang: bool,
    transportasi: list[str],
    nama: str,
) -> str:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            INSERT INTO kredensial
                (pengguna_id, kredensial_id, kunci_publik, penghitung,
                 jenis_perangkat, tercadang, transportasi, nama)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (pengguna_id, kredensial_id, kunci_publik, penghitung,
             jenis_perangkat, tercadang, transportasi, nama),
        )
        return str((await k.fetchone())["id"])


async def cari(kredensial_id: bytes) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT ks.id, ks.pengguna_id, ks.kredensial_id, ks.kunci_publik,
                   ks.penghitung, ks.nama, u.email, u.nama AS nama_pengguna, u.peran
            FROM kredensial ks JOIN users u ON u.id = ks.pengguna_id
            WHERE ks.kredensial_id = %s
            """,
            (kredensial_id,),
        )
        return await k.fetchone()


async def milik(pengguna_id: str) -> list[dict[str, Any]]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT id, kredensial_id, nama, jenis_perangkat, tercadang, "
            "transportasi, dibuat_pada, dipakai_pada "
            "FROM kredensial WHERE pengguna_id = %s ORDER BY dibuat_pada",
            (pengguna_id,),
        )
        return await k.fetchall()


async def perbarui_pemakaian(kredensial_id: bytes, penghitung: int) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE kredensial SET penghitung = %s, dipakai_pada = now() "
            "WHERE kredensial_id = %s",
            (penghitung, kredensial_id),
        )


async def hapus(pengguna_id: str, kredensial_uuid: str) -> bool:
    """Pemilik disebut di WHERE, bukan diperiksa lebih dulu di layanan.

    Memeriksa lebih dulu lalu menghapus berdasarkan id saja berarti ada
    jendela di antara keduanya, dan jendela semacam itu adalah cara klasik
    menghapus kredensial milik orang lain.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "DELETE FROM kredensial WHERE id = %s AND pengguna_id = %s",
            (kredensial_uuid, pengguna_id),
        )
        return k.rowcount > 0


async def jumlah(pengguna_id: str) -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT count(*) AS n FROM kredensial WHERE pengguna_id = %s", (pengguna_id,)
        )
        return (await k.fetchone())["n"]
