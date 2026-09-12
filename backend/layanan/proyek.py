"""Aturan bisnis untuk proyek."""

from __future__ import annotations

from typing import Any

from backend.repositori import proyek as repo
from backend.skema.proyek import DaftarProyek, KumpulanFitur, Proyek
from backend.skema.umum import Teks


def _teks(baris: dict[str, Any], nama: str) -> Teks:
    return Teks(en=baris[f"{nama}_en"], id=baris[f"{nama}_id"])


def _proyek(baris: dict[str, Any]) -> Proyek:
    return Proyek(
        slug=baris["slug"],
        urut=baris["urut"],
        judul=_teks(baris, "judul"),
        ringkas=_teks(baris, "ringkas"),
        peran=_teks(baris, "peran"),
        badge=_teks(baris, "badge"),
        kategori=list(baris["kategori"]),
        jenis_peta=baris["jenis_peta"],
        teknologi=list(baris["teknologi"]),
        gambar=baris["gambar"],
        gambar_alt=_teks(baris, "gambar_alt"),
        lng=baris["lng"],
        lat=baris["lat"],
    )


async def daftar(batas: int, lewati: int, kategori: str | None) -> DaftarProyek:
    baris = await repo.daftar(batas, lewati, kategori)
    return DaftarProyek(
        jumlah=await repo.jumlah(kategori),
        batas=batas,
        lewati=lewati,
        isi=[_proyek(b) for b in baris],
    )


async def satu(slug: str) -> Proyek | None:
    baris = await repo.satu(slug)
    return None if baris is None else _proyek(baris)


async def geojson() -> KumpulanFitur:
    """Divalidasi lewat Pydantic sebelum keluar.

    PostGIS sudah merakitnya dengan benar, tetapi memvalidasinya sekali lagi
    berarti perubahan skema yang merusak bentuk GeoJSON gagal di sini, bukan
    di peta orang lain berminggu minggu kemudian.
    """
    return KumpulanFitur.model_validate(await repo.geojson())


async def dekat(lng: float, lat: float, meter: int, batas: int) -> list[dict[str, Any]]:
    baris = await repo.dekat(lng, lat, meter, batas)
    return [{**_proyek(b).model_dump(), "jarak_m": b["jarak_m"]} for b in baris]
