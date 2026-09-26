"""Menerima foto dan video, dan menolak yang bukan keduanya.

Satu aturan yang menjelaskan hampir seluruh berkas ini: **jenis berkas
ditentukan dari isinya, bukan dari yang dikatakan pengirimnya.**

Nama berkas dan header Content-Type keduanya datang dari pengirim, jadi
keduanya bisa berbunyi apa saja. "foto.jpg" yang isinya HTML akan disajikan
lagi dari alamat situs ini, dan kalau peramban sempat menebak jenisnya, yang
jalan adalah skrip milik pengirimnya di atas asal situs ini. Karena itu yang
dipercaya di sini hanya bita pertama berkasnya, dan akhiran nama yang dipakai
di cakram ditentukan dari situ, bukan dari kiriman.

Yang tidak dikerjakan di sini, dan sengaja disebut supaya tidak ada yang
mengiranya ada:

- Tidak ada pemindaian malware. Berkas yang lolos bentuknya tetap bisa berisi
  apa saja di dalamnya.
- Tidak ada pengubahan ukuran atau pemampatan. Foto delapan megabita akan
  terbit sebagai foto delapan megabita.
- Metadata EXIF tidak dibuang **kecuali diminta**. Foto dari ponsel bisa
  membawa koordinat tempat pemotretannya, dan itu akan ikut terbit. Sejak
  19 September 2026 ada kotak centang untuk membuangnya, mati secara bawaan,
  sebab yang tahu apakah tempatnya boleh diketahui umum adalah pemiliknya,
  bukan berkas ini. Yang bisa dibuang cuma JPEG, PNG, dan WebP; GIF dan AVIF
  ditolak ketika pembuangan diminta, bukan diterima diam diam. Lihat
  backend/layanan/metadata.py.
"""

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
    """Unggahan yang tidak sah, dengan alasan yang bisa dibaca penulisnya."""


class TidakAda(Exception):
    """Berkas yang diminta tidak ada."""


class MasihDipakai(Exception):
    """Berkas yang masih disebut sebuah tulisan, beserta slug-nya."""

    def __init__(self, slug: list[str]) -> None:
        super().__init__(", ".join(slug))
        self.slug = slug


# Yang diterima, dan akhiran yang dipakai di cakram untuk masing masing.
#
# Daftarnya sengaja pendek. Tiap format tambahan adalah satu pengurai lagi di
# peramban pembaca, dan yang jarang dipakai adalah yang jarang diperiksa.
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


# --------------------------------------------------------------- tempatnya ---


def folder() -> pathlib.Path:
    """Folder tempat berkasnya duduk, dibuat kalau belum ada."""
    jalur = pathlib.Path(pengaturan().unggahan_dir)
    if not jalur.is_absolute():
        jalur = pathlib.Path(__file__).resolve().parents[2] / jalur
    jalur.mkdir(parents=True, exist_ok=True)
    return jalur


def jalur(nama: str) -> pathlib.Path:
    """Jalur berkas di cakram, dengan nama yang sudah dipastikan aman.

    Nama yang sampai ke sini selalu buatan berkas ini sendiri, dan tetap
    diperiksa lagi. Pemeriksaan yang hanya mengandalkan "pemanggilnya pasti
    benar" adalah pemeriksaan yang gugur pada hari ada pemanggil kedua.
    """
    if not nama or "/" in nama or "\\" in nama or nama.startswith("."):
        raise Ditolak(f"nama berkas tidak sah: {nama[:40]!r}")
    hasil = (folder() / nama).resolve()
    if hasil.parent != folder().resolve():
        raise Ditolak(f"nama berkas tidak sah: {nama[:40]!r}")
    return hasil


# ------------------------------------------------------------- mengenalinya ---


def kenali(awal: bytes) -> tuple[str, str]:
    """Jenis dan tipe MIME dari bita pertama berkasnya.

    Melempar Ditolak untuk apa pun yang tidak dikenali, termasuk berkas yang
    terlalu pendek untuk dikenali sama sekali.
    """
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

    # ISO base media: mp4 dan avif memakai pembungkus yang sama, yang
    # membedakan mereknya di kotak ftyp.
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
    """Lebar dan tinggi gambar, dibaca dari kepala berkasnya.

    Tidak memakai pustaka gambar, dan itu bukan penghematan iseng. Membuka
    gambar dengan pustaka berarti mengurai seluruh isinya, termasuk isi yang
    disusun untuk membuat pengurainya meledak, dan berarti menaruh satu
    permukaan serangan lagi tepat di jalur yang menerima berkas dari luar.
    Yang dibaca di sini cuma beberapa puluh bita pertama.
    """
    if tipe == "image/png":
        # IHDR selalu kotak pertama, dan ukurannya selalu di tempat yang sama.
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
    """Menelusuri segmen JPEG sampai bertemu SOF.

    Ukurannya tidak ada di tempat tetap: sebelum SOF bisa ada komentar, profil
    warna, dan thumbnail EXIF yang panjangnya berapa saja.
    """
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
        # SOF0..SOF15, kecuali DHT (C4), JPG (C8), dan DAC (CC) yang
        # kebetulan duduk di rentang yang sama.
        if 0xC0 <= tanda <= 0xCF and tanda not in (0xC4, 0xC8, 0xCC):
            return (int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"))
        i += 2 + panjang
    return None


def _ukuran_webp(data: bytes) -> tuple[int, int] | None:
    """Tiga bentuk WebP, tiga tempat ukurannya."""
    if len(data) < 30:
        return None
    bentuk = data[12:16]

    if bentuk == b"VP8 ":
        return (int.from_bytes(data[26:28], "little") & 0x3FFF,
                int.from_bytes(data[28:30], "little") & 0x3FFF)

    if bentuk == b"VP8L":
        # Empat belas bit lebar lalu empat belas bit tinggi, keduanya
        # disimpan sebagai nilai dikurangi satu.
        angka = int.from_bytes(data[21:25], "little")
        return ((angka & 0x3FFF) + 1, ((angka >> 14) & 0x3FFF) + 1)

    if bentuk == b"VP8X":
        return (int.from_bytes(data[24:27], "little") + 1,
                int.from_bytes(data[27:30], "little") + 1)

    return None


def _ukuran_ispe(data: bytes) -> tuple[int, int] | None:
    """Kotak ispe di dalam pembungkus ISO base media, dipakai AVIF.

    Dicari, bukan dihitung dari susunan kotaknya. Menelusuri susunannya
    dengan benar menuntut pengurai ISO-BMFF yang utuh, dan yang dibutuhkan
    di sini cuma dua angka.
    """
    tempat = data.find(b"ispe")
    if tempat == -1 or tempat + 16 > len(data):
        return None
    # ispe: 4 bita versi dan flag, lalu lebar dan tinggi masing masing 4 bita.
    awal = tempat + 4 + 4
    lebar = int.from_bytes(data[awal:awal + 4], "big")
    tinggi = int.from_bytes(data[awal + 4:awal + 8], "big")
    if not (0 < lebar <= 40000 and 0 < tinggi <= 40000):
        return None
    return lebar, tinggi


# ------------------------------------------------------------- menerimanya ---


def batas(jenis: str) -> int:
    atur = pengaturan()
    mb = atur.unggahan_gambar_maks_mb if jenis == "gambar" else atur.unggahan_video_maks_mb
    return mb * 1024 * 1024


async def periksa_kuota(tambahan_bita: int) -> None:
    """Batas di atas batas per berkas.

    Batas per berkas tidak menjaga apa apa terhadap yang mengunggah seribu
    berkas. Cakram yang penuh mematikan PostgreSQL, dan PostgreSQL yang mati
    mematikan seluruh situs; ruang cakram adalah urusan keamanan, bukan
    urusan kerapian.

    Diperiksa sebelum berkasnya ditulis, bukan sesudahnya. Menulis dulu lalu
    menghapus kalau ternyata melewati batas berarti ada saat cakramnya memang
    sudah penuh.
    """
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
        # Menahan akun yang sudah diambil orang memakai situs ini sebagai
        # tempat penitipan berkas dalam satu malam. Tidak menahan pemilik yang
        # memang sedang menulis banyak: besok angkanya nol lagi.
        raise Ditolak(
            f"sudah {pakai['hari_ini']} berkas masuk dalam sehari terakhir, "
            f"dan batasnya {atur.unggahan_per_hari_maks}. Coba lagi besok."
        )


def _baca(aliran: BinaryIO) -> tuple[bytes, str, str]:
    """Membaca seluruh berkas ke memori, sambil menjaga batasnya.

    Batasnya diperiksa di tengah pembacaan, bukan sesudahnya. Membaca dulu
    lalu menolak belakangan berarti berkas satu gigabita tetap sempat masuk
    ke memori proses ini, dan penolakan sesudah itu tidak menolong siapa pun.
    """
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
    # Potongan pertama ikut diperiksa. Memeriksa hanya potongan berikutnya
    # berarti batas yang lebih kecil daripada satu potongan tidak pernah
    # berlaku sama sekali, dan itu jenis lubang yang hanya terlihat ketika
    # batasnya diturunkan, yaitu saat seseorang mengiranya sedang bekerja.
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
    """Nama acak, ditambah ukurannya kalau ia gambar.

    Acak, bukan sidik isinya, supaya alamat sebuah berkas tidak memberi tahu
    siapa pun bahwa berkas dengan isi tertentu ada di sini. Sidiknya tetap
    dicatat di basis data untuk mengenali unggahan kembar.
    """
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
    """Satu unggahan, dari aliran bita sampai baris di basis data."""
    data, jenis, tipe = _baca(aliran)

    if buang_metadata:
        if jenis != "gambar":
            raise Ditolak("metadata video tidak dibuang di sini")
        try:
            data = metadata.buang(tipe, data)
        except metadata.TidakBisa as galat:
            # Ditolak, bukan diterima apa adanya. Menerima berkas yang
            # metadatanya diminta dibuang lalu membiarkannya utuh berarti
            # membuat orangnya mengira koordinat rumahnya sudah hilang.
            raise Ditolak(str(galat)) from galat

    ukur = ukuran(tipe, data) if jenis == "gambar" else None
    sidik = hashlib.sha256(data).hexdigest()

    sudah = await repo.lewat_sidik(sidik)
    if sudah is not None:
        # Berkas dengan isi yang sama sudah ada. Yang dikembalikan yang lama,
        # dan itu bukan kegagalan: alamatnya tetap menunjuk gambar yang
        # dimaksud penulisnya. Kalau berkasnya hilang dari cakram, ia ditulis
        # lagi dari data yang barusan diterima.
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
        # Baris gagal ditulis, jadi berkasnya tidak boleh tertinggal di
        # cakram. Berkas tanpa catatan tidak akan pernah muncul di daftar,
        # tidak akan pernah bisa dihapus lewat dashboard, dan tidak ada yang
        # tahu ia ada.
        jalur(nama).unlink(missing_ok=True)
        raise

    return {**baris, "sudah_ada": False}


def _tulis(nama: str, data: bytes) -> None:
    """Menulis lewat berkas sementara lalu menggantinya sekaligus.

    Menulis langsung ke nama tujuannya berarti ada saat berkasnya sudah ada
    dan isinya baru separuh. Kalau saat itu ada yang membukanya, yang sampai
    gambar terpotong, bukan galat.
    """
    tujuan = jalur(nama)
    sementara = tujuan.with_name(f".{nama}.{secrets.token_hex(4)}.sebagian")
    try:
        sementara.write_bytes(data)
        os.replace(sementara, tujuan)
    finally:
        sementara.unlink(missing_ok=True)


def _rapikan_nama(nama: str) -> str:
    """Nama asli, dipotong dan dibersihkan, hanya untuk dilihat orang.

    Ia tidak pernah dipakai membentuk jalur, dan tetap dibersihkan: nama yang
    memuat baris baru atau karakter kendali akan muncul lagi di daftar berkas
    dan di log, dan di keduanya ia bisa merusak bacaan.
    """
    bersih = "".join(h for h in nama if h.isprintable() and h not in "\r\n")
    bersih = bersih.replace("\\", "/").rsplit("/", 1)[-1].strip()
    return bersih[:255] or "tanpa-nama"


# ------------------------------------------------------------- membacanya ---


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
