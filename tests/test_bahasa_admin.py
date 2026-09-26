from __future__ import annotations

import re

import pytest

from konftes import AKAR

ADMIN = AKAR / "next" / "components" / "admin"
BERKAS = sorted(ADMIN.glob("*.tsx"))

BATAS_PARAGRAF = 45
BATAS_KALIMAT = 28


def _paragraf(teks: str) -> list[tuple[str, str]]:
    hasil = []
    for blok in re.findall(
        r"<p className=\{`?gaya\.(penjelasan|ket)`?\}[^>]*>(.*?)</p>", teks, re.S
    ):
        kelas, isi = blok
        bersih = re.sub(r"\{[^{}]*\}", " ", isi)
        bersih = re.sub(r"<[^>]+>", " ", bersih)
        bersih = re.sub(r"\s+", " ", bersih).strip()
        if bersih:
            hasil.append((kelas, bersih))
    return hasil


@pytest.mark.parametrize("berkas", BERKAS, ids=lambda p: p.name)
def test_tidak_ada_paragraf_yang_kepanjangan(berkas):
    teks = berkas.read_text(encoding="utf-8")
    panjang = [
        (len(isi.split()), isi[:60])
        for _, isi in _paragraf(teks)
        if len(isi.split()) > BATAS_PARAGRAF
    ]
    assert not panjang, (
        f"{berkas.name} punya paragraf lebih dari {BATAS_PARAGRAF} kata: {panjang}"
    )


@pytest.mark.parametrize("berkas", BERKAS, ids=lambda p: p.name)
def test_tidak_ada_kalimat_yang_kepanjangan(berkas):
    teks = berkas.read_text(encoding="utf-8")
    buruk = []
    for _, isi in _paragraf(teks):
        for kalimat in re.split(r"(?<=[.!?])\s+", isi):
            n = len(kalimat.split())
            if n > BATAS_KALIMAT:
                buruk.append((n, kalimat[:70]))
    assert not buruk, f"{berkas.name} punya kalimat lebih dari {BATAS_KALIMAT} kata: {buruk}"


def test_peringatan_verifikasi_wajah_tidak_ikut_hilang():
    teks = (ADMIN / "PanelKeamanan.tsx").read_text(encoding="utf-8")
    rendah = teks.lower()
    for kata in ("rekaman video", "sidik jari"):
        assert kata in rendah, f"peringatan wajah kehilangan kata kunci: {kata}"
    assert "tidak disimpan" in rendah, "layar tidak lagi mengatakan fotonya tidak disimpan"


def test_layar_tetap_menyebut_yang_belum_siap():
    teks = (ADMIN / "PanelKeamanan.tsx").read_text(encoding="utf-8")
    for penanda in ("SMTP_HOST", "KUNCI_KOLOM", "ambil_model.py"):
        assert penanda in teks, f"layar tidak lagi menyebut {penanda}"


@pytest.mark.parametrize("berkas", BERKAS, ids=lambda p: p.name)
def test_tanpa_tanda_strip_panjang(berkas):
    for isi in (i for _, i in _paragraf(berkas.read_text(encoding="utf-8"))):
        assert "—" not in isi and "–" not in isi, f"tanda strip panjang di {berkas.name}"
