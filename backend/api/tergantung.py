"""Dependensi yang dipakai router. Termasuk penjaga otorisasi.

Bab 15.9: otorisasi wajib diverifikasi di backend. Tidak ada satu pun
keputusan akses yang dipercayakan ke peramban.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from backend.core import keamanan
from backend.core.konfigurasi import pengaturan


def alamat_teringkas(permintaan: Request) -> str:
    """IP tidak pernah disimpan apa adanya, bahkan di tabel percobaan gagal."""
    alamat = permintaan.client.host if permintaan.client else "tidak-diketahui"
    return keamanan.ringkas(alamat)


async def pengguna_kini(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not pengaturan().auth_siap:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="autentikasi belum dikonfigurasi",
        )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="butuh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    muatan = keamanan.baca_access_token(authorization.split(" ", 1)[1].strip())
    if muatan is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token tidak berlaku",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": muatan["sub"], "peran": muatan.get("peran", "visitor")}


async def butuh_admin(
    pengguna: Annotated[dict, Depends(pengguna_kini)],
) -> dict:
    """Bab 15.9: bedakan autentikasi dan otorisasi.

    Token yang sah belum tentu token yang berhak. 403 dan 401 juga berbeda
    artinya: yang satu belum masuk, yang satu sudah masuk tetapi tidak boleh.
    """
    if pengguna["peran"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="bukan admin")
    return pengguna
