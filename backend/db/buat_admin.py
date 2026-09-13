"""Memasang sandi untuk akun admin.

    python backend/db/buat_admin.py                    # diketik, tidak terlihat
    python backend/db/buat_admin.py --stdin            # dari pipa
    python backend/db/buat_admin.py --acak             # dibangkitkan, DICETAK sekali

Sandinya tidak pernah diminta lewat argumen baris perintah. Argumen tersimpan
di riwayat shell dan terlihat di daftar proses; itu dua tempat rahasia bocor
tanpa ada yang berniat.

**Tentang --acak.** Mode itu satu satunya di berkas ini yang mencetak sandi ke
layar, dan itu memang melanggar kebiasaan yang benar. Alasannya satu: sandi
yang dibangkitkan mesin tidak ada gunanya kalau tidak pernah sampai ke
pemiliknya. Konsekuensinya disebut terus terang tiap kali ia dipakai, yaitu
sandinya tertinggal di gulungan terminal dan sebaiknya diganti begitu Anda
bisa masuk. Untuk pemakaian yang tidak menuntut manusia membacanya, pakai
`--stdin`, yang tidak mencetak apa pun.

Daftar kata untuk --acak sengaja bahasa Indonesia. Sandi yang bisa dibaca dan
diketik ulang tanpa salah adalah sandi yang benar benar dipakai; yang berupa
deretan simbol acak berakhir ditempel di catatan kuning.

Jumlah katanya dihitung dari ambang entropi, bukan dipatok. Percobaan pertama
berkas ini memakai lima kata dan menghasilkan 33 bit, yang terlalu sedikit
untuk sandi yang menjaga jalur tulis.
"""

from __future__ import annotations

import argparse
import getpass
import math
import os
import pathlib
import secrets
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

import psycopg  # noqa: E402

from backend.core.keamanan import hash_sandi  # noqa: E402

PANJANG_MINIMAL = 12

# 96 kata. Dipilih yang tidak punya ejaan kembar dan tidak mudah tertukar
# saat didiktekan lewat telepon.
KATA = (
    "peta jalan sungai gunung lembah pantai pulau hutan sawah kebun danau muara "
    "utara selatan timur barat pagi siang sore malam fajar senja hujan angin "
    "batu pasir tanah lumpur kapur garam besi baja kayu bambu rotan damar "
    "biru hijau merah kuning ungu jingga cokelat kelabu perak emas hitam putih "
    "satu dua tiga empat lima enam tujuh delapan sembilan sepuluh belas puluh "
    "cepat lambat tinggi rendah lebar sempit panjang pendek tebal tipis berat ringan "
    "kota desa pasar pelabuhan bandara jembatan menara benteng candi masjid gereja pura "
    "lurus belok simpang tanjakan turunan tikungan lintasan koridor gerbang lorong teras beranda"
).split()


# Ambang entropi, bukan jumlah kata. Jumlah kata yang dipatok akan berbohong
# begitu daftar katanya diubah panjangnya; ambang bit tetap benar.
#
# 64 bit. Sandi ini dijaga Argon2id dan dibatasi lima percobaan per 15 menit,
# jadi tebakan lewat jaringan bukan ancamannya; yang jadi ancaman adalah hash
# yang ikut bocor lalu ditebak di luar jaringan, dan di situ yang berlaku
# hanya entropinya. Percobaan pertama berkas ini memakai lima kata, yaitu 33
# bit, dan itu terlalu sedikit untuk dipakai menjaga apa pun.
MINIMAL_BIT = 64


def jumlah_kata_untuk(bit: int = MINIMAL_BIT) -> int:
    return math.ceil(bit / math.log2(len(KATA)))


def sandi_acak(jumlah_kata: int | None = None) -> tuple[str, float]:
    """Mengembalikan sandinya beserta entropinya dalam bit.

    secrets.choice, bukan random.choice. Yang kedua memakai Mersenne Twister,
    yang keluarannya bisa diramalkan dari beberapa nilai sebelumnya, dan itu
    persis yang tidak boleh untuk sandi.
    """
    jumlah_kata = jumlah_kata or jumlah_kata_untuk()
    kata = [secrets.choice(KATA) for _ in range(jumlah_kata)]
    entropi = jumlah_kata * math.log2(len(KATA))
    return "-".join(kata), entropi


def baca_sandi(mode: str) -> tuple[str, float | None]:
    if mode == "acak":
        sandi, entropi = sandi_acak()
        return sandi, entropi

    if mode == "stdin":
        sandi = sys.stdin.readline().rstrip("\n")
        if not sandi:
            sys.exit("stdin kosong")
        return sandi, None

    sandi = getpass.getpass("sandi baru: ")
    if sandi != getpass.getpass("ulangi sandi: "):
        sys.exit("sandi tidak sama")
    return sandi, None


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--email", help="kalau kosong, ditanyakan")
    kelompok = alasan.add_mutually_exclusive_group()
    kelompok.add_argument("--acak", action="store_true",
                          help="bangkitkan sandi lalu CETAK sekali ke layar")
    kelompok.add_argument("--stdin", action="store_true",
                          help="baca sandi dari stdin, tidak mencetak apa pun")
    pilihan = alasan.parse_args()

    dsn = os.environ.get("DSN")
    if not dsn:
        sys.exit("DSN belum diisi")

    email = (pilihan.email or input("email admin: ")).strip()
    if not email:
        sys.exit("email kosong")

    mode = "acak" if pilihan.acak else "stdin" if pilihan.stdin else "ketik"
    sandi, entropi = baca_sandi(mode)

    if len(sandi) < PANJANG_MINIMAL:
        sys.exit(f"sandi minimal {PANJANG_MINIMAL} karakter")

    with psycopg.connect(dsn) as s, s.cursor() as k:
        k.execute(
            "UPDATE users SET sandi_hash = %s, peran = 'admin' WHERE lower(email) = lower(%s)",
            (hash_sandi(sandi), email),
        )
        if k.rowcount == 0:
            sys.exit(f"tidak ada pengguna dengan email {email}. Jalankan muat_awal.py dulu.")
        # Sesi lama dicabut di sini juga, bukan cuma disarankan. Sandi yang
        # diganti karena dicurigai bocor tidak ada gunanya kalau sesi yang
        # sudah terbit dengan sandi lama tetap hidup.
        k.execute(
            "UPDATE sesi SET dicabut_pada = now() "
            "WHERE pengguna_id = (SELECT id FROM users WHERE lower(email) = lower(%s)) "
            "AND dicabut_pada IS NULL",
            (email,),
        )
        dicabut = k.rowcount
        s.commit()

    print(f"sandi dipasang untuk {email}")
    print(f"{dicabut} sesi lama dicabut")

    if mode == "acak":
        print()
        print("  email :", email)
        print("  sandi :", sandi)
        print()
        print(f"  Entropi {entropi:.0f} bit, dari {len(KATA)} kata pilihan.")
        print("  Panjang, dan memang begitu: sandi ini menjaga jalur tulis.")
        print("  Sandi ini TERCETAK di layar dan tertinggal di gulungan terminal.")
        print("  Gantilah begitu Anda bisa masuk, lalu daftarkan passkey supaya")
        print("  sandinya tidak lagi jadi satu satunya jalan masuk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
