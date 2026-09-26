from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Teks(BaseModel):
    model_config = ConfigDict(frozen=True)

    en: str = Field(min_length=1)
    id: str = Field(min_length=1)


class Halaman(BaseModel):
    jumlah: int
    batas: int
    lewati: int
