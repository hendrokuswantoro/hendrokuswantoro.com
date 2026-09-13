"""SQL untuk verifikasi email, kode sekali pakai, TOTP, pemulihan, dan jejak.

Satu aturan berlaku di seluruh berkas ini: yang masuk dan keluar kolom
`kode_hash` selalu sidiknya, tidak pernah kodenya. Fungsi di sini tidak pernah
menerima kode mentah dan tidak pernah mengembalikannya.

Aturan kedua, yang lebih halus: kode dipakai lewat satu pernyataan
`UPDATE ... RETURNING`, bukan SELECT lalu UPDATE. Dua pernyataan terpisah
membuka jendela bagi dua permintaan yang tiba bersamaan untuk sama sama
melihat kode itu masih belum terpakai. Pola yang sama sudah dipakai tabel
`tantangan` milik passkey, dan alasannya sama.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from backend.core.basis_data import koneksi

# ------------------------------------------------------- verifikasi email ---


async def tandai_email_terverifikasi(pengguna_id: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE users SET email_terverifikasi_pada = now() WHERE id = %s",
            (pengguna_id,),
        )


async def keadaan(pengguna_id: str) -> dict[str, Any] | None:
    """Semua yang halaman keamanan perlu tahu, dalam satu perjalanan."""
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT u.id, u.email, u.nama,
                   u.email_terverifikasi_pada,
                   (u.totp_rahasia IS NOT NULL) AS totp_terpasang,
                   u.totp_aktif_pada,
                   (u.sandi_hash IS NOT NULL) AS punya_sandi,
                   (SELECT count(*) FROM kredensial WHERE pengguna_id = u.id) AS passkey,
                   (SELECT count(*) FROM kode_pemulihan
                     WHERE pengguna_id = u.id AND dipakai_pada IS NULL) AS pemulihan_sisa
            FROM users u WHERE u.id = %s
            """,
            (pengguna_id,),
        )
        return await k.fetchone()


# ------------------------------------------------------ kode sekali pakai ---


async def simpan_kode(
    pengguna_id: str, tujuan: str, kode_hash: str,
    kadaluarsa: dt.datetime, alamat: str | None,
) -> str:
    async with koneksi() as s, s.cursor() as k:
        # Kode lama untuk tujuan yang sama dimatikan lebih dulu. Meminta kode
        # baru harus berarti yang lama tidak berlaku lagi; kalau tidak, tiap
        # permintaan menambah satu kode hidup dan ruang tebakannya tumbuh.
        await k.execute(
            """
            UPDATE kode_sekali SET dipakai_pada = now()
            WHERE pengguna_id = %s AND tujuan = %s AND dipakai_pada IS NULL
            """,
            (pengguna_id, tujuan),
        )
        await k.execute(
            """
            INSERT INTO kode_sekali (pengguna_id, tujuan, kode_hash, kadaluarsa, alamat_ringkas)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (pengguna_id, tujuan, kode_hash, kadaluarsa, alamat),
        )
        return str((await k.fetchone())["id"])


async def pakai_kode(tujuan: str, kode_hash: str) -> dict[str, Any] | None:
    """Menandai kode terpakai dan mengembalikan pemiliknya, dalam satu langkah.

    Mengembalikan None kalau kodenya tidak ada, sudah dipakai, sudah lewat
    waktunya, atau jatah tebakannya habis. Keempatnya sengaja tidak dibedakan
    di sini: yang memanggil tidak perlu tahu, dan jawaban yang membedakannya
    memberi tahu penebak sejauh mana ia sudah sampai.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            UPDATE kode_sekali SET dipakai_pada = now()
            WHERE id = (
                SELECT id FROM kode_sekali
                WHERE tujuan = %s AND kode_hash = %s
                  AND dipakai_pada IS NULL
                  AND kadaluarsa > now()
                  AND percobaan < 5
                ORDER BY dibuat_pada DESC
                LIMIT 1
                FOR UPDATE
            )
            RETURNING pengguna_id
            """,
            (tujuan, kode_hash),
        )
        return await k.fetchone()


async def catat_tebakan_gagal(pengguna_id: str, tujuan: str) -> int:
    """Menaikkan penghitung tebakan pada kode yang sedang hidup.

    Dihitung pada barisnya, bukan per alamat IP. Penebak yang berpindah pindah
    alamat tetap membakar jatah kode yang sama, dan kodenya mati sebelum ruang
    tebakan enam angka habis.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            UPDATE kode_sekali SET percobaan = percobaan + 1
            WHERE pengguna_id = %s AND tujuan = %s
              AND dipakai_pada IS NULL AND kadaluarsa > now()
            RETURNING percobaan
            """,
            (pengguna_id, tujuan),
        )
        baris = await k.fetchone()
        return baris["percobaan"] if baris else 0


async def kode_hidup(pengguna_id: str, tujuan: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT dibuat_pada, kadaluarsa, percobaan FROM kode_sekali
            WHERE pengguna_id = %s AND tujuan = %s
              AND dipakai_pada IS NULL AND kadaluarsa > now()
            ORDER BY dibuat_pada DESC LIMIT 1
            """,
            (pengguna_id, tujuan),
        )
        return await k.fetchone()


# ------------------------------------------------------------------ TOTP ---


async def simpan_rahasia_totp(pengguna_id: str, tersandi: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE users SET totp_rahasia = %s, totp_aktif_pada = NULL WHERE id = %s",
            (tersandi, pengguna_id),
        )


async def aktifkan_totp(pengguna_id: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "UPDATE users SET totp_aktif_pada = now() WHERE id = %s AND totp_rahasia IS NOT NULL",
            (pengguna_id,),
        )


async def matikan_totp(pengguna_id: str) -> None:
    async with koneksi() as s, s.cursor() as k:
        # Rahasianya dihapus, bukan sekadar dinonaktifkan, dan kode
        # pemulihannya ikut. Rahasia yang tertinggal adalah rahasia yang masih
        # bisa dipakai kalau kolom aktifnya suatu saat terisi lagi.
        await k.execute(
            "UPDATE users SET totp_rahasia = NULL, totp_aktif_pada = NULL WHERE id = %s",
            (pengguna_id,),
        )
        await k.execute("DELETE FROM kode_pemulihan WHERE pengguna_id = %s", (pengguna_id,))


async def rahasia_totp(pengguna_id: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            "SELECT totp_rahasia, totp_aktif_pada FROM users WHERE id = %s",
            (pengguna_id,),
        )
        return await k.fetchone()


# ------------------------------------------------------------- pemulihan ---


async def ganti_kode_pemulihan(pengguna_id: str, sidik: list[str]) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute("DELETE FROM kode_pemulihan WHERE pengguna_id = %s", (pengguna_id,))
        for satu in sidik:
            await k.execute(
                "INSERT INTO kode_pemulihan (pengguna_id, kode_hash) VALUES (%s, %s)",
                (pengguna_id, satu),
            )


async def pakai_kode_pemulihan(pengguna_id: str, kode_hash: str) -> bool:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            UPDATE kode_pemulihan SET dipakai_pada = now()
            WHERE pengguna_id = %s AND kode_hash = %s AND dipakai_pada IS NULL
            RETURNING id
            """,
            (pengguna_id, kode_hash),
        )
        return (await k.fetchone()) is not None


# --------------------------------------------------------------- peristiwa --


async def catat(
    pengguna_id: str | None, jenis: str, berhasil: bool,
    keterangan: str | None = None, alamat: str | None = None,
    peramban: str | None = None,
) -> None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            INSERT INTO peristiwa_keamanan
                (pengguna_id, jenis, berhasil, keterangan, alamat_ringkas, peramban)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (pengguna_id, jenis, berhasil, keterangan, alamat, (peramban or "")[:200] or None),
        )


async def peristiwa(pengguna_id: str, batas: int = 40) -> list[dict[str, Any]]:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT jenis, berhasil, keterangan, alamat_ringkas, peramban, pada
            FROM peristiwa_keamanan
            WHERE pengguna_id = %s
            ORDER BY pada DESC LIMIT %s
            """,
            (pengguna_id, batas),
        )
        return list(await k.fetchall())
