from __future__ import annotations

import re
import subprocess
import sys

import pytest

from konftes import AKAR, HALAMAN, nama

sys.path.insert(0, str(AKAR / "tools"))

from gaya_next import bangkitkan
from hash_skrip import hash_csp, hash_terpasang, skrip_sebaris
from kontras import AMBANG, matriks, rasio, token

GAYA = (AKAR / "assets" / "css" / "style.css").read_text(encoding="utf-8")
GAYA_TANPA_KOMENTAR = re.sub(r"/\*.*?\*/", "", GAYA, flags=re.DOTALL)
KEPALA = (AKAR / "_headers").read_text(encoding="utf-8")


@pytest.mark.parametrize("tema", ["terang", "gelap"])
def test_setiap_pasangan_teks_lolos_wcag(tema):
    buruk = [(t, l, round(n, 2)) for t, l, n in matriks(tema) if n < AMBANG]
    assert not buruk, f"di bawah {AMBANG}:1 pada tema {tema}: {buruk}"


def test_latar_terang_memang_putih_keabuan():
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


def test_angka_kontras_yang_dicatat_memang_dihitung():
    warna = token("terang")
    disebut = {
        "ink": 19.43, "ink-2": 7.01, "ink-3": 5.31, "accent": 4.96,
    }
    for n, nilai in disebut.items():
        nyata = rasio(warna[n], warna["bg"])
        assert abs(nyata - nilai) < 0.02, (
            f"tercatat --{n} {nilai}:1 terhadap --bg, "
            f"yang sebenarnya {nyata:.2f}:1"
        )


def test_paling_rendah_yang_disebut_memang_paling_rendah():
    for tema, sebut in (("terang", 4.54), ("gelap", 5.19)):
        terendah = min(n for _, _, n in matriks(tema))
        assert abs(terendah - sebut) < 0.02, (
            f"tema {tema}: tercatat {sebut}:1, terendah sebenarnya {terendah:.2f}:1"
        )


def test_semua_token_warna_ada_di_kedua_tema():
    terang, gelap = token("terang"), token("gelap")
    hanya_gelap = set(gelap) - set(terang)
    assert not hanya_gelap, f"token cuma ada di tema gelap: {sorted(hanya_gelap)}"


def test_tema_gelap_tidak_lagi_otomatis():
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


def test_hash_csp_cocok_dengan_skrip_yang_ada():
    assert subprocess.run(
        [sys.executable, str(AKAR / "tools" / "hash_skrip.py")],
        capture_output=True,
    ).returncode == 0, "hash di _headers tidak cocok dengan skrip sebaris di halaman"


def test_csp_tidak_membuka_unsafe_inline_untuk_skrip():
    csp = next(b for b in KEPALA.splitlines() if "Content-Security-Policy" in b)
    skrip = next(b.strip() for b in csp.split(";") if b.strip().startswith("script-src"))
    assert "'unsafe-inline'" not in skrip, skrip
    assert "'unsafe-eval'" not in skrip, skrip
    assert "'sha256-" in skrip, "skrip sebaris tidak diizinkan lewat hash"


@pytest.mark.parametrize("berkas", HALAMAN, ids=nama)
def test_tidak_ada_skrip_sebaris_lain(berkas):
    for isi in skrip_sebaris(berkas):
        assert hash_csp(isi) in hash_terpasang(), (
            f"{nama(berkas)} punya skrip sebaris tanpa hash di _headers:\n  {isi[:80]}"
        )


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
    app = (AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    tata = (AKAR / "next" / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert 'TEMA_KEY = "hk-tema"' in app
    assert '"hk-tema"' in tata


FONT = AKAR / "assets" / "fonts"
TEBAL_PRELOAD = (400, 600, 700)


def _nama_font_di_css() -> list[str]:
    return re.findall(r'url\("/assets/fonts/([^"]+)"\)', GAYA)


@pytest.mark.parametrize("berkas", HALAMAN)
def test_tidak_ada_halaman_yang_memanggil_google(berkas):
    teks = berkas.read_text(encoding="utf-8")
    for asal in ("fonts.googleapis.com", "fonts.gstatic.com"):
        assert asal not in teks, (
            f"{nama(berkas)} masih memanggil {asal}. Fontnya ada di assets/fonts."
        )


def test_csp_menutup_asal_font_luar():
    arahan = "\n".join(
        b for b in KEPALA.splitlines() if not b.lstrip().startswith("#")
    )
    assert "font-src 'self';" in arahan, "font-src harus mengunci font ke asal sendiri"
    assert "fonts.googleapis.com" not in arahan, "CSP masih mengizinkan Google Fonts"
    assert "fonts.gstatic.com" not in arahan


def test_setiap_font_yang_dideklarasikan_ada_berkasnya():
    berkas = _nama_font_di_css()
    assert berkas, "style.css tidak mendeklarasikan satu pun @font-face"
    for n in berkas:
        assert (FONT / n).exists(), f"@font-face menunjuk {n} yang tidak ada"
        assert (FONT / n).read_bytes()[:4] == b"wOF2", f"{n} bukan woff2"


def test_catatan_font_cocok_dengan_berkasnya():
    hasil = subprocess.run(
        [sys.executable, str(AKAR / "tools" / "ambil_font.py"), "--periksa"],
        capture_output=True, text=True, cwd=AKAR,
    )
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr


def test_lisensi_font_ikut_dibawa():
    ofl = (FONT / "OFL.txt").read_text(encoding="utf-8")
    assert "SIL Open Font License" in ofl
    assert "Poppins" in ofl


@pytest.mark.parametrize("berkas", HALAMAN)
def test_preload_font_menunjuk_alamat_yang_dipakai_css(berkas):
    teks = berkas.read_text(encoding="utf-8")
    dimuat = re.findall(r'<link rel="preload" href="(/assets/fonts/[^"]+)"[^>]*>', teks)
    assert len(dimuat) == len(TEBAL_PRELOAD), (
        f"{nama(berkas)} memuat awal {len(dimuat)} font, seharusnya {len(TEBAL_PRELOAD)}"
    )

    di_css = {f"/assets/fonts/{n}" for n in _nama_font_di_css()}
    for alamat in dimuat:
        assert alamat in di_css, (
            f"{nama(berkas)} memuat awal {alamat}, alamat yang tidak dipakai @font-face. "
            "Berkasnya akan diunduh dua kali."
        )

    for tebal in TEBAL_PRELOAD:
        assert any(f"-{tebal}-latin.woff2" in a for a in dimuat), (
            f"{nama(berkas)} tidak memuat awal tebal {tebal}"
        )


@pytest.mark.parametrize("berkas", HALAMAN)
def test_preload_font_memakai_crossorigin(berkas):
    teks = berkas.read_text(encoding="utf-8")
    for tag in re.findall(r'<link rel="preload"[^>]*assets/fonts[^>]*>', teks):
        assert 'as="font"' in tag, tag
        assert 'type="font/woff2"' in tag, tag
        assert "crossorigin" in tag, f"preload font tanpa crossorigin: {tag}"


def test_hanya_subset_latin_yang_disimpan():
    semua = sorted(p.name for p in FONT.glob("*.woff2"))
    assert semua, "tidak ada berkas font"
    for n in semua:
        assert "devanagari" not in n, f"{n} subset yang tidak dipakai situs ini"

    latin = sum(
        p.stat().st_size for p in FONT.glob("*.woff2") if p.stem.endswith("-latin")
    )
    assert latin < 40 * 1024, f"subset latin berjumlah {latin / 1024:.1f} KB"


ADMIN_CSS = (AKAR / "next" / "app" / "admin" / "admin.module.css").read_text(encoding="utf-8")
ADMIN_KODE = re.sub(r"/\*.*?\*/", "", ADMIN_CSS, flags=re.DOTALL)

SKALA = ("--fs-xs", "--fs-sm", "--fs-md", "--fs-lg", "--fs-xl")


@pytest.mark.parametrize("nama", SKALA)
def test_skala_huruf_ada_di_root(nama):
    warna = token("terang")
    assert warna
    akar = GAYA.split("\n:root {", 1)[1].split("\n}", 1)[0]
    assert f"{nama}:" in akar, f"{nama} tidak ada di :root"


def test_dashboard_tidak_mengetik_ukuran_huruf_sendiri():
    harfiah = re.findall(r"font-size:\s*([0-9.]+(?:rem|px|em))", ADMIN_KODE)
    assert not harfiah, f"ukuran huruf yang diketik langsung: {sorted(set(harfiah))}"


def test_dashboard_memakai_skalanya():
    dipakai = {n for n in SKALA if f"var({n})" in ADMIN_KODE}
    assert len(dipakai) >= 4, f"dashboard cuma memakai {dipakai}"


def test_situs_juga_memakai_skala_yang_sama():
    for nama in ("--fs-xs", "--fs-sm", "--fs-md"):
        assert GAYA.count(f"var({nama})") >= 3, f"{nama} hampir tidak dipakai situs"


def test_font_size_tidak_tertimpa_pemendekan_font():
    for blok in re.findall(r"\{[^{}]*font:\s*inherit[^{}]*\}", ADMIN_KODE):
        if "font-size" not in blok:
            continue
        assert blok.index("font: inherit") < blok.index("font-size"), (
            f"font-size ditulis sebelum `font: inherit`, jadi ia diabaikan:\n{blok}"
        )
