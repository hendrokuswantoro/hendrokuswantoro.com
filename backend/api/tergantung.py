from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from backend.core import cabut as daftar_cabut
from backend.core import keamanan
from backend.core.konfigurasi import pengaturan


def alamat_teringkas(permintaan: Request) -> str:
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

    if await daftar_cabut.sudah_dicabut(muatan.get("sid")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="sesi sudah dicabut",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": muatan["sub"],
        "peran": muatan.get("peran", "visitor"),
        "sesi": muatan.get("sid"),
        "faktor_kedua": bool(muatan.get("f2")),
    }


async def butuh_admin(
    pengguna: Annotated[dict, Depends(pengguna_kini)],
) -> dict:
    if pengguna["peran"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="bukan admin")
    return pengguna


async def butuh_admin_kuat(
    pengguna: Annotated[dict, Depends(butuh_admin)],
) -> dict:
    if not pengaturan().faktor_kedua_wajib:
        return pengguna
    if pengguna.get("faktor_kedua"):
        return pengguna
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "jalur ini menuntut faktor kedua. Pasang TOTP atau passkey di "
            "halaman keamanan, lalu masuk lagi."
        ),
    )


async def butuh_admin_pendaftar(
    pengguna: Annotated[dict, Depends(butuh_admin)],
) -> dict:
    if not pengaturan().faktor_kedua_wajib:
        return pengguna
    if pengguna.get("faktor_kedua"):
        return pengguna
    from backend.layanan import keamanan as lapis

    if await lapis.punya_faktor(pengguna["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "akun ini sudah punya faktor kedua. Masuk lewat faktor itu dulu, "
                "baru daftarkan yang lain."
            ),
        )
    return pengguna
