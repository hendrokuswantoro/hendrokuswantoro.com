from __future__ import annotations

import datetime as dt
import pathlib
import re
import smtplib
import ssl
import uuid
from dataclasses import dataclass
from email.message import EmailMessage

from backend.core.konfigurasi import pengaturan

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
KOTAK = AKAR / "cadangan" / "surat"

BARIS_BARU = re.compile(r"[\r\n]")


class TidakTerkirim(RuntimeError):
    pass


@dataclass(frozen=True)
class Hasil:
    terkirim: bool
    kemana: str
    catatan: str


def _atur() -> dict:
    a = pengaturan()
    return {
        "host": a.smtp_host.strip(),
        "porta": a.smtp_porta,
        "pengguna": a.smtp_pengguna.strip(),
        "sandi": a.smtp_sandi,
        "dari": a.surat_dari.strip(),
        "wajib": a.surat_wajib,
    }


def siap() -> bool:
    a = _atur()
    return bool(a["host"] and a["dari"])


def _bersih(nilai: str) -> str:
    return BARIS_BARU.sub(" ", nilai).strip()


def _tulis_ke_berkas(pesan: EmailMessage, alasan: str) -> Hasil:
    KOTAK.mkdir(parents=True, exist_ok=True)
    nama = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}.eml"
    jalur = KOTAK / nama
    jalur.write_bytes(bytes(pesan))
    return Hasil(
        terkirim=False,
        kemana=pesan["To"],
        catatan=(
            f"{alasan} Suratnya ditulis ke {jalur.relative_to(AKAR)} dan TIDAK dikirim. "
            "Isi SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, dan SURAT_DARI di .env "
            "supaya ia benar benar berangkat."
        ),
    )


def kirim(kepada: str, subjek: str, isi: str) -> Hasil:
    a = _atur()
    pesan = EmailMessage()
    pesan["From"] = a["dari"] or "hendrokuswantoro.com <tanpa-konfigurasi@localhost>"
    pesan["To"] = _bersih(kepada)
    pesan["Subject"] = _bersih(subjek)
    pesan["Date"] = dt.datetime.now(dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    pesan.set_content(isi)

    if not siap():
        if a["wajib"]:
            raise TidakTerkirim(
                "SMTP_HOST atau SURAT_DARI belum diisi, sedangkan SURAT_WAJIB=1"
            )
        return _tulis_ke_berkas(pesan, "SMTP belum dikonfigurasi.")

    try:
        konteks = ssl.create_default_context()
        if a["porta"] == 465:
            with smtplib.SMTP_SSL(a["host"], a["porta"], context=konteks, timeout=20) as s:
                if a["pengguna"]:
                    s.login(a["pengguna"], a["sandi"])
                s.send_message(pesan)
        else:
            with smtplib.SMTP(a["host"], a["porta"], timeout=20) as s:
                s.starttls(context=konteks)
                if a["pengguna"]:
                    s.login(a["pengguna"], a["sandi"])
                s.send_message(pesan)
    except Exception as galat:  # noqa: BLE001 
        if a["wajib"]:
            raise TidakTerkirim(f"SMTP menolak: {type(galat).__name__}") from galat
        return _tulis_ke_berkas(pesan, f"SMTP gagal ({type(galat).__name__}).")

    return Hasil(terkirim=True, kemana=pesan["To"], catatan="terkirim")
