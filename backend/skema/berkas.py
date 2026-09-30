from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, computed_field


class Berkas(BaseModel):
    id: uuid.UUID
    nama: str
    nama_asal: str
    jenis: str
    tipe_mime: str
    bita: int
    lebar: int | None = None
    tinggi: int | None = None
    dibuat_pada: dt.datetime

    @computed_field
    @property
    def alamat(self) -> str:
        return f"/unggahan/{self.nama}"

    @computed_field
    @property
    def markah(self) -> str:
        if self.jenis == "video":
            return f"!video[]({self.alamat})"
        return f"![]({self.alamat})"


class BerkasBaru(Berkas):
    sudah_ada: bool = False


class DaftarBerkas(BaseModel):
    jumlah: int
    isi: list[Berkas]
