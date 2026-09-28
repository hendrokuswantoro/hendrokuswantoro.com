from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass

import webauthn
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from backend.core.konfigurasi import pengaturan
from backend.layanan import autentikasi
from backend.repositori import passkey as repo
from backend.repositori import pengguna as repo_pengguna

UMUR_TANTANGAN_DETIK = 300

NAMA_MAKS = 80


class Ditolak(Exception):
    pass


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


async def mulai_daftar(pengguna_id: str, jenis: str = "perangkat") -> dict:
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
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
            authenticator_attachment=(
                AuthenticatorAttachment.PLATFORM if jenis == "perangkat"
                else AuthenticatorAttachment.CROSS_PLATFORM
            ),
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


async def mulai_masuk() -> dict:
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
    tantangan_mentah = _tantangan_dari(jawaban)
    if await repo.pakai_tantangan("masuk", tantangan_mentah) is None:
        raise Ditolak("tantangan tidak berlaku")

    tersimpan = await _periksa_tanda_tangan(jawaban, tantangan_mentah)

    pengguna = await repo_pengguna.cari_id(str(tersimpan["pengguna_id"]))
    if pengguna is None:
        raise Ditolak("kredensial tidak dikenal")

    return await autentikasi.terbitkan(pengguna, faktor_kedua=True)


async def mulai_buka(pengguna_id: str) -> dict:
    rp_id, _ = _rp()
    milik = await repo.milik(pengguna_id)
    if not milik:
        raise Ditolak("belum ada sidik jari atau passkey yang terdaftar")
    tantangan = await _tantangan_baru("buka", pengguna_id)

    pilihan = webauthn.generate_authentication_options(
        rp_id=rp_id,
        challenge=tantangan,
        timeout=UMUR_TANTANGAN_DETIK * 1000,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=bytes(k["kredensial_id"])) for k in milik
        ],
    )
    return {"pilihan": webauthn.options_to_json(pilihan)}


async def selesaikan_buka(pengguna_id: str, jawaban: dict) -> None:
    tantangan_mentah = _tantangan_dari(jawaban)
    dipakai = await repo.pakai_tantangan("buka", tantangan_mentah)
    if dipakai is None or str(dipakai["pengguna_id"]) != str(pengguna_id):
        raise Ditolak("tantangan tidak berlaku")

    tersimpan = await _periksa_tanda_tangan(jawaban, tantangan_mentah)
    if str(tersimpan["pengguna_id"]) != str(pengguna_id):
        raise Ditolak("kredensial bukan milik akun ini")


async def _periksa_tanda_tangan(jawaban: dict, tantangan_mentah: bytes) -> dict:
    rp_id, asal = _rp()

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
    return tersimpan


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


def _tantangan_dari(jawaban: dict) -> bytes:
    import json

    try:
        data = json.loads(base64url_to_bytes(jawaban["response"]["clientDataJSON"]))
        return base64url_to_bytes(data["challenge"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as galat:
        raise Ditolak("jawaban tidak berbentuk WebAuthn") from galat


def _transportasi(jawaban: dict) -> list[str]:
    dikenal = {"usb", "nfc", "ble", "internal", "hybrid", "smart-card", "cable"}
    nilai = (jawaban.get("response") or {}).get("transports") or []
    if not isinstance(nilai, list):
        return []
    return [t for t in nilai if isinstance(t, str) and t in dikenal]

