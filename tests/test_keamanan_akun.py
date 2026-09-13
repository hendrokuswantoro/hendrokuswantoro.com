"""Verifikasi email, TOTP, kode pemulihan, dan jejak keamanan.

Sebagian besar uji di sini menguji **penolakan**, bukan keberhasilan. Faktor
kedua yang bisa dilewati adalah faktor kedua yang tidak ada, dan yang paling
mudah terjadi bukan "kodenya salah diterima" melainkan hal hal yang lebih
sunyi: kode yang masih hidup setelah dipakai, tiket faktor kedua yang ternyata
diterima sebagai token akses, rahasia TOTP yang tersimpan apa adanya, dan kode
yang ikut tercetak ke log.

Yang tidak butuh basis data dijalankan selalu; sisanya dilewati kalau Postgres
tidak ada, dengan alasan yang disebut.
"""

from __future__ import annotations

import asyncio
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

# --------------------------------------------------------------- TOTP ---

# Vektor uji resmi RFC 6238, lampiran B, baris SHA1. Kuncinya untai ASCII
# "12345678901234567890".
#
# Ini yang membedakan implementasi TOTP yang benar dari yang kebetulan
# menghasilkan enam angka. Tanpa vektor ini, kode yang salah geser satu bit
# tetap tampak bekerja sampai ada yang mencoba memakainya dengan aplikasi
# authenticator sungguhan.
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
    """Jam perangkat tidak pernah persis sama dengan jam server."""
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
    """Kode ini disalin dari kertas. I dan 1, O dan 0, tidak boleh ada."""
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
    """30 huruf, 10 posisi: sekitar 49 bit. Jauh di atas yang bisa ditebak
    lewat jaringan."""
    import math

    bit = math.log2(len(totp.ABJAD)) * totp.PANJANG_BAGIAN * 2
    assert bit > 45, f"cuma {bit:.1f} bit"


# ------------------------------------------------------ penyandian kolom ---

from backend.core import rahasia  # noqa: E402


@pytest.fixture(autouse=True)
def pengaturan_segar():
    """Pengaturan di-cache seumur proses.

    Sejak kunci dan SMTP dibaca lewat Pengaturan, bukan lewat os.environ,
    monkeypatch pada variabel lingkungan tidak berpengaruh apa apa sampai
    cache-nya dibuang. Uji yang lupa membuangnya akan lulus atau gagal
    tergantung urutan uji sebelumnya, dan itu jenis kegagalan yang paling
    lama dicari.
    """
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
    """Nonce acak. Tanpa itu, dua pengguna dengan rahasia sama punya kolom
    yang sama persis, dan itu terlihat dari dump basis datanya."""
    r = totp.rahasia_baru()
    assert rahasia.sandikan(r) != rahasia.sandikan(r)


def test_tanpa_kunci_tidak_diam_diam_menyimpan_apa_adanya(monkeypatch):
    """Fitur yang menurunkan jaminannya sendiri saat konfigurasinya kurang
    adalah fitur yang jaminannya tidak pernah bisa dipercaya."""
    # Dikosongkan, bukan dihapus: nilai di .env akan menang kalau variabelnya
    # cuma dihilangkan, dan ujinya berubah perilaku begitu kuncinya dipasang
    # di mesin pemilik situs.
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


# ------------------------------------------------------------------ surat ---

from backend.core import surat  # noqa: E402


@pytest.fixture
def tanpa_smtp(monkeypatch):
    """Dikosongkan, bukan dihapus.

    Pengaturan membaca variabel lingkungan LALU .env. Menghapus variabelnya
    hanya membuat nilai di .env yang menang, jadi uji ini akan berubah
    perilakunya begitu pemilik situs mengisi SMTP di berkasnya sendiri, dan
    berubahnya di mesin dia saja. Diisi untai kosong, yang tetap menang atas
    .env dan artinya memang "tidak ada".
    """
    from backend.core import konfigurasi

    for nama in ("SMTP_HOST", "SMTP_PENGGUNA", "SMTP_SANDI", "SURAT_DARI"):
        monkeypatch.setenv(nama, "")
    # bool, bukan untai: pydantic menolak "" sebagai boolean, dan benar.
    monkeypatch.setenv("SURAT_WAJIB", "0")
    konfigurasi.pengaturan.cache_clear()


def test_tanpa_smtp_surat_tidak_pernah_mengaku_terkirim(tanpa_smtp):
    """Godaan yang ditolak: mencetak kodenya ke log lalu membalas "terkirim".
    Verifikasi email yang emailnya tidak pernah sampai bukan verifikasi apa apa,
    dan lebih buruk daripada tidak ada, sebab sesudahnya ada kolom di basis
    data yang mengatakan alamat itu sudah terbukti."""
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
    """Baris baru di subjek adalah cara paling tua mengubah satu surat jadi
    surat ke orang lain."""
    import email as pustaka_email
    import pathlib

    sebelum = set((surat.KOTAK).glob("*.eml")) if surat.KOTAK.exists() else set()
    hasil = surat.kirim(
        "orang@contoh.id\nBcc: penyusup@contoh.id",
        "Coba\nBcc: penyusup@contoh.id",
        "isi",
    )
    assert "\n" not in hasil.kemana

    # Dibaca kembali dari berkas .eml yang ditulis, bukan dari nilai yang
    # dikembalikan: yang menentukan aman atau tidak adalah bentuk surat yang
    # benar benar berangkat, bukan apa yang dilaporkan pemanggilnya.
    baru = [p for p in surat.KOTAK.glob("*.eml") if p not in sebelum]
    assert baru, "suratnya tidak ditulis ke mana pun"
    pesan = pustaka_email.message_from_bytes(
        pathlib.Path(sorted(baru)[-1]).read_bytes()
    )
    assert pesan["Bcc"] is None, "baris baru berhasil menyuntikkan header"
    assert "penyusup" not in (pesan["Subject"] or "") or "\n" not in (pesan["Subject"] or "")


def _segarkan() -> None:
    """Membuang cache Pengaturan supaya setenv berikutnya benar benar terbaca."""
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


# ----------------------------------------------------- tiket faktor kedua ---

from backend.core import keamanan as inti  # noqa: E402


@pytest.fixture
def rahasia_jwt(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "u" * 48)
    from backend.core import konfigurasi

    konfigurasi.pengaturan.cache_clear()
    yield
    konfigurasi.pengaturan.cache_clear()


def test_tiket_tidak_bisa_dipakai_sebagai_token_akses(rahasia_jwt):
    """Ini yang membuat tiket lebih aman daripada sesi yang ditandai belum
    lengkap: yang menolaknya pustaka JWT-nya sendiri lewat audiens, bukan satu
    baris if yang bisa terlupa di satu pintu."""
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


# --------------------------------------------------- tidak ada kode di kode ---


def test_tidak_ada_kunci_atau_rahasia_yang_ditulis_di_dalam_kode():
    """Bab 15.11. Rahasia bawaan adalah rahasia yang sudah bocor."""
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
    """Pesan galat masuk log. Log bukan tempat yang aman untuk kode sekali
    pakai, dan `surat.py` sengaja hanya menyebut jenis galatnya."""
    isi = (AKAR / "backend" / "core" / "surat.py").read_text(encoding="utf-8")
    assert "type(galat).__name__" in isi
    assert "str(galat)" not in isi, "pesan galat SMTP bisa memuat isi suratnya"
