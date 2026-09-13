"""Titik akhir passkey.

Empat untuk alurnya, dua untuk mengelolanya. Alur WebAuthn selalu dua
langkah, mulai lalu selesai, karena tantangannya harus lahir di server dan
ditandatangani perangkat di antara keduanya.

Perhatikan yang **tidak** ada di sini: tidak ada titik akhir yang menerima
email lalu menjawab kredensial mana yang dimilikinya. Jawaban semacam itu
memberi tahu siapa pun yang bertanya bahwa sebuah email terdaftar, dan itu
separuh pekerjaan penebak. Passkey discoverable tidak membutuhkannya.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from backend.api.tergantung import butuh_admin
from backend.api.v1.auth import JawabanMasuk, pasang_cookie
from backend.layanan import passkey as layanan

rute = APIRouter(prefix="/auth/passkey", tags=["auth"])


class JawabanDaftar(BaseModel):
    nama: str = Field(default="", max_length=layanan.NAMA_MAKS)
    jawaban: dict[str, Any]


class JawabanMasukPasskey(BaseModel):
    jawaban: dict[str, Any]


def _siap() -> None:
    from backend.core.konfigurasi import pengaturan

    if not pengaturan().passkey_siap:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="passkey belum dikonfigurasi",
        )


@rute.get("/siap", summary="Apakah jalur passkey hidup")
async def siap() -> dict:
    """Dipakai halaman admin untuk memutuskan menampilkan tombolnya atau
    tidak. Tidak menyebut apa pun tentang pengguna mana pun."""
    from backend.core.konfigurasi import pengaturan

    return {"siap": pengaturan().passkey_siap}


# --------------------------------------------------------------- daftar ---


@rute.post("/daftar/mulai", summary="Mulai mendaftarkan perangkat ini")
async def daftar_mulai(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    _siap()
    return await layanan.mulai_daftar(str(pengguna["id"]))


@rute.post("/daftar/selesai", status_code=status.HTTP_201_CREATED,
           summary="Selesaikan pendaftaran perangkat")
async def daftar_selesai(
    badan: JawabanDaftar, pengguna: Annotated[dict, Depends(butuh_admin)]
) -> dict:
    _siap()
    try:
        hasil = await layanan.selesaikan_daftar(
            str(pengguna["id"]), badan.jawaban, badan.nama
        )
    except layanan.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak
    return {"id": hasil.id, "nama": hasil.nama}


# ---------------------------------------------------------------- masuk ---


@rute.post("/masuk/mulai", summary="Mulai masuk dengan passkey")
async def masuk_mulai() -> dict:
    _siap()
    return await layanan.mulai_masuk()


@rute.post("/masuk/selesai", response_model=JawabanMasuk,
           summary="Selesaikan masuk dengan passkey")
async def masuk_selesai(badan: JawabanMasukPasskey, jawaban: Response) -> JawabanMasuk:
    _siap()
    try:
        hasil = await layanan.selesaikan_masuk(badan.jawaban)
    except layanan.Ditolak as ditolak:
        # 401 apa pun sebabnya. Membedakan "kredensial tidak dikenal" dari
        # "tanda tangan salah" memberi tahu penebak mana yang sudah benar.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="passkey tidak berlaku"
        ) from ditolak

    pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


# ------------------------------------------------------------- mengelola ---


@rute.get("", summary="Daftar passkey milik saya")
async def daftar(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return {"daftar": await layanan.daftar_milik(str(pengguna["id"]))}


@rute.delete("/{kredensial_id}", status_code=status.HTTP_204_NO_CONTENT,
             summary="Cabut satu passkey")
async def cabut(
    kredensial_id: str, pengguna: Annotated[dict, Depends(butuh_admin)]
) -> None:
    if not await layanan.hapus(str(pengguna["id"]), kredensial_id):
        # 404, bukan 403. Membedakan "bukan milikmu" dari "tidak ada" akan
        # memberi tahu penanya bahwa kredensial itu ada dan milik orang lain.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
