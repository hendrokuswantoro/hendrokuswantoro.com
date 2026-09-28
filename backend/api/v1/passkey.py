from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from backend.api.tergantung import butuh_admin, butuh_admin_kuat, butuh_admin_pendaftar
from backend.api.v1.auth import JawabanMasuk, pasang_cookie
from backend.layanan import kabar
from backend.layanan import keamanan as lapis
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
    from backend.core.konfigurasi import pengaturan

    return {"siap": pengaturan().passkey_siap}


@rute.post("/daftar/mulai", summary="Mulai mendaftarkan perangkat ini")
async def daftar_mulai(
    pengguna: Annotated[dict, Depends(butuh_admin_pendaftar)],
    jenis: str = "perangkat",
) -> dict:
    if jenis not in ("perangkat", "kunci"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="jenis harus perangkat atau kunci",
        )
    _siap()
    return await layanan.mulai_daftar(str(pengguna["id"]), jenis)


@rute.post("/daftar/selesai", status_code=status.HTTP_201_CREATED,
           summary="Selesaikan pendaftaran perangkat")
async def daftar_selesai(
    badan: JawabanDaftar, pengguna: Annotated[dict, Depends(butuh_admin_pendaftar)]
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
    await _kabari(pengguna, f"sidik jari atau passkey ditambahkan: {hasil.nama}")
    return {"id": hasil.id, "nama": hasil.nama}


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="passkey tidak berlaku"
        ) from ditolak

    pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


@rute.get("", summary="Daftar passkey milik saya")
async def daftar(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return {"daftar": await layanan.daftar_milik(str(pengguna["id"]))}


@rute.delete("/{kredensial_id}", status_code=status.HTTP_204_NO_CONTENT,
             summary="Cabut satu passkey")
async def cabut(
    kredensial_id: str, pengguna: Annotated[dict, Depends(butuh_admin_kuat)]
) -> None:
    if not await layanan.hapus(str(pengguna["id"]), kredensial_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tidak ada")
    await _kabari(pengguna, "satu sidik jari atau passkey dihapus")


@rute.post("/buka/mulai", summary="Mulai membuka kunci layar dengan sidik jari")
async def buka_mulai(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    _siap()
    try:
        return await layanan.mulai_buka(str(pengguna["id"]))
    except layanan.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak


@rute.post("/buka/selesai", summary="Selesaikan membuka kunci layar")
async def buka_selesai(
    badan: JawabanMasukPasskey, pengguna: Annotated[dict, Depends(butuh_admin)]
) -> dict:
    _siap()
    try:
        await layanan.selesaikan_buka(str(pengguna["id"]), badan.jawaban)
    except layanan.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="sidik jari tidak cocok"
        ) from ditolak
    return {"terbuka": True}


async def _kabari(pengguna: dict, apa: str) -> None:
    penuh = await lapis.pengguna(str(pengguna["id"]))
    if penuh:
        await kabar.kabari_perubahan_keamanan(penuh, apa)
