from __future__ import annotations

import subprocess
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

import markah
from isi import IsiSalah, SumberBerkas, Teks

SUMBER = SumberBerkas(AKAR / "content")


def test_semua_tulisan_terbaca():
    semua = SUMBER.tulisan()
    assert len(semua) >= 3, "content/blog kehilangan tulisan"


def test_urut_terbaru_dulu():
    tanggal = [t.tanggal for t in SUMBER.tulisan()]
    assert tanggal == sorted(tanggal, reverse=True)


def test_setiap_berkas_punya_pasangan_html():
    for t in SUMBER.tulisan():
        assert (AKAR / "blog" / f"{t.slug}.html").exists(), f"{t.slug} belum dibangkitkan"


def test_terjemahan_kosong_ditolak():
    with pytest.raises(IsiSalah):
        Teks(en="ada", id="   ")
    with pytest.raises(IsiSalah):
        Teks(en="", id="ada")


def test_jumlah_blok_dua_bahasa_sama():
    for t in SUMBER.tulisan():
        en = markah.blok(t.isi_en)
        idn = markah.blok(t.isi_id)
        assert len(en) == len(idn), (
            f"{t.slug}: {len(en)} blok Inggris lawan {len(idn)} blok Indonesia"
        )
        for nomor, (a, b) in enumerate(zip(en, idn), 1):
            assert a.jenis == b.jenis, f"{t.slug}: blok ke {nomor} beda jenis"


@pytest.mark.parametrize("mentah,alasan", [
    ("# Judul", "judul"),
    ("```py\nkode\n```", "kode"),
    ("| a | b |", "tabel"),
    ("<div>mentah</div>", "HTML"),
    ("![gambar](https://contoh.example/a.png)", "diunggah ke situs ini"),
    ("![gambar](/unggahan/a.pdf)", "berakhiran"),
    ("![gambar](/unggahan/../rahasia.png)", "'..'"),
    ("!video[a](/unggahan/a.mkv)", "berakhiran"),
    ("![tanpa kurung tutup](/unggahan/a.webp", "tidak dikenali"),
])
def test_markah_menolak_yang_tidak_didukung(mentah, alasan):
    with pytest.raises(markah.MarkahSalah) as galat:
        markah.blok(mentah)
    assert "baris" in str(galat.value)
    assert alasan in str(galat.value), str(galat.value)


@pytest.mark.parametrize("mentah,jenis,butir", [
    ("- satu\n- dua", "ul", 2),
    ("* satu\n* dua\n* tiga", "ul", 3),
    ("1. satu\n2. dua", "ol", 2),
])
def test_markah_menerima_daftar(mentah, jenis, butir):
    hasil = markah.blok(mentah)
    assert len(hasil) == 1
    assert hasil[0].jenis == jenis
    assert len(hasil[0].butir) == butir


def test_markah_menerima_gambar_dan_video_yang_diunggah_ke_sini():
    hasil = markah.blok(
        "![Sebuah jalan](/unggahan/9f3c1a7b-1600x900.webp)\n\n"
        "!video[Menyusuri jalan](/unggahan/9f3c1a7b.mp4)"
    )
    assert [b.jenis for b in hasil] == ["gambar", "video"]
    assert hasil[0].alamat == "/unggahan/9f3c1a7b-1600x900.webp"
    assert hasil[0].teks == "Sebuah jalan"
    assert hasil[1].alamat == "/unggahan/9f3c1a7b.mp4"


def test_ukuran_gambar_dibaca_dari_nama_berkasnya():
    assert markah.ukuran("/unggahan/9f3c1a7b-1600x900.webp") == (1600, 900)
    assert markah.ukuran("/unggahan/9f3c1a7b.mp4") is None


def test_daftar_ditutup_paragraf_berikutnya():
    hasil = markah.blok("Satu.\n- a\n- b\nDua.")
    assert [b.jenis for b in hasil] == ["p", "ul", "p"]


def test_markah_sebaris():
    assert markah.sebaris("*a*") == "<em>a</em>"
    assert markah.sebaris("**a**") == "<strong>a</strong>"
    assert markah.sebaris("`a`") == "<code>a</code>"
    assert markah.sebaris("[a](/b)") == '<a href="/b">a</a>'
    assert markah.sebaris("a < b & c") == "a &lt; b &amp; c"


def test_markah_polos_aman_untuk_atribut():
    assert '"' not in markah.polos('kata "ini" dan *itu*').replace("&quot;", "")
    assert markah.polos("**tebal**") == "tebal"
    assert markah.polos("[teks](/a)") == "teks"


def test_html_yang_ter_commit_sama_dengan_hasil_bangkitan():
    hasil = subprocess.run(
        [sys.executable, "tools/bangun_tulisan.py", "--periksa"],
        cwd=AKAR, capture_output=True, text=True,
    )
    assert hasil.returncode == 0, (
        "berkas yang ter-commit tidak sama dengan hasil pembangkitan.\n"
        "jalankan: python tools/bangun_tulisan.py\n\n" + hasil.stdout + hasil.stderr
    )


@pytest.mark.parametrize("jahat", [
    "[klik](javascript:alert(1))",
    "[klik](JaVaScRiPt:alert(1))",
    "[klik](data:text/html,<script>alert(1)</script>)",
    "[klik](vbscript:msgbox)",
])
def test_skema_tautan_berbahaya_ditolak(jahat):
    with pytest.raises(markah.MarkahSalah):
        markah.sebaris(jahat)


@pytest.mark.parametrize("wajar", [
    "[k](https://contoh.id)",
    "[k](http://contoh.id)",
    "[k](mailto:kuswantoro.hendro01@gmail.com)",
    "[k](/blog/)",
    "[k](#bagian)",
    "[k](tentang.html)",
    "[k](../naik)",
])
def test_tautan_wajar_tetap_lewat(wajar):
    assert "<a href=" in markah.sebaris(wajar)


def test_tautan_diperiksa_juga_saat_memecah_blok():
    with pytest.raises(markah.MarkahSalah) as galat:
        markah.blok("Baris satu.\n\nHalo [klik](javascript:alert(1)) dunia.")
    assert "baris 3" in str(galat.value), str(galat.value)


def test_html_mentah_tetap_ditolak_dan_tag_sebaris_di_escape():
    with pytest.raises(markah.MarkahSalah):
        markah.blok("<div>halo</div>")
    assert "&lt;script&gt;" in markah.sebaris("teks <script>alert(1)</script> biasa")
