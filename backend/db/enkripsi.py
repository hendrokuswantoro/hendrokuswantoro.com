"""Enkripsi berkas cadangan. Bab 15.18.

Cadangan basis data adalah salinan lengkap dari segala yang pernah ditulis,
termasuk alamat email, hash sandi, dan kunci publik passkey. Selama ia duduk
di folder `cadangan/` pada mesin yang sama dengan basis datanya, enkripsi
tidak menambah apa apa: siapa pun yang bisa membaca berkasnya sudah bisa
membaca basis datanya. Ia jadi penting begitu cadangannya dikirim keluar,
ke object storage, ke laptop lain, ke mana pun yang bukan mesin ini. Karena
itu ada berkas ini, dan karena itu juga ia tidak diwajibkan untuk cadangan
lokal.

**Tidak ada protokol buatan sendiri di sini**, sesuai larangan bab 15.8.
Yang dipakai AES-256-GCM dari pustaka `cryptography`, satu panggilan, tanpa
pembingkaian potong potong buatan sendiri. Bentuk berkasnya sesederhana yang
bisa: penanda, nonce, lalu ciphertext beserta tag autentikasinya.

    HKCAD1\\n   7 bita, supaya berkasnya bisa dikenali tanpa dicoba dibuka
    nonce      12 bita acak, tidak pernah dipakai dua kali dengan kunci sama
    ciphertext sisa berkas, sudah termasuk tag 16 bita di ujungnya

GCM memberi kerahasiaan sekaligus keutuhan: berkas yang diubah satu bit pun
gagal dibuka, bukan terbuka jadi sampah. Itu yang membedakannya dari mode
yang hanya menyandi, dan itu yang membuat cadangan yang rusak di tengah
jalan ketahuan saat dipulihkan, bukan sesudah dipakai.

Satu batasan yang disebut terus terang: seluruh isinya masuk memori sekali
jalan. Untuk cadangan situs empat halaman itu bukan masalah, dan menuliskan
pemotongan sendiri demi berkas besar berarti merancang format sendiri, yang
justru dilarang. Kalau suatu hari cadangannya melewati BATAS_BITA, berkas
ini menolak, bukan diam diam memakan seluruh memori mesin.

Kuncinya tidak pernah ada di dalam kode. Ia datang dari environment:

    python backend/db/enkripsi.py kunci     # buat satu, lalu simpan di .env
"""

from __future__ import annotations

import base64
import os
import secrets
import sys

PENANDA = b"HKCAD1\n"
PANJANG_NONCE = 12
PANJANG_KUNCI = 32

# 512 MB. Jauh di atas ukuran cadangan situs ini, dan jauh di bawah titik
# tempat memuat seluruhnya ke memori jadi berbahaya.
BATAS_BITA = 512 * 1024 * 1024

NAMA_ENV = "CADANGAN_KUNCI"


class KunciTidakAda(RuntimeError):
    """Diminta mengenkripsi tanpa kunci di environment."""


class TidakBisaDibuka(RuntimeError):
    """Kunci salah, berkasnya berubah, atau bukan berkas cadangan."""


def buat_kunci() -> str:
    """32 bita acak, ditulis base64 supaya muat di satu baris .env."""
    return base64.b64encode(secrets.token_bytes(PANJANG_KUNCI)).decode("ascii")


def kunci_dari_env(wajib: bool = True) -> bytes | None:
    mentah = os.environ.get(NAMA_ENV, "").strip()
    if not mentah:
        if wajib:
            raise KunciTidakAda(
                f"{NAMA_ENV} belum diisi. Buat satu dengan:\n"
                "    python backend/db/enkripsi.py kunci"
            )
        return None

    try:
        kunci = base64.b64decode(mentah, validate=True)
    except Exception as galat:
        raise KunciTidakAda(f"{NAMA_ENV} bukan base64 yang sah") from galat

    if len(kunci) != PANJANG_KUNCI:
        raise KunciTidakAda(
            f"{NAMA_ENV} panjangnya {len(kunci)} bita, seharusnya {PANJANG_KUNCI}"
        )
    return kunci


def _aesgcm(kunci: bytes):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return AESGCM(kunci)


def terenkripsi(isi: bytes) -> bool:
    return isi[:len(PENANDA)] == PENANDA


def kunci(isi: bytes, kunci_rahasia: bytes) -> bytes:
    if len(isi) > BATAS_BITA:
        raise ValueError(
            f"isinya {len(isi) // 1024 // 1024} MB, di atas batas "
            f"{BATAS_BITA // 1024 // 1024} MB yang dibaca sekali jalan"
        )
    nonce = secrets.token_bytes(PANJANG_NONCE)
    # Penanda ikut diautentikasi sebagai associated data: berkas yang
    # penandanya diganti akan gagal dibuka, bukan diterima diam diam.
    sandi = _aesgcm(kunci_rahasia).encrypt(nonce, isi, PENANDA)
    return PENANDA + nonce + sandi


def buka(isi: bytes, kunci_rahasia: bytes) -> bytes:
    if not terenkripsi(isi):
        raise TidakBisaDibuka("berkas ini tidak terenkripsi")

    badan = isi[len(PENANDA):]
    if len(badan) <= PANJANG_NONCE + 16:
        raise TidakBisaDibuka("berkasnya terpotong")

    nonce, sandi = badan[:PANJANG_NONCE], badan[PANJANG_NONCE:]
    try:
        return _aesgcm(kunci_rahasia).decrypt(nonce, sandi, PENANDA)
    except Exception as galat:
        raise TidakBisaDibuka(
            "gagal dibuka: kuncinya salah, atau berkasnya berubah sejak dibuat"
        ) from galat


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] != "kunci":
        print(__doc__)
        print("Pemakaian: python backend/db/enkripsi.py kunci")
        return 1

    print(f"{NAMA_ENV}={buat_kunci()}")
    print()
    print("Salin baris di atas ke .env, lalu simpan juga salinannya di tempat")
    print("yang BUKAN mesin ini. Kunci yang hilang berarti seluruh cadangan")
    print("yang sudah terenkripsi tidak akan pernah bisa dibuka lagi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
