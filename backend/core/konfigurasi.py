from __future__ import annotations

import functools
import ipaddress
import pathlib

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent


def _alamat_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return True


class Pengaturan(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=AKAR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    dsn: str = Field(default="", alias="DSN")
    redis_url: str = Field(default="", alias="REDIS_URL")

    asal_diizinkan: list[str] = Field(
        default=["https://www.hendrokuswantoro.com"],
        alias="ASAL_DIIZINKAN",
    )

    laju_jumlah: int = Field(default=120, alias="LAJU_JUMLAH")
    laju_jendela_detik: int = Field(default=60, alias="LAJU_JENDELA_DETIK")

    jwt_rahasia: str = Field(default="", alias="JWT_SECRET")

    jwt_rahasia_lama: str = Field(default="", alias="JWT_SECRET_LAMA")
    akses_umur_menit: int = Field(default=15, alias="AKSES_UMUR_MENIT")
    refresh_umur_hari: int = Field(default=14, alias="REFRESH_UMUR_HARI")
    masuk_gagal_maks: int = Field(default=5, alias="MASUK_GAGAL_MAKS")

    faktor_kedua_wajib: bool = Field(default=True, alias="FAKTOR_KEDUA_WAJIB")
    masuk_jendela_menit: int = Field(default=15, alias="MASUK_JENDELA_MENIT")
    cookie_aman: bool = Field(default=True, alias="COOKIE_AMAN")

    webauthn_rp_id: str = Field(default="", alias="WEBAUTHN_RP_ID")
    webauthn_rp_nama: str = Field(default="Hendro Kuswantoro", alias="WEBAUTHN_RP_NAMA")
    webauthn_asal: list[str] = Field(default=[], alias="WEBAUTHN_ASAL")

    kunci_kolom: str = Field(default="", alias="KUNCI_KOLOM")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_porta: int = Field(default=587, alias="SMTP_PORTA")
    smtp_pengguna: str = Field(default="", alias="SMTP_PENGGUNA")
    smtp_sandi: str = Field(default="", alias="SMTP_SANDI")
    surat_dari: str = Field(default="", alias="SURAT_DARI")
    surat_wajib: bool = Field(default=False, alias="SURAT_WAJIB")

    unggahan_dir: str = Field(default="unggahan", alias="UNGGAHAN_DIR")

    unggahan_gambar_maks_mb: int = Field(default=10, alias="UNGGAHAN_GAMBAR_MAKS_MB")
    unggahan_video_maks_mb: int = Field(default=80, alias="UNGGAHAN_VIDEO_MAKS_MB")

    unggahan_total_maks_mb: int = Field(default=2048, alias="UNGGAHAN_TOTAL_MAKS_MB")
    unggahan_jumlah_maks: int = Field(default=2000, alias="UNGGAHAN_JUMLAH_MAKS")
    unggahan_per_hari_maks: int = Field(default=100, alias="UNGGAHAN_PER_HARI_MAKS")

    kolam_min: int = Field(default=1, alias="KOLAM_MIN")
    kolam_maks: int = Field(default=8, alias="KOLAM_MAKS")

    @property
    def siap(self) -> bool:
        return bool(self.dsn)

    @property
    def passkey_siap(self) -> bool:
        if not (self.auth_siap and self.webauthn_rp_id and self.webauthn_asal):
            return False
        return not _alamat_ip(self.webauthn_rp_id)

    @property
    def auth_siap(self) -> bool:
        return bool(self.jwt_rahasia) and len(self.jwt_rahasia) >= 32


@functools.lru_cache
def pengaturan() -> Pengaturan:
    return Pengaturan()
