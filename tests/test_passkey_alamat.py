from __future__ import annotations

import re

import pytest

from konftes import AKAR

_ADMIN = AKAR / "backend" / "admin"
ADMIN_STATIS = "\n".join(
    (_ADMIN / nama).read_text(encoding="utf-8")
    for nama in ["index.html", *sorted(p.name for p in _ADMIN.glob("dasbor*.js"))]
)
LIB_TS = (AKAR / "next" / "lib" / "passkey.ts").read_text(encoding="utf-8")
MASUK_TSX = (AKAR / "next" / "components" / "admin" / "MasukView.tsx").read_text(encoding="utf-8")
PANEL_TSX = (AKAR / "next" / "components" / "admin" / "PanelPasskey.tsx").read_text(encoding="utf-8")


try:
    import pydantic
    import pydantic_settings

    ADA_BACKEND = True
except ModuleNotFoundError:
    ADA_BACKEND = False

butuh_backend = pytest.mark.skipif(
    not ADA_BACKEND,
    reason="backend belum terpasang. Jalankan: pip install -r backend/requirements.txt",
)


@butuh_backend
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
    from backend.core.konfigurasi import Pengaturan

    dasar = {
        "JWT_SECRET": "x" * 48,
        "WEBAUTHN_RP_ID": "localhost",
        "WEBAUTHN_ASAL": ["http://localhost:8000"],
    }
    dasar.update(ubah)
    return Pengaturan(**dasar)


@butuh_backend
def test_siap_dengan_nama_domain():
    assert _atur().passkey_siap is True


@butuh_backend
@pytest.mark.parametrize("rp", ["127.0.0.1", "192.168.1.4", "::1"])
def test_tidak_siap_kalau_rp_id_alamat_ip(rp):
    assert _atur(WEBAUTHN_RP_ID=rp).passkey_siap is False


@butuh_backend
def test_tetap_tidak_siap_tanpa_rahasia_jwt():
    assert _atur(JWT_SECRET="").passkey_siap is False


def _badan_fungsi(sumber: str, nama: str) -> str:
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
    badan = _badan_fungsi(ADMIN_STATIS, fungsi)
    assert "kendalaPasskey()" in badan, f"{fungsi} tidak memeriksa alamat sama sekali"
    assert badan.index("kendalaPasskey()") < badan.index(panggilan), (
        f"{fungsi} memanggil {panggilan} sebelum alamatnya diperiksa"
    )


@pytest.mark.parametrize("fungsi", ["masukPasskey", "daftarkanKunci"])
def test_securityerror_diterjemahkan(fungsi):
    badan = _badan_fungsi(ADMIN_STATIS, fungsi)
    assert '"SecurityError"' in badan, f"{fungsi} membiarkan SecurityError apa adanya"


def test_tombolnya_tidak_disembunyikan_melainkan_dimatikan():
    assert 'id="kendala-passkey"' in ADMIN_STATIS
    assert '$("tombol-passkey").disabled = true' in ADMIN_STATIS


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
    awal = MASUK_TSX.index("async function denganPasskey()")
    badan = MASUK_TSX[awal : awal + 1600]
    assert badan.index("passkey.kendala()") < badan.index("passkey.masuk()")


def test_keterangan_env_memperingatkan_alamat_ip():
    keterangan = (AKAR / "docs" / "lingkungan.md").read_text(encoding="utf-8")
    assert "127.0.0.1" in keterangan
    assert "nama domain" in keterangan.lower()
    assert re.search(r"localhost:\d+/admin", keterangan), (
        "docs/lingkungan.md tidak menyebut alamat gantinya"
    )
