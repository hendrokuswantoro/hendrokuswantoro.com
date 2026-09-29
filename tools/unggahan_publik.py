from __future__ import annotations

import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

import markah
from isi import IsiSalah, Tulisan

AWALAN = "/unggahan/"
BATAS_BITA = 25 * 1024 * 1024


def rujukan(tulisan: list[Tulisan]) -> dict[str, list[str]]:
    hasil: dict[str, list[str]] = {}
    for t in tulisan:
        for isi in (t.isi_en, t.isi_id):
            try:
                semua_blok = markah.blok(isi)
            except markah.MarkahSalah as galat:
                raise IsiSalah(f"{t.slug}: {galat}") from galat
            for b in semua_blok:
                if b.alamat and b.alamat.startswith(AWALAN):
                    nama = b.alamat[len(AWALAN):]
                    if not nama or "/" in nama or "\\" in nama or nama.startswith("."):
                        raise IsiSalah(f"{t.slug}: nama unggahan tidak sah: {b.alamat}")
                    slug = hasil.setdefault(nama, [])
                    if t.slug not in slug:
                        slug.append(t.slug)
    return hasil


def _berkas(folder: pathlib.Path) -> set[str]:
    if not folder.is_dir():
        return set()
    return {p.name for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")}


def periksa(dipakai: dict[str, list[str]], folder: pathlib.Path, batas: int = BATAS_BITA) -> list[str]:
    ada = _berkas(folder)
    masalah = []
    for nama in sorted(dipakai):
        if nama not in ada:
            masalah.append(f"HILANG content/unggahan/{nama}, disebut {', '.join(dipakai[nama])}")
        elif (folder / nama).stat().st_size > batas:
            masalah.append(f"TERLALU BESAR content/unggahan/{nama}: Cloudflare menolak berkas di atas "
                           f"{batas // (1024 * 1024)} MB")
    for nama in sorted(ada - set(dipakai)):
        masalah.append(f"YATIM content/unggahan/{nama}: tidak disebut tulisan mana pun")
    return masalah


def salin(dipakai: dict[str, list[str]], folder: pathlib.Path, pangkal: str,
          batas: int = BATAS_BITA, waktu_tunggu: int = 60) -> list[str]:
    folder.mkdir(parents=True, exist_ok=True)
    baru = []
    for nama in sorted(dipakai):
        tujuan = folder / nama
        if tujuan.exists():
            continue
        alamat = f"{pangkal.rstrip('/')}{AWALAN}{urllib.parse.quote(nama)}"
        sementara = folder / f".{nama}.sebagian"
        try:
            with urllib.request.urlopen(alamat, timeout=waktu_tunggu) as jawaban:
                data = jawaban.read(batas + 1)
        except urllib.error.URLError as galat:
            raise IsiSalah(f"{alamat}: {galat}") from galat
        if len(data) > batas:
            raise IsiSalah(
                f"{nama} lebih dari {batas // (1024 * 1024)} MB, disebut {', '.join(dipakai[nama])}. "
                "Cloudflare menolak berkas sebesar itu; perkecil dulu, lalu unggah ulang."
            )
        try:
            sementara.write_bytes(data)
            os.replace(sementara, tujuan)
        finally:
            sementara.unlink(missing_ok=True)
        baru.append(nama)
    return baru


def pangkas(dipakai: dict[str, list[str]], folder: pathlib.Path) -> list[str]:
    buang = sorted(_berkas(folder) - set(dipakai))
    for nama in buang:
        (folder / nama).unlink()
    return buang
