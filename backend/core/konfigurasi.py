"""Pengaturan yang dibaca sekali dari environment.

Bab 15.11: tidak ada rahasia di dalam kode. Semua datang dari environment,
yang di mesin pengembangan diisi .env dan di produksi diisi penyedia.
"""

from __future__ import annotations

import functools
import pathlib

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent


class Pengaturan(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=AKAR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    dsn: str = Field(default="", alias="DSN")
    redis_url: str = Field(default="", alias="REDIS_URL")

    asal_diizinkan: list[str] = Field(
        default=["http://127.0.0.1:8081", "https://www.hendrokuswantoro.com"],
        alias="ASAL_DIIZINKAN",
    )

    # bab 15.11: pembatasan laju per IP
    laju_jumlah: int = Field(default=120, alias="LAJU_JUMLAH")
    laju_jendela_detik: int = Field(default=60, alias="LAJU_JENDELA_DETIK")

    # --- autentikasi ---
    jwt_rahasia: str = Field(default="", alias="JWT_SECRET")
    akses_umur_menit: int = Field(default=15, alias="AKSES_UMUR_MENIT")
    refresh_umur_hari: int = Field(default=14, alias="REFRESH_UMUR_HARI")
    masuk_gagal_maks: int = Field(default=5, alias="MASUK_GAGAL_MAKS")
    masuk_jendela_menit: int = Field(default=15, alias="MASUK_JENDELA_MENIT")
    cookie_aman: bool = Field(default=True, alias="COOKIE_AMAN")

    kolam_min: int = Field(default=1, alias="KOLAM_MIN")
    kolam_maks: int = Field(default=8, alias="KOLAM_MAKS")

    @property
    def siap(self) -> bool:
        return bool(self.dsn)

    @property
    def auth_siap(self) -> bool:
        """Tanpa JWT_SECRET, seluruh jalur admin ditutup, bukan dibuka dengan
        rahasia bawaan. Rahasia bawaan adalah rahasia yang sudah bocor."""
        return bool(self.jwt_rahasia) and len(self.jwt_rahasia) >= 32


@functools.lru_cache
def pengaturan() -> Pengaturan:
    return Pengaturan()
