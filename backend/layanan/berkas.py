from __future__ import annotations

import hashlib
import os
import pathlib
import secrets
from typing import Any, BinaryIO

from backend.core.konfigurasi import pengaturan
from backend.layanan import metadata
from backend.repositori import berkas as repo


class Ditolak(Exception):
    pass


class TidakAda(Exception):
    pass


class MasihDipakai(Exception):
    def __init__(self, slug: list[str]) -> None:
        super().__init__(", ".join(slug))
        self.slug = slug


GAMBAR = {
    "image/webp": ".webp",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/avif": ".avif",
}
VIDEO = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}

POTONG = 1024 * 256


def folder() -> pathlib.Path:
    jalur = pathlib.Path(pengaturan().unggahan_dir)
    if not jalur.is_absolute():
        jalur = pathlib.Path(__file__).resolve().parents[2] / jalur
    jalur.mkdir(parents=True, exist_ok=True)
    return jalur


def jalur(nama: str) -> pathlib.Path:
    if not nama or "/" in nama or "\\" in nama or nama.startswith("."):
        raise Ditolak(f"nama berkas tidak sah: {nama[:40]!r}")
    hasil = (folder() / nama).resolve()
    if hasil.parent != folder().resolve():
        raise Ditolak(f"nama berkas tidak sah: {nama[:40]!r}")
    return hasil


def kenali(awal: bytes) -> tuple[str, str]:
    if awal.startswith(metadata.TANDA_PNG):
        return "gambar", "image/png"
    if awal.startswith(b"\xff\xd8\xff"):
        return "gambar", "image/jpeg"
    if awal.startswith((b"GIF87a", b"GIF89a")):
        return "gambar", "image/gif"
    if metadata.adalah_webp(awal):
        return "gambar", "image/webp"
    if awal.startswith(b"\x1a\x45\xdf\xa3"):
        return "video", "video/webm"

    if awal[4:8] == b"ftyp":
        merek = awal[8:12]
        if merek in (b"avif", b"avis"):
            return "gambar", "image/avif"
        if merek in (b"isom", b"iso2", b"iso4", b"iso5", b"iso6", b"mp41",
                     b"mp42", b"avc1", b"M4V ", b"dash"):
            return "video", "video/mp4"
        raise Ditolak(
            f"berkas MP4 dengan merek {merek.decode('latin-1')!r} tidak dikenali"
        )

    raise Ditolak(
        "isi berkasnya bukan foto atau video yang dikenali. "
        "Yang diterima: " + ", ".join([*GAMBAR, *VIDEO])
    )


def ukuran(tipe: str, data: bytes) -> tuple[int, int]:
    if tipe == "image/png":
        if len(data) >= 24 and data[12:16] == b"IHDR":
            return (int.from_bytes(data[16:20], "big"),
                    int.from_bytes(data[20:24], "big"))

    elif tipe == "image/gif":
        if len(data) >= 10:
            return (int.from_bytes(data[6:8], "little"),
                    int.from_bytes(data[8:10], "little"))

    elif tipe == "image/jpeg":
        hasil = _ukuran_jpeg(data)
        if hasil:
            return hasil

    elif tipe == "image/webp":
        hasil = _ukuran_webp(data)
        if hasil:
            return hasil

    elif tipe == "image/avif":
        hasil = _ukuran_ispe(data)
        if hasil:
            return hasil

    raise Ditolak(
        "ukuran gambarnya tidak terbaca dari kepala berkasnya, jadi ia "
        "ditolak. Gambar tanpa ukuran membuat tulisan di bawahnya melompat "
        "saat gambarnya tiba."
    )


def _ukuran_jpeg(data: bytes) -> tuple[int, int] | None:
    i = 2
    batas = len(data)
    while i + 9 < batas:
        if data[i] != 0xFF:
            i += 1
            continue
        tanda = data[i + 1]
        if tanda in (0xD8, 0x01) or 0xD0 <= tanda <= 0xD7:
            i += 2
            continue
        panjang = int.from_bytes(data[i + 2:i + 4], "big")
        if panjang < 2:
            return None
        if 0xC0 <= tanda <= 0xCF and tanda not in (0xC4, 0xC8, 0xCC):
            return (int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"))
        i += 2 + panjang
    return None


def _ukuran_webp(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30:
        return None
    bentuk = data[12:16]

    if bentuk == b"VP8 ":
        return (int.from_bytes(data[26:28], "little") & 0x3FFF,
                int.from_bytes(data[28:30], "little") & 0x3FFF)

    if bentuk == b"VP8L":
        angka = int.from_bytes(data[21:25], "little")
        return ((angka & 0x3FFF) + 1, ((angka >> 14) & 0x3FFF) + 1)

    if bentuk == b"VP8X":
        return (int.from_bytes(data[24:27], "little") + 1,
                int.from_bytes(data[27:30], "little") + 1)

    return None


def _ukuran_ispe(data: bytes) -> tuple[int, int] | None:
    tempat = data.find(b"ispe")
    if tempat == -1 or tempat + 16 > len(data):
        return None
    awal = tempat + 4 + 4
    lebar = int.from_bytes(data[awal:awal + 4], "big")
    tinggi = int.from_bytes(data[awal + 4:awal + 8], "big")
    if not (0 < lebar <= 40000 and 0 < tinggi <= 40000):
        return None
    return lebar, tinggi


def batas(jenis: str) -> int:
    atur = pengaturan()
    mb = atur.unggahan_gambar_maks_mb if jenis == "gambar" else atur.unggahan_video_maks_mb
    return mb * 1024 * 1024


async def periksa_kuota(tambahan_bita: int) -> None:
    atur = pengaturan()
    pakai = await repo.pemakaian()

    if pakai["jumlah"] >= atur.unggahan_jumlah_maks:
        raise Ditolak(
            f"sudah ada {pakai['jumlah']} berkas, dan batasnya "
            f"{atur.unggahan_jumlah_maks}. Hapus yang tidak dipakai lebih dulu."
        )

    maks_bita = atur.unggahan_total_maks_mb * 1024 * 1024
    if pakai["bita"] + tambahan_bita > maks_bita:
        terpakai = pakai["bita"] // (1024 * 1024)
        raise Ditolak(
            f"ruang unggahan sudah terpakai {terpakai} MB dari "
            f"{atur.unggahan_total_maks_mb} MB. Hapus yang tidak dipakai lebih dulu."
        )

    if pakai["hari_ini"] >= atur.unggahan_per_hari_maks:
        raise Ditolak(
            f"sudah {pakai['hari_ini']} berkas masuk dalam sehari terakhir, "
            f"dan batasnya {atur.unggahan_per_hari_maks}. Coba lagi besok."
        )


def _baca(aliran: BinaryIO) -> tuple[bytes, str, str]:
    awal = aliran.read(POTONG)
    if not awal:
        raise Ditolak("berkasnya kosong")

    jenis, tipe = kenali(awal)
    maksimum = batas(jenis)

    def terlalu_besar() -> Ditolak:
        return Ditolak(
            f"{jenis} ini lebih besar daripada batasnya, "
            f"{maksimum // (1024 * 1024)} MB"
        )

    potongan = [awal]
    panjang = len(awal)
    if panjang > maksimum:
        raise terlalu_besar()

    while True:
        lagi = aliran.read(POTONG)
        if not lagi:
            break
        panjang += len(lagi)
        if panjang > maksimum:
            raise terlalu_besar()
        potongan.append(lagi)

    return b"".join(potongan), jenis, tipe


def nama_baru(jenis: str, tipe: str, ukur: tuple[int, int] | None) -> str:
    akhiran = (GAMBAR | VIDEO)[tipe]
    inti = secrets.token_hex(8)
    if ukur is not None:
        return f"{inti}-{ukur[0]}x{ukur[1]}{akhiran}"
    return f"{inti}{akhiran}"


async def terima(
    aliran: BinaryIO,
    nama_asal: str,
    pengunggah_id: str | None,
    buang_metadata: bool = False,
) -> dict[str, Any]:
    data, jenis, tipe = _baca(aliran)

    if buang_metadata:
        if jenis != "gambar":
            raise Ditolak("metadata video tidak dibuang di sini")
        try:
            data = metadata.buang(tipe, data)
        except metadata.TidakBisa as galat:
            raise Ditolak(str(galat)) from galat

    ukur = ukuran(tipe, data) if jenis == "gambar" else None
    sidik = hashlib.sha256(data).hexdigest()

    sudah = await repo.lewat_sidik(sidik)
    if sudah is not None:
        if not jalur(sudah["nama"]).exists():
            _tulis(sudah["nama"], data)
        return {**sudah, "sudah_ada": True}

    await periksa_kuota(len(data))

    nama = nama_baru(jenis, tipe, ukur)
    _tulis(nama, data)

    try:
        baris = await repo.simpan(
            {
                "nama": nama,
                "nama_asal": _rapikan_nama(nama_asal),
                "jenis": jenis,
                "tipe_mime": tipe,
                "bita": len(data),
                "lebar": ukur[0] if ukur else None,
                "tinggi": ukur[1] if ukur else None,
                "sidik": sidik,
            },
            pengunggah_id,
        )
    except Exception:
        jalur(nama).unlink(missing_ok=True)
        raise

    return {**baris, "sudah_ada": False}


def _tulis(nama: str, data: bytes) -> None:
    tujuan = jalur(nama)
    sementara = tujuan.with_name(f".{nama}.{secrets.token_hex(4)}.sebagian")
    try:
        sementara.write_bytes(data)
        os.replace(sementara, tujuan)
    finally:
        sementara.unlink(missing_ok=True)


def _rapikan_nama(nama: str) -> str:
    bersih = "".join(h for h in nama if h.isprintable() and h not in "\r\n")
    bersih = bersih.replace("\\", "/").rsplit("/", 1)[-1].strip()
    return bersih[:255] or "tanpa-nama"


async def daftar(batas_baris: int, lewati: int) -> dict[str, Any]:
    isi = await repo.daftar(batas_baris, lewati)
    return {"jumlah": await repo.jumlah(), "isi": isi}


async def hapus(nama: str) -> None:
    baris = await repo.satu(nama)
    if baris is None:
        raise TidakAda(nama)

    dipakai = await repo.dipakai_tulisan(f"/unggahan/{nama}")
    if dipakai:
        raise MasihDipakai(dipakai)

    await repo.hapus(nama)
    jalur(nama).unlink(missing_ok=True)
