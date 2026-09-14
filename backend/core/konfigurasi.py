"""Pengaturan yang dibaca sekali dari environment.

Bab 15.11: tidak ada rahasia di dalam kode. Semua datang dari environment,
yang di mesin pengembangan diisi .env dan di produksi diisi penyedia.
"""

from __future__ import annotations

import functools
import ipaddress
import pathlib

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent


def _alamat_ip(host: str) -> bool:
    """Apakah host ini alamat IP, bukan nama domain.

    Dipakai memutuskan apakah jalur passkey bisa hidup sama sekali. Kurung
    siku IPv6 dibuang lebih dulu, sebab bentuk yang ditulis orang di URL
    adalah [::1], sedangkan yang dikenali pustakanya ::1.
    """
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

    # --- passkey, WebAuthn ---
    #
    # rp_id adalah nama host tanpa skema dan tanpa porta, misalnya
    # "hendrokuswantoro.com". Ia harus sama dengan atau induk dari host yang
    # membuka halamannya, dan tidak bisa ditebak dari permintaan: header Host
    # datang dari peramban, jadi memercayainya berarti membiarkan penyerang
    # memilih rp_id sendiri. Karena itu ia datang dari environment.
    webauthn_rp_id: str = Field(default="", alias="WEBAUTHN_RP_ID")
    webauthn_rp_nama: str = Field(default="Hendro Kuswantoro", alias="WEBAUTHN_RP_NAMA")
    webauthn_asal: list[str] = Field(default=[], alias="WEBAUTHN_ASAL")

    # --- penyandian kolom, dipakai rahasia TOTP ---
    #
    # Dibaca lewat Pengaturan, bukan lewat os.environ langsung, dan itu bukan
    # selera. Aplikasi web ini tidak pernah memuat .env ke dalam os.environ:
    # yang membaca .env adalah pydantic-settings, untuk medan di kelas ini
    # saja. Jadi nilai yang hanya ada di .env tidak akan pernah terlihat oleh
    # os.environ.get, dan fitur yang membacanya begitu akan diam diam mengira
    # kuncinya belum ada padahal ia tertulis di .env. Itu sudah terjadi.
    kunci_kolom: str = Field(default="", alias="KUNCI_KOLOM")

    # --- SMTP, dipakai verifikasi email dan kode masuk ---
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_porta: int = Field(default=587, alias="SMTP_PORTA")
    smtp_pengguna: str = Field(default="", alias="SMTP_PENGGUNA")
    smtp_sandi: str = Field(default="", alias="SMTP_SANDI")
    surat_dari: str = Field(default="", alias="SURAT_DARI")
    surat_wajib: bool = Field(default=False, alias="SURAT_WAJIB")

    kolam_min: int = Field(default=1, alias="KOLAM_MIN")
    kolam_maks: int = Field(default=8, alias="KOLAM_MAKS")

    @property
    def siap(self) -> bool:
        return bool(self.dsn)

    @property
    def passkey_siap(self) -> bool:
        """Tanpa rp_id dan daftar asal, jalur passkey menjawab 503, bukan
        menebak keduanya dari permintaan. Nilai bawaan untuk keduanya adalah
        cara paling langsung membuat verifikasi asal berhenti berarti.

        rp_id berupa alamat IP juga dihitung belum siap, dan itu bukan sikap
        rewel. WebAuthn menuntut rp_id berupa nama domain; peramban menolak
        alamat IP sebelum satu pun permintaan dikirim, dengan SecurityError
        berbunyi "This is an invalid domain". Sudah diperiksa di Chromium,
        termasuk rp_id "127.0.0.1" dari halaman 127.0.0.1, dan ditolak sama
        persis. Jadi konfigurasi semacam itu tidak pernah bisa bekerja, dan
        menjawab siap=true untuknya berarti menyuruh halaman admin memasang
        tombol yang mustahil berhasil.
        """
        if not (self.auth_siap and self.webauthn_rp_id and self.webauthn_asal):
            return False
        return not _alamat_ip(self.webauthn_rp_id)

    @property
    def auth_siap(self) -> bool:
        """Tanpa JWT_SECRET, seluruh jalur admin ditutup, bukan dibuka dengan
        rahasia bawaan. Rahasia bawaan adalah rahasia yang sudah bocor."""
        return bool(self.jwt_rahasia) and len(self.jwt_rahasia) >= 32


@functools.lru_cache
def pengaturan() -> Pengaturan:
    return Pengaturan()
