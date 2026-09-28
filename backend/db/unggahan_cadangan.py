from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import os
import pathlib
import random
import shutil

from backend.db import enkripsi

AKHIRAN = ".enc"
TERHAPUS = "terhapus"
SIMPAN_TERHAPUS_HARI = 30


class Salah(Exception):
    pass


@dataclasses.dataclass
class Laporan:
    baru: list[str] = dataclasses.field(default_factory=list)
    dipindah: list[str] = dataclasses.field(default_factory=list)
    dibuang: list[str] = dataclasses.field(default_factory=list)
    rusak: list[str] = dataclasses.field(default_factory=list)


def _berkas(folder: pathlib.Path) -> list[pathlib.Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))


def _nama_asli(cadangan: pathlib.Path) -> str:
    return cadangan.name.removesuffix(AKHIRAN)


def _cadangan_dari(tujuan: pathlib.Path, nama: str) -> pathlib.Path | None:
    for calon in (tujuan / (nama + AKHIRAN), tujuan / nama):
        if calon.is_file():
            return calon
    return None


def _nama_sah(nama: str) -> str:
    if not nama or "/" in nama or "\\" in nama or nama.startswith("."):
        raise Salah(f"nama berkas tidak sah: {nama[:40]!r}")
    return nama


def isi(cadangan: pathlib.Path, kunci: bytes | None) -> bytes:
    mentah = cadangan.read_bytes()
    if not enkripsi.terenkripsi(mentah):
        return mentah
    if kunci is None:
        raise Salah(f"{cadangan.name} terenkripsi, sedangkan {enkripsi.NAMA_ENV} kosong")
    return enkripsi.buka(mentah, kunci)


def _tulis(target: pathlib.Path, data: bytes) -> None:
    sementara = target.with_name(f".{target.name}.sebagian")
    try:
        sementara.write_bytes(data)
        os.replace(sementara, target)
    finally:
        sementara.unlink(missing_ok=True)


def _sidik(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def salin(sumber: pathlib.Path, tujuan: pathlib.Path, kunci: bytes | None,
          hari_ini: dt.date | None = None) -> Laporan:
    hari_ini = hari_ini or dt.date.today()
    laporan = Laporan()
    if not sumber.is_dir():
        raise Salah(f"folder unggahan tidak ada: {sumber}")

    asli = {p.name: p for p in _berkas(sumber)}
    tersimpan = _berkas(tujuan)
    if not asli and tersimpan:
        raise Salah(
            f"folder unggahan {sumber} kosong, padahal cadangannya menyimpan {len(tersimpan)} "
            "berkas. Periksa UNGGAHAN_DIR sebelum cadangannya disingkirkan."
        )

    tujuan.mkdir(parents=True, exist_ok=True)
    for nama, berkas in asli.items():
        terenkripsi = tujuan / (nama + AKHIRAN)
        polos = tujuan / nama
        if terenkripsi.exists() or (kunci is None and polos.exists()):
            continue
        data = berkas.read_bytes()
        target = terenkripsi if kunci else polos
        _tulis(target, enkripsi.kunci(data, kunci) if kunci else data)
        if _sidik(isi(target, kunci)) != _sidik(data):
            target.unlink()
            laporan.rusak.append(nama)
            continue
        laporan.baru.append(nama)
        if kunci and polos.exists():
            polos.unlink()

    for cadangan in _berkas(tujuan):
        if _nama_asli(cadangan) in asli:
            continue
        folder = tujuan / TERHAPUS / hari_ini.isoformat()
        folder.mkdir(parents=True, exist_ok=True)
        os.replace(cadangan, folder / cadangan.name)
        laporan.dipindah.append(_nama_asli(cadangan))

    gudang = tujuan / TERHAPUS
    if gudang.is_dir():
        for folder in sorted(gudang.iterdir()):
            try:
                tanggal = dt.date.fromisoformat(folder.name)
            except ValueError:
                continue
            if (hari_ini - tanggal).days > SIMPAN_TERHAPUS_HARI:
                shutil.rmtree(folder)
                laporan.dibuang.append(folder.name)
    return laporan


def periksa(sumber: pathlib.Path, tujuan: pathlib.Path, kunci: bytes | None,
            contoh: int = 3, acak: random.Random | None = None) -> list[str]:
    acak = acak or random.Random()
    masalah = []
    berpasangan = []
    for berkas in _berkas(sumber):
        cadangan = _cadangan_dari(tujuan, berkas.name)
        if cadangan is None:
            masalah.append(f"tanpa cadangan: {berkas.name}")
        else:
            berpasangan.append((berkas, cadangan))

    for berkas, cadangan in acak.sample(berpasangan, min(contoh, len(berpasangan))):
        try:
            cocok = _sidik(isi(cadangan, kunci)) == _sidik(berkas.read_bytes())
        except (Salah, enkripsi.TidakBisaDibuka) as galat:
            masalah.append(f"tidak bisa dibuka: {cadangan.name} ({type(galat).__name__})")
            continue
        if not cocok:
            masalah.append(f"isinya berbeda: {cadangan.name}")
    return masalah


def pulihkan(tujuan: pathlib.Path, sumber: pathlib.Path, kunci: bytes | None,
             nama: str | None = None) -> list[str]:
    if nama is not None:
        nama = _nama_sah(nama)
        calon = [_cadangan_dari(tujuan, nama)]
        gudang = tujuan / TERHAPUS
        if gudang.is_dir():
            for folder in sorted(gudang.iterdir(), reverse=True):
                calon.append(_cadangan_dari(folder, nama))
        calon = [c for c in calon if c is not None][:1]
        if not calon:
            raise Salah(f"tidak ada cadangan untuk {nama}")
    else:
        calon = _berkas(tujuan)

    sumber.mkdir(parents=True, exist_ok=True)
    kembali = []
    for cadangan in calon:
        target = sumber / _nama_asli(cadangan)
        if target.exists():
            continue
        _tulis(target, isi(cadangan, kunci))
        kembali.append(target.name)
    return kembali
