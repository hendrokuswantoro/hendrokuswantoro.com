"""Palet, kontras, tema, dan satu satunya skrip sebaris di situs ini.

Warna adalah tempat paling mudah membuat klaim yang tidak diuji. Komentar di
kepala `style.css` menyebut angka rasio kontras; tanpa berkas ini, angka itu
hanya kalimat yang kebetulan ada di sana, dan akan tetap ada di sana lama
sesudah warnanya bergeser.

Yang dijaga:

1. Tiap pasangan teks dan latar lolos 4,5:1, dihitung ulang dari CSS-nya,
   bukan dari angka yang diketik di komentar.
2. Angka yang ditulis di komentar memang angka yang dihitung.
3. Tema gelap tidak kembali menempel pada prefers-color-scheme.
4. Tiap halaman punya skrip anti-kedip, dan hash CSP-nya cocok.
5. Salinan CSS di port Next.js tidak tertinggal.
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

from konftes import AKAR, HALAMAN, nama

sys.path.insert(0, str(AKAR / "tools"))

from gaya_next import bangkitkan  # noqa: E402
from hash_skrip import hash_csp, hash_terpasang, skrip_sebaris  # noqa: E402
from kontras import AMBANG, matriks, rasio, token  # noqa: E402

GAYA = (AKAR / "assets" / "css" / "style.css").read_text(encoding="utf-8")
# Komentar dibuang sebelum diperiksa: komentar boleh menyebut aturan lama
# untuk menjelaskan kenapa ia diganti, dan uji yang melarang itu akan
# menghukum penjelasan yang justru berguna.
GAYA_TANPA_KOMENTAR = re.sub(r"/\*.*?\*/", "", GAYA, flags=re.DOTALL)
KEPALA = (AKAR / "_headers").read_text(encoding="utf-8")


# ------------------------------------------------------------------ warna ---


@pytest.mark.parametrize("tema", ["terang", "gelap"])
def test_setiap_pasangan_teks_lolos_wcag(tema):
    buruk = [(t, l, round(n, 2)) for t, l, n in matriks(tema) if n < AMBANG]
    assert not buruk, f"di bawah {AMBANG}:1 pada tema {tema}: {buruk}"


def test_latar_terang_memang_putih_keabuan():
    """Permintaannya jelas: putih agak ke abu abu, seperti aplikasi Uber.
    Bukan putih polos, bukan abu abu tua, dan bukan abu abu yang punya rona."""
    warna = token("terang")
    heks = warna["bg"].lstrip("#")
    r, g, b = (int(heks[i:i + 2], 16) for i in (0, 2, 4))

    assert r == g == b, f"--bg {warna['bg']} punya rona; abu abu Uber netral"
    assert 0xF0 <= r <= 0xFA, f"--bg {warna['bg']} bukan putih keabuan"
    assert warna["card"] == "#ffffff", "kartu tetap putih supaya terangkat dari latar"
    assert warna["bg"] != warna["card"], "latar dan kartu tidak boleh sama"


def test_seluruh_abu_abu_terang_netral():
    warna = token("terang")
    for n in ("bg", "surface", "surface-2", "line", "line-strong"):
        heks = warna[n].lstrip("#")
        r, g, b = (int(heks[i:i + 2], 16) for i in (0, 2, 4))
        assert r == g == b, f"--{n} {warna[n]} punya rona; palet Uber netral"


def test_angka_di_komentar_memang_dihitung():
    """Komentar yang berbohong lebih berbahaya daripada tidak ada komentar."""
    warna = token("terang")
    disebut = {
        "ink": 19.43, "ink-2": 7.01, "ink-3": 5.31, "accent": 4.96,
    }
    for n, nilai in disebut.items():
        nyata = rasio(warna[n], warna["bg"])
        assert abs(nyata - nilai) < 0.02, (
            f"komentar menyebut --{n} {nilai}:1 terhadap --bg, "
            f"yang sebenarnya {nyata:.2f}:1"
        )

    terendah = min(n for _, _, n in matriks("terang"))
    assert "4.54:1" in GAYA, f"pasangan terendah sekarang {terendah:.2f}:1"


def test_paling_rendah_yang_disebut_memang_paling_rendah():
    for tema, sebut in (("terang", 4.54), ("gelap", 5.19)):
        terendah = min(n for _, _, n in matriks(tema))
        assert abs(terendah - sebut) < 0.02, (
            f"tema {tema}: komentar menyebut {sebut}:1, terendah sebenarnya {terendah:.2f}:1"
        )


def test_semua_token_warna_ada_di_kedua_tema():
    """Token yang cuma ada di satu tema akan mewarisi nilai tema satunya,
    dan itu hampir selalu tabrakan yang tidak terlihat di layar penulisnya."""
    terang, gelap = token("terang"), token("gelap")
    hanya_gelap = set(gelap) - set(terang)
    assert not hanya_gelap, f"token cuma ada di tema gelap: {sorted(hanya_gelap)}"


# ------------------------------------------------------------------- tema ---


def test_tema_gelap_tidak_lagi_otomatis():
    """Kalau ini kembali jadi @media, pembaca yang sistemnya gelap tidak akan
    pernah melihat latar putih keabuan yang diminta, dan tidak punya cara
    memintanya."""
    assert ':root[data-theme="dark"] {' in GAYA_TANPA_KOMENTAR
    assert "prefers-color-scheme" not in GAYA_TANPA_KOMENTAR, (
        "palet gelap kembali menempel pada setelan sistem"
    )


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_setiap_halaman_punya_saklar_tema(berkas):
    teks = berkas.read_text(encoding="utf-8")
    assert 'class="tema"' in teks, f"{nama(berkas)} tidak punya saklar tema"
    assert 'aria-pressed="false"' in teks
    assert 'data-ind-label="Tema gelap"' in teks, "saklar tema tidak dwibahasa"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_skrip_tema_jalan_sebelum_lembar_gaya(berkas):
    """Urutannya penting. Skrip yang datang sesudah CSS tetap mencegah kedip,
    tetapi skrip yang datang sesudah <body> tidak."""
    teks = berkas.read_text(encoding="utf-8")
    assert "hk-tema" in teks, f"{nama(berkas)} tidak punya skrip anti-kedip"
    assert teks.index("hk-tema") < teks.index("<body"), (
        f"{nama(berkas)} memasang tema sesudah <body>, jadi halamannya akan berkedip"
    )


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_theme_color_ikut_latar(berkas):
    teks = berkas.read_text(encoding="utf-8")
    cocok = re.search(r'<meta name="theme-color" content="([^"]+)">', teks)
    assert cocok, f"{nama(berkas)} tidak menyebut theme-color"
    assert cocok.group(1) == token("terang")["bg"], (
        "bilah peramban tidak sewarna latar halaman"
    )


# -------------------------------------------------------------------- CSP ---


def test_hash_csp_cocok_dengan_skrip_yang_ada():
    assert subprocess.run(
        [sys.executable, str(AKAR / "tools" / "hash_skrip.py")],
        capture_output=True,
    ).returncode == 0, "hash di _headers tidak cocok dengan skrip sebaris di halaman"


def test_csp_tidak_membuka_unsafe_inline_untuk_skrip():
    """Hash mengizinkan satu skrip yang sudah dikenal. 'unsafe-inline'
    mengizinkan semuanya, termasuk yang disuntikkan lewat XSS."""
    csp = next(b for b in KEPALA.splitlines() if "Content-Security-Policy" in b)
    skrip = next(b.strip() for b in csp.split(";") if b.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in skrip, skrip
    assert "'unsafe-eval'" not in skrip, skrip
    assert "'sha256-" in skrip, "skrip sebaris tidak diizinkan lewat hash"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_tidak_ada_skrip_sebaris_lain(berkas):
    """Tiap skrip sebaris baru butuh hash baru, dan yang lupa dihitung akan
    diam diam ditolak peramban tanpa satu pun pesan di halaman."""
    for isi in skrip_sebaris(berkas):
        assert hash_csp(isi) in hash_terpasang(), (
            f"{nama(berkas)} punya skrip sebaris tanpa hash di _headers:\n  {isi[:80]}"
        )


# ------------------------------------------------------------ port Next.js ---


def test_gaya_port_next_tidak_tertinggal():
    tujuan = AKAR / "next" / "app" / "globals.css"
    assert tujuan.read_text(encoding="utf-8") == bangkitkan(), (
        "next/app/globals.css tertinggal. Jalankan: python tools/gaya_next.py"
    )


def test_port_next_punya_saklar_tema_juga():
    header = (AKAR / "next" / "components" / "Header.tsx").read_text(encoding="utf-8")
    assert "<ThemeSwitch />" in header, "port Next.js punya palet gelap tanpa jalan ke sana"

    tata = (AKAR / "next" / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert "hk-tema" in tata, "port Next.js akan berkedip saat memuat tema gelap"


def test_kunci_penyimpanan_sama_di_kedua_versi():
    """Kalau kuncinya berbeda, pindah dari satu versi ke satunya akan
    melupakan pilihan pembacanya tanpa alasan yang bisa dijelaskan."""
    app = (AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    tata = (AKAR / "next" / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert 'TEMA_KEY = "hk-tema"' in app
    assert '"hk-tema"' in tata
