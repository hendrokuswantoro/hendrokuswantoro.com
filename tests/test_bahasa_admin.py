"""Bahasa di dashboard admin: pendek, dan tetap jujur.

Permukaan admin sempat berbahasa seperti dokumen. Halaman keamanannya
menjelaskan alasan di balik tiap lapisan dalam paragraf panjang, yang paling
panjang 95 kata, dan seluruhnya 433 kata. Yang membacanya jadi membaca
dokumen, bukan memakai aplikasi.

Alasannya sekarang tinggal di `docs/`, dan layarnya menyebut apa yang terjadi
dan apa yang perlu diketahui. Terukur 191 kata, paragraf terpanjang 29.

Dua hal dijaga di sini, dan keduanya perlu berdiri bersama:

1. **Pendek.** Tidak ada paragraf yang melewati batas, dan tidak ada kalimat
   yang melewati batas.
2. **Tetap jujur.** Peringatan yang paling mudah hilang ketika sebuah teks
   dipendekkan adalah peringatannya sendiri, sebab ia bagian yang paling tidak
   menyenangkan untuk ditulis. Uji di bawah menuntut kalimat yang menyebut
   batas verifikasi wajah tetap ada di layar tempat ia dinyalakan.

Batasnya longgar dengan sengaja. Yang dijaga bukan gaya melainkan kembalinya
paragraf yang tidak akan dibaca siapa pun.
"""

from __future__ import annotations

import re

import pytest

from konftes import AKAR

ADMIN = AKAR / "next" / "components" / "admin"
BERKAS = sorted(ADMIN.glob("*.tsx"))

BATAS_PARAGRAF = 45   # kata
BATAS_KALIMAT = 28    # kata


def _paragraf(teks: str) -> list[tuple[str, str]]:
    """Isi tiap <p className={gaya.penjelasan}> dan {gaya.ket}, sebagai teks biasa.

    Ekspresi JSX seperti {" "} dan {keadaan.email} dibuang: yang diuji kalimat
    yang dibaca orang, bukan kode yang menyusunnya.
    """
    hasil = []
    for blok in re.findall(
        r"<p className=\{`?gaya\.(penjelasan|ket)`?\}[^>]*>(.*?)</p>", teks, re.S
    ):
        kelas, isi = blok
        bersih = re.sub(r"\{[^{}]*\}", " ", isi)       # ekspresi JSX
        bersih = re.sub(r"<[^>]+>", " ", bersih)        # tag di dalamnya
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
    """Kalimat bertingkat tingkat adalah cara paling cepat membuat layar
    berhenti dibaca. Dipisah pada titik, bukan pada koma: koma memang dipakai,
    titik dua dan titik koma yang dihindari."""
    teks = berkas.read_text(encoding="utf-8")
    buruk = []
    for _, isi in _paragraf(teks):
        for kalimat in re.split(r"(?<=[.!?])\s+", isi):
            n = len(kalimat.split())
            if n > BATAS_KALIMAT:
                buruk.append((n, kalimat[:70]))
    assert not buruk, f"{berkas.name} punya kalimat lebih dari {BATAS_KALIMAT} kata: {buruk}"


def test_peringatan_verifikasi_wajah_tidak_ikut_hilang():
    """Yang paling mudah hilang saat teks dipendekkan adalah peringatannya.

    Verifikasi wajah bisa ditembus rekaman video, dan kalimat itu wajib ada di
    layar tempat ia dinyalakan, bukan hanya di docs/. Orang menyalakan fitur
    dari layar, bukan dari repositori.
    """
    teks = (ADMIN / "PanelKeamanan.tsx").read_text(encoding="utf-8")
    rendah = teks.lower()
    for kata in ("rekaman video", "sidik jari"):
        assert kata in rendah, f"peringatan wajah kehilangan kata kunci: {kata}"
    assert "tidak disimpan" in rendah, "layar tidak lagi mengatakan fotonya tidak disimpan"


def test_layar_tetap_menyebut_yang_belum_siap():
    """Tombol yang diam diam gagal lebih buruk daripada tombol yang
    menjelaskan kenapa ia belum bisa dipakai. Ketiga keterangan itu pendek,
    dan tidak boleh ikut terpangkas."""
    teks = (ADMIN / "PanelKeamanan.tsx").read_text(encoding="utf-8")
    for penanda in ("SMTP_HOST", "KUNCI_KOLOM", "ambil_model.py"):
        assert penanda in teks, f"layar tidak lagi menyebut {penanda}"


@pytest.mark.parametrize("berkas", BERKAS, ids=lambda p: p.name)
def test_tanpa_tanda_strip_panjang(berkas):
    """Aturan gaya yang sama dengan situsnya."""
    for isi in (i for _, i in _paragraf(berkas.read_text(encoding="utf-8"))):
        assert "—" not in isi and "–" not in isi, f"tanda strip panjang di {berkas.name}"
