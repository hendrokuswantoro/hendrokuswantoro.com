from __future__ import annotations

import datetime as dt
import re

from pydantic import BaseModel, Field, field_validator, model_validator

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


PANJANG_ISI = 200_000
PANJANG_LEDE = 2_000


class TulisanMasuk(BaseModel):
    slug: str = Field(min_length=3, max_length=150)
    tanggal: dt.date

    judul_en: str = Field(min_length=1, max_length=200)
    judul_id: str = Field(min_length=1, max_length=200)
    ringkas_en: str = Field(min_length=1, max_length=300)
    ringkas_id: str = Field(min_length=1, max_length=300)
    keterangan_en: str = Field(min_length=1, max_length=300)
    keterangan_id: str = Field(min_length=1, max_length=300)
    lede_en: str = Field(min_length=1, max_length=PANJANG_LEDE)
    lede_id: str = Field(min_length=1, max_length=PANJANG_LEDE)
    isi_en: str = Field(min_length=1, max_length=PANJANG_ISI)
    isi_id: str = Field(min_length=1, max_length=PANJANG_ISI)

    tag_en: str = Field(min_length=1, max_length=50)
    tag_id: str = Field(min_length=1, max_length=50)
    baca_en: str = Field(min_length=1, max_length=30)
    baca_id: str = Field(min_length=1, max_length=30)

    @field_validator("slug")
    @classmethod
    def slug_bentuknya_benar(cls, nilai: str) -> str:
        if not SLUG.match(nilai):
            raise ValueError(
                "slug hanya boleh huruf kecil, angka, dan tanda hubung, "
                "sebab slug adalah alamatnya"
            )
        return nilai

    @model_validator(mode="after")
    def dua_bahasa_sebangun(self) -> "TulisanMasuk":
        import pathlib
        import sys

        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
        import markah

        try:
            en = markah.blok(self.isi_en)
            idn = markah.blok(self.isi_id)
        except markah.MarkahSalah as galat:
            raise ValueError(str(galat)) from galat

        if len(en) != len(idn):
            raise ValueError(
                f"jumlah blok tidak sama: Inggris {len(en)}, Indonesia {len(idn)}"
            )
        for nomor, (a, b) in enumerate(zip(en, idn), 1):
            if a.jenis != b.jenis:
                raise ValueError(
                    f"blok ke {nomor} beda jenis: {a.jenis} lawan {b.jenis}"
                )
        return self


class TulisanUbah(BaseModel):
    judul_en: str | None = Field(default=None, min_length=1, max_length=200)
    judul_id: str | None = Field(default=None, min_length=1, max_length=200)
    ringkas_en: str | None = Field(default=None, min_length=1, max_length=300)
    ringkas_id: str | None = Field(default=None, min_length=1, max_length=300)
    keterangan_en: str | None = Field(default=None, min_length=1, max_length=300)
    keterangan_id: str | None = Field(default=None, min_length=1, max_length=300)
    lede_en: str | None = Field(default=None, min_length=1, max_length=PANJANG_LEDE)
    lede_id: str | None = Field(default=None, min_length=1, max_length=PANJANG_LEDE)
    isi_en: str | None = Field(default=None, min_length=1, max_length=PANJANG_ISI)
    isi_id: str | None = Field(default=None, min_length=1, max_length=PANJANG_ISI)
    tag_en: str | None = Field(default=None, min_length=1, max_length=50)
    tag_id: str | None = Field(default=None, min_length=1, max_length=50)
    baca_en: str | None = Field(default=None, min_length=1, max_length=30)
    baca_id: str | None = Field(default=None, min_length=1, max_length=30)
    tanggal: dt.date | None = None

    @model_validator(mode="after")
    def ada_yang_diubah(self) -> "TulisanUbah":
        if not self.model_dump(exclude_none=True):
            raise ValueError("tidak ada satu pun kolom yang diubah")
        return self
