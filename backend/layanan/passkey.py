"""Aturan passkey. WebAuthn level 2, lewat pustaka `webauthn`.

Tidak ada satu baris pun kriptografi buatan sendiri di sini, dan itu bukan
kebetulan: bab 15.8 melarangnya. Yang dikerjakan berkas ini hanya empat hal
yang memang keputusan, bukan matematika.

1. **Tantangan lahir di server, sekali pakai, berumur pendek.** Ini bagian
   yang paling sering salah. Tantangan yang dikirim ke peramban lalu
   dipercaya kembali apa adanya berarti penyerang boleh memilih tantangannya
   sendiri, dan seluruh jaminan kesegaran tanda tangan lenyap.

2. **rp_id dan origin diperiksa, keduanya, dari konfigurasi.** Ini yang
   membuat passkey tahan halaman palsu: authenticator menolak menandatangani
   untuk alamat yang bukan alamat ini, dan server menolak tanda tangan yang
   dibuat untuk alamat lain. Sandi tidak punya pertahanan yang setara,
   sebanyak apa pun ia di-hash.

3. **Penghitung tanda tangan yang mundur berarti kredensialnya disalin.**
   Nol selamanya bukan pelanggaran, banyak authenticator memang begitu;
   yang melanggar adalah nilai yang turun.

4. **Mendaftar menuntut sudah masuk.** Titik akhir pendaftaran yang terbuka
   adalah pintu belakang: siapa pun yang menemukannya bisa menambahkan kunci
   miliknya ke akun orang lain.

Passkey di sini dibuat discoverable, sehingga pemiliknya bisa masuk tanpa
mengetik email lebih dulu. Konsekuensinya `allow_credentials` dikosongkan
saat masuk, dan pemilik kredensialnya baru diketahui sesudah tanda tangannya
diverifikasi.
"""

from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass

import webauthn
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from backend.core.konfigurasi import pengaturan
from backend.layanan import autentikasi
from backend.repositori import passkey as repo
from backend.repositori import pengguna as repo_pengguna

# Cukup lama untuk mengambil ponsel dari saku, cukup pendek supaya tantangan
# yang bocor dari layar tidak berguna satu jam kemudian.
UMUR_TANTANGAN_DETIK = 300

NAMA_MAKS = 80


class Ditolak(Exception):
    """Tantangan mati, tanda tangan tidak berlaku, atau kredensial asing."""


@dataclass(frozen=True)
class Terdaftar:
    id: str
    nama: str


def _rp() -> tuple[str, list[str]]:
    atur = pengaturan()
    if not atur.passkey_siap:
        raise Ditolak("passkey belum dikonfigurasi")
    return atur.webauthn_rp_id, list(atur.webauthn_asal)


async def _tantangan_baru(tujuan: str, pengguna_id: str | None = None) -> bytes:
    nilai = secrets.token_bytes(32)
    kadaluarsa = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=UMUR_TANTANGAN_DETIK)
    await repo.simpan_tantangan(tujuan, nilai, kadaluarsa, pengguna_id)
    return nilai


# ------------------------------------------------------------- mendaftar ---


async def mulai_daftar(pengguna_id: str) -> dict:
    """Pilihan pendaftaran untuk perangkat yang sedang dipakai.

    Email dan nama dibaca dari basis data, bukan dari token. Token sengaja
    hanya membawa id dan peran: tiap kolom tambahan di dalamnya adalah kolom
    yang sudah tidak bisa dicabut sampai tokennya kedaluwarsa.

    Kredensial yang sudah terdaftar ikut dikirim sebagai `exclude_credentials`
    supaya peramban menolak mendaftarkan perangkat yang sama dua kali, dan
    pemiliknya tidak berakhir dengan daftar kunci yang tidak bisa dibedakan.
    """
    rp_id, _ = _rp()

    pengguna = await repo_pengguna.cari_id(pengguna_id)
    if pengguna is None:
        raise Ditolak("pengguna tidak ada")

    sudah = await repo.milik(pengguna_id)
    tantangan = await _tantangan_baru("daftar", pengguna_id)

    pilihan = webauthn.generate_registration_options(
        rp_id=rp_id,
        rp_name=pengaturan().webauthn_rp_nama,
        user_id=pengguna_id.encode("utf-8"),
        user_name=pengguna["email"],
        user_display_name=pengguna.get("nama") or pengguna["email"],
        challenge=tantangan,
        timeout=UMUR_TANTANGAN_DETIK * 1000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            # Discoverable: kuncinya menyimpan siapa pemiliknya, sehingga
            # masuk tidak perlu mengetik email lebih dulu.
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=bytes(k["kredensial_id"])) for k in sudah
        ],
    )
    return {"pilihan": webauthn.options_to_json(pilihan)}


async def selesaikan_daftar(pengguna_id: str, jawaban: dict, nama: str) -> Terdaftar:
    rp_id, asal = _rp()

    nama = (nama or "").strip()[:NAMA_MAKS] or "Perangkat tanpa nama"

    tantangan_mentah = _tantangan_dari(jawaban)
    baris = await repo.pakai_tantangan("daftar", tantangan_mentah)
    if baris is None or str(baris["pengguna_id"]) != pengguna_id:
        raise Ditolak("tantangan tidak berlaku")

    try:
        hasil = webauthn.verify_registration_response(
            credential=jawaban,
            expected_challenge=tantangan_mentah,
            expected_rp_id=rp_id,
            expected_origin=asal,
            require_user_verification=True,
        )
    except (InvalidRegistrationResponse, ValueError) as galat:
        raise Ditolak("pendaftaran tidak berlaku") from galat

    transportasi = _transportasi(jawaban)

    id_baru = await repo.simpan(
        pengguna_id=pengguna_id,
        kredensial_id=hasil.credential_id,
        kunci_publik=hasil.credential_public_key,
        penghitung=hasil.sign_count,
        jenis_perangkat=hasil.credential_device_type.value,
        tercadang=bool(hasil.credential_backed_up),
        transportasi=transportasi,
        nama=nama,
    )
    return Terdaftar(id=id_baru, nama=nama)


# ----------------------------------------------------------------- masuk ---


async def mulai_masuk() -> dict:
    """`allow_credentials` sengaja kosong.

    Menyebutkan daftar kredensial milik sebuah email berarti memberi tahu
    siapa pun yang bertanya bahwa email itu terdaftar dan punya berapa kunci.
    Passkey discoverable tidak perlu daftar itu: perangkatnya sendiri yang
    tahu kunci mana yang cocok untuk alamat ini.
    """
    rp_id, _ = _rp()
    tantangan = await _tantangan_baru("masuk")

    pilihan = webauthn.generate_authentication_options(
        rp_id=rp_id,
        challenge=tantangan,
        timeout=UMUR_TANTANGAN_DETIK * 1000,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return {"pilihan": webauthn.options_to_json(pilihan)}


async def selesaikan_masuk(jawaban: dict) -> autentikasi.Masuk:
    rp_id, asal = _rp()

    tantangan_mentah = _tantangan_dari(jawaban)
    if await repo.pakai_tantangan("masuk", tantangan_mentah) is None:
        raise Ditolak("tantangan tidak berlaku")

    try:
        kredensial_id = base64url_to_bytes(jawaban["id"])
    except (KeyError, TypeError, ValueError) as galat:
        raise Ditolak("jawaban tidak berbentuk kredensial") from galat

    tersimpan = await repo.cari(kredensial_id)
    if tersimpan is None:
        raise Ditolak("kredensial tidak dikenal")

    try:
        hasil = webauthn.verify_authentication_response(
            credential=jawaban,
            expected_challenge=tantangan_mentah,
            expected_rp_id=rp_id,
            expected_origin=asal,
            credential_public_key=bytes(tersimpan["kunci_publik"]),
            credential_current_sign_count=tersimpan["penghitung"],
            require_user_verification=True,
        )
    except (InvalidAuthenticationResponse, ValueError) as galat:
        raise Ditolak("tanda tangan tidak berlaku") from galat

    await repo.perbarui_pemakaian(kredensial_id, hasil.new_sign_count)

    pengguna = await repo_pengguna.cari_id(str(tersimpan["pengguna_id"]))
    if pengguna is None:
        raise Ditolak("kredensial tidak dikenal")

    # Sesi yang terbit sama persis dengan sesi hasil sandi: access token
    # pendek plus refresh token berputar. Passkey mengganti cara membuktikan
    # siapa, bukan cara sesinya dikelola.
    return await autentikasi.terbitkan(pengguna)


# ------------------------------------------------------------- mengelola ---


async def daftar_milik(pengguna_id: str) -> list[dict]:
    return [
        {
            "id": str(k["id"]),
            "nama": k["nama"],
            "jenis_perangkat": k["jenis_perangkat"],
            "tercadang": k["tercadang"],
            "transportasi": list(k["transportasi"] or []),
            "dibuat_pada": k["dibuat_pada"],
            "dipakai_pada": k["dipakai_pada"],
        }
        for k in await repo.milik(pengguna_id)
    ]


async def hapus(pengguna_id: str, kredensial_uuid: str) -> bool:
    return await repo.hapus(pengguna_id, kredensial_uuid)


# ------------------------------------------------------------- pembantu ---


def _tantangan_dari(jawaban: dict) -> bytes:
    """Tantangan dibaca dari clientDataJSON, bukan dari kolom terpisah.

    Alasannya bukan kerapian. clientDataJSON adalah bagian yang ikut
    ditandatangani authenticator; kolom lain di badan permintaan tidak.
    Mencari barisnya memakai nilai yang ditandatangani berarti permintaan
    tidak bisa menunjuk satu tantangan sambil menandatangani yang lain.
    """
    import json

    try:
        data = json.loads(base64url_to_bytes(jawaban["response"]["clientDataJSON"]))
        return base64url_to_bytes(data["challenge"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as galat:
        raise Ditolak("jawaban tidak berbentuk WebAuthn") from galat


def _transportasi(jawaban: dict) -> list[str]:
    """Cara perangkat itu dijangkau: usb, nfc, ble, internal, hybrid.

    Datang dari peramban dan **tidak** ditandatangani, jadi ia disaring
    terhadap daftar yang dikenal dan tidak pernah dipercaya untuk keputusan
    apa pun. Gunanya hanya satu: memberi petunjuk ke peramban lain kali,
    supaya ia tidak menyalakan Bluetooth untuk kunci yang tertanam.
    """
    dikenal = {"usb", "nfc", "ble", "internal", "hybrid", "smart-card", "cable"}
    nilai = (jawaban.get("response") or {}).get("transports") or []
    if not isinstance(nilai, list):
        return []
    return [t for t in nilai if isinstance(t, str) and t in dikenal]


def sebagai_base64url(nilai: bytes) -> str:
    return bytes_to_base64url(nilai)
