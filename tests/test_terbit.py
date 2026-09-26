from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET

import pytest

from konftes import AKAR, HALAMAN, berkas_dari_jalur, nama

SITUS = "https://www.hendrokuswantoro.com"
HEADERS = (AKAR / "_headers").read_text(encoding="utf-8")
WRANGLER = (AKAR / "wrangler.toml").read_text(encoding="utf-8")


def versi(berkas: pathlib.Path, aset: str) -> str | None:
    cocok = re.search(re.escape(aset) + r"\?v=([0-9a-z]+)", berkas.read_text(encoding="utf-8"))
    return cocok.group(1) if cocok else None


@pytest.mark.parametrize("aset", ["/assets/css/style.css", "/assets/js/app.js"])
def test_versi_seragam(aset):
    dipakai = {nama(b): versi(b, aset) for b in HALAMAN}
    hilang = [k for k, v in dipakai.items() if v is None]
    assert not hilang, f"{aset} has no version string on {hilang}"
    assert len(set(dipakai.values())) == 1, f"{aset} versions drifted apart: {dipakai}"


def test_peta_ikut_diberi_versi():
    app = (AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"peta\.js\?v=[0-9a-z]+", app), "peta.js is loaded without a version"


def test_nomor_aset_tidak_tertinggal_dari_isinya():
    import subprocess
    import sys

    hasil = subprocess.run(
        [sys.executable, str(AKAR / "tools" / "versi_aset.py"), "--periksa"],
        capture_output=True, text=True, cwd=AKAR,
    )
    assert hasil.returncode == 0, hasil.stdout + hasil.stderr


def test_nomor_aset_memang_sidik_isinya():
    import hashlib

    beranda = (AKAR / "index.html").read_text(encoding="utf-8")
    for aset, jalur in (
        ("/assets/css/style.css", AKAR / "assets" / "css" / "style.css"),
        ("/assets/js/app.js", AKAR / "assets" / "js" / "app.js"),
    ):
        tertulis = re.search(re.escape(aset) + r"\?v=([0-9a-z]+)", beranda).group(1)
        sebenarnya = hashlib.sha256(jalur.read_bytes()).hexdigest()[:10]
        assert tertulis == sebenarnya, (
            f"{aset} bernomor {tertulis} sedangkan isinya bersidik {sebenarnya}. "
            "Pembaca lama tidak akan pernah menerima perubahannya."
        )


POLA_GAMBAR_KARYA = re.compile(r"/assets/img/work/([a-z0-9-]+\.webp)(?:\?v=([0-9a-z]+))?")
WAJIB_MENYEBUT_KARYA = {
    "index.html",
    "project.html",
    "parkir-jogja.html",
    "next/content/projects.ts",
    "next/content/parkir-jogja.ts",
    "next/components/ParkirJogjaView.tsx",
}


def _penyebut_gambar_karya() -> dict[str, list[tuple[str, str | None]]]:
    tidak = {"next", "dist", "backend", ".git", "node_modules", ".claude"}
    calon = [p for p in AKAR.rglob("*.html") if not tidak & set(p.relative_to(AKAR).parts)]
    calon += list((AKAR / "assets" / "js").glob("*.js"))
    for folder in ("app", "components", "content", "lib"):
        calon += [p for p in (AKAR / "next" / folder).rglob("*") if p.suffix in {".ts", ".tsx"}]

    hasil = {}
    for p in calon:
        sebutan = POLA_GAMBAR_KARYA.findall(p.read_text(encoding="utf-8"))
        if sebutan:
            hasil[p.relative_to(AKAR).as_posix()] = sebutan
    return hasil


def test_gambar_karya_bernomor_sidik_isinya():
    import hashlib

    penyebut = _penyebut_gambar_karya()
    hilang = WAJIB_MENYEBUT_KARYA - set(penyebut)
    assert not hilang, (
        f"tidak ada gambar karya yang ditemukan di {sorted(hilang)}. "
        "Kalau berkasnya pindah, pindahkan juga daftarnya di sini."
    )

    salah = []
    for berkas, sebutan in penyebut.items():
        for nama, tertulis in sebutan:
            gambar = AKAR / "assets" / "img" / "work" / nama
            assert gambar.exists(), f"{berkas} menyebut {nama}, berkasnya tidak ada"
            sebenarnya = hashlib.sha256(gambar.read_bytes()).hexdigest()[:10]
            if tertulis != sebenarnya:
                salah.append(f"{berkas}: {nama} bernomor {tertulis or 'kosong'}, sidiknya {sebenarnya}")

    assert not salah, (
        "Gambar karya tanpa nomor yang benar. Pembaca lama tetap melihat gambar "
        "lama selama setahun. Jalankan: python tools/versi_aset.py\n  "
        + "\n  ".join(salah)
    )


def test_nomor_gambar_karya_diganti_bukan_ditumpuk():
    import hashlib
    import sys

    sys.path.insert(0, str(AKAR / "tools"))
    from versi_aset import cap_karya

    sidik = hashlib.sha256(
        (AKAR / "assets" / "img" / "work" / "fire.webp").read_bytes()).hexdigest()[:10]
    for masuk in ("/assets/img/work/fire.webp 800w", "/assets/img/work/fire.webp?v=0000000000 800w"):
        assert cap_karya(masuk) == f"/assets/img/work/fire.webp?v={sidik} 800w"


def test_gambar_karya_di_tulisan_ikut_bernomor():
    import hashlib
    import sys

    sys.path.insert(0, str(AKAR / "tools"))
    import bangun_tulisan

    sidik = hashlib.sha256(
        (AKAR / "assets" / "img" / "work" / "fish.webp").read_bytes()).hexdigest()[:10]
    keluar = bangun_tulisan.badan(
        "![Fish](/assets/img/work/fish.webp)", "![Ikan](/assets/img/work/fish.webp)")
    assert f'src="/assets/img/work/fish.webp?v={sidik}"' in keluar, keluar


def test_pustaka_peta_dipanggil_dari_folder_berversi():
    app = (AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    versi_pustaka = (AKAR / "assets" / "vendor" / "maplibre" / "VERSI").read_text(
        encoding="utf-8").strip()
    for berkas in ("maplibre-gl.css", "maplibre-gl.mjs"):
        assert f"/assets/vendor/maplibre/{versi_pustaka}/{berkas}" in app, (
            f"{berkas} dipanggil dari alamat yang tidak memuat versi pustakanya"
        )


def test_konfigurasi_dikecualikan_dari_immutable():
    assert "/assets/js/konfigurasi.js" in HEADERS, (
        "_headers tidak mengecualikan konfigurasi.js dari immutable"
    )
    potong = HEADERS.split("/assets/js/konfigurasi.js", 1)[1]
    aturan = potong.split("\n\n", 1)[0]
    assert "must-revalidate" in aturan, aturan
    assert "immutable" not in aturan, aturan

    baris_aturan = [
        b.strip() for b in HEADERS.splitlines()
        if b.startswith("/") and not b.strip().startswith("#")
    ]
    assert "/assets/*" not in baris_aturan, (
        "/assets/* ikut mencakup konfigurasi.js, dan aturannya digabung, "
        "bukan diganti. Sebut foldernya satu per satu."
    )

    nginx = (AKAR / "infrastructure" / "nginx" / "hendrokuswantoro.conf").read_text(
        encoding="utf-8")
    assert "location = /assets/js/konfigurasi.js" in nginx, (
        "nginx menyajikan konfigurasi.js sebagai immutable seperti aset lain"
    )


def test_dua_pembangun_sepakat():
    py = (AKAR / "tools" / "build_dist.py").read_text(encoding="utf-8")
    sh = (AKAR / "tools" / "bangun_situs.sh").read_text(encoding="utf-8")

    daftar_py = set(re.findall(r'^\s+"([\w.\-]+)",', py, re.M))
    blok = re.search(r"for berkas in (.*?); do", sh, re.S)
    assert blok, "the copy loop in bangun_situs.sh changed shape"
    daftar_sh = {k for k in blok.group(1).split() if k != chr(92)}

    assert daftar_py == daftar_sh, (
        f"only in the zip: {sorted(daftar_py - daftar_sh)}\n"
        f"only in dist/  : {sorted(daftar_sh - daftar_py)}"
    )


def test_sitemap_menunjuk_berkas_nyata():
    akar = ET.parse(AKAR / "sitemap.xml").getroot()
    ruang = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    alamat = [e.text or "" for e in akar.findall(".//s:loc", ruang)]
    assert alamat, "the sitemap is empty"

    for a in alamat:
        assert a.startswith(SITUS), f"sitemap lists a foreign address: {a}"
        berkas = berkas_dari_jalur(a[len(SITUS):])
        assert berkas.exists(), f"sitemap lists {a}, which does not exist"


def test_setiap_tulisan_terdaftar():
    tulisan = sorted(p.stem for p in (AKAR / "blog").glob("*.html") if p.stem != "index")
    sitemap = (AKAR / "sitemap.xml").read_text(encoding="utf-8")
    umpan = (AKAR / "feed.xml").read_text(encoding="utf-8")
    for t in tulisan:
        assert f"/blog/{t}<" in sitemap, f"{t} is missing from the sitemap"
        assert f"/blog/{t}<" in umpan, f"{t} is missing from the feed"


def test_umpan_terbaca():
    akar = ET.parse(AKAR / "feed.xml").getroot()
    item = akar.findall(".//item")
    assert len(item) >= 3, "the feed lost posts"
    for i in item:
        for bagian in ("title", "link", "guid", "description", "pubDate"):
            assert (i.find(bagian) is not None) and i.find(bagian).text, (
                f"a feed item is missing {bagian}"
            )


def test_robots_menunjuk_sitemap():
    robots = (AKAR / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {SITUS}/sitemap.xml" in robots


@pytest.mark.parametrize("arahan", [
    "X-Content-Type-Options: nosniff",
    "X-Frame-Options: DENY",
    "Referrer-Policy: strict-origin-when-cross-origin",
    "Strict-Transport-Security:",
    "Content-Security-Policy:",
])
def test_header_keamanan_ada(arahan):
    assert arahan in HEADERS, f"_headers lost {arahan}"


@pytest.mark.parametrize("sumber", [
    "default-src 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "script-src 'self' blob:",
    "https://api.mapbox.com",
])
def test_csp_menahan_yang_penting(sumber):
    csp = [b for b in HEADERS.splitlines() if "Content-Security-Policy:" in b][0]
    assert sumber in csp, f"the CSP lost {sumber}"


def test_tidak_ada_redirects_lagi():
    assert not (AKAR / "_redirects").exists(), (
        "_redirects is back. Workers will refuse the deploy with code 100324."
    )


def test_wrangler_menunjuk_dist():
    assert 'name = "hendrokuswantoro-com"' in WRANGLER, "the worker name no longer matches"
    assert 'directory = "./dist"' in WRANGLER
    assert 'not_found_handling = "404-page"' in WRANGLER


PEMBANGUN = {
    "tools/bangun_situs.sh": (AKAR / "tools" / "bangun_situs.sh").read_text(encoding="utf-8"),
    "tools/build_dist.py": (AKAR / "tools" / "build_dist.py").read_text(encoding="utf-8"),
}


@pytest.mark.parametrize(
    "berkas",
    [p for p in HALAMAN if p.parent == AKAR],
    ids=nama,
)
def test_setiap_halaman_ikut_dibangun(berkas):
    for nama_pembangun, isi in PEMBANGUN.items():
        assert berkas.name in isi, (
            f"{berkas.name} tidak disebut {nama_pembangun}, "
            f"jadi ia tidak akan ikut terbit"
        )
