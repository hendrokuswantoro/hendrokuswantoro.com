"""Menyimpan Poppins di repositori ini, dan menjaga salinannya tetap jujur.

    python tools/ambil_font.py            # unduh dari Google, tulis ulang
    python tools/ambil_font.py --periksa   # hanya periksa, luring, untuk CI
    python tools/ambil_font.py --periksa --daring
                                           # plus bandingkan dengan Google

Kenapa fontnya dibawa masuk, bukan dipanggil dari fonts.googleapis.com:

1. Dua asal tambahan di jalur render. Peramban harus menyelesaikan DNS, TCP,
   dan TLS ke fonts.googleapis.com, menunggu sebuah stylesheet yang memblokir
   render, baru tahu bahwa berkas fontnya ada di fonts.gstatic.com, lalu
   mengulang DNS, TCP, dan TLS ke sana. Dua jabat tangan dan satu perjalanan
   bolak balik tambahan sebelum huruf pertama boleh digambar.
2. Bitanya tidak pernah terukur. Berkas dari asal lain melaporkan
   `transferSize` nol kepada Resource Timing kecuali servernya mengirim
   `Timing-Allow-Origin`, dan Google tidak mengirimnya. Jadi anggaran performa
   di `tests/test_performa.py` selama ini menghitung satu kilobyte untuk font
   yang sebenarnya tiga puluh, dan angka yang ditulisnya tidak benar.
3. Setiap kunjungan memberi tahu pihak ketiga alamat IP dan halaman yang
   sedang dibaca. Itu tidak dibutuhkan untuk menggambar huruf.

Yang diunduh hanya subset `latin` dan `latin-ext`. Poppins juga membawa
devanagari, sekitar 17 KB per tebal, dan situs ini tidak memuat satu pun
aksara itu. Nama berkasnya memuat nomor versi font dari Google, misalnya
`poppins-v24-400-latin.woff2`, sebab `/assets/*` disajikan dengan
`immutable` selama setahun: berkas yang isinya berubah wajib berganti nama,
atau pembaca lama akan memegang versi basi sampai setahun ke depan.

`assets/fonts/sumber.json` mencatat alamat asal, sha256, dan ukuran tiap
berkas. `--periksa` membandingkan berkas yang ada dengan catatan itu tanpa
menyentuh jaringan, jadi CI tidak ikut bergantung pada Google. `--daring`
menambahkan perbandingan dengan apa yang Google sajikan hari ini, yang
gunanya satu: tahu kalau Poppins naik versi.

Blok `@font-face` di `assets/css/style.css` juga ditulis oleh berkas ini, di
antara dua penanda. Dua daftar font yang harus dijaga seirama dengan tangan
adalah dua daftar yang akan berbeda.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.request

AKAR = pathlib.Path(__file__).resolve().parent.parent
FONT = AKAR / "assets" / "fonts"
CATATAN = FONT / "sumber.json"
GAYA = AKAR / "assets" / "css" / "style.css"

KELUARGA = "Poppins"
TEBAL = (400, 500, 600, 700)
SUBSET = ("latin", "latin-ext")

ALAMAT = (
    "https://fonts.googleapis.com/css2"
    "?family=Poppins:wght@400;500;600;700&display=swap"
)

# Tanpa User-Agent sebuah peramban modern, Google menyajikan @font-face
# berformat ttf demi peramban tua, dan berkasnya tiga kali lebih besar.
PERAMBAN = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

MULAI = "/* >>> font, dibangkitkan tools/ambil_font.py, jangan disunting */"
SELESAI = "/* <<< font */"


class Gagal(Exception):
    pass


# ------------------------------------------------------------------ jaringan ---


def _ambil(alamat: str) -> bytes:
    permintaan = urllib.request.Request(alamat, headers={"User-Agent": PERAMBAN})
    with urllib.request.urlopen(permintaan, timeout=30) as jawab:
        return jawab.read()


def dari_google() -> list[dict]:
    """Membaca css2 Google lalu mengembalikan satu entri per berkas woff2."""
    css = _ambil(ALAMAT).decode("utf-8")
    blok = re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S)

    hasil: list[dict] = []
    for subset, isi in blok:
        if subset not in SUBSET:
            continue
        tebal = int(re.search(r"font-weight:\s*(\d+)", isi).group(1))
        if tebal not in TEBAL:
            continue
        url = re.search(r"url\((https://[^)]+)\)", isi).group(1)
        rentang = re.search(r"unicode-range:\s*([^;]+);", isi).group(1).strip()
        versi = re.search(r"/(v\d+)/", url).group(1)
        hasil.append({
            "nama": f"poppins-{versi}-{tebal}-{subset}.woff2",
            "tebal": tebal,
            "subset": subset,
            "versi": versi,
            "rentang": rentang,
            "asal": url,
        })

    kurang = {(t, s) for t in TEBAL for s in SUBSET} - {
        (e["tebal"], e["subset"]) for e in hasil
    }
    if kurang:
        raise Gagal(f"Google tidak menyajikan sebagian subset: {sorted(kurang)}")

    hasil.sort(key=lambda e: (e["tebal"], e["subset"]))
    return hasil


# ------------------------------------------------------------------- berkas ---


def _sidik(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unduh() -> list[dict]:
    FONT.mkdir(parents=True, exist_ok=True)
    entri = dari_google()
    for e in entri:
        data = _ambil(e["asal"])
        if data[:4] != b"wOF2":
            raise Gagal(f"{e['nama']} bukan woff2, empat bita pertamanya {data[:4]!r}")
        (FONT / e["nama"]).write_bytes(data)
        e["bita"] = len(data)
        e["sha256"] = _sidik(data)
        print(f"  {e['nama']:<34} {e['bita'] / 1024:5.1f} KB")
    return entri


def tulis_catatan(entri: list[dict]) -> None:
    CATATAN.write_text(
        json.dumps(
            {
                "keluarga": KELUARGA,
                "lisensi": "OFL-1.1, salinannya di assets/fonts/OFL.txt",
                "perintah": "python tools/ambil_font.py",
                "berkas": entri,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def baca_catatan() -> list[dict]:
    if not CATATAN.exists():
        raise Gagal(f"{CATATAN.relative_to(AKAR)} tidak ada. Jalankan: python tools/ambil_font.py")
    return json.loads(CATATAN.read_text(encoding="utf-8"))["berkas"]


# ---------------------------------------------------------------------- css ---


def blok_css(entri: list[dict]) -> str:
    baris = [
        MULAI,
        "/* Poppins, OFL-1.1, disimpan sendiri. Lihat assets/fonts/sumber.json. */",
    ]
    for e in entri:
        baris += [
            "@font-face {",
            f'  font-family: "{KELUARGA}";',
            "  font-style: normal;",
            f"  font-weight: {e['tebal']};",
            "  font-display: swap;",
            f"  src: url(\"/assets/fonts/{e['nama']}\") format(\"woff2\");",
            f"  unicode-range: {e['rentang']};",
            "}",
        ]
    baris.append(SELESAI)
    return "\n".join(baris)


def gaya_dengan(blok: str) -> str:
    teks = GAYA.read_text(encoding="utf-8")
    if MULAI in teks:
        mulai = teks.index(MULAI)
        akhir = teks.index(SELESAI) + len(SELESAI)
        return teks[:mulai] + blok + teks[akhir:]
    # Pertama kali: diletakkan paling atas supaya peramban menemukan fontnya
    # pada bita pertama stylesheet, bukan sesudah empat puluh kilobyte aturan.
    return blok + "\n\n" + teks


# ------------------------------------------------------------------ periksa ---


def periksa(daring: bool) -> int:
    salah: list[str] = []
    try:
        entri = baca_catatan()
    except Gagal as g:
        print(f"GAGAL: {g}")
        return 1

    for e in entri:
        jalur = FONT / e["nama"]
        if not jalur.exists():
            salah.append(f"hilang: {e['nama']}")
            continue
        data = jalur.read_bytes()
        if len(data) != e["bita"]:
            salah.append(f"ukuran beda: {e['nama']}, {len(data)} bukan {e['bita']}")
        elif _sidik(data) != e["sha256"]:
            salah.append(f"sha256 beda: {e['nama']}")

    asing = {p.name for p in FONT.glob("*.woff2")} - {e["nama"] for e in entri}
    if asing:
        salah.append(f"ada berkas font yang tidak tercatat: {sorted(asing)}")

    harus = blok_css(entri)
    if harus not in GAYA.read_text(encoding="utf-8"):
        salah.append("blok @font-face di style.css tidak sama dengan daftar fontnya")

    if daring:
        try:
            baru = dari_google()
        except Exception as g:  # noqa: BLE001 - jaringan, apa pun sebabnya
            print(f"  lewat: pemeriksaan daring tidak bisa dijalankan, {g}")
        else:
            versi_lokal = {e["versi"] for e in entri}
            versi_baru = {e["versi"] for e in baru}
            if versi_lokal != versi_baru:
                salah.append(
                    f"Google sekarang menyajikan {sorted(versi_baru)}, "
                    f"salinan di sini {sorted(versi_lokal)}"
                )

    if salah:
        for s in salah:
            print(f"GAGAL: {s}")
        print("Jalankan: python tools/ambil_font.py")
        return 1

    total = sum(e["bita"] for e in entri if e["subset"] == "latin")
    print(f"cocok: {len(entri)} berkas font, subset latin berjumlah {total / 1024:.1f} KB")
    return 0


# -------------------------------------------------------------------- utama ---


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true",
                        help="jangan menulis apa pun, hanya bandingkan dengan catatan")
    alasan.add_argument("--daring", action="store_true",
                        help="dengan --periksa: tanyakan juga ke Google apa versinya sekarang")
    pilihan = alasan.parse_args()

    if pilihan.periksa:
        return periksa(pilihan.daring)

    try:
        entri = unduh()
    except Gagal as g:
        print(f"GAGAL: {g}")
        return 1

    tulis_catatan(entri)
    GAYA.write_text(gaya_dengan(blok_css(entri)), encoding="utf-8", newline="\n")
    latin = sum(e["bita"] for e in entri if e["subset"] == "latin")
    print(f"ditulis: {len(entri)} berkas, catatan, dan blok @font-face di style.css")
    print(f"         subset latin berjumlah {latin / 1024:.1f} KB untuk {len(TEBAL)} tebal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
