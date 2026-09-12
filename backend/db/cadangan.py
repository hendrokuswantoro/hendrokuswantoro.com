"""Cadangan dan pemulihan basis data. Bab 15.18.

    python backend/db/cadangan.py buat
    python backend/db/cadangan.py daftar
    python backend/db/cadangan.py pulihkan cadangan/hk-2026-09-12-1530.sql.gz
    python backend/db/cadangan.py uji-pulih

`uji-pulih` yang paling penting. Cadangan yang belum pernah dipulihkan belum
terbukti apa apa, dan pemulihan pertama tidak boleh dicoba pada hari datanya
benar benar hilang. Perintah itu memulihkan cadangan ke basis data sementara,
menghitung isinya, lalu membuang basis data sementara itu.

pg_dump dan psql dipakai langsung kalau kliennya ada di mesin ini, misalnya
di runner CI. Kalau tidak ada, keduanya dijalankan di dalam kontainer basis
datanya sendiri, sehingga mesin pengembangan tidak perlu memasang klien
PostgreSQL sama sekali dan versi klien dijamin sama dengan servernya.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import pathlib
import shutil
import subprocess
import sys
import urllib.parse

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

import os  # noqa: E402

CADANGAN = AKAR / "cadangan"
WADAH = "hk_db"

# Bab 15.18 menuntut retensi disebut, bukan dibiarkan tumbuh selamanya.
SIMPAN_TERAKHIR = 14


def bagian_dsn() -> dict[str, str]:
    alamat = os.environ.get("DSN")
    if not alamat:
        sys.exit("DSN belum diisi")
    pecah = urllib.parse.urlparse(alamat)
    return {
        "pengguna": pecah.username or "",
        "basis": (pecah.path or "/").lstrip("/"),
    }


def punya_klien() -> bool:
    """Runner CI sudah membawa klien PostgreSQL, mesin pengembangan belum."""
    return shutil.which("pg_dump") is not None and shutil.which("psql") is not None


def _basis_sasaran(perintah: list[str]) -> str:
    for i, bagian in enumerate(perintah):
        if bagian == "-d" and i + 1 < len(perintah):
            return perintah[i + 1]
    return bagian_dsn()["basis"]


def _dsn_untuk(basis: str) -> str:
    pecah = urllib.parse.urlparse(os.environ["DSN"])
    return urllib.parse.urlunparse(pecah._replace(path="/" + basis))


def di_wadah(perintah: list[str], masukan: bytes | None = None) -> bytes:
    """Menjalankan pg_dump atau psql, di mana pun ia tersedia.

    Kalau kliennya ada di mesin ini, dipakai langsung lewat DSN. Kalau tidak,
    dijalankan di dalam kontainer basis datanya sendiri, sehingga tidak perlu
    memasang klien PostgreSQL dan versi klien dijamin sama dengan servernya.
    """
    if punya_klien():
        bersih, lewati = [perintah[0]], False
        for bagian in perintah[1:]:
            if lewati:
                lewati = False
                continue
            if bagian in ("-U", "-d"):
                lewati = True
                continue
            bersih.append(bagian)
        penuh = [*bersih, _dsn_untuk(_basis_sasaran(perintah))]
    else:
        penuh = ["docker", "exec", "-i", WADAH, *perintah]

    hasil = subprocess.run(penuh, input=masukan, capture_output=True)
    if hasil.returncode != 0:
        pesan = hasil.stderr.decode("utf-8", "replace").strip()
        sys.exit(f"gagal: {' '.join(penuh[:2])}\n{pesan[:800]}")
    return hasil.stdout


def buat() -> pathlib.Path:
    d = bagian_dsn()
    CADANGAN.mkdir(exist_ok=True)
    cap = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    tujuan = CADANGAN / f"hk-{cap}.sql.gz"

    isi = di_wadah(["pg_dump", "-U", d["pengguna"], "-d", d["basis"], "--clean", "--if-exists"])
    tujuan.write_bytes(gzip.compress(isi, 6))

    print(f"cadangan dibuat: {tujuan.name}, {tujuan.stat().st_size // 1024} KB")
    pangkas()
    return tujuan


def pangkas() -> None:
    semua = sorted(CADANGAN.glob("hk-*.sql.gz"))
    buang = semua[:-SIMPAN_TERAKHIR] if len(semua) > SIMPAN_TERAKHIR else []
    for berkas in buang:
        berkas.unlink()
        print(f"  dibuang, di luar retensi {SIMPAN_TERAKHIR}: {berkas.name}")


def daftar() -> None:
    semua = sorted(CADANGAN.glob("hk-*.sql.gz")) if CADANGAN.exists() else []
    if not semua:
        print("belum ada cadangan")
        return
    for berkas in semua:
        ukuran = berkas.stat().st_size // 1024
        print(f"  {berkas.name}  {ukuran} KB")
    print(f"\n{len(semua)} cadangan, retensi {SIMPAN_TERAKHIR} terakhir")


def _pulihkan_ke(berkas: pathlib.Path, basis: str) -> None:
    d = bagian_dsn()
    isi = gzip.decompress(berkas.read_bytes())
    di_wadah(["psql", "-U", d["pengguna"], "-d", basis, "-v", "ON_ERROR_STOP=1", "-q"], isi)


def pulihkan(berkas: pathlib.Path) -> None:
    if not berkas.exists():
        sys.exit(f"tidak ada: {berkas}")
    d = bagian_dsn()
    jawab = input(
        f"Memulihkan {berkas.name} ke basis data {d['basis']}.\n"
        "Isi yang sekarang akan tertimpa. Ketik PULIHKAN untuk lanjut: "
    )
    if jawab.strip() != "PULIHKAN":
        sys.exit("dibatalkan")
    _pulihkan_ke(berkas, d["basis"])
    print("selesai dipulihkan")


def hitung(basis: str) -> dict[str, int]:
    d = bagian_dsn()
    keluar = di_wadah([
        "psql", "-U", d["pengguna"], "-d", basis, "-t", "-A", "-F", ",", "-c",
        "SELECT (SELECT count(*) FROM blog_posts), (SELECT count(*) FROM projects), "
        "(SELECT count(*) FROM users), (SELECT count(*) FROM skema_migrasi)",
    ])
    a, b, c, e = keluar.decode().strip().split(",")
    return {"tulisan": int(a), "proyek": int(b), "pengguna": int(c), "migrasi": int(e)}


def uji_pulih() -> int:
    """Membuktikan cadangan terbaru benar benar bisa dipulihkan.

    Dipulihkan ke basis data sementara, bukan ke yang asli. Uji pemulihan
    yang menimpa data sungguhan bukan uji, itu taruhan.
    """
    d = bagian_dsn()
    semua = sorted(CADANGAN.glob("hk-*.sql.gz")) if CADANGAN.exists() else []
    if not semua:
        sys.exit("belum ada cadangan. Jalankan: python backend/db/cadangan.py buat")

    terbaru = semua[-1]
    sementara = "hk_uji_pulih"

    asli = hitung(d["basis"])
    print(f"asli      : {asli}")

    di_wadah(["psql", "-U", d["pengguna"], "-d", "postgres", "-q", "-c",
              f'DROP DATABASE IF EXISTS {sementara}'])
    di_wadah(["psql", "-U", d["pengguna"], "-d", "postgres", "-q", "-c",
              f'CREATE DATABASE {sementara}'])
    try:
        _pulihkan_ke(terbaru, sementara)
        dipulihkan = hitung(sementara)
        print(f"dipulihkan: {dipulihkan}")
    finally:
        di_wadah(["psql", "-U", d["pengguna"], "-d", "postgres", "-q", "-c",
                  f'DROP DATABASE IF EXISTS {sementara}'])

    if dipulihkan != asli:
        print(f"\nGAGAL: isi cadangan {terbaru.name} tidak sama dengan yang asli")
        return 1

    print(f"\nBERHASIL: {terbaru.name} pulih utuh, seluruh jumlah baris cocok")
    return 0


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("perintah", choices=["buat", "daftar", "pulihkan", "uji-pulih"])
    alasan.add_argument("berkas", nargs="?")
    pilihan = alasan.parse_args()

    if pilihan.perintah == "buat":
        buat()
    elif pilihan.perintah == "daftar":
        daftar()
    elif pilihan.perintah == "pulihkan":
        if not pilihan.berkas:
            sys.exit("sebutkan berkas cadangannya")
        pulihkan(pathlib.Path(pilihan.berkas))
    else:
        return uji_pulih()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
