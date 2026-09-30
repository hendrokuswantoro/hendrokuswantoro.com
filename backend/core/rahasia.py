from __future__ import annotations

import base64

from backend.core.konfigurasi import pengaturan
from backend.db import enkripsi

NAMA_ENV = "KUNCI_KOLOM"


class KunciTidakAda(RuntimeError):
    pass


def siap() -> bool:
    try:
        _kunci()
    except KunciTidakAda:
        return False
    return True


def _kunci() -> bytes:
    nilai = (pengaturan().kunci_kolom or "").strip()
    if not nilai:
        raise KunciTidakAda(
            f"{NAMA_ENV} belum diisi. Buat satu dengan: "
            f"python backend/db/enkripsi.py kunci, lalu ganti nama variabelnya "
            f"jadi {NAMA_ENV} di .env"
        )
    try:
        mentah = base64.b64decode(nilai, validate=True)
    except Exception as galat:
        raise KunciTidakAda(f"{NAMA_ENV} bukan base64 yang sah") from galat
    if len(mentah) != enkripsi.PANJANG_KUNCI:
        raise KunciTidakAda(
            f"{NAMA_ENV} panjangnya {len(mentah)} bita, seharusnya {enkripsi.PANJANG_KUNCI}"
        )
    return mentah


def sandikan(teks: str) -> str:
    return base64.b64encode(enkripsi.kunci(teks.encode("utf-8"), _kunci())).decode("ascii")


def bukakan(tersimpan: str) -> str:
    return enkripsi.buka(base64.b64decode(tersimpan), _kunci()).decode("utf-8")
