from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from backend.skema.umum import Halaman, Teks


class TulisanRingkas(BaseModel):
    """Yang dibutuhkan kartu di halaman Blog."""

    model_config = ConfigDict(frozen=True)

    slug: str
    tanggal: dt.date
    judul: Teks
    ringkas: Teks
    tag: Teks
    baca: Teks


class TulisanPenuh(TulisanRingkas):
    keterangan: Teks
    lede: Teks
    isi_en: str = Field(min_length=1)
    isi_id: str = Field(min_length=1)


class DaftarTulisan(Halaman):
    isi: list[TulisanRingkas]
