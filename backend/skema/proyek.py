from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.skema.umum import Halaman, Teks

Kategori = Literal["app", "analysis", "satellite", "design"]


class Proyek(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    urut: int
    judul: Teks
    ringkas: Teks
    peran: Teks
    badge: Teks
    kategori: list[Kategori] = Field(min_length=1)
    jenis_peta: Kategori
    teknologi: list[str] = Field(min_length=1)
    gambar: str
    gambar_alt: Teks
    lng: float = Field(ge=94, le=142)
    lat: float = Field(ge=-12, le=7)


class DaftarProyek(Halaman):
    isi: list[Proyek]


# --- GeoJSON, bentuknya ditentukan RFC 7946 ---------------------------------


class Titik(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class SifatProyek(BaseModel):
    model_config = ConfigDict(frozen=True)
    slug: str
    judul: Teks
    kategori: list[Kategori]
    jenis_peta: Kategori
    teknologi: list[str]


class Fitur(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: Literal["Feature"] = "Feature"
    geometry: Titik
    properties: SifatProyek


class KumpulanFitur(BaseModel):
    """Titik ini tempat menggantungkan penanda, bukan koordinat survei.
    Keterangan yang sama tercetak di bawah peta dan di komentar kolom geom."""

    model_config = ConfigDict(frozen=True)
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Fitur]
