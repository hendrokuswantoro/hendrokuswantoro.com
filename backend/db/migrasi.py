"""Menjalankan migrasi SQL bernomor, sekali saja masing masing.

    python backend/db/migrasi.py            # terapkan yang belum
    python backend/db/migrasi.py --status   # lihat saja

Kenapa SQL bernomor dan bukan Alembic: skema ini dibaca lebih sering
daripada diubah, dan SQL yang bisa dibaca langsung lebih jujur daripada
Python yang membangkitkan SQL. Proyek Parkir Jogja memakai pola yang sama,
jadi keduanya konsisten.

Yang sudah diterapkan dicatat di tabel `skema_migrasi` beserta sidik jari
isinya. Mengubah berkas migrasi yang sudah jalan akan ketahuan, bukan
diterapkan diam diam separuh.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys

try:
    import psycopg
except ImportError:  # pragma: no cover
    sys.exit("psycopg belum terpasang. Jalankan: pip install -r backend/requirements.txt")

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR / "tools"))
from muat_env import muat  # noqa: E402

muat()

MIGRASI = pathlib.Path(__file__).resolve().parent / "migrations"

BUAT_TABEL = """
CREATE TABLE IF NOT EXISTS skema_migrasi (
    nama            VARCHAR(150) PRIMARY KEY,
    sidik           CHAR(64) NOT NULL,
    diterapkan_pada TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def dsn() -> str:
    alamat = os.environ.get("DSN")
    if not alamat:
        sys.exit("DSN belum diisi. Salin .env.example ke .env lalu isi.")
    return alamat


def sidik(teks: str) -> str:
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()


def berkas_migrasi() -> list[pathlib.Path]:
    return sorted(MIGRASI.glob("*.sql"))


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--status", action="store_true", help="lihat saja, jangan terapkan")
    pilihan = alasan.parse_args()

    semua = berkas_migrasi()
    if not semua:
        sys.exit("tidak ada berkas migrasi di %s" % MIGRASI)

    with psycopg.connect(dsn()) as sambung:
        with sambung.cursor() as kursor:
            kursor.execute(BUAT_TABEL)
            sambung.commit()

            kursor.execute("SELECT nama, sidik FROM skema_migrasi")
            sudah = dict(kursor.fetchall())

        baru = 0
        for berkas in semua:
            isi = berkas.read_text(encoding="utf-8")
            cap = sidik(isi)

            if berkas.name in sudah:
                if sudah[berkas.name] != cap:
                    sys.exit(
                        f"{berkas.name} berubah sesudah diterapkan.\n"
                        "Migrasi yang sudah jalan tidak boleh disunting. "
                        "Buat berkas baru dengan nomor berikutnya."
                    )
                print(f"lewat  {berkas.name}")
                continue

            if pilihan.status:
                print(f"BELUM  {berkas.name}")
                baru += 1
                continue

            with sambung.cursor() as kursor:
                kursor.execute(isi)
                kursor.execute(
                    "INSERT INTO skema_migrasi (nama, sidik) VALUES (%s, %s)",
                    (berkas.name, cap),
                )
            sambung.commit()
            print(f"terap  {berkas.name}")
            baru += 1

    if pilihan.status:
        print(f"\n{baru} migrasi belum diterapkan")
    else:
        print(f"\n{baru} migrasi diterapkan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
