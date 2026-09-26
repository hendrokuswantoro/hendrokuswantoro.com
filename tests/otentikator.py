from __future__ import annotations

import hashlib
import json
import secrets

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from webauthn.helpers import bytes_to_base64url

UP = 0x01
UV = 0x04
BE = 0x08
BS = 0x10
AT = 0x40


class Otentikator:
    def __init__(self, rp_id: str, aaguid: bytes = b"\x00" * 16) -> None:
        self.rp_id_hash = hashlib.sha256(rp_id.encode("utf-8")).digest()
        self.aaguid = aaguid
        self.kunci = ec.generate_private_key(ec.SECP256R1())
        self.kredensial_id = secrets.token_bytes(32)
        self.penghitung = 0


    def _cose(self) -> bytes:
        angka = self.kunci.public_key().public_numbers()
        return cbor2.dumps({
            1: 2,
            3: -7,
            -1: 1,
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
        self.penghitung = ke


def tantangan_dari(pilihan: str) -> bytes:
    from webauthn.helpers import base64url_to_bytes

    return base64url_to_bytes(json.loads(pilihan)["challenge"])
