"""Authenticator tiruan, untuk menguji passkey tanpa perangkat sungguhan.

Tanpa berkas ini, satu satunya cara menguji WebAuthn adalah menancapkan
kunci keamanan lalu menyentuhnya, dan uji yang menuntut jari manusia adalah
uji yang tidak pernah dijalankan. Jadi di sini ada authenticator ES256 yang
benar benar membuat pasangan kunci, benar benar menandatangani, dan
tanda tangannya benar benar diverifikasi pustaka `webauthn` yang sama dengan
yang dipakai produksi.

Yang **tidak** dikerjakan di sini: tidak ada satu pun potongan kriptografi
yang dipakai jalur produksi. Berkas ini hanya ada di `tests/`, memerankan
peramban dan perangkatnya, dan sengaja bisa berbohong. Kemampuan berbohong
itu justru intinya: `tanda_tangan_palsu` dan `mundurkan_penghitung` ada
supaya ada yang membuktikan servernya menolak.

Bentuk authenticator data mengikuti WebAuthn level 2 bagian 6.1:

    rpIdHash   32 bita
    flags       1 bita
    signCount   4 bita, big endian
    attestedCredentialData, hanya saat mendaftar:
        aaguid             16 bita
        credentialIdLength  2 bita, big endian
        credentialId
        credentialPublicKey, COSE_Key
"""

from __future__ import annotations

import hashlib
import json
import secrets

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from webauthn.helpers import bytes_to_base64url

UP = 0x01   # user present, ada jari yang menyentuh
UV = 0x04   # user verified, jari itu juga dikenali
BE = 0x08   # backup eligible, kuncinya boleh disalin ke perangkat lain
BS = 0x10   # backup state, kuncinya memang sedang tersalin
AT = 0x40   # attested credential data ikut disertakan


class Otentikator:
    """Satu perangkat, satu pasang kunci, satu penghitung."""

    def __init__(self, rp_id: str, aaguid: bytes = b"\x00" * 16) -> None:
        self.rp_id_hash = hashlib.sha256(rp_id.encode("utf-8")).digest()
        self.aaguid = aaguid
        self.kunci = ec.generate_private_key(ec.SECP256R1())
        self.kredensial_id = secrets.token_bytes(32)
        self.penghitung = 0

    # ---------------------------------------------------------- pembantu ---

    def _cose(self) -> bytes:
        """COSE_Key untuk ES256. RFC 8152 tabel 2 dan 5."""
        angka = self.kunci.public_key().public_numbers()
        return cbor2.dumps({
            1: 2,    # kty: EC2
            3: -7,   # alg: ES256
            -1: 1,   # crv: P-256
            -2: angka.x.to_bytes(32, "big"),
            -3: angka.y.to_bytes(32, "big"),
        })

    def _data_klien(self, jenis: str, tantangan: bytes, asal: str) -> bytes:
        return json.dumps({
            "type": jenis,
            "challenge": bytes_to_base64url(tantangan),
            "origin": asal,
            "crossOrigin": False,
        }).encode("utf-8")

    def _data_otentikator(self, bendera: int, dengan_kredensial: bool) -> bytes:
        bagian = [self.rp_id_hash, bytes([bendera]), self.penghitung.to_bytes(4, "big")]
        if dengan_kredensial:
            bagian += [
                self.aaguid,
                len(self.kredensial_id).to_bytes(2, "big"),
                self.kredensial_id,
                self._cose(),
            ]
        return b"".join(bagian)

    # ----------------------------------------------------------- mendaftar ---

    def daftar(self, tantangan: bytes, asal: str, terverifikasi: bool = True) -> dict:
        data_klien = self._data_klien("webauthn.create", tantangan, asal)
        bendera = UP | BE | BS | AT | (UV if terverifikasi else 0)
        data_otentikator = self._data_otentikator(bendera, dengan_kredensial=True)

        atestasi = cbor2.dumps({
            "fmt": "none",
            "attStmt": {},
            "authData": data_otentikator,
        })

        return {
            "id": bytes_to_base64url(self.kredensial_id),
            "rawId": bytes_to_base64url(self.kredensial_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": bytes_to_base64url(data_klien),
                "attestationObject": bytes_to_base64url(atestasi),
                "transports": ["internal", "hybrid"],
            },
            "clientExtensionResults": {},
        }

    # --------------------------------------------------------------- masuk ---

    def masuk(
        self,
        tantangan: bytes,
        asal: str,
        naikkan: int = 1,
        tanda_tangan_palsu: bool = False,
    ) -> dict:
        self.penghitung += naikkan
        data_klien = self._data_klien("webauthn.get", tantangan, asal)
        data_otentikator = self._data_otentikator(UP | UV | BE | BS, dengan_kredensial=False)

        pesan = data_otentikator + hashlib.sha256(data_klien).digest()
        if tanda_tangan_palsu:
            # Ditandatangani kunci lain. Bentuknya sempurna, isinya bukan
            # milik kredensial ini, dan itulah yang harus ditolak server.
            kunci = ec.generate_private_key(ec.SECP256R1())
        else:
            kunci = self.kunci
        tanda = kunci.sign(
            hashlib.sha256(pesan).digest(), ec.ECDSA(Prehashed(hashes.SHA256()))
        )

        return {
            "id": bytes_to_base64url(self.kredensial_id),
            "rawId": bytes_to_base64url(self.kredensial_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": bytes_to_base64url(data_klien),
                "authenticatorData": bytes_to_base64url(data_otentikator),
                "signature": bytes_to_base64url(tanda),
                "userHandle": None,
            },
            "clientExtensionResults": {},
        }

    def mundurkan_penghitung(self, ke: int = 0) -> None:
        """Memerankan kredensial yang disalin: penghitungnya tidak ikut naik."""
        self.penghitung = ke


def tantangan_dari(pilihan: str) -> bytes:
    """Membaca tantangan dari JSON pilihan yang dikirim server."""
    from webauthn.helpers import base64url_to_bytes

    return base64url_to_bytes(json.loads(pilihan)["challenge"])
