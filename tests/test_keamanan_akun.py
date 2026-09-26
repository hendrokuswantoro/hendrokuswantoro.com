from __future__ import annotations

import base64
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

pytest.importorskip("cryptography")

from backend.layanan import totp  # noqa: E402


RAHASIA_RFC = base64.b32encode(b"12345678901234567890").decode().rstrip("=")

VEKTOR = [
    (59, "287082"),
    (1111111109, "081804"),
    (1111111111, "050471"),
    (1234567890, "005924"),
    (2000000000, "279037"),
    (20000000000, "353130"),
]


@pytest.mark.parametrize("detik,harapan", VEKTOR)
def test_totp_cocok_dengan_vektor_rfc(detik, harapan):
    assert totp.kode_sekarang(RAHASIA_RFC, detik) == harapan


def test_totp_menerima_jendela_tetangga():
    saat = 1111111111
    for geser in (-totp.LANGKAH, 0, totp.LANGKAH):
        kode = totp.kode_sekarang(RAHASIA_RFC, saat + geser)
        assert totp.cocok(RAHASIA_RFC, kode, saat) is not None, geser


def test_totp_menolak_yang_terlalu_jauh():
    jauh = totp.kode_sekarang(RAHASIA_RFC, 1111111111 + totp.LANGKAH * 3)
    assert totp.cocok(RAHASIA_RFC, jauh, 1111111111) is None


@pytest.mark.parametrize("buruk", ["", "12345", "1234567", "abcdef", None])
def test_totp_menolak_kode_yang_bentuknya_salah(buruk):
    assert totp.cocok(RAHASIA_RFC, buruk, 1111111111) is None


def test_rahasia_baru_selalu_berbeda():
    assert len({totp.rahasia_baru() for _ in range(30)}) == 30


def test_rahasia_baru_terbaca_aplikasi():
    r = totp.rahasia_baru()
    assert totp.kode_sekarang(r, 0).isdigit()
    alamat = totp.alamat_otpauth(r, "orang@contoh.id")
    assert alamat.startswith("otpauth://totp/")
    assert "issuer=hendrokuswantoro.com" in alamat
    assert f"secret={r}" in alamat


def test_kode_pemulihan_tanpa_huruf_yang_tertukar():
    for terlarang in "IL O U01":
        assert terlarang not in totp.ABJAD
    kode = totp.kode_pemulihan_baru()
    assert len(kode) == totp.PANJANG_BAGIAN * 2 + 1
    assert kode[totp.PANJANG_BAGIAN] == "-"


def test_kode_pemulihan_dinormalkan_saat_diketik_ulang():
    kode = totp.kode_pemulihan_baru()
    bersih = totp.normalkan_pemulihan(kode)
    for bentuk in (kode.lower(), kode.replace("-", ""), f"  {kode}  ", kode.replace("-", " ")):
        assert totp.normalkan_pemulihan(bentuk) == bersih


def test_kode_pemulihan_punya_cukup_entropi():
    import math

    bit = math.log2(len(totp.ABJAD)) * totp.PANJANG_BAGIAN * 2
    assert bit > 45, f"cuma {bit:.1f} bit"


from backend.core import rahasia  # noqa: E402


@pytest.fixture(autouse=True)
def pengaturan_segar():
    from backend.core import konfigurasi

    konfigurasi.pengaturan.cache_clear()
    yield
    konfigurasi.pengaturan.cache_clear()


@pytest.fixture
def kunci_kolom(monkeypatch):
    from backend.core import konfigurasi
    from backend.db import enkripsi

    monkeypatch.setenv(rahasia.NAMA_ENV, enkripsi.buat_kunci())
    konfigurasi.pengaturan.cache_clear()


def test_rahasia_totp_bolak_balik(kunci_kolom):
    asli = totp.rahasia_baru()
    tersandi = rahasia.sandikan(asli)
    assert asli not in tersandi
    assert rahasia.bukakan(tersandi) == asli


def test_dua_kali_menyandi_menghasilkan_untai_berbeda(kunci_kolom):
    r = totp.rahasia_baru()
    assert rahasia.sandikan(r) != rahasia.sandikan(r)


def test_tanpa_kunci_tidak_diam_diam_menyimpan_apa_adanya(monkeypatch):
    monkeypatch.setenv(rahasia.NAMA_ENV, "")
    _segarkan()
    assert rahasia.siap() is False
    with pytest.raises(rahasia.KunciTidakAda):
        rahasia.sandikan("apa pun")


@pytest.mark.parametrize("buruk", ["bukan base64!!", base64.b64encode(b"pendek").decode()])
def test_kunci_yang_salah_bentuk_ditolak_dengan_jelas(monkeypatch, buruk):
    monkeypatch.setenv(rahasia.NAMA_ENV, buruk)
    _segarkan()
    with pytest.raises(rahasia.KunciTidakAda):
        rahasia.sandikan("apa pun")


def test_kolom_yang_diubah_satu_bit_ketahuan(kunci_kolom):
    from backend.db import enkripsi

    tersandi = bytearray(base64.b64decode(rahasia.sandikan(totp.rahasia_baru())))
    tersandi[-1] ^= 0x01
    with pytest.raises(enkripsi.TidakBisaDibuka):
        rahasia.bukakan(base64.b64encode(bytes(tersandi)).decode())


from backend.core import surat  # noqa: E402


@pytest.fixture
def tanpa_smtp(monkeypatch):
    from backend.core import konfigurasi

    for nama in ("SMTP_HOST", "SMTP_PENGGUNA", "SMTP_SANDI", "SURAT_DARI"):
        monkeypatch.setenv(nama, "")
    monkeypatch.setenv("SURAT_WAJIB", "0")
    konfigurasi.pengaturan.cache_clear()


def test_tanpa_smtp_surat_tidak_pernah_mengaku_terkirim(tanpa_smtp):
    hasil = surat.kirim("orang@contoh.id", "Coba", "isi")
    assert hasil.terkirim is False
    assert "TIDAK dikirim" in hasil.catatan
    assert "SMTP_HOST" in hasil.catatan


def test_surat_wajib_melempar_bukan_menulis_berkas(monkeypatch, tanpa_smtp):
    monkeypatch.setenv("SURAT_WAJIB", "1")
    _segarkan()
    with pytest.raises(surat.TidakTerkirim):
        surat.kirim("orang@contoh.id", "Coba", "isi")


def test_header_tidak_bisa_disuntik_lewat_baris_baru(tanpa_smtp):
    import email as pustaka_email
    import pathlib

    sebelum = set((surat.KOTAK).glob("*.eml")) if surat.KOTAK.exists() else set()
    hasil = surat.kirim(
        "orang@contoh.id\nBcc: penyusup@contoh.id",
        "Coba\nBcc: penyusup@contoh.id",
        "isi",
    )
    assert "\n" not in hasil.kemana

    baru = [p for p in surat.KOTAK.glob("*.eml") if p not in sebelum]
    assert baru, "suratnya tidak ditulis ke mana pun"
    pesan = pustaka_email.message_from_bytes(
        pathlib.Path(sorted(baru)[-1]).read_bytes()
    )
    assert pesan["Bcc"] is None, "baris baru berhasil menyuntikkan header"
    assert "penyusup" not in (pesan["Subject"] or "") or "\n" not in (pesan["Subject"] or "")


def _segarkan() -> None:
    from backend.core import konfigurasi

    konfigurasi.pengaturan.cache_clear()


def test_siap_hanya_kalau_host_dan_pengirim_ada(monkeypatch, tanpa_smtp):
    assert surat.siap() is False
    monkeypatch.setenv("SMTP_HOST", "smtp.contoh.id")
    _segarkan()
    assert surat.siap() is False, "host saja belum cukup"
    monkeypatch.setenv("SURAT_DARI", "situs@contoh.id")
    _segarkan()
    assert surat.siap() is True


from backend.core import keamanan as inti  # noqa: E402


@pytest.fixture
def rahasia_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "u" * 48)
    from backend.core import konfigurasi

    konfigurasi.pengaturan.cache_clear()
    yield
    konfigurasi.pengaturan.cache_clear()


def test_tiket_tidak_bisa_dipakai_sebagai_token_akses(rahasia_jwt):
    tiket, _ = inti.buat_tiket_faktor_kedua("abc", ["totp"])
    assert inti.baca_access_token(tiket) is None
    assert inti.baca_tiket_faktor_kedua(tiket) is not None


def test_token_akses_tidak_bisa_dipakai_sebagai_tiket(rahasia_jwt):
    akses, _ = inti.buat_access_token("abc", "admin")
    assert inti.baca_tiket_faktor_kedua(akses) is None


def test_tiket_membawa_cara_yang_boleh_dipakai(rahasia_jwt):
    tiket, umur = inti.buat_tiket_faktor_kedua("abc", ["totp", "pemulihan"])
    muatan = inti.baca_tiket_faktor_kedua(tiket)
    assert muatan["cara"] == ["totp", "pemulihan"]
    assert umur == inti.TIKET_UMUR_MENIT * 60


def test_tiket_umurnya_pendek():
    assert inti.TIKET_UMUR_MENIT <= 10, "tiket yang hidup lama adalah sesi separuh"


def test_tidak_ada_kunci_atau_rahasia_yang_ditulis_di_dalam_kode():
    for nama in ("backend/core/rahasia.py", "backend/core/surat.py",
                 "backend/layanan/keamanan.py", "backend/layanan/totp.py"):
        isi = (AKAR / nama).read_text(encoding="utf-8")
        for baris in isi.splitlines():
            bersih = baris.strip()
            if bersih.startswith("#") or '"""' in bersih:
                continue
            for terlarang in ("KUNCI_KOLOM=", "SMTP_SANDI=", "JWT_SECRET="):
                assert terlarang not in bersih, f"{nama}: {baris}"


def test_kode_tidak_pernah_ikut_ke_pesan_galat():
    isi = (AKAR / "backend" / "core" / "surat.py").read_text(encoding="utf-8")
    assert "type(galat).__name__" in isi
    assert "str(galat)" not in isi, "pesan galat SMTP bisa memuat isi suratnya"
