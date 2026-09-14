"""Alamat halaman menentukan apakah passkey bisa dipakai sama sekali.

Pada 14 September 2026 sidik jari tidak bisa dipakai untuk masuk, dan sebabnya
bukan di server. Halaman admin dibuka lewat `http://127.0.0.1:<porta>/admin`,
dan WebAuthn menuntut rp_id berupa **nama domain**. Alamat IP bukan nama
domain. Peramban menolaknya sebelum satu pun permintaan dikirim.

Sudah dibuktikan di Chromium, bukan disimpulkan dari dokumentasi:

    dari http://127.0.0.1:8099
      rpId "localhost" -> SecurityError, "This is an invalid domain."
      rpId "127.0.0.1" -> SecurityError, "This is an invalid domain."
    dari http://localhost:8099
      rpId "localhost" -> diterima, peramban membuka dialog sidik jari

Perhatikan baris kedua. Bahkan rp_id yang sama persis dengan hostnya pun
ditolak, jadi tidak ada nilai konfigurasi mana pun yang menyelamatkan
127.0.0.1. Yang bisa dikerjakan cuma dua: berhenti mengaku siap, dan
mengatakan ke mana orang harus pergi.

Dua hal yang dijaga di sini:

1. **Server berhenti mengaku siap** kalau rp_id-nya alamat IP. Menjawab
   siap=true berarti menyuruh halaman admin memasang tombol yang mustahil
   berhasil.
2. **Layarnya menyebut sebabnya, dan menyebut alamat penggantinya.** Kegagalan
   aslinya berbunyi "This is an invalid domain", kalimat berbahasa Inggris yang
   benar tetapi tidak memberi tahu siapa pun apa yang harus dilakukan.

Tidak ada uji di berkas ini yang memerlukan basis data.
"""

from __future__ import annotations

import re

import pytest

from konftes import AKAR

ADMIN_STATIS = (AKAR / "backend" / "admin" / "index.html").read_text(encoding="utf-8")
LIB_TS = (AKAR / "next" / "lib" / "passkey.ts").read_text(encoding="utf-8")
MASUK_TSX = (AKAR / "next" / "components" / "admin" / "MasukView.tsx").read_text(encoding="utf-8")
PANEL_TSX = (AKAR / "next" / "components" / "admin" / "PanelPasskey.tsx").read_text(encoding="utf-8")
CONTOH_ENV = (AKAR / ".env.example").read_text(encoding="utf-8")


# ----------------------------------------------------------------- server ---

@pytest.mark.parametrize(
    "host, ip",
    [
        ("localhost", False),
        ("hendrokuswantoro.com", False),
        ("www.hendrokuswantoro.com", False),
        ("testserver", False),
        ("", False),
        ("127.0.0.1", True),
        ("192.168.1.4", True),
        ("::1", True),
        ("[::1]", True),
    ],
)
def test_mengenali_alamat_ip(host, ip):
    from backend.core.konfigurasi import _alamat_ip

    assert _alamat_ip(host) is ip


def _atur(**ubah):
    """Pengaturan dengan nilai yang disebut tersurat.

    Aliasnya dipakai sebagai nama argumen, sama seperti yang dibaca dari
    environment, supaya ujinya tidak bergantung pada .env mesin siapa pun.
    """
    from backend.core.konfigurasi import Pengaturan

    # Diberikan sebagai daftar sungguhan, bukan teks JSON. Penguraian JSON
    # hanya terjadi pada nilai yang datang dari environment.
    dasar = {
        "JWT_SECRET": "x" * 48,
        "WEBAUTHN_RP_ID": "localhost",
        "WEBAUTHN_ASAL": ["http://localhost:8000"],
    }
    dasar.update(ubah)
    return Pengaturan(**dasar)


def test_siap_dengan_nama_domain():
    assert _atur().passkey_siap is True


@pytest.mark.parametrize("rp", ["127.0.0.1", "192.168.1.4", "::1"])
def test_tidak_siap_kalau_rp_id_alamat_ip(rp):
    """Ini bukan sikap rewel. Konfigurasi semacam ini tidak pernah bisa
    bekerja di peramban mana pun, jadi mengaku siap hanya memindahkan
    kegagalannya ke tempat yang lebih membingungkan."""
    assert _atur(WEBAUTHN_RP_ID=rp).passkey_siap is False


def test_tetap_tidak_siap_tanpa_rahasia_jwt():
    """Yang lama tidak boleh ikut longgar gara gara yang baru ditambahkan."""
    assert _atur(JWT_SECRET="").passkey_siap is False


# ------------------------------------------------------------ admin statis ---

def _badan_fungsi(sumber: str, nama: str) -> str:
    """Isi satu fungsi JavaScript, dari tanda kurung kurawal pembuka sampai
    penutupnya. Dihitung dengan menyeimbangkan kurawal, bukan dengan regex,
    sebab regex akan berhenti di kurawal pertama yang ia temukan."""
    awal = sumber.index(f"function {nama}(")
    buka = sumber.index("{", awal)
    dalam = 0
    for i in range(buka, len(sumber)):
        if sumber[i] == "{":
            dalam += 1
        elif sumber[i] == "}":
            dalam -= 1
            if dalam == 0:
                return sumber[buka : i + 1]
    raise AssertionError(f"fungsi {nama} tidak tertutup")


def test_admin_statis_punya_pemeriksa_alamat():
    assert "function kendalaPasskey(" in ADMIN_STATIS
    assert "function pesanKendala(" in ADMIN_STATIS


@pytest.mark.parametrize(
    "fungsi, panggilan",
    [
        ("masukPasskey", "navigator.credentials.get"),
        ("daftarkanKunci", "navigator.credentials.create"),
    ],
)
def test_alamat_diperiksa_sebelum_webauthn_dipanggil(fungsi, panggilan):
    """Urutannya yang penting, bukan sekadar keberadaannya.

    Memeriksa sesudah `credentials.get` berarti dialog peramban sudah telanjur
    gagal, dan pesan yang benar datang terlambat.
    """
    badan = _badan_fungsi(ADMIN_STATIS, fungsi)
    assert "kendalaPasskey()" in badan, f"{fungsi} tidak memeriksa alamat sama sekali"
    assert badan.index("kendalaPasskey()") < badan.index(panggilan), (
        f"{fungsi} memanggil {panggilan} sebelum alamatnya diperiksa"
    )


@pytest.mark.parametrize("fungsi", ["masukPasskey", "daftarkanKunci"])
def test_securityerror_diterjemahkan(fungsi):
    """SecurityError datang dari peramban dan bunyinya "This is an invalid
    domain". Kalimat itu benar dan tidak berguna."""
    badan = _badan_fungsi(ADMIN_STATIS, fungsi)
    assert '"SecurityError"' in badan, f"{fungsi} membiarkan SecurityError apa adanya"


def test_tombolnya_tidak_disembunyikan_melainkan_dimatikan():
    """Menyembunyikan tombolnya menyembunyikan sebabnya juga, lalu orang
    mengira passkey belum dipasang di server padahal ia sudah siap."""
    assert 'id="kendala-passkey"' in ADMIN_STATIS
    assert '$("tombol-passkey").disabled = true' in ADMIN_STATIS


# --------------------------------------------------------------- port Next ---

def test_pustaka_next_punya_pemeriksa_yang_sama():
    assert "export function kendala()" in LIB_TS
    assert "isSecureContext" in LIB_TS


@pytest.mark.parametrize(
    "berkas, isi",
    [("MasukView.tsx", MASUK_TSX), ("PanelPasskey.tsx", PANEL_TSX)],
)
def test_kedua_layar_memakai_pemeriksanya(berkas, isi):
    assert "passkey.kendala()" in isi, f"{berkas} tidak memeriksa alamat"


def test_masuk_memeriksa_sebelum_memanggil_servernya():
    """`passkey.masuk()` menembak ke server lebih dulu, lalu baru memanggil
    WebAuthn. Memeriksa alamat sesudah itu berarti satu permintaan sia sia dan
    satu tantangan terbuang."""
    awal = MASUK_TSX.index("async function denganPasskey()")
    badan = MASUK_TSX[awal : awal + 1600]
    assert badan.index("passkey.kendala()") < badan.index("passkey.masuk()")


# --------------------------------------------------------------- dokumen ---

def test_contoh_env_memperingatkan_alamat_ip():
    """Yang membaca .env.example sedang memutuskan apa yang akan ia tulis.
    Di situlah peringatannya berguna, bukan sesudah tombolnya gagal."""
    rendah = CONTOH_ENV.lower()
    assert "127.0.0.1" in CONTOH_ENV
    assert "nama domain" in rendah
    assert re.search(r"localhost:\d+/admin", CONTOH_ENV), (
        ".env.example tidak menyebut alamat gantinya"
    )
