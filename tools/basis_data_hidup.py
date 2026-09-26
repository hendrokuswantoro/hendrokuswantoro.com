from __future__ import annotations

import os
import pathlib
import socket
import sys
import urllib.parse

AKAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR / "tools"))

TENGGAT_DETIK = 3.0


def dsn() -> str:
    nilai = os.environ.get("DSN", "")
    if nilai:
        return nilai
    berkas = AKAR / ".env"
    if not berkas.exists():
        return ""
    for baris in berkas.read_text(encoding="utf-8").splitlines():
        baris = baris.strip()
        if baris.startswith("DSN=") and not baris.startswith("#"):
            return baris.split("=", 1)[1].strip()
    return ""


def hidup(alamat: str) -> bool:
    if not alamat:
        return False
    urai = urllib.parse.urlparse(alamat)
    inang = urai.hostname or "127.0.0.1"
    porta = urai.port or 5432
    try:
        with socket.create_connection((inang, porta), timeout=TENGGAT_DETIK):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(0 if hidup(dsn()) else 1)
