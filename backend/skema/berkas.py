"""Bentuk jawaban untuk foto dan video yang diunggah.

Tidak ada skema masuk di sini, dan itu bukan kelalaian. Yang masuk berupa
multipart, bukan JSON, dan yang memvalidasinya `layanan/berkas.py` dengan
membaca bita pertama berkasnya. Pydantic tidak bisa memeriksa apakah sebuah
berkas benar benar gambar; yang bisa cuma pembacaan isinya.
"""

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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alamat(self) -> str:
        """Alamat yang dipakai di dalam tulisan.

        Dihitung di sini, bukan disimpan, supaya hanya ada satu tempat yang
        memutuskan bentuknya. Dua tempat yang menyusun alamat yang sama akan
        berpisah pada hari salah satunya diubah.
        """
        return f"/unggahan/{self.nama}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def markah(self) -> str:
        """Baris markah siap tempel, sesuai yang diterima tools/markah.py."""
        if self.jenis == "video":
            return f"!video[]({self.alamat})"
        return f"![]({self.alamat})"


class BerkasBaru(Berkas):
    """Jawaban unggahan.

    `sudah_ada` benar kalau berkas dengan isi yang sama persis sudah pernah
    diunggah. Yang dikembalikan yang lama, dan penulisnya perlu tahu itu:
    tanpa keterangan ini, mengunggah foto yang sama dua kali terlihat seperti
    dua berkas padahal satu.
    """

    sudah_ada: bool = False


class DaftarBerkas(BaseModel):
    jumlah: int
    isi: list[Berkas]
