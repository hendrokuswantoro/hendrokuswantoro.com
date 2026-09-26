"""Dependensi yang dipakai router. Termasuk penjaga otorisasi.

Bab 15.9: otorisasi wajib diverifikasi di backend. Tidak ada satu pun
keputusan akses yang dipercayakan ke peramban.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from backend.core import cabut as daftar_cabut
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

    # Sesi yang sudah dicabut mematikan tokennya sekarang, bukan lima belas
    # menit lagi. Menjawab False saat Redis tidak ada, dan halaman keamanan
    # menyebutkan kalau pemendekan itu sedang tidak berlaku.
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
    """Bab 15.9: bedakan autentikasi dan otorisasi.

    Token yang sah belum tentu token yang berhak. 403 dan 401 juga berbeda
    artinya: yang satu belum masuk, yang satu sudah masuk tetapi tidak boleh.
    """
    if pengguna["peran"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="bukan admin")
    return pengguna


async def butuh_admin_kuat(
    pengguna: Annotated[dict, Depends(butuh_admin)],
) -> dict:
    """Admin yang sesinya lahir lewat faktor kedua.

    Dipakai jalur yang mengubah isi situs: menulis, menerbitkan, mengunggah,
    menghapus. Sandi saja membuka permukaan itu sampai 19 September 2026, dan
    satu rahasia yang bisa ditebak, dipakai ulang, atau dipancing lewat
    halaman palsu bukan penjaga yang pantas untuknya.

    Yang TIDAK memakainya: halaman keamanan. Kalau ia ikut ditutup, pemilik
    yang belum memasang TOTP tidak akan pernah bisa memasangnya, dan aturan
    ini berubah jadi pintu yang dikunci dari dalam. Jadi jalan masuknya tetap
    terbuka, dan yang tertutup cuma jalan menulisnya.

    Passkey dihitung faktor kedua dengan sendirinya: ia menandatangani dengan
    kunci yang tidak pernah meninggalkan perangkat dan terikat pada alamat
    situs ini.

    403, bukan 401. Tokennya sah; yang kurang buktinya, dan menjawab 401 akan
    membuat peramban mengira sesinya habis lalu memutar refresh selamanya.
    """
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
