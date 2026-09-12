"""Bentuk data yang dipertukarkan API. Pydantic memvalidasi dua arah.

Kelas Teks di sini sengaja mencerminkan kolom berpasangan di basis data:
dua bahasa, keduanya wajib. Kalau suatu saat salah satunya hilang, yang
gagal adalah responnya, bukan halaman yang sudah terbit.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Teks(BaseModel):
    model_config = ConfigDict(frozen=True)

    en: str = Field(min_length=1)
    id: str = Field(min_length=1)


class Halaman(BaseModel):
    """Pembungkus daftar. Bab 15.20 menuntut pagination sejak awal, bukan
    ditambahkan setelah datanya terlanjur banyak."""

    jumlah: int
    batas: int
    lewati: int
