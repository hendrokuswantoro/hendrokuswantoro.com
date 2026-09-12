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


class SumberIsi(Protocol):
    def tulisan(self) -> list[Tulisan]:
        """Terbaru lebih dulu."""


PISAH = re.compile(r"^=== (en|id) ===\s*$", re.M)


class SumberBerkas:
    """Fase 0. Membaca content/blog/*.md."""

    def __init__(self, akar: pathlib.Path) -> None:
        self.akar = akar

    def tulisan(self) -> list[Tulisan]:
        hasil = [self._baca(p) for p in sorted(self.akar.glob("*.md"))]
        hasil.sort(key=lambda t: t.tanggal, reverse=True)
        return hasil

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
