"""Mengisi basis data dari content/, bukan dari berkas SQL berisi data.

    python backend/db/muat_awal.py
    python backend/db/muat_awal.py --ulang   # kosongkan dulu

Sumbernya sengaja sama dengan sumber yang dipakai membangun situs statis:
`tools/isi.py`. Kalau pemuat ini punya salinan datanya sendiri, dua salinan
itu pasti berpisah jalan, dan basis data yang isinya berbeda dari situs yang
terbit adalah jenis kesalahan yang paling lama tidak ketahuan.

Jalankan berkali kali aman. Baris yang sudah ada diperbarui, bukan digandakan.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR / "tools"))

try:
    import psycopg
except ImportError:  # pragma: no cover
    sys.exit("psycopg belum terpasang. Jalankan: pip install -r backend/requirements.txt")

from isi import Proyek, SumberBerkas, Tulisan  # noqa: E402
from muat_env import muat  # noqa: E402

muat()

PEMILIK = ("kuswantoro.hendro01@gmail.com", "Hendro Kuswantoro")


def dsn() -> str:
    alamat = os.environ.get("DSN")
    if not alamat:
        sys.exit("DSN belum diisi. Salin .env.example ke .env lalu isi.")
    return alamat


def pemilik(kursor) -> str:
    kursor.execute(
        """
        INSERT INTO users (email, nama, peran)
        VALUES (%s, %s, 'admin')
        ON CONFLICT (email) DO UPDATE SET nama = EXCLUDED.nama
        RETURNING id
        """,
        PEMILIK,
    )
    return kursor.fetchone()[0]


def muat_tulisan(kursor, semua: list[Tulisan], penulis: str) -> None:
    for t in semua:
        kursor.execute(
            """
            INSERT INTO blog_posts (
                slug, judul_en, judul_id, ringkas_en, ringkas_id,
                keterangan_en, keterangan_id, lede_en, lede_id, isi_en, isi_id,
                tag_en, tag_id, baca_en, baca_id,
                status, terbit_pada, penulis_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, 'terbit', %s, %s
            )
            ON CONFLICT (slug) DO UPDATE SET
                judul_en = EXCLUDED.judul_en, judul_id = EXCLUDED.judul_id,
                ringkas_en = EXCLUDED.ringkas_en, ringkas_id = EXCLUDED.ringkas_id,
                keterangan_en = EXCLUDED.keterangan_en,
                keterangan_id = EXCLUDED.keterangan_id,
                lede_en = EXCLUDED.lede_en, lede_id = EXCLUDED.lede_id,
                isi_en = EXCLUDED.isi_en, isi_id = EXCLUDED.isi_id,
                tag_en = EXCLUDED.tag_en, tag_id = EXCLUDED.tag_id,
                baca_en = EXCLUDED.baca_en, baca_id = EXCLUDED.baca_id,
                status = EXCLUDED.status, terbit_pada = EXCLUDED.terbit_pada
            """,
            (
                t.slug, t.judul.en, t.judul.id, t.ringkas.en, t.ringkas.id,
                t.keterangan.en, t.keterangan.id, t.lede.en, t.lede.id,
                t.isi_en, t.isi_id, t.tag.en, t.tag.id, t.baca.en, t.baca.id,
                t.tanggal, penulis,
            ),
        )


def muat_proyek(kursor, semua: list[Proyek]) -> None:
    for p in semua:
        kursor.execute(
            """
            INSERT INTO projects (
                slug, urut, judul_en, judul_id, ringkas_en, ringkas_id,
                peran_en, peran_id, badge_en, badge_id,
                kategori, jenis_peta, teknologi,
                gambar, gambar_alt_en, gambar_alt_id, geom
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s::kategori_proyek[], %s::kategori_proyek, %s,
                %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            )
            ON CONFLICT (slug) DO UPDATE SET
                urut = EXCLUDED.urut,
                judul_en = EXCLUDED.judul_en, judul_id = EXCLUDED.judul_id,
                ringkas_en = EXCLUDED.ringkas_en, ringkas_id = EXCLUDED.ringkas_id,
                peran_en = EXCLUDED.peran_en, peran_id = EXCLUDED.peran_id,
                badge_en = EXCLUDED.badge_en, badge_id = EXCLUDED.badge_id,
                kategori = EXCLUDED.kategori, jenis_peta = EXCLUDED.jenis_peta,
                teknologi = EXCLUDED.teknologi, gambar = EXCLUDED.gambar,
                gambar_alt_en = EXCLUDED.gambar_alt_en,
                gambar_alt_id = EXCLUDED.gambar_alt_id,
                geom = EXCLUDED.geom
            """,
            (
                p.slug, p.urut, p.judul.en, p.judul.id, p.ringkas.en, p.ringkas.id,
                p.peran.en, p.peran.id, p.badge.en, p.badge.id,
                list(p.kategori), p.jenis_peta, list(p.teknologi),
                p.gambar, p.gambar_alt.en, p.gambar_alt.id, p.lng, p.lat,
            ),
        )


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--ulang", action="store_true", help="kosongkan tabel isi lebih dulu")
    pilihan = alasan.parse_args()

    sumber = SumberBerkas(AKAR / "content")
    tulisan, proyek = sumber.tulisan(), sumber.proyek()

    with psycopg.connect(dsn()) as sambung:
        with sambung.cursor() as kursor:
            if pilihan.ulang:
                kursor.execute("TRUNCATE blog_posts, projects RESTART IDENTITY CASCADE")
                print("tabel isi dikosongkan")

            penulis = pemilik(kursor)
            muat_tulisan(kursor, tulisan, penulis)
            muat_proyek(kursor, proyek)

            kursor.execute("SELECT count(*) FROM blog_posts")
            jumlah_tulisan = kursor.fetchone()[0]
            kursor.execute("SELECT count(*) FROM projects")
            jumlah_proyek = kursor.fetchone()[0]
        sambung.commit()

    print(f"basis data berisi {jumlah_tulisan} tulisan dan {jumlah_proyek} proyek")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
