"""Pratinjau tulisan, dibangun oleh pembangkit yang sama dengan situsnya.

Kenapa lewat server dan bukan di peramban. Pratinjau yang dihitung sendiri
oleh peramban berarti pengurai markah yang kedua, dan dua pengurai untuk satu
bahasa markah akan berpisah. Yang berpisah diam diam paling mahal: layar
pratinjau mengatakan tulisannya baik, lalu penyimpanan menolaknya dengan
alasan yang tidak pernah terlihat di pratinjau, atau lebih buruk, keduanya
menerima dan yang terbit berbeda dari yang dilihat penulisnya.

Jadi yang dipanggil di sini `tools/bangun_tulisan.badan()` persis, yaitu
fungsi yang sama yang membangun halaman blog yang sudah terbit. Kalau
pratinjaunya berhasil, yang terbit akan sama; kalau ia menolak, penyimpanan
akan menolak dengan alasan yang sama.
"""

from __future__ import annotations

import pathlib
import sys

AKAR = pathlib.Path(__file__).resolve().parents[2]
if str(AKAR / "tools") not in sys.path:
    sys.path.insert(0, str(AKAR / "tools"))

import bangun_tulisan  # noqa: E402
import markah  # noqa: E402


class Ditolak(Exception):
    """Markah yang tidak bisa dibangun, dengan alasan yang bisa dibaca."""


def bangun(isi_en: str, isi_id: str) -> dict[str, object]:
    """HTML badan tulisan, beserta hitungan katanya.

    SystemExit ditangkap dengan sengaja. `badan()` adalah alat baris perintah
    yang berhenti dengan SystemExit ketika dua bahasanya tidak sebangun, dan
    SystemExit bukan turunan Exception: kalau ia dibiarkan naik dari dalam
    sebuah permintaan HTTP, yang berhenti bukan permintaannya melainkan
    pekerjanya.
    """
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
    """Hitungan kata, sesudah markahnya ditanggalkan.

    Yang dihitung kata yang akan dibaca orang, bukan tanda bintang dan kurung
    siku. Alamat di dalam tautan juga tidak ikut, sebab tidak ada yang
    membacanya.
    """
    try:
        blok = markah.blok(sumber)
    except markah.MarkahSalah:
        # Saat penulisnya masih mengetik, markahnya memang sering setengah
        # jadi. Hitungan kasar lebih berguna daripada angka yang menghilang.
        return len([k for k in sumber.split() if k])

    jumlah = 0
    for b in blok:
        for potong in (b.teks, *b.butir):
            jumlah += len([k for k in markah.polos(potong).split() if k])
    return jumlah
