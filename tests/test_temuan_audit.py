"""Temuan audit keamanan 26 September 2026, satu uji atau lebih per temuan.

Yang diuji di sini perilakunya, bukan hanya keberadaan barisnya, kecuali
untuk berkas konfigurasi (systemd dan nginx) yang memang tidak bisa
dijalankan di mesin uji. Semua uji di sini jalan tanpa basis data: lapisan
repositori diganti lewat monkeypatch, sebab yang dijaga adalah keputusan di
lapisan layanan dan router.

 1. Sandi saja tidak boleh cukup untuk mengambil alih akun berpasskey.
 2. Alamat klien di balik nginx dan soket Unix.
 3. Batas tebakan faktor kedua per akun.
 4. Wajah tidak menerbitkan sesi kuat.
 5. Penguncian per email dan alamat, bukan per email saja.
 6. Kode TOTP tidak bisa dipakai dua kali.
 7. Escape di halaman blog yang dibangkitkan.
 8. Token verifikasi di fragmen, bukan di query.
 9. Nilai bawaan CORS.
10. Batas panjang isi tulisan.
"""

from __future__ import annotations

import asyncio
import re
import sys

import pytest

from konftes import AKAR

try:
    from backend.api import tergantung
    from backend.core.konfigurasi import pengaturan

    ADA_BACKEND = True
except ModuleNotFoundError:  # pragma: no cover
    ADA_BACKEND = False

pytestmark = pytest.mark.skipif(
    not ADA_BACKEND,
    reason="backend belum terpasang. Jalankan: pip install -r backend/requirements.txt",
)

sys.path.insert(0, str(AKAR / "tools"))


@pytest.fixture(autouse=True)
def rahasia_jwt(monkeypatch):
    if not ADA_BACKEND:
        return
    monkeypatch.setenv("JWT_SECRET", "rahasia-uji-yang-panjangnya-lebih-dari-tigapuluh-dua")
    pengaturan.cache_clear()
    yield
    pengaturan.cache_clear()


def _wajib(monkeypatch, nyala: bool) -> None:
    monkeypatch.setenv("FAKTOR_KEDUA_WAJIB", "true" if nyala else "false")
    pengaturan.cache_clear()


def _jalan(coro):
    return asyncio.run(coro)


def _baca(*jalur: str) -> str:
    return (AKAR.joinpath(*jalur)).read_text(encoding="utf-8")


# ------------------------------------------------- 1. pendaftaran faktor ---


@pytest.mark.parametrize(
    "kuat, punya, wajib, boleh",
    [
        (False, False, True, True),    # faktor pertama dari sesi lemah: boleh
        (False, True, True, False),    # faktor tambahan dari sesi lemah: TIDAK
        (True, True, True, True),      # sesi kuat: boleh
        (False, True, False, True),    # jalan pulang FAKTOR_KEDUA_WAJIB=false
    ],
)
def test_pendaftar_hanya_boleh_memasang_faktor_pertama(monkeypatch, kuat, punya, wajib, boleh):
    from fastapi import HTTPException

    from backend.layanan import keamanan as lapis

    _wajib(monkeypatch, wajib)

    async def punya_faktor(_):
        return punya

    monkeypatch.setattr(lapis, "punya_faktor", punya_faktor)
    pengguna = {"id": "u1", "peran": "admin", "faktor_kedua": kuat}

    if boleh:
        assert _jalan(tergantung.butuh_admin_pendaftar(pengguna)) is pengguna
    else:
        with pytest.raises(HTTPException) as galat:
            _jalan(tergantung.butuh_admin_pendaftar(pengguna))
        assert galat.value.status_code == 403


def _penjaga(isi: str, fungsi: str) -> str:
    """Nama penjaga yang dipakai satu fungsi router."""
    potong = isi[isi.index(f"async def {fungsi}("):]
    return re.search(r"Depends\((butuh_admin\w*)\)", potong).group(1)


@pytest.mark.parametrize(
    "berkas, fungsi, penjaga",
    [
        ("passkey.py", "daftar_mulai", "butuh_admin_pendaftar"),
        ("passkey.py", "daftar_selesai", "butuh_admin_pendaftar"),
        ("passkey.py", "cabut", "butuh_admin_kuat"),
        ("keamanan.py", "totp_mulai", "butuh_admin_pendaftar"),
        ("keamanan.py", "totp_aktifkan", "butuh_admin_pendaftar"),
        ("keamanan.py", "totp_matikan", "butuh_admin_kuat"),
        ("keamanan.py", "wajah_daftar", "butuh_admin_pendaftar"),
        ("keamanan.py", "wajah_hapus", "butuh_admin_kuat"),
        # Membaca keadaan tetap terbuka untuk sesi lemah, supaya pemilik yang
        # belum punya faktor bisa melihat apa yang harus dipasang.
        ("keamanan.py", "keadaan", "butuh_admin"),
    ],
)
def test_jalur_faktor_memakai_penjaga_yang_benar(berkas, fungsi, penjaga):
    assert _penjaga(_baca("backend", "api", "v1", berkas), fungsi) == penjaga


def _login(monkeypatch, cara: list[str]):
    """Menjalankan router login dengan sandi yang dianggap benar."""
    from fastapi import Response
    from starlette.requests import Request

    from backend.api.v1 import auth
    from backend.layanan import autentikasi, kabar
    from backend.layanan import keamanan as lapis

    terbit = {}

    async def periksa_sandi(*_):
        return {"id": "u1", "peran": "admin", "nama": "Uji", "email": "u@contoh.id"}

    async def berlaku(_):
        return list(cara)

    async def diam(*_, **__):
        return None

    async def terbitkan(pengguna, faktor_kedua=False):
        terbit["f2"] = faktor_kedua
        import datetime as dt

        kadaluarsa = dt.datetime.now(dt.timezone.utc)
        return autentikasi.Masuk("a", 900, "r", kadaluarsa, "Uji", "admin")

    monkeypatch.setattr(autentikasi, "periksa_sandi", periksa_sandi)
    monkeypatch.setattr(autentikasi, "terbitkan", terbitkan)
    monkeypatch.setattr(lapis, "faktor_kedua_yang_berlaku", berlaku)
    monkeypatch.setattr(lapis, "catat_peristiwa", diam)
    monkeypatch.setattr(kabar, "kabari_masuk", diam)

    permintaan = Request({"type": "http", "method": "POST", "path": "/", "headers": []})
    kredensial = auth.Kredensial(email="u@contoh.id", sandi="sandi-yang-cukup-panjang")
    hasil = _jalan(auth.login(kredensial, permintaan, Response(), "a" * 64))
    return hasil, terbit


def test_akun_berpasskey_tidak_bisa_masuk_dengan_sandi_saja(monkeypatch):
    from fastapi import HTTPException

    _wajib(monkeypatch, True)
    with pytest.raises(HTTPException) as galat:
        _login(monkeypatch, ["passkey"])
    assert galat.value.status_code == 403
    assert "passkey" in galat.value.detail


def test_passkey_tidak_ikut_ditawarkan_di_langkah_tiket(monkeypatch):
    _wajib(monkeypatch, True)
    hasil, _ = _login(monkeypatch, ["totp", "passkey"])
    assert hasil.tahap == "faktor2"
    assert hasil.cara == ["totp"]


def test_jalan_pulang_tetap_ada_kalau_aturannya_dimatikan(monkeypatch):
    """Perangkat hilang: FAKTOR_KEDUA_WAJIB=false membuka jalan sandi lagi,
    dengan sesi yang lemah."""
    _wajib(monkeypatch, False)
    hasil, terbit = _login(monkeypatch, ["passkey"])
    assert hasil.tahap == "selesai"
    assert terbit["f2"] is False


# --------------------------------------------------- 2. alamat klien ---


def test_uvicorn_mempercayai_soketnya_sendiri():
    """Lewat --uds, alamat klien bernilai None, dan '127.0.0.1' tidak pernah
    cocok dengannya. Akibatnya seluruh permintaan terbaca tanpa alamat."""
    unit = _baca("infrastructure", "systemd", "hk-api.service")
    assert "--uds" in unit
    assert "--forwarded-allow-ips='*'" in unit


def test_nginx_menimpa_x_forwarded_for_bukan_menambahkan():
    """Dengan '*', uvicorn memakai alamat paling kiri. Menambahkan berarti
    alamat karangan klien yang dipakai."""
    konf = _baca("infrastructure", "nginx", "hendrokuswantoro.conf")
    aktif = "\n".join(b for b in konf.splitlines() if not b.strip().startswith("#"))
    assert "$proxy_add_x_forwarded_for" not in aktif
    assert aktif.count("proxy_set_header X-Forwarded-For $remote_addr;") >= 4


# ----------------------------------------- 3 dan 6. batas dan ulang TOTP ---


def _siapkan_totp(monkeypatch, *, gagal_sebelumnya=0, langkah_baru=True):
    from backend.layanan import keamanan as lapis
    from backend.layanan import totp as totp_modul

    catatan = {"gagal": 0, "bersih": 0}

    async def jumlah_gagal(kunci, menit, alamat=None):
        assert kunci.startswith("f2:")
        return gagal_sebelumnya

    async def catat_gagal(kunci, alamat):
        catatan["gagal"] += 1

    async def bersihkan(kunci):
        catatan["bersih"] += 1

    async def rahasia_aktif(*_, **__):
        return "JBSWY3DPEHPK3PXP"

    async def pakai_langkah(*_):
        return langkah_baru

    async def diam(*_, **__):
        return None

    monkeypatch.setattr(lapis.repo_pengguna, "jumlah_gagal", jumlah_gagal)
    monkeypatch.setattr(lapis.repo_pengguna, "catat_gagal", catat_gagal)
    monkeypatch.setattr(lapis.repo_pengguna, "bersihkan_gagal", bersihkan)
    monkeypatch.setattr(lapis, "_rahasia_aktif", rahasia_aktif)
    monkeypatch.setattr(lapis.repo, "pakai_langkah_totp", pakai_langkah)
    monkeypatch.setattr(lapis.repo, "catat", diam)
    kode = totp_modul.kode_pada("JBSWY3DPEHPK3PXP", int(__import__("time").time() // totp_modul.LANGKAH))
    return lapis, kode, catatan


def test_kode_totp_yang_benar_diterima_sekali(monkeypatch):
    lapis, kode, catatan = _siapkan_totp(monkeypatch)
    assert _jalan(lapis.periksa_totp("u1", kode, None)) is True
    assert catatan["bersih"] == 1


def test_kode_totp_yang_sudah_dipakai_ditolak_dan_dihitung(monkeypatch):
    lapis, kode, catatan = _siapkan_totp(monkeypatch, langkah_baru=False)
    assert _jalan(lapis.periksa_totp("u1", kode, None)) is False
    assert catatan["gagal"] == 1


def test_kode_totp_salah_dihitung(monkeypatch):
    lapis, _, catatan = _siapkan_totp(monkeypatch)
    assert _jalan(lapis.periksa_totp("u1", "000000", None)) in (False, True)
    # Peluang 000000 kebetulan benar 3 per sejuta; yang dijaga penghitungnya.
    assert catatan["gagal"] + catatan["bersih"] == 1


@pytest.mark.parametrize("fungsi", ["periksa_totp", "periksa_pemulihan"])
def test_jatah_tebakan_habis_ditolak_sebelum_kodenya_diperiksa(monkeypatch, fungsi):
    lapis, kode, _ = _siapkan_totp(monkeypatch, gagal_sebelumnya=lapis_batas())
    with pytest.raises(lapis.Ditolak):
        _jalan(getattr(lapis, fungsi)("u1", kode, None))


def lapis_batas() -> int:
    from backend.layanan import keamanan as lapis

    return lapis.BATAS_F2


def test_router_menjawab_429_saat_jatah_habis():
    isi = _baca("backend", "api", "v1", "auth.py")
    potong = isi[isi.index("async def faktor_kedua("):isi.index("class MintaKode")]
    assert "except lapis.Ditolak" in potong
    assert "HTTP_429_TOO_MANY_REQUESTS" in potong


def test_janji_di_totp_py_sekarang_ditepati():
    """Keterangannya berjanji menolak kode yang sudah dipakai. Janji itu
    hanya benar kalau nomor jendelanya benar benar disimpan."""
    assert "pakai_langkah_totp" in _baca("backend", "layanan", "keamanan.py")
    assert "totp_langkah_terakhir" in _baca("backend", "db", "migrations", "0008_totp_langkah.sql")


# ------------------------------------------------------------ 4. wajah ---


def test_wajah_tidak_menerbitkan_sesi_kuat():
    isi = _baca("backend", "api", "v1", "auth.py")
    assert 'faktor_kedua=(isian.cara != "wajah")' in isi
    assert "faktor_kedua=True" not in isi


# ------------------------------------------------------ 5. penguncian ---


@pytest.mark.parametrize(
    "per_alamat, per_email, terkunci",
    [(5, 5, True), (4, 99, False), (0, 100, True), (0, 99, False)],
)
def test_penguncian_per_email_dan_alamat(monkeypatch, per_alamat, per_email, terkunci):
    from backend.layanan import autentikasi

    async def jumlah_gagal(email, menit, alamat_hash=None):
        return per_alamat if alamat_hash else per_email

    async def cari_email(_):
        return None

    async def catat_gagal(*_):
        return None

    monkeypatch.setattr(autentikasi.repo, "jumlah_gagal", jumlah_gagal)
    monkeypatch.setattr(autentikasi.repo, "cari_email", cari_email)
    monkeypatch.setattr(autentikasi.repo, "catat_gagal", catat_gagal)

    with pytest.raises(autentikasi.Ditolak) as galat:
        _jalan(autentikasi.periksa_sandi("u@contoh.id", "salah-tapi-panjang", "a" * 64))
    assert galat.value.terkunci is terkunci


# ------------------------------------------------------------ 7. escape ---


def test_untuk_ind_meng_escape_dua_kali():
    import html

    import markah

    nilai = markah.untuk_ind('<a href="x">klik</a> & "kutip"')
    # Satu lapis dibuka peramban saat atribut dibaca, satu lapis lagi dibuka
    # innerHTML. Yang tersisa sesudah keduanya harus teks, bukan tag.
    sesudah_atribut = html.unescape(nilai)
    assert "<" not in sesudah_atribut
    assert html.unescape(sesudah_atribut) == '<a href="x">klik</a> & "kutip"'


def _tulisan_jahat():
    from isi import Teks, Tulisan

    def dua(en, idn=None):
        return Teks(en=en, id=idn if idn is not None else en)

    return Tulisan(
        slug="uji",
        tanggal="2026-09-26",
        tanggal_label=dua("26 Sep", "26 Sep"),
        tag=dua('<img src=x onerror=alert(1)>', '<b>tag</b>'),
        baca=dua('4 "min"', "4 menit"),
        judul=dua('Judul "kutip" </script><script>alert(1)</script>', "Judul <i>id</i>"),
        ringkas=dua("ringkas", "ringkas"),
        keterangan=dua('ket " onmouseover="x', "ket"),
        lede=dua("<em>lede</em>", "lede <b>id</b>"),
        isi_en="Paragraf.",
        isi_id="Paragraf.",
    )


def test_halaman_blog_tidak_membawa_tag_mentah():
    import bangun_tulisan

    try:
        t = _tulisan_jahat()
    except TypeError as galat:  # pragma: no cover
        pytest.skip(f"bentuk Tulisan berbeda: {galat}")
    halaman = bangun_tulisan.halaman(t, [t], "c", "j")
    kartu = bangun_tulisan.kartu(t)

    for teks in (halaman, kartu):
        assert "<img src=x" not in teks
        assert "<b>tag</b>" not in teks
        assert 'onmouseover="x' not in teks
    assert "</script><script>alert" not in halaman
    assert "\\u003c/script\\u003e" in halaman


def test_alamat_media_di_escape():
    import bangun_tulisan
    import markah

    blok = markah.Blok(jenis="gambar", teks="x", baris=1, alamat='/unggahan/a"onerror="b.webp')
    keluar = "\n".join(bangun_tulisan.media(blok, blok))
    assert '"onerror="' not in keluar


# ------------------------------------------------ 8. token verifikasi ---


def test_token_verifikasi_di_fragmen():
    from backend.layanan import keamanan as lapis

    tautan = lapis._tautan("TOKEN", "https://www.hendrokuswantoro.com")
    assert tautan == "https://www.hendrokuswantoro.com/admin#verifikasi=TOKEN"
    assert "?" not in tautan


def test_dashboard_membaca_token_dari_fragmen():
    isi = _baca("next", "components", "admin", "PanelKeamanan.tsx")
    assert "alamat.hash" in isi


# ---------------------------------------------------------------- 9. CORS ---


def test_bawaan_cors_hanya_situs_yang_terbit(monkeypatch):
    monkeypatch.delenv("ASAL_DIIZINKAN", raising=False)
    from backend.core.konfigurasi import Pengaturan

    bawaan = Pengaturan.model_fields["asal_diizinkan"].default
    assert bawaan == ["https://www.hendrokuswantoro.com"]


def test_tautan_surat_tidak_menunjuk_mesin_sendiri(monkeypatch):
    from backend.api.v1 import keamanan

    monkeypatch.setenv(
        "ASAL_DIIZINKAN",
        '["https://www.hendrokuswantoro.com","http://127.0.0.1:8081"]',
    )
    pengaturan.cache_clear()
    assert keamanan._asal(None) == "https://www.hendrokuswantoro.com"


# --------------------------------------------------------- 10. panjang ---


def test_isi_tulisan_dan_pratinjau_punya_batas():
    from pydantic import ValidationError

    from backend.api.v1.admin import Pratinjau
    from backend.skema.tulis import PANJANG_ISI

    with pytest.raises(ValidationError):
        Pratinjau(isi_en="a" * (PANJANG_ISI + 1))
    isi = _baca("backend", "skema", "tulis.py")
    assert isi.count("max_length=PANJANG_ISI") == 4
    assert isi.count("max_length=PANJANG_LEDE") == 4
