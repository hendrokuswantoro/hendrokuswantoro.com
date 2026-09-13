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


# ------------------------------------------------------------ skema tautan ---
#
# Ditemukan lewat penyisiran 13 September 2026, bukan lewat membaca kode.
# markah.py meng-escape seluruh HTML dengan benar dan menolak HTML mentah,
# tetapi alamat di dalam [label](alamat) hanya di-escape, tidak pernah
# diperiksa skemanya. `[klik](javascript:alert(1))` lolos sempurna.


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
    """Kalau pemeriksaannya hanya ada di sebaris(), tulisan bertautan
    javascript: akan diterima API dengan tenang, tersimpan di basis data, dan
    baru meledak berhari hari kemudian saat situsnya dibangun ulang."""
    with pytest.raises(markah.MarkahSalah) as galat:
        markah.blok("Baris satu.\n\nHalo [klik](javascript:alert(1)) dunia.")
    assert "baris 3" in str(galat.value), str(galat.value)


def test_html_mentah_tetap_ditolak_dan_tag_sebaris_di_escape():
    with pytest.raises(markah.MarkahSalah):
        markah.blok("<div>halo</div>")
    assert "&lt;script&gt;" in markah.sebaris("teks <script>alert(1)</script> biasa")
