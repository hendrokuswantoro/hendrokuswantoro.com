"""Unggah foto dan video. Seluruhnya di belakang butuh_admin.

Ia terpisah dari `admin.py` karena bentuk permintaannya berbeda dari seluruh
jalur admin lain: multipart, bukan JSON, dan yang memvalidasinya pembacaan
bita berkasnya, bukan Pydantic. Menaruhnya di berkas yang sama akan membuat
satu satunya rute yang tidak berskema masuk tersembunyi di tengah sembilan
rute yang berskema.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile, status)

from backend.api.tergantung import butuh_admin_kuat
from backend.layanan import berkas as layanan
from backend.skema.berkas import BerkasBaru, DaftarBerkas

# butuh_admin_kuat: mengunggah berkas yang akan disajikan lagi dari alamat
# situs ini adalah perubahan isi, bukan pembacaan.
rute = APIRouter(
    prefix="/admin/berkas", tags=["berkas"], dependencies=[Depends(butuh_admin_kuat)]
)


@rute.get("", response_model=DaftarBerkas, summary="Foto dan video yang sudah diunggah")
async def daftar(
    batas: int = Query(40, ge=1, le=100),
    lewati: int = Query(0, ge=0),
) -> dict:
    return await layanan.daftar(batas, lewati)


@rute.post(
    "",
    response_model=BerkasBaru,
    status_code=status.HTTP_201_CREATED,
    summary="Unggah satu foto atau satu video",
)
async def unggah(
    pengguna: Annotated[dict, Depends(butuh_admin_kuat)],
    berkas: Annotated[UploadFile, File()],
    buang_metadata: Annotated[bool, Form()] = False,
) -> dict:
    """Jenisnya ditentukan dari isi berkasnya, bukan dari yang dikatakan
    pengirimnya.

    `berkas.content_type` dan `berkas.filename` keduanya datang dari
    pengirim, jadi keduanya bisa berbunyi apa saja, dan tidak satu pun dipakai
    memutuskan apa apa di sini.
    """
    try:
        return await layanan.terima(
            berkas.file,
            berkas.filename or "tanpa-nama",
            pengguna["id"],
            buang_metadata,
        )
    except layanan.Ditolak as galat:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(galat)
        ) from galat


@rute.delete(
    "/{nama}", status_code=status.HTTP_204_NO_CONTENT, summary="Hapus satu berkas"
)
async def hapus(nama: str) -> None:
    try:
        await layanan.hapus(nama)
    except layanan.TidakAda as galat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="berkas tidak ada"
        ) from galat
    except layanan.MasihDipakai as galat:
        # 409, bukan 204 diam diam. Menghapus berkas yang masih dipakai adalah
        # kegagalan yang tidak bersuara: tulisannya tetap terbit, hanya
        # gambarnya jadi kotak kosong, dan yang menyadarinya pembaca.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="berkas ini masih dipakai tulisan: " + ", ".join(galat.slug),
        ) from galat
    except layanan.Ditolak as galat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(galat)
        ) from galat
