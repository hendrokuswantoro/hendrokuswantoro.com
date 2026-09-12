"""Membaca .env ke dalam environment untuk skrip yang dijalankan langsung.

Dipakai skrip basis data supaya `python backend/db/migrasi.py` cukup
dijalankan begitu saja, tanpa lebih dulu mengekspor variabelnya di shell.
Berkas .env tidak pernah ikut git, lihat .gitignore.
"""

from __future__ import annotations

import os
import pathlib


def muat(berkas: pathlib.Path | None = None) -> int:
    berkas = berkas or pathlib.Path(__file__).resolve().parent.parent / ".env"
    if not berkas.exists():
        return 0

    jumlah = 0
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        baris = baris.strip()
        if not baris or baris.startswith("#") or "=" not in baris:
            continue
        kunci, _, nilai = baris.partition("=")
        kunci, nilai = kunci.strip(), nilai.strip().strip('"').strip("'")
        # yang sudah ada di environment menang, supaya CI bisa menimpanya
        if kunci and kunci not in os.environ:
            os.environ[kunci] = nilai
            jumlah += 1
    return jumlah
