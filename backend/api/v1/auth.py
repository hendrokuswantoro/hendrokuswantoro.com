"""Masuk, perpanjang, keluar.

Refresh token hidup di cookie HttpOnly Secure SameSite=Strict, bukan di
badan jawaban. Bab 15.10. Token yang bisa dibaca JavaScript adalah token
yang bisa diambil satu XSS.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from backend.api.tergantung import alamat_teringkas, butuh_admin
from backend.core import keamanan as inti
from backend.core.konfigurasi import pengaturan
from backend.layanan import autentikasi as layanan
from backend.layanan import keamanan as lapis

rute = APIRouter(prefix="/auth", tags=["auth"])

NAMA_COOKIE = "hk_refresh"


class Kredensial(BaseModel):
    email: EmailStr
    sandi: str = Field(min_length=8, max_length=200)


class JawabanMasuk(BaseModel):
    """Satu bentuk jawaban untuk dua keadaan, dan `tahap` yang membedakannya.

    `tahap="selesai"` berarti sesinya terbit dan `akses` terisi.
    `tahap="faktor2"` berarti sandinya benar dan belum cukup: `tiket` terisi,
    `akses` kosong, dan `cara` menyebut faktor kedua apa yang bisa dipakai.

    Kenapa tiket, bukan sesi yang ditandai "belum lengkap": sesi sudah berupa
    kunci, dan apa pun yang lupa memeriksa tandanya akan menerimanya. Tiket
    audiensnya berbeda, jadi pustaka JWT-nya sendiri yang menolaknya di setiap
    pintu selain pintu faktor kedua, bukan satu baris if yang bisa terlupa.
    """

    tahap: str = "selesai"
    akses: str = ""
    umur_detik: int = 0
    nama: str = ""
    peran: str = ""
    tiket: str = ""
    cara: list[str] = []


def pasang_cookie(jawaban: Response, hasil: layanan.Masuk) -> None:
    """Dipakai jalur sandi dan jalur passkey. Satu tempat, supaya tidak
    mungkin salah satunya lupa httponly atau lupa samesite."""
    atur = pengaturan()
    jawaban.set_cookie(
        NAMA_COOKIE,
        hasil.refresh,
        httponly=True,
        secure=atur.cookie_aman,
        samesite="strict",
        expires=hasil.refresh_kadaluarsa,
        path="/api/v1/auth",
    )


def _wajib_siap() -> None:
    if not pengaturan().auth_siap:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="autentikasi belum dikonfigurasi",
        )


@rute.post("/login", response_model=JawabanMasuk, summary="Masuk sebagai admin")
async def login(
    kredensial: Kredensial,
    permintaan: Request,
    jawaban: Response,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> JawabanMasuk:
    _wajib_siap()
    try:
        pengguna = await layanan.periksa_sandi(kredensial.email, kredensial.sandi, alamat)
    except layanan.Ditolak as ditolak:
        # 429 kalau terkunci, 401 kalau salah. Keduanya tidak pernah
        # menyebut apakah emailnya terdaftar.
        kode = status.HTTP_429_TOO_MANY_REQUESTS if ditolak.terkunci else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=kode, detail=str(ditolak)) from ditolak

    peramban = permintaan.headers.get("user-agent", "")

    # Sandi yang benar belum tentu cukup. Kalau ada faktor kedua yang berlaku,
    # yang terbit tiket, bukan sesi.
    cara = await lapis.faktor_kedua_yang_berlaku(pengguna)
    if cara:
        tiket, umur = inti.buat_tiket_faktor_kedua(str(pengguna["id"]), cara)
        await lapis.catat_peristiwa(
            str(pengguna["id"]), "sandi_benar", True, "menunggu faktor kedua", alamat, peramban
        )
        if cara == ["email"]:
            # Kodenya dikirim sekarang juga: satu langkah lebih sedikit untuk
            # pemiliknya, dan kode yang kedaluwarsa tetap bisa diminta ulang.
            try:
                await lapis.kirim_otp_masuk(pengguna, alamat)
            except lapis.Ditolak:
                pass
        return JawabanMasuk(tahap="faktor2", tiket=tiket, umur_detik=umur, cara=cara)

    hasil = await layanan.terbitkan(pengguna)
    pasang_cookie(jawaban, hasil)
    await lapis.catat_peristiwa(str(pengguna["id"]), "masuk", True, "sandi", alamat, peramban)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


class FaktorKedua(BaseModel):
    """Satu bentuk untuk empat cara, dan yang tidak dipakai dibiarkan kosong.

    `kode` untuk totp, email, dan pemulihan. `tantangan` dan `bingkai` untuk
    wajah. Dipisah jadi dua model akan membuat routernya bercabang dua sejak
    baris pertama tanpa alasan: yang berbeda cuma isian, bukan alurnya.
    """

    tiket: str
    cara: str = Field(pattern="^(totp|email|pemulihan|wajah)$")
    kode: str = Field(default="", max_length=40)
    tantangan: str = Field(default="", max_length=64)
    # Tiga bingkai base64. Batas panjangnya dijaga lagi di lapisan wajah,
    # per bingkai, dan itu yang benar benar menahan: batas di sini menahan
    # badan permintaan, batas di sana menahan gambar yang didekode.
    bingkai: list[str] = Field(default_factory=list, max_length=5)


@rute.post("/faktor-kedua", response_model=JawabanMasuk, summary="Selesaikan faktor kedua")
async def faktor_kedua(
    isian: FaktorKedua,
    permintaan: Request,
    jawaban: Response,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> JawabanMasuk:
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="tiket tidak berlaku atau sudah kedaluwarsa, ulangi dari awal",
        )

    pengguna_id = muatan["sub"]
    if isian.cara not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cara tidak tersedia")

    if isian.cara == "wajah":
        if not isian.tantangan or not isian.bingkai:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="butuh tantangan dan bingkai",
            )
        lolos = await lapis.periksa_wajah(
            pengguna_id, isian.tantangan, isian.bingkai, alamat
        )
    elif not isian.kode:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="kode kosong")
    elif isian.cara == "totp":
        lolos = await lapis.periksa_totp(pengguna_id, isian.kode, alamat)
    elif isian.cara == "email":
        lolos = await lapis.periksa_otp_masuk(pengguna_id, isian.kode, alamat)
    else:
        lolos = await lapis.periksa_pemulihan(pengguna_id, isian.kode, alamat)

    if not lolos:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="kode salah")

    pengguna = await lapis.pengguna(pengguna_id)
    if not pengguna:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="kode salah")

    hasil = await layanan.terbitkan(pengguna)
    pasang_cookie(jawaban, hasil)
    await lapis.catat_peristiwa(
        pengguna_id, "masuk", True, isian.cara, alamat, permintaan.headers.get("user-agent", "")
    )
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


class MintaKode(BaseModel):
    tiket: str


@rute.post("/faktor-kedua/tantangan-wajah", summary="Minta urutan gerakan untuk verifikasi wajah")
async def tantangan_wajah(isian: MintaKode) -> dict:
    """Urutan gerakannya diputuskan server dan berlaku dua menit.

    Tanpa ini, "kirim tiga foto wajah Anda" bisa dijawab dengan tiga berkas
    yang sudah disiapkan sejak lama. Dengan ini, ketiganya harus kebetulan
    memuat urutan yang baru saja diminta. Perlu dikatakan terus terang bahwa
    menyulitkan bukan menutup: rekaman video yang cukup panjang tetap memuat
    semuanya.
    """
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None or "wajah" not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")
    try:
        return await lapis.tantangan_wajah(muatan["sub"])
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(ditolak)
        ) from ditolak


@rute.post("/faktor-kedua/kirim-ulang", summary="Kirim ulang kode ke email")
async def kirim_ulang(
    isian: MintaKode,
    alamat: Annotated[str, Depends(alamat_teringkas)],
) -> dict:
    _wajib_siap()
    muatan = inti.baca_tiket_faktor_kedua(isian.tiket)
    if muatan is None or "email" not in muatan.get("cara", []):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")

    pengguna = await lapis.pengguna(muatan["sub"])
    if not pengguna:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tiket tidak berlaku")
    try:
        hasil = await lapis.kirim_otp_masuk(pengguna, alamat)
    except lapis.Ditolak as ditolak:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(ditolak)
        ) from ditolak
    return {"terkirim": hasil.terkirim, "catatan": hasil.catatan}


@rute.post("/refresh", response_model=JawabanMasuk, summary="Putar refresh token")
async def refresh(permintaan: Request, jawaban: Response) -> JawabanMasuk:
    _wajib_siap()
    token = permintaan.cookies.get(NAMA_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="tidak ada sesi")
    try:
        hasil = await layanan.perpanjang(token)
    except layanan.Ditolak as ditolak:
        jawaban.delete_cookie(NAMA_COOKIE, path="/api/v1/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ditolak)
        ) from ditolak

    pasang_cookie(jawaban, hasil)
    return JawabanMasuk(
        akses=hasil.akses, umur_detik=hasil.umur_detik, nama=hasil.nama, peran=hasil.peran
    )


@rute.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Keluar")
async def logout(permintaan: Request, jawaban: Response) -> None:
    token = permintaan.cookies.get(NAMA_COOKIE)
    if token:
        await layanan.keluar(token)
    jawaban.delete_cookie(NAMA_COOKIE, path="/api/v1/auth")


@rute.post("/logout-semua", summary="Keluar dari semua perangkat")
async def logout_semua(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    jumlah = await layanan.keluar_semua(pengguna["id"])
    return {"sesi_dicabut": jumlah}


@rute.get("/saya", summary="Siapa yang sedang masuk")
async def saya(pengguna: Annotated[dict, Depends(butuh_admin)]) -> dict:
    return pengguna
