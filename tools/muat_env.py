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
        if kunci and kunci not in os.environ:
            os.environ[kunci] = nilai
            jumlah += 1
    return jumlah
