from __future__ import annotations

import json
import math

from konftes import AKAR

SUMBER = AKAR / "content" / "parkir"
AMBANG_M = 30.0


def baca(nama: str):
    return json.loads((SUMBER / f"{nama}.json").read_text(encoding="utf-8"))


KAWASAN = baca("kawasan")
TARIF = baca("tarif")
CAKUPAN = baca("cakupan")


def _di_dalam_cincin(x: float, y: float, cincin: list) -> bool:
    dalam = False
    n = len(cincin)
    for i in range(n):
        x1, y1 = cincin[i]
        x2, y2 = cincin[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            dalam = not dalam
    return dalam


def di_dalam_cakupan(lat: float, lon: float) -> bool:
    cincin = CAKUPAN["geometry"]["coordinates"]
    if not _di_dalam_cincin(lon, lat, cincin[0]):
        return False
    return not any(_di_dalam_cincin(lon, lat, c) for c in cincin[1:])


def _jarak(p, a, b, m):
    px, py = (p[0] - a[0]) * m[0], (p[1] - a[1]) * m[1]
    bx, by = (b[0] - a[0]) * m[0], (b[1] - a[1]) * m[1]
    kuadrat = bx * bx + by * by
    t = 0.0 if kuadrat == 0 else max(0.0, min(1.0, (px * bx + py * by) / kuadrat))
    return math.hypot(px - t * bx, py - t * by)


def cari_kawasan(lat: float, lon: float) -> dict:
    if not di_dalam_cakupan(lat, lon):
        return {"kawasan": None, "ruas": None, "luar": True}
    m = (111320 * math.cos(math.radians(lat)), 110540)
    terbaik = (math.inf, None)
    for fitur in KAWASAN["features"]:
        c = fitur["geometry"]["coordinates"]
        for i in range(len(c) - 1):
            d = _jarak((lon, lat), c[i], c[i + 1], m)
            if d < terbaik[0]:
                terbaik = (d, fitur["properties"])
    if terbaik[0] > AMBANG_M:
        return {"kawasan": "III", "ruas": None, "luar": False}
    return {"kawasan": terbaik[1]["k"], "ruas": terbaik[1]["n"], "luar": False}


def hitung_tarif(kendaraan: str, kawasan: str | None, jam: float, layanan: str) -> int | None:
    if not kawasan:
        return None
    kw = "-" if layanan == "pasar" else kawasan
    baris = next(
        (t for t in TARIF
         if t["layanan"] == layanan and t["kendaraan"] == kendaraan and t["kawasan"] == kw),
        None,
    )
    if baris is None:
        return None
    lanjut = baris["tarif_per_jam_lanjut"]
    if not baris["progresif"] or lanjut is None:
        return baris["tarif_2jam_pertama"]
    return baris["tarif_2jam_pertama"] + max(math.ceil(jam) - 2, 0) * lanjut
