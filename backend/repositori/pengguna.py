"""SQL untuk pengguna, sesi, dan catatan percobaan masuk yang gagal."""

from __future__ import annotations

import datetime as dt
from typing import Any

from backend.core.basis_data import koneksi


async def cari_email(email: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT id, email, nama, peran, sandi_hash FROM users WHERE lower(email) = lower(%s)",
            (email,),
        )
        return await k.fetchone()


async def cari_id(pengguna_id: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("SELECT id, email, nama, peran FROM users WHERE id = %s", (pengguna_id,))
        return await k.fetchone()


async def simpan_hash(pengguna_id: str, hash_baru: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("UPDATE users SET sandi_hash = %s WHERE id = %s", (hash_baru, pengguna_id))


# ------------------------------------------------------------------ sesi ---


async def buat_sesi(pengguna_id: str, token_hash: str, kadaluarsa: dt.datetime) -> str:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "INSERT INTO sesi (pengguna_id, token_hash, kadaluarsa) VALUES (%s, %s, %s) RETURNING id",
            (pengguna_id, token_hash, kadaluarsa),
        )
        return (await k.fetchone())["id"]


async def sesi_hidup(token_hash: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT s.id, s.pengguna_id, u.peran
            FROM sesi s JOIN users u ON u.id = s.pengguna_id
            WHERE s.token_hash = %s
              AND s.dicabut_pada IS NULL
              AND s.kadaluarsa > now()
            """,
            (token_hash,),
        )
        return await k.fetchone()


async def cabut(token_hash: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE sesi SET dicabut_pada = now() WHERE token_hash = %s AND dicabut_pada IS NULL",
            (token_hash,),
        )


async def daftar_sesi(pengguna_id: str) -> list[dict[str, Any]]:
    """Sesi yang masih hidup, terbaru lebih dulu.

    Yang dikembalikan sengaja sedikit: kapan dibuat, kapan kedaluwarsa, dan
    sidik token yang dipendekkan supaya antarmuka bisa menandai mana sesi
    perangkat yang sedang dipakai. Tidak ada nama perangkat dan tidak ada
    alamat IP, sebab keduanya memang tidak pernah disimpan. Menambahkannya
    sekarang berarti mulai mencatat tempat pemiliknya berada, dan itu
    keputusan tersendiri yang bukan milik sebuah panel.

    Dengan begitu panelnya tetap menjawab pertanyaan yang penting: ada berapa
    sesi yang hidup, dan apakah jumlahnya lebih banyak daripada perangkat yang
    Anda ingat.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT id, token_hash, dibuat_pada, kadaluarsa
            FROM sesi
            WHERE pengguna_id = %s AND dicabut_pada IS NULL AND kadaluarsa > now()
            ORDER BY dibuat_pada DESC
            """,
            (pengguna_id,),
        )
        return await k.fetchall()


async def cabut_lain(pengguna_id: str, token_hash: str) -> int:
    """Keluar dari perangkat lain, menyisakan yang sedang dipakai.

    Dipisahkan dari `cabut_semua` dengan sengaja. Tombol yang mengeluarkan
    pemiliknya sendiri bersama penyusupnya akan ragu ragu ditekan, padahal
    justru saat curiga itulah ia harus ditekan cepat.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE sesi SET dicabut_pada = now() "
            "WHERE pengguna_id = %s AND dicabut_pada IS NULL AND token_hash <> %s",
            (pengguna_id, token_hash),
        )
        return k.rowcount


async def cabut_semua(pengguna_id: str) -> int:
    """Keluar dari semua perangkat. Bab 15.10."""
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE sesi SET dicabut_pada = now() "
            "WHERE pengguna_id = %s AND dicabut_pada IS NULL",
            (pengguna_id,),
        )
        return k.rowcount


async def bersihkan_kadaluarsa() -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM sesi WHERE kadaluarsa < now() - interval '30 days'")
        return k.rowcount


# ------------------------------------------------------- percobaan gagal ---


async def catat_gagal(email: str, alamat_hash: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "INSERT INTO gagal_masuk (email, alamat_hash) VALUES (%s, %s)",
            (email, alamat_hash),
        )


async def jumlah_gagal(email: str, menit: int) -> int:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT count(*) AS n FROM gagal_masuk "
            "WHERE lower(email) = lower(%s) AND pada > now() - make_interval(mins => %s)",
            (email, menit),
        )
        return (await k.fetchone())["n"]


async def bersihkan_gagal(email: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM gagal_masuk WHERE lower(email) = lower(%s)", (email,))
