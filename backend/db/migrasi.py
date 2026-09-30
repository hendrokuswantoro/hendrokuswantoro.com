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
except ImportError:
    sys.exit("psycopg belum terpasang. Jalankan: pip install -r backend/requirements.txt")

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR / "tools"))
from muat_env import muat

muat()

MIGRASI = pathlib.Path(__file__).resolve().parent / "migrations"

SIDIK_TANPA_KOMENTAR = {
    "0001_awal.sql": (
        "711b379443ef072f59488339d1858cc8a7e3ff59e69023403d0b89081c9c245a",
        "64cf1402fbab26988cb6e8d412c0e0afeb38246d8831f767db1a12286b570de8",
    ),
    "0002_sesi.sql": (
        "5561f3194732f78210c5115e2391a07848cabde720e451aea2094fd949dd0fa6",
        "a8a306d3e4bfcf07613bafd695b78eb112207a4a7a44d52d7b5c8c69b63c4a39",
    ),
    "0003_passkey.sql": (
        "c4172aaef992d0db1d6c900772e2b30d71ca09871f4b934bc83df516f24ae723",
        "90cf59069eede81f8aeb69d82ccc53440d9b402e84b95214f888929c885a013a",
    ),
    "0004_keamanan.sql": (
        "ded71a232dd0026f88b8e924f181e6493f94a5dae4501d7eb1df2517b85d57bf",
        "322baa86e26f696bf48811af66a06319fe9df5858504459febfb4777834b4cd6",
    ),
    "0005_wajah.sql": (
        "101dbe2c6cae7fc0defcede1f07d6c0c0b54e9ce6c45d8f52c209bea0290d653",
        "92fb38a03bf3908d06657b0f92b7411cf7739e01c910b3c3976c3e27420dc19e",
    ),
    "0006_berkas.sql": (
        "aea1bca1430f026aa560c112e610ae8dd3bc384d0d8738d8cf695d1ff36e79a3",
        "1d3bd1b98d7ee85a3dd4620242f0c8ad674dfd72e6ca2380503ace060923adeb",
    ),
    "0007_sesi_kuat.sql": (
        "2825123505228bd71da54b20725939fa6a060cce0e5b55c3d7c30ef114515427",
        "d906e3c1737b184997c4f31a3c038664aed917547eb7a47852033aec85a575bf",
    ),
    "0008_totp_langkah.sql": (
        "dd4cf1d1367faeae6f71f17744cc7504537bde52eed4daf53365baff1a5e60c6",
        "13a7d7b3cb425f61288cc0fc3783a38611823f033d857151f1a18adeafc5f88d",
    ),
    "0009_setelan_keamanan.sql": (
        "ff11eae665b24a4b6e2edfed463bca2d58195bfd3c2c362f3540fa436c3783b9",
        "a6f855b9b59edc4a020859f409e861bda24b451913ac162ede1b6f4f5a41f5bf",
    ),
    "0010_sesi_ketat.sql": (
        "660fae00ce6d39316750cd6f7d6d38ff96cefdef9d4078f92b2514d22d4f656a",
        "6dde3cd2a83ddea6c7d5fbbf9035d45fe2d72ad190c8be0442ed6ae219a72745",
    ),
}

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
                if (sudah[berkas.name], cap) == SIDIK_TANPA_KOMENTAR.get(berkas.name):
                    if not pilihan.status:
                        with sambung.cursor() as kursor:
                            kursor.execute(
                                "UPDATE skema_migrasi SET sidik = %s WHERE nama = %s",
                                (cap, berkas.name),
                            )
                        sambung.commit()
                        print(f"tanda  {berkas.name}")
                    sudah[berkas.name] = cap
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
