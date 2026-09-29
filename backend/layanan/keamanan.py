from __future__ import annotations

import asyncio
import datetime as dt
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

BATAS_F2 = 5
JENDELA_F2_MENIT = 15


class Ditolak(Exception):
    pass


class BelumSiap(Exception):
    pass


@dataclass(frozen=True)
class Kiriman:
    terkirim: bool
    catatan: str


def _kode_angka() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _tautan(token: str, asal: str) -> str:
    return f"{asal.rstrip('/')}/admin#verifikasi={token}"


async def kirim_verifikasi_email(pengguna: dict, asal: str, alamat: str | None) -> Kiriman:
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

    hasil = await asyncio.to_thread(
        surat.kirim,
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

    hasil = await asyncio.to_thread(
        surat.kirim,
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


def _kunci_f2(pengguna_id: str) -> str:
    return f"f2:{pengguna_id}"


async def cek_kunci_f2(pengguna_id: str) -> None:
    if await repo_pengguna.jumlah_gagal(_kunci_f2(pengguna_id), JENDELA_F2_MENIT) >= BATAS_F2:
        raise Ditolak(
            f"terlalu banyak kode salah. Tunggu {JENDELA_F2_MENIT} menit, lalu ulangi dari awal."
        )


async def _gagal_f2(pengguna_id: str, alamat: str | None) -> None:
    await repo_pengguna.catat_gagal(
        _kunci_f2(pengguna_id), alamat or inti.ringkas("tidak-diketahui")
    )


async def _berhasil_f2(pengguna_id: str) -> None:
    await repo_pengguna.bersihkan_gagal(_kunci_f2(pengguna_id))


async def mulai_totp(pengguna: dict) -> dict:
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
    rahasia_nya = await _rahasia_aktif(pengguna["id"], harus_aktif=False)
    langkah = totp_modul.cocok(rahasia_nya, kode)
    if langkah is None:
        await repo.catat(pengguna["id"], "totp_aktifkan", False, "kode salah", alamat)
        raise Ditolak("kode dari aplikasi tidak cocok")

    await repo.aktifkan_totp(pengguna["id"])
    await repo.pakai_langkah_totp(pengguna["id"], langkah)
    kode_pemulihan = [totp_modul.kode_pemulihan_baru() for _ in range(totp_modul.JUMLAH_PEMULIHAN)]
    await repo.ganti_kode_pemulihan(
        pengguna["id"],
        [inti.ringkas(totp_modul.normalkan_pemulihan(k)) for k in kode_pemulihan],
    )
    await repo.catat(pengguna["id"], "totp_aktifkan", True, None, alamat)
    return kode_pemulihan


async def matikan_totp(pengguna: dict, kode: str, alamat: str | None) -> None:
    rahasia_nya = await _rahasia_aktif(pengguna["id"], harus_aktif=True)
    if totp_modul.cocok(rahasia_nya, kode) is None:
        await repo.catat(pengguna["id"], "totp_matikan", False, "kode salah", alamat)
        raise Ditolak("kode dari aplikasi tidak cocok")
    await repo.matikan_totp(pengguna["id"])
    await repo.catat(pengguna["id"], "totp_matikan", True, None, alamat)


async def periksa_totp(pengguna_id: str, kode: str, alamat: str | None) -> bool:
    await cek_kunci_f2(pengguna_id)
    try:
        rahasia_nya = await _rahasia_aktif(pengguna_id, harus_aktif=True)
    except Ditolak:
        return False
    langkah = totp_modul.cocok(rahasia_nya, kode)
    if langkah is not None:
        if await repo.pakai_langkah_totp(pengguna_id, langkah):
            await _berhasil_f2(pengguna_id)
            return True
        await repo.catat(pengguna_id, "totp_salah", False, "kode sudah dipakai", alamat)
    else:
        await repo.catat(pengguna_id, "totp_salah", False, None, alamat)
    await _gagal_f2(pengguna_id, alamat)
    return False


async def periksa_pemulihan(pengguna_id: str, kode: str, alamat: str | None) -> bool:
    await cek_kunci_f2(pengguna_id)
    bersih = totp_modul.normalkan_pemulihan(kode)
    dipakai = False
    if len(bersih) == totp_modul.PANJANG_BAGIAN * 2:
        dipakai = await repo.pakai_kode_pemulihan(pengguna_id, inti.ringkas(bersih))
        await repo.catat(pengguna_id, "kode_pemulihan", dipakai, None, alamat)
    if dipakai:
        await _berhasil_f2(pengguna_id)
    else:
        await _gagal_f2(pengguna_id, alamat)
    return dipakai


async def faktor_kedua_yang_berlaku(pengguna: dict) -> list[str]:
    baris = await repo.keadaan(pengguna["id"])
    cara: list[str] = []
    if baris and baris["totp_aktif_pada"]:
        cara.append("totp")
        if baris["pemulihan_sisa"]:
            cara.append("pemulihan")
    ketat = bool(baris and baris["mode_ketat"] and (baris["totp_aktif_pada"] or baris["passkey"]))
    if baris and baris["wajah_didaftar_pada"] and wajah_modul.siap() and not ketat:
        cara.append("wajah")

    if baris and baris["passkey"]:
        cara.append("passkey")

    if cara:
        return cara

    if baris and baris["email_terverifikasi_pada"] and surat.siap():
        cara.append("email")
    return cara


async def punya_faktor(pengguna_id: str) -> bool:
    b = await repo.keadaan(pengguna_id)
    return bool(b and (b["totp_aktif_pada"] or b["passkey"] or b["wajah_didaftar_pada"]))


NAMA_SETELAN = {
    "kabar_masuk": ("kabar masuk dari perangkat baru", "setelan_kabar"),
    "kabar_perubahan": ("kabar perubahan keamanan", "setelan_kabar"),
    "mode_ketat": ("mode ketat", "mode_ketat"),
}


async def ubah_setelan(
    pengguna_id: str, perubahan: dict[str, bool], alamat: str | None
) -> list[str]:
    sekarang = await repo.keadaan(pengguna_id)
    if not sekarang:
        raise Ditolak("akun tidak ada")

    baru = {k: v for k, v in perubahan.items() if k in NAMA_SETELAN and sekarang[k] != v}
    if baru.get("mode_ketat") and not (sekarang["totp_aktif_pada"] or sekarang["passkey"]):
        raise Ditolak("pasang authenticator atau sidik jari dulu, baru mode ketat bisa dinyalakan")

    await repo.simpan_setelan(pengguna_id, baru)
    ringkasan = []
    for kunci, nilai in baru.items():
        nama, jenis = NAMA_SETELAN[kunci]
        ringkasan.append(f"{nama} {'dinyalakan' if nilai else 'dimatikan'}")
        await repo.catat(pengguna_id, jenis, True, ringkasan[-1], alamat)
    return ringkasan


async def setelan(pengguna_id: str) -> dict:
    return dict(await repo.setelan(pengguna_id) or {})


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


UMUR_TANTANGAN_WAJAH_DETIK = 120


async def daftarkan_wajah(pengguna: dict, bingkai: list[str], alamat: str | None) -> dict:
    if not rahasia.siap():
        raise BelumSiap(
            "KUNCI_KOLOM belum diisi, jadi ciri wajah tidak bisa disimpan tersandi. "
            "Data biometrik yang tersimpan apa adanya adalah data yang ikut bocor "
            "bersama basis datanya."
        )
    try:
        ciri = await asyncio.to_thread(wajah_modul.ciri_dari_bingkai, bingkai)
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
    await cek_kunci_f2(pengguna_id)
    lolos = await _periksa_wajah(pengguna_id, tantangan_id, bingkai, alamat)
    if lolos:
        await _berhasil_f2(pengguna_id)
    else:
        await _gagal_f2(pengguna_id, alamat)
    return lolos


async def _periksa_wajah(
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
        hasil = await asyncio.to_thread(
            wajah_modul.periksa, bingkai, diminta, wajah_modul.dari_untai(rahasia.bukakan(tersimpan))
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
