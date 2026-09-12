"""Isi situs dan dari mana ia datang.

`SumberIsi` sengaja dibuat antarmuka sejak hari pertama. Hari ini isinya
datang dari berkas Markdown di `content/`, dan suatu saat dari API yang
membaca PostgreSQL. Pembangkit situs tidak boleh tahu bedanya: berpindah
harus berarti mengganti satu baris yang memilih implementasi, bukan menulis
ulang pembangkitnya. Lihat docs/rancangan-platform.md bagian 5.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Protocol


class IsiSalah(ValueError):
    """Berkas isi yang tidak bisa dibaca, disertai nama berkasnya."""


@dataclass(frozen=True)
class Teks:
    """Satu kalimat dalam dua bahasa. Keduanya selalu wajib ada.

    Ini cerminan dari keputusan skema di rancangan: kolom berpasangan yang
    NOT NULL, bukan tabel terjemahan, supaya tulisan tanpa terjemahan jadi
    keadaan yang mustahil, bukan sekadar tidak dianjurkan.
    """

    en: str
    id: str

    def __post_init__(self) -> None:
        if not self.en.strip() or not self.id.strip():
            raise IsiSalah(f"terjemahan kosong: en={self.en!r} id={self.id!r}")


@dataclass(frozen=True)
class Tulisan:
    slug: str
    tanggal: str            # ISO, 2026-09-02
    tanggal_label: Teks     # "2 Sep 2026"
    judul: Teks
    tag: Teks
    baca: Teks              # "3 min read"
    ringkas: Teks           # kartu di halaman Blog
    keterangan: Teks        # meta description
    lede: Teks              # paragraf pembuka artikel
    isi_en: str             # Markdown
    isi_id: str             # Markdown


@dataclass(frozen=True)
class Proyek:
    slug: str
    urut: int
    kategori: tuple[str, ...]      # app, analysis, satellite, design
    jenis_peta: str                # yang menentukan warna penanda di peta
    lng: float
    lat: float
    badge: Teks
    judul: Teks
    ringkas: Teks
    peran: Teks
    gambar: str
    gambar_alt: Teks
    teknologi: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.kategori:
            raise IsiSalah(f"{self.slug}: kategori kosong")
        if not 94 <= self.lng <= 142 or not -12 <= self.lat <= 7:
            raise IsiSalah(f"{self.slug}: titik di luar Indonesia")

class SumberIsi(Protocol):
    def tulisan(self) -> list[Tulisan]:
        """Terbaru lebih dulu."""

    def proyek(self) -> list[Proyek]:
        """Urut sesuai kolom urut."""


PISAH = re.compile(r"^=== (en|id) ===\s*$", re.M)


class SumberBerkas:
    """Fase 0. Membaca content/blog/*.md."""

    def __init__(self, akar: pathlib.Path) -> None:
        """`akar` adalah folder content/, yang memuat blog/ dan proyek/."""
        self.akar = akar

    def tulisan(self) -> list[Tulisan]:
        hasil = [self._baca(p) for p in sorted((self.akar / "blog").glob("*.md"))]
        hasil.sort(key=lambda t: t.tanggal, reverse=True)
        return hasil

    def proyek(self) -> list[Proyek]:
        hasil = [self._baca_proyek(p) for p in sorted((self.akar / "proyek").glob("*.md"))]
        hasil.sort(key=lambda p: p.urut)
        return hasil

    def _baca_proyek(self, berkas: pathlib.Path) -> Proyek:
        mentah = berkas.read_text(encoding="utf-8")
        try:
            kepala, _ = self._pisah_depan(mentah)
            return Proyek(
                slug=berkas.stem,
                urut=int(kepala["urut"]),
                kategori=tuple(kepala["kategori"].split()),
                jenis_peta=kepala["jenis_peta"],
                lng=float(kepala["lng"]),
                lat=float(kepala["lat"]),
                badge=self._dua(kepala, "badge"),
                judul=self._dua(kepala, "judul"),
                ringkas=self._dua(kepala, "ringkas"),
                peran=self._dua(kepala, "peran"),
                gambar=kepala["gambar"],
                gambar_alt=self._dua(kepala, "gambar_alt"),
                teknologi=tuple(x.strip() for x in kepala["teknologi"].split(",")),
            )
        except (KeyError, IsiSalah, ValueError) as galat:
            raise IsiSalah(f"{berkas.name}: {galat}") from galat

    def _baca(self, berkas: pathlib.Path) -> Tulisan:
        mentah = berkas.read_text(encoding="utf-8")
        try:
            kepala, badan = self._pisah_depan(mentah)
            bagian = self._pisah_bahasa(badan)
            return Tulisan(
                slug=berkas.stem,
                tanggal=kepala["tanggal"],
                tanggal_label=self._dua(kepala, "tanggal_label"),
                judul=self._dua(kepala, "judul"),
                tag=self._dua(kepala, "tag"),
                baca=self._dua(kepala, "baca"),
                ringkas=self._dua(kepala, "ringkas"),
                keterangan=self._dua(kepala, "keterangan"),
                lede=self._dua(kepala, "lede"),
                isi_en=bagian["en"],
                isi_id=bagian["id"],
            )
        except (KeyError, IsiSalah, ValueError) as galat:
            raise IsiSalah(f"{berkas.name}: {galat}") from galat

    @staticmethod
    def _dua(kepala: dict[str, str], nama: str) -> Teks:
        return Teks(en=kepala[f"{nama}_en"], id=kepala[f"{nama}_id"])

    @staticmethod
    def _pisah_depan(mentah: str) -> tuple[dict[str, str], str]:
        if not mentah.startswith("---\n"):
            raise IsiSalah("berkas harus dimulai dengan baris ---")
        akhir = mentah.index("\n---\n", 4)
        kepala: dict[str, str] = {}
        for nomor, baris in enumerate(mentah[4:akhir].splitlines(), 2):
            if not baris.strip():
                continue
            if ":" not in baris:
                raise IsiSalah(f"baris {nomor} bukan 'kunci: nilai'")
            kunci, _, nilai = baris.partition(":")
            kepala[kunci.strip()] = nilai.strip()
        return kepala, mentah[akhir + 5:]

    @staticmethod
    def _pisah_bahasa(badan: str) -> dict[str, str]:
        potong = PISAH.split(badan)
        if len(potong) != 5 or potong[1] != "en" or potong[3] != "id":
            raise IsiSalah("badan harus berisi '=== en ===' lalu '=== id ==='")
        return {"en": potong[2].strip("\n"), "id": potong[4].strip("\n")}
