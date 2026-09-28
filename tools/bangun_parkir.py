"""Membangun data peta parkir dari content/parkir/*.json, untuk kedua port.

    assets/js/parkir-data.js       situs yang terbit
    next/content/parkir-data.json  port Next

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
TUJUAN_NEXT = AKAR / "next" / "content" / "parkir-data.json"
BAGIAN = ("kawasan", "tarif", "titik", "cakupan")


def data() -> dict:
    return {
        nama: json.loads((SUMBER / f"{nama}.json").read_text(encoding="utf-8"))
        for nama in BAGIAN
    }


def padat() -> str:
    return json.dumps(data(), ensure_ascii=False, separators=(",", ":"))


def isi() -> str:
    return f"window.HK_PARKIR_DATA={padat()};\n"


def isi_next() -> str:
    return padat() + "\n"


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true")
    pilihan = alasan.parse_args()

    beda = 0
    for tujuan, baru in ((TUJUAN, isi()), (TUJUAN_NEXT, isi_next())):
        nama = tujuan.relative_to(AKAR).as_posix()
        lama = tujuan.read_text(encoding="utf-8") if tujuan.exists() else None
        if pilihan.periksa:
            print(f"{'sama ' if lama == baru else 'BEDA '} {nama}")
            beda += lama != baru
        elif lama != baru:
            tujuan.write_text(baru, encoding="utf-8", newline="\n")
            print(f"tulis {nama}")
        else:
            print(f"tetap {nama}")
    return 1 if beda else 0


if __name__ == "__main__":
    sys.exit(main())
