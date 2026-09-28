"""Daftar alamat Cloudflare untuk nginx dan firewall VPS.

    infrastructure/cloudflare-ip.txt           sumbernya, satu jaringan per baris
    infrastructure/nginx/hendrokuswantoro.conf baris set_real_ip_from

    python tools/ip_cloudflare.py            # tulis ulang nginx dari cloudflare-ip.txt
    python tools/ip_cloudflare.py --ambil    # ambil daftar terbaru dari api.cloudflare.com dulu
    python tools/ip_cloudflare.py --periksa  # bandingkan saja, keluar 1 bila beda
    python tools/ip_cloudflare.py --banding  # bandingkan cloudflare-ip.txt dengan api.cloudflare.com
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import pathlib
import re
import sys
import urllib.request

AKAR = pathlib.Path(__file__).resolve().parent.parent
DAFTAR = AKAR / "infrastructure" / "cloudflare-ip.txt"
NGINX = AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf"
SUMBER = "https://api.cloudflare.com/client/v4/ips"
BLOK = re.compile(r"(?:set_real_ip_from [^;\n]+;\n)+")


def ambil() -> list[str]:
    minta = urllib.request.Request(SUMBER, headers={"User-Agent": "hendrokuswantoro.com ip_cloudflare"})
    with urllib.request.urlopen(minta, timeout=20) as jawaban:
        isi = json.load(jawaban)
    if not isi.get("success"):
        raise SystemExit("api.cloudflare.com tidak memberi daftar alamat")
    hasil = isi["result"]
    return bersihkan(hasil["ipv4_cidrs"] + hasil["ipv6_cidrs"])


def bersihkan(baris: list[str]) -> list[str]:
    jaringan = [ipaddress.ip_network(b.strip()) for b in baris if b.strip()]
    if not jaringan:
        raise SystemExit("daftar alamat Cloudflare kosong")
    return [str(j) for j in jaringan]


def baca() -> list[str]:
    return bersihkan(DAFTAR.read_text(encoding="ascii").splitlines())


def nginx_baru(jaringan: list[str]) -> str:
    lama = NGINX.read_text(encoding="utf-8")
    cocok = list(BLOK.finditer(lama))
    if len(cocok) != 1:
        raise SystemExit(f"{NGINX.name}: harus ada tepat satu blok set_real_ip_from, ada {len(cocok)}")
    isi = "".join(f"set_real_ip_from {j};\n" for j in jaringan)
    return lama[: cocok[0].start()] + isi + lama[cocok[0].end():]


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alasan.add_argument("--ambil", action="store_true")
    alasan.add_argument("--periksa", action="store_true")
    alasan.add_argument("--banding", action="store_true")
    pilihan = alasan.parse_args()

    if pilihan.banding:
        terbit, simpan = set(ambil()), set(baca())
        for j in sorted(terbit - simpan):
            print(f"BARU  {j}")
        for j in sorted(simpan - terbit):
            print(f"HILANG {j}")
        if terbit != simpan:
            print("jalankan: python tools/ip_cloudflare.py --ambil, lalu pasang ulang firewall VPS")
            return 1
        print(f"sama, {len(simpan)} jaringan")
        return 0

    if pilihan.ambil:
        jaringan = ambil()
        DAFTAR.write_text("\n".join(jaringan) + "\n", encoding="ascii", newline="\n")
        print(f"tulis {DAFTAR.relative_to(AKAR).as_posix()}, {len(jaringan)} jaringan")
    else:
        jaringan = baca()

    lama = NGINX.read_text(encoding="utf-8")
    baru = nginx_baru(jaringan)
    nama = NGINX.relative_to(AKAR).as_posix()
    if pilihan.periksa:
        print(f"{'sama ' if lama == baru else 'BEDA '} {nama}")
        return 0 if lama == baru else 1
    if lama != baru:
        NGINX.write_text(baru, encoding="utf-8", newline="\n")
        print(f"tulis {nama}")
    else:
        print(f"tetap {nama}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
