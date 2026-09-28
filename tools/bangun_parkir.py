"""Membangun assets/js/parkir-data.js dari content/parkir/*.json.

    python tools/bangun_parkir.py            # tulis
    python tools/bangun_parkir.py --periksa  # bandingkan saja, keluar 1 bila beda
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent
SUMBER = AKAR / "content" / "parkir"
TUJUAN = AKAR / "assets" / "js" / "parkir-data.js"
BAGIAN = ("kawasan", "tarif", "titik", "cakupan")


def data() -> dict:
    return {
        nama: json.loads((SUMBER / f"{nama}.json").read_text(encoding="utf-8"))
        for nama in BAGIAN
    }


def isi() -> str:
    teks = json.dumps(data(), ensure_ascii=False, separators=(",", ":"))
    return f"window.HK_PARKIR_DATA={teks};\n"


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true")
    pilihan = alasan.parse_args()

    baru = isi()
    lama = TUJUAN.read_text(encoding="utf-8") if TUJUAN.exists() else None
    if pilihan.periksa:
        if lama != baru:
            print(f"BEDA  {TUJUAN.relative_to(AKAR).as_posix()}")
            return 1
        print(f"sama  {TUJUAN.relative_to(AKAR).as_posix()}")
        return 0
    if lama != baru:
        TUJUAN.write_text(baru, encoding="utf-8", newline="\n")
        print(f"tulis {TUJUAN.relative_to(AKAR).as_posix()}")
    else:
        print(f"tetap {TUJUAN.relative_to(AKAR).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
