from __future__ import annotations

import re

import pytest

from konftes import AKAR

SURAT_JALUR = AKAR / "backend" / "layanan" / "kabar.py"
AUTH = (AKAR / "backend" / "api" / "v1" / "auth.py").read_text(encoding="utf-8")
KABAR = SURAT_JALUR.read_text(encoding="utf-8")


def test_kabar_dikirim_sebelum_peristiwanya_dicatat():
    potong = AUTH[AUTH.index('hasil = await layanan.terbitkan(pengguna, faktor_kedua=False)') - 900:]
    kirim = potong.index("kabari_masuk")
    catat = potong.index('catat_peristiwa(str(pengguna["id"]), "masuk"')
    assert kirim < catat, (
        "peristiwanya dicatat sebelum kabarnya dikirim, jadi tidak akan pernah "
        "ada perangkat yang terlihat baru"
    )


@pytest.mark.parametrize("cara", ["sandi", "faktor kedua"])
def test_kedua_jalur_masuk_mengabari(cara):
    assert AUTH.count("kabar.kabari_masuk(") >= 2, (
        "hanya satu jalur masuk yang mengabari, jadi yang lain diam diam lolos"
    )


def test_suratnya_tidak_membawa_apa_apa_yang_berharga():
    isi = "\n".join(
        b for b in KABAR.splitlines() if b.strip().startswith(('"', "'", "f\""))
    )
    for jahat in ("token", "kode_", "alamat IP", "otpauth", "rahasia"):
        assert jahat not in isi, f"isi surat menyebut {jahat!r}"


def test_gagal_kirim_tidak_menggagalkan_yang_memicunya():
    assert KABAR.count("except Exception") >= 2
    assert "raise" not in KABAR.split("except Exception")[1][:400]


def test_galat_smtp_tidak_ikut_ke_log():
    assert "type(galat).__name__" in KABAR
    assert "str(galat)" not in KABAR


def test_perubahan_keamanan_ikut_dikabari():
    keamanan = (AKAR / "backend" / "api" / "v1" / "keamanan.py").read_text(encoding="utf-8")
    assert "kabari_perubahan_keamanan" in keamanan


def test_perangkat_baru_dibandingkan_dari_ringkasannya_bukan_alamatnya():
    repo = (AKAR / "backend" / "repositori" / "keamanan.py").read_text(encoding="utf-8")
    potong = repo[repo.index("async def pernah_masuk_dari"):]
    assert "alamat_ringkas" in potong
    assert re.search(r"LIMIT 1", potong), "kueri tanpa LIMIT, padahal yang ditanya ada atau tidak"
