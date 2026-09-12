"""Isi blog dan pengurainya.

Sejak Fase 0 tulisan blog adalah data, bukan markup. Uji di berkas ini
menjaga dua hal: berkas isinya terbaca sebagaimana mestinya, dan HTML yang
sudah di-commit benar benar hasil pembangkitan dari isi itu.

Uji terakhir yang paling penting. Tanpanya, seseorang bisa menyunting
blog/*.html dengan tangan, hasilnya terbit, lalu hilang tanpa jejak pada
pembangkitan berikutnya.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

import markah  # noqa: E402
from isi import IsiSalah, SumberBerkas, Teks  # noqa: E402

SUMBER = SumberBerkas(AKAR / "content" / "blog")


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
    """Kolom berpasangan yang NOT NULL di rancangan, versi berkasnya."""
    with pytest.raises(IsiSalah):
        Teks(en="ada", id="   ")
    with pytest.raises(IsiSalah):
        Teks(en="", id="ada")


def test_jumlah_blok_dua_bahasa_sama():
    """Satu bahasa kehilangan satu paragraf adalah kegagalan yang diam."""
    for t in SUMBER.tulisan():
        en = markah.blok(t.isi_en)
        idn = markah.blok(t.isi_id)
        assert len(en) == len(idn), (
            f"{t.slug}: {len(en)} blok Inggris lawan {len(idn)} blok Indonesia"
        )
        for nomor, (a, b) in enumerate(zip(en, idn), 1):
            assert a.jenis == b.jenis, f"{t.slug}: blok ke {nomor} beda jenis"


@pytest.mark.parametrize("mentah,alasan", [
    ("- satu\n- dua", "daftar"),
    ("# Judul", "judul"),
    ("```py\nkode\n```", "kode"),
    ("| a | b |", "tabel"),
    ("![gambar](/a.png)", "gambar"),
    ("<div>mentah</div>", "HTML"),
])
def test_markah_menolak_yang_tidak_didukung(mentah, alasan):
    """Menolak dengan nomor baris lebih baik daripada diam diam salah."""
    with pytest.raises(markah.MarkahSalah) as galat:
        markah.blok(mentah)
    assert "baris" in str(galat.value)


def test_markah_sebaris():
    assert markah.sebaris("*a*") == "<em>a</em>"
    assert markah.sebaris("**a**") == "<strong>a</strong>"
    assert markah.sebaris("`a`") == "<code>a</code>"
    assert markah.sebaris("[a](/b)") == '<a href="/b">a</a>'
    assert markah.sebaris("a < b & c") == "a &lt; b &amp; c"


def test_markah_polos_aman_untuk_atribut():
    """Nilai data-ind masuk ke dalam tanda kutip ganda di HTML."""
    assert '"' not in markah.polos('kata "ini" dan *itu*').replace("&quot;", "")
    assert markah.polos("**tebal**") == "tebal"
    assert markah.polos("[teks](/a)") == "teks"


def test_html_yang_ter_commit_sama_dengan_hasil_bangkitan():
    """Penjaga utama Fase 0.

    Menyunting blog/*.html dengan tangan akan lolos ke produksi lalu lenyap
    diam diam pada pembangkitan berikutnya. Uji ini membuat penyuntingan itu
    gagal di CI, bukan gagal diam diam berminggu minggu kemudian.
    """
    hasil = subprocess.run(
        [sys.executable, "tools/bangun_tulisan.py", "--periksa"],
        cwd=AKAR, capture_output=True, text=True,
    )
    assert hasil.returncode == 0, (
        "berkas yang ter-commit tidak sama dengan hasil pembangkitan.\n"
        "jalankan: python tools/bangun_tulisan.py\n\n" + hasil.stdout + hasil.stderr
    )
