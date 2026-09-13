"""Verifikasi email, kode sekali pakai, TOTP, kode pemulihan, jejak keamanan.

Bagian ini menambah lapisan yang sudah ada, bukan menggantinya. Yang sudah
ada: sandi Argon2id, passkey WebAuthn, sesi yang berputar dan bisa dicabut.
Yang ditambahkan:

1. **Alamat email dibuktikan.** Akun yang emailnya tidak pernah dibuktikan
   adalah akun yang jalur pemulihannya menuju entah ke mana, dan seluruh
   lapisan lain berdiri di atas anggapan bahwa alamat itu milik pemiliknya.
2. **Faktor kedua.** TOTP dari aplikasi authenticator, atau kode enam angka
   lewat email kalau TOTP belum dipasang.
3. **Kode pemulihan.** Delapan, sekali pakai, dicetak sekali. Tanpa ini,
   ponsel yang hilang berarti akun yang terkunci selamanya, dan akun yang
   terkunci selamanya membuat orang mematikan faktor keduanya.
4. **Jejak.** Yang berhasil dan yang GAGAL. Yang berhasil hanya memberi tahu
   pemiliknya apa yang sudah ia lakukan; yang gagal memberi tahu bahwa ada
   orang lain sedang mencoba.

Dua hal yang dijaga ketat di seluruh berkas ini:

- **Tidak ada kode yang tersimpan apa adanya.** Yang masuk basis data selalu
  sha256-nya. Kode OTP yang tersimpan apa adanya sama saja dengan sandi yang
  tersimpan apa adanya, hanya umurnya lebih pendek.
- **Tidak ada kode yang masuk log.** Pesan galat di sini tidak pernah memuat
  kodenya, dan `surat.py` sengaja tidak menaruh isi surat di pesan galatnya.
"""

from __future__ import annotations

import datetime as dt
import hmac
import secrets
from dataclasses import dataclass

from backend.core import keamanan as inti
from backend.core import rahasia, surat
from backend.layanan import totp as totp_modul
from backend.layanan import wajah as wajah_modul
from backend.repositori import keamanan as repo
from backend.repositori import pengguna as repo_pengguna

UMUR_TAUTAN_JAM = 24
UMUR_OTP_MENIT = 10
JEDA_KIRIM_DETIK = 60


class Ditolak(Exception):
    """Kode salah, kedaluwarsa, atau langkahnya tidak boleh dikerjakan."""


class BelumSiap(Exception):
    """Konfigurasi yang dibutuhkan belum ada. Disebut, bukan disiasati."""


@dataclass(frozen=True)
class Kiriman:
    terkirim: bool
    catatan: str


def _kode_angka() -> str:
    """Enam angka, dari secrets, bukan random.

    `random` bisa ditebak seluruhnya setelah beberapa keluaran terlihat.
    Untuk kode yang menjaga jalan masuk, itu bukan detail.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def _tautan(token: str, asal: str) -> str:
    return f"{asal.rstrip('/')}/admin?verifikasi={token}"


# ------------------------------------------------------- verifikasi email ---


async def kirim_verifikasi_email(pengguna: dict, asal: str, alamat: str | None) -> Kiriman:
    """Mengirim tautan verifikasi. Tautannya sekali pakai dan hidup 24 jam."""
    sedang = await repo.kode_hidup(pengguna["id"], "email")
    if sedang:
        umur = dt.datetime.now(dt.timezone.utc) - sedang["dibuat_pada"]
        if umur.total_seconds() < JEDA_KIRIM_DETIK:
            raise Ditolak(
                f"tunggu {JEDA_KIRIM_DETIK - int(umur.total_seconds())} detik lagi"
            )

    token = secrets.token_urlsafe(32)
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=UMUR_TAUTAN_JAM)
    await repo.simpan_kode(pengguna["id"], "email", inti.ringkas(token), kadaluarsa, alamat)

    hasil = surat.kirim(
        pengguna["email"],
        "Buktikan alamat email ini untuk hendrokuswantoro.com",
        (
            f"Halo {pengguna.get('nama') or ''},\n\n"
            "Buka tautan di bawah untuk membuktikan bahwa alamat email ini memang Anda "
            f"yang menguasainya. Tautannya berlaku {UMUR_TAUTAN_JAM} jam dan hanya bisa "
            "dipakai sekali.\n\n"
            f"{_tautan(token, asal)}\n\n"
            "Kalau bukan Anda yang memintanya, abaikan saja surat ini. Selama tautannya "
            "tidak dibuka, tidak ada yang berubah pada akun Anda.\n"
        ),
    )
    await repo.catat(
        pengguna["id"], "verifikasi_email_dikirim", hasil.terkirim,
        None if hasil.terkirim else hasil.catatan[:200], alamat,
    )
    return Kiriman(hasil.terkirim, hasil.catatan)


async def selesaikan_verifikasi_email(token: str, alamat: str | None) -> dict:
    baris = await repo.pakai_kode("email", inti.ringkas(token))
    if not baris:
        await repo.catat(None, "verifikasi_email", False, "tautan tidak berlaku", alamat)
        raise Ditolak("tautan verifikasi tidak berlaku atau sudah dipakai")

    pengguna_id = str(baris["pengguna_id"])
    await repo.tandai_email_terverifikasi(pengguna_id)
    await repo.catat(pengguna_id, "verifikasi_email", True, None, alamat)
    return await repo_pengguna.cari_id(pengguna_id)


# ---------------------------------------------------------- OTP via email ---


async def kirim_otp_masuk(pengguna: dict, alamat: str | None) -> Kiriman:
    sedang = await repo.kode_hidup(pengguna["id"], "masuk")
    if sedang:
        umur = dt.datetime.now(dt.timezone.utc) - sedang["dibuat_pada"]
        if umur.total_seconds() < JEDA_KIRIM_DETIK:
            raise Ditolak(
                f"kode sudah dikirim, tunggu {JEDA_KIRIM_DETIK - int(umur.total_seconds())} detik"
            )

    kode = _kode_angka()
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=UMUR_OTP_MENIT)
    await repo.simpan_kode(pengguna["id"], "masuk", inti.ringkas(kode), kadaluarsa, alamat)

    hasil = surat.kirim(
        pengguna["email"],
        f"{kode} adalah kode masuk Anda",
        (
            f"Kode masuk untuk dashboard hendrokuswantoro.com:\n\n"
            f"    {kode}\n\n"
            f"Berlaku {UMUR_OTP_MENIT} menit dan hanya bisa dipakai sekali.\n\n"
            "Kalau bukan Anda yang mencoba masuk, seseorang mengetahui kata sandi Anda. "
            "Gantilah kata sandinya sekarang juga, dan nyalakan aplikasi authenticator "
            "supaya kode masuk tidak lagi lewat email.\n"
        ),
    )
    await repo.catat(
        pengguna["id"], "otp_dikirim", hasil.terkirim,
        None if hasil.terkirim else hasil.catatan[:200], alamat,
    )
    return Kiriman(hasil.terkirim, hasil.catatan)


async def periksa_otp_masuk(pengguna_id: str, kode: str, alamat: str | None) -> bool:
    bersih = "".join(ch for ch in (kode or "") if ch.isdigit())
    baris = await repo.pakai_kode("masuk", inti.ringkas(bersih)) if bersih else None
    if baris and str(baris["pengguna_id"]) == str(pengguna_id):
        return True
    sisa = await repo.catat_tebakan_gagal(pengguna_id, "masuk")
    await repo.catat(pengguna_id, "otp_salah", False, f"percobaan ke {sisa}", alamat)
    return False


# ------------------------------------------------------------------ TOTP ---


async def mulai_totp(pengguna: dict) -> dict:
    """Membuat rahasia baru dan mengembalikan URI otpauth untuk kode QR.

    Rahasianya disimpan tersandi tetapi BELUM aktif. Yang mengaktifkannya satu
    kode yang benar dari perangkatnya, sebab rahasia yang diaktifkan tanpa
    pernah dibuktikan terbaca adalah cara mengunci diri sendiri di luar.
    """
    if not rahasia.siap():
        raise BelumSiap(
            "KUNCI_KOLOM belum diisi, jadi rahasia TOTP tidak bisa disimpan tersandi. "
            "Buat kunci dengan: python backend/db/enkripsi.py kunci"
        )
    baru = totp_modul.rahasia_baru()
    await repo.simpan_rahasia_totp(pengguna["id"], rahasia.sandikan(baru))
    alamat = totp_modul.alamat_otpauth(baru, pengguna["email"])
    return {
        "rahasia": baru,
        "otpauth": alamat,
        # QR-nya digambar di sini, bukan diminta ke layanan luar. Alamat
        # otpauth MEMUAT rahasianya; mengirimnya ke pembuat QR mana pun berarti
        # menyerahkan faktor kedua kepada orang yang tidak pernah diminta
        # menjaganya.
        "qr": totp_modul.qr_svg(alamat),
    }


async def _rahasia_aktif(pengguna_id: str, harus_aktif: bool) -> str:
    baris = await repo.rahasia_totp(pengguna_id)
    if not baris or not baris["totp_rahasia"]:
        raise Ditolak("aplikasi authenticator belum dipasang")
    if harus_aktif and not baris["totp_aktif_pada"]:
        raise Ditolak("aplikasi authenticator belum diaktifkan")
    return rahasia.bukakan(baris["totp_rahasia"])


async def aktifkan_totp(pengguna: dict, kode: str, alamat: str | None) -> list[str]:
    """Mengaktifkan TOTP dan mengembalikan delapan kode pemulihan.

    Kodenya dikembalikan SEKALI, di sini, dan tidak pernah bisa dilihat lagi:
    yang tersimpan cuma sidiknya.
    """
    rahasia_nya = await _rahasia_aktif(pengguna["id"], harus_aktif=False)
    if totp_modul.cocok(rahasia_nya, kode) is None:
        await repo.catat(pengguna["id"], "totp_aktifkan", False, "kode salah", alamat)
        raise Ditolak("kode dari aplikasi tidak cocok")

    await repo.aktifkan_totp(pengguna["id"])
    kode_pemulihan = [totp_modul.kode_pemulihan_baru() for _ in range(totp_modul.JUMLAH_PEMULIHAN)]
    await repo.ganti_kode_pemulihan(
        pengguna["id"],
        [inti.ringkas(totp_modul.normalkan_pemulihan(k)) for k in kode_pemulihan],
    )
    await repo.catat(pengguna["id"], "totp_aktifkan", True, None, alamat)
    return kode_pemulihan


async def matikan_totp(pengguna: dict, kode: str, alamat: str | None) -> None:
    """Mematikan menuntut satu kode yang benar, sama seperti menyalakannya.

    Tanpa itu, siapa pun yang sempat memegang sesi yang sudah masuk bisa
    mencabut faktor kedua tanpa pernah memilikinya."""
    rahasia_nya = await _rahasia_aktif(pengguna["id"], harus_aktif=True)
    if totp_modul.cocok(rahasia_nya, kode) is None:
        await repo.catat(pengguna["id"], "totp_matikan", False, "kode salah", alamat)
        raise Ditolak("kode dari aplikasi tidak cocok")
    await repo.matikan_totp(pengguna["id"])
    await repo.catat(pengguna["id"], "totp_matikan", True, None, alamat)


async def periksa_totp(pengguna_id: str, kode: str, alamat: str | None) -> bool:
    try:
        rahasia_nya = await _rahasia_aktif(pengguna_id, harus_aktif=True)
    except Ditolak:
        return False
    if totp_modul.cocok(rahasia_nya, kode) is not None:
        return True
    await repo.catat(pengguna_id, "totp_salah", False, None, alamat)
    return False


# ------------------------------------------------------- kode pemulihan ---


async def periksa_pemulihan(pengguna_id: str, kode: str, alamat: str | None) -> bool:
    bersih = totp_modul.normalkan_pemulihan(kode)
    if len(bersih) != totp_modul.PANJANG_BAGIAN * 2:
        return False
    dipakai = await repo.pakai_kode_pemulihan(pengguna_id, inti.ringkas(bersih))
    await repo.catat(pengguna_id, "kode_pemulihan", dipakai, None, alamat)
    return dipakai


# ------------------------------------------------ apa yang masih kurang ---


async def faktor_kedua_yang_berlaku(pengguna: dict) -> list[str]:
    """Cara faktor kedua apa saja yang bisa dipakai pengguna ini sekarang.

    Kosong berarti tidak ada faktor kedua sama sekali, dan lapisan masuk akan
    menerbitkan sesi langsung. Itu keadaan yang boleh, dan halaman keamanan
    menyebutnya terus terang alih alih diam.
    """
    baris = await repo.keadaan(pengguna["id"])
    cara: list[str] = []
    if baris and baris["totp_aktif_pada"]:
        cara.append("totp")
        if baris["pemulihan_sisa"]:
            cara.append("pemulihan")
    # Wajah berdiri sendiri dan bisa dipakai bersama TOTP. Ia ditawarkan hanya
    # kalau memang sudah didaftarkan DAN modelnya ada di mesin ini; menawarkan
    # cara yang pasti gagal berarti mengunci pemiliknya di luar pintunya.
    if baris and baris["wajah_didaftar_pada"] and wajah_modul.siap():
        cara.append("wajah")

    if cara:
        return cara

    if baris and baris["email_terverifikasi_pada"] and surat.siap():
        # OTP email hanya ditawarkan kalau alamatnya sudah dibuktikan DAN surat
        # memang bisa dikirim. Menawarkan kode yang tidak akan pernah sampai
        # berarti mengunci pemiliknya di luar pintunya sendiri.
        cara.append("email")
    return cara


def cocok_aman(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


# ------------------------------------------- pintu untuk lapisan router ---

# Router berbicara ke layanan, layanan berbicara ke repositori. Tiga fungsi di
# bawah ini ada supaya aturan itu tetap berlaku untuk hal hal kecil juga:
# mencatat satu peristiwa dan membaca satu pengguna terasa terlalu sepele untuk
# dilewatkan lapisan, dan justru di situlah lapisan biasanya mulai bocor.
# `tests/test_api.py` menolak router yang mengimpor repositori, dan ia sudah
# menangkap saya sekali di sini.


async def catat_peristiwa(
    pengguna_id: str | None, jenis: str, berhasil: bool,
    keterangan: str | None = None, alamat: str | None = None,
    peramban: str | None = None,
) -> None:
    await repo.catat(pengguna_id, jenis, berhasil, keterangan, alamat, peramban)


async def pengguna(pengguna_id: str) -> dict | None:
    return await repo_pengguna.cari_id(pengguna_id)


async def keadaan_akun(pengguna_id: str) -> dict | None:
    return await repo.keadaan(pengguna_id)


async def jejak(pengguna_id: str, batas: int = 40) -> list[dict]:
    return await repo.peristiwa(pengguna_id, batas)


# ------------------------------------------------------------------ wajah ---

# Batas lapisan ini ditulis panjang di backend/layanan/wajah.py, dan diulang di
# layar tempat ia dinyalakan. Ringkasnya: ia menaikkan ongkos masuk bagi orang
# yang sudah tahu kata sandinya, dan ia TIDAK membuktikan kehadiran. Rekaman
# video wajah pemiliknya akan lolos. Karena itu ia tambahan yang dinyalakan
# sendiri, bukan bawaan, dan bukan pengganti passkey.

UMUR_TANTANGAN_WAJAH_DETIK = 120


async def daftarkan_wajah(pengguna: dict, bingkai: list[str], alamat: str | None) -> dict:
    """Mendaftarkan wajah dari beberapa bingkai. Fotonya tidak disimpan."""
    if not rahasia.siap():
        raise BelumSiap(
            "KUNCI_KOLOM belum diisi, jadi ciri wajah tidak bisa disimpan tersandi. "
            "Data biometrik yang tersimpan apa adanya adalah data yang ikut bocor "
            "bersama basis datanya."
        )
    try:
        ciri = wajah_modul.ciri_dari_bingkai(bingkai)
    except wajah_modul.Ditolak as ditolak:
        await repo.catat(pengguna["id"], "wajah_daftar", False, str(ditolak)[:200], alamat)
        raise Ditolak(str(ditolak)) from ditolak

    await repo.simpan_wajah(pengguna["id"], rahasia.sandikan(wajah_modul.ke_untai(ciri)))
    await repo.catat(pengguna["id"], "wajah_daftar", True, None, alamat)
    return {"terdaftar": True, "bingkai": len(bingkai)}


async def hapus_wajah(pengguna: dict, alamat: str | None) -> None:
    await repo.hapus_wajah(pengguna["id"])
    await repo.catat(pengguna["id"], "wajah_hapus", True, None, alamat)


async def tantangan_wajah(pengguna_id: str) -> dict:
    """Urutan gerakan yang diputuskan server, berlaku dua menit, sekali pakai."""
    if not await repo.ciri_wajah(pengguna_id):
        raise Ditolak("wajah belum didaftarkan")
    gerakan = wajah_modul.gerakan_acak()
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        seconds=UMUR_TANTANGAN_WAJAH_DETIK
    )
    tantangan_id = await repo.tantangan_wajah_baru(pengguna_id, gerakan, kadaluarsa)
    return {
        "tantangan": tantangan_id,
        "gerakan": gerakan,
        "umur_detik": UMUR_TANTANGAN_WAJAH_DETIK,
    }


async def periksa_wajah(
    pengguna_id: str, tantangan_id: str, bingkai: list[str], alamat: str | None
) -> bool:
    diminta = await repo.pakai_tantangan_wajah(pengguna_id, tantangan_id)
    if diminta is None:
        await repo.catat(pengguna_id, "wajah_salah", False, "tantangan tidak berlaku", alamat)
        return False

    tersimpan = await repo.ciri_wajah(pengguna_id)
    if not tersimpan:
        return False

    try:
        hasil = wajah_modul.periksa(
            bingkai, diminta, wajah_modul.dari_untai(rahasia.bukakan(tersimpan))
        )
    except wajah_modul.Ditolak as ditolak:
        await repo.catat(pengguna_id, "wajah_salah", False, str(ditolak)[:200], alamat)
        return False
    except wajah_modul.BelumSiap as belum:
        await repo.catat(pengguna_id, "wajah_salah", False, str(belum)[:200], alamat)
        return False

    await repo.catat(
        pengguna_id, "wajah_cocok", True, f"kemiripan {hasil['terendah']}", alamat
    )
    return True
