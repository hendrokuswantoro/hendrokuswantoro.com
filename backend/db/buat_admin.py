"""Memasang sandi untuk akun admin.

    python backend/db/buat_admin.py

Sandinya diminta lewat prompt, tidak pernah lewat argumen baris perintah.
Argumen baris perintah tersimpan di riwayat shell dan terlihat di daftar
proses; itu dua tempat rahasia bocor tanpa ada yang berniat.
"""

from __future__ import annotations

import getpass
import os
import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

import psycopg  # noqa: E402

from backend.core.keamanan import hash_sandi  # noqa: E402

PANJANG_MINIMAL = 12


def main() -> int:
    dsn = os.environ.get("DSN")
    if not dsn:
        sys.exit("DSN belum diisi")

    email = input("email admin: ").strip()
    if not email:
        sys.exit("email kosong")

    sandi = getpass.getpass("sandi baru: ")
    if len(sandi) < PANJANG_MINIMAL:
        sys.exit(f"sandi minimal {PANJANG_MINIMAL} karakter")
    if sandi != getpass.getpass("ulangi sandi: "):
        sys.exit("sandi tidak sama")

    with psycopg.connect(dsn) as s, s.cursor() as k:
        k.execute(
            "UPDATE users SET sandi_hash = %s, peran = 'admin' WHERE lower(email) = lower(%s)",
            (hash_sandi(sandi), email),
        )
        if k.rowcount == 0:
            sys.exit(f"tidak ada pengguna dengan email {email}. Jalankan muat_awal.py dulu.")
        s.commit()

    # sandinya tidak pernah dicetak, bahkan sebagian
    print(f"sandi dipasang untuk {email}")
    print("Seluruh sesi lama sebaiknya dicabut: POST /api/v1/auth/logout-semua")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
