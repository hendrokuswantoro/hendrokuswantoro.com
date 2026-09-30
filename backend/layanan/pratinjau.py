from __future__ import annotations

import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parents[2]
if str(AKAR / "tools") not in sys.path:
    sys.path.insert(0, str(AKAR / "tools"))

import bangun_tulisan
import markah


class Ditolak(Exception):
    pass


def bangun(isi_en: str, isi_id: str) -> dict[str, object]:
    try:
        badan = bangun_tulisan.badan(isi_en, isi_id)
    except markah.MarkahSalah as galat:
        raise Ditolak(str(galat)) from galat
    except SystemExit as galat:
        raise Ditolak(str(galat)) from galat

    return {
        "html": badan,
        "kata_en": kata(isi_en),
        "kata_id": kata(isi_id),
        "blok": len(markah.blok(isi_en)),
    }


def kata(sumber: str) -> int:
    try:
        blok = markah.blok(sumber)
    except markah.MarkahSalah:
        return len([k for k in sumber.split() if k])

    jumlah = 0
    for b in blok:
        for potong in (b.teks, *b.butir):
            jumlah += len([k for k in markah.polos(potong).split() if k])
    return jumlah
