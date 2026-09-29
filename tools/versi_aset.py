"""Menomori aset dari isinya, bukan dari ingatan orang yang mengubahnya.

    python tools/versi_aset.py            # tulis ulang
    python tools/versi_aset.py --periksa  # hanya periksa, untuk CI

Kenapa berkas ini ada.

`/assets/*` disajikan dengan `Cache-Control: immutable, max-age=31536000`.
Janji `immutable` berarti peramban boleh menyimpan berkas itu setahun penuh
dan **tidak pernah menanyakannya lagi**, bahkan tidak dengan permintaan
bersyarat. Janji itu hanya boleh diberikan kalau alamatnya berganti setiap kali
isinya berganti. Kalau tidak, pembaca lama memegang berkas lama selama setahun,
dan tidak ada satu pun galat yang muncul di mana pun.

Sampai 13 September 2026 janji itu diberikan tanpa dipenuhi:

| berkas | commit yang mengubahnya | nomor ?v= |
| --- | --- | --- |
| assets/js/peta.js | 10 | tidak pernah naik sejak dipasang |
| assets/css/style.css | 15 | naik sesekali, dengan tangan |
| assets/js/app.js | 17 | naik sesekali, dengan tangan |
| assets/vendor/maplibre/maplibre-gl.css | 2 | tidak punya nomor sama sekali |
| assets/js/konfigurasi.js | tiap kali dibangun | tidak punya nomor sama sekali |

Akibatnya bukan teoretis. `maplibre-gl.css` diganti seluruhnya saat MapLibre
naik dari 4 ke 6, di alamat yang sama. Komentar di `assets/css/style.css`
sendiri menjelaskan apa yang terjadi kalau lembar gaya itu tidak cocok dengan
markup petanya: `.maplibregl-map { position: relative }` menang, kotak petanya
mengerut jadi nol, dan **seluruh petanya hilang**. Begitu juga `peta.js`:
sepuluh commit mengubahnya, termasuk perbaikan peta yang berputar sendiri,
dan tidak satu pun pembaca lama pernah menerimanya.

Nomor yang diketik tangan akan hanyut. Nomor yang dihitung dari isi berkasnya
tidak bisa hanyut, sebab ia berubah tepat ketika isinya berubah dan tidak
pernah pada saat lain.

Yang dinomori:

- `style.css`, `app.js`, `peta.js`, `parkir.js`, dan `parkir-data.js` lewat
  `?v=<sepuluh heksa pertama sha256>`
- pustaka MapLibre lewat **nama foldernya**, bukan lewat query. Modul
  `maplibre-gl.mjs` mengimpor `maplibre-gl-shared.mjs` secara relatif lewat
  `import.meta.url`, jadi query pada modul induk tidak ikut menurun ke
  anaknya, dan anak yang basi sama merusaknya dengan induk yang basi.
  Folder berversi menomori keempatnya sekaligus.
- gambar kartu karya, `assets/img/work/*.webp`, lewat `?v=` yang sama, tiap
  berkas dengan sidiknya sendiri. `tools/build_work_images.py` menulis ulang
  gambar gambar itu di alamat yang sama, misalnya ketika nama situs mulai
  digambar di pojoknya. Tanpa nomor, pembaca lama tetap melihat gambar lama
  selama setahun. Yang dinomori setiap sebutannya: `src`, `srcset`, dan isian
  `image` di port Next.

Yang **tidak** dinomori: `assets/js/konfigurasi.js`. Isinya ditulis saat
membangun dari variabel lingkungan, jadi sidiknya baru diketahui sesudah
`app.js` yang menyebutnya selesai ditulis. Berkas itu 298 bita dan dikecualikan
dari `immutable` lewat `_headers` dan nginx, jadi peramban menanyakannya lagi
tiap kali. Satu permintaan bersyarat per kunjungan adalah harga yang murah
untuk berkas yang memang berganti tiap kali diterbitkan.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent

BERSIDIK = {
    "assets/css/style.css": r"/assets/css/style\.css\?v=([0-9a-z]+)",
    "assets/js/app.js": r"/assets/js/app\.js\?v=([0-9a-z]+)",
    "assets/js/peta.js": r"/assets/js/peta\.js\?v=([0-9a-z]+)",
    "assets/js/parkir.js": r"/assets/js/parkir\.js\?v=([0-9a-z]+)",
    "assets/js/parkir-data.js": r"/assets/js/parkir-data\.js\?v=([0-9a-z]+)",
}
DIMUAT_APP = ("assets/js/parkir.js", "assets/js/parkir-data.js")

VENDOR = AKAR / "assets" / "vendor" / "maplibre"
POLA_VENDOR = re.compile(r"/assets/vendor/maplibre/(?:[0-9][0-9a-zA-Z.\-]*/)?(maplibre-gl[a-z.\-]*)")

KARYA = AKAR / "assets" / "img" / "work"
POLA_KARYA = re.compile(r"/assets/img/work/([a-z0-9\-]+\.webp)(?:\?v=[0-9a-z]+)?")

NEXT = AKAR / "next"
FOLDER_NEXT = ("app", "components", "content", "lib")

def halaman() -> list[pathlib.Path]:
    tidak = {"next", "dist", "backend", ".git", ".claude", "hasil-uji-keamanan"}
    return sorted(
        p for p in AKAR.rglob("*.html")
        if not tidak & set(p.relative_to(AKAR).parts)
    )


def berkas_next() -> list[pathlib.Path]:
    hasil = []
    for folder in FOLDER_NEXT:
        for p in (NEXT / folder).rglob("*"):
            if p.suffix in {".ts", ".tsx"} and POLA_KARYA.search(p.read_text(encoding="utf-8")):
                hasil.append(p)
    return sorted(hasil)


def sidik(jalur: pathlib.Path) -> str:
    return hashlib.sha256(jalur.read_bytes()).hexdigest()[:10]


def cap_karya(teks: str) -> str:
    tercatat: dict[str, str] = {}

    def satu(m: re.Match) -> str:
        nama = m.group(1)
        if nama not in tercatat:
            berkas = KARYA / nama
            if not berkas.exists():
                sys.exit(f"gambar karya tidak ada: {berkas.relative_to(AKAR).as_posix()}")
            tercatat[nama] = sidik(berkas)
        return f"/assets/img/work/{nama}?v={tercatat[nama]}"

    return POLA_KARYA.sub(satu, teks)


def versi_vendor() -> str:
    berkas = VENDOR / "VERSI"
    if not berkas.exists():
        sys.exit(f"{berkas.relative_to(AKAR)} tidak ada")
    return berkas.read_text(encoding="utf-8").strip()


def _ganti(teks: str, pola: str, nilai: str) -> tuple[str, int]:
    jumlah = 0

    def satu(m: re.Match) -> str:
        nonlocal jumlah
        jumlah += 1
        return m.group(0).replace(m.group(1), nilai)

    return re.sub(pola, satu, teks), jumlah


def rencana() -> dict[str, str]:
    hasil: dict[str, str] = {}
    vendor = versi_vendor()

    peta = cap_karya((AKAR / "assets" / "js" / "peta.js").read_text(encoding="utf-8"))
    hasil["assets/js/peta.js"] = peta

    app = cap_karya((AKAR / "assets" / "js" / "app.js").read_text(encoding="utf-8"))
    app, _ = _ganti(app, BERSIDIK["assets/js/peta.js"], _sidik_teks(peta))
    for aset in DIMUAT_APP:
        app, _ = _ganti(app, BERSIDIK[aset], sidik(AKAR / aset))
    app = POLA_VENDOR.sub(rf"/assets/vendor/maplibre/{vendor}/\1", app)
    hasil["assets/js/app.js"] = app

    nomor = {
        "assets/css/style.css": sidik(AKAR / "assets/css/style.css"),
        "assets/js/app.js": _sidik_teks(app),
    }

    for p in halaman():
        teks = p.read_text(encoding="utf-8")
        for aset, pola in BERSIDIK.items():
            if aset in nomor:
                teks, _ = _ganti(teks, pola, nomor[aset])
        hasil[p.relative_to(AKAR).as_posix()] = cap_karya(teks)

    for p in berkas_next():
        hasil[p.relative_to(AKAR).as_posix()] = cap_karya(p.read_text(encoding="utf-8"))

    return hasil


def _sidik_teks(isi: str) -> str:
    return hashlib.sha256(isi.encode("utf-8")).hexdigest()[:10]


PER_BITA = {"assets/js/app.js", "assets/js/peta.js"}


def _tertinggal(nama: str, isi: str) -> bool:
    jalur = AKAR / nama
    if nama in PER_BITA:
        return jalur.read_bytes() != isi.encode("utf-8")
    return jalur.read_text(encoding="utf-8") != isi


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true",
                        help="keluar 1 kalau ada nomor yang tertinggal dari isinya")
    pilihan = alasan.parse_args()

    harus = rencana()
    beda = [nama for nama, isi in harus.items() if _tertinggal(nama, isi)]

    if pilihan.periksa:
        if not beda:
            print(f"cocok: {len(harus)} berkas, nomor asetnya sama dengan isinya")
            return 0
        print("NOMOR ASET TERTINGGAL DARI ISINYA:")
        for nama in beda:
            print(f"  {nama}")
        print()
        print("Peramban menyimpan /assets/* selama setahun dengan janji immutable.")
        print("Alamat yang tidak berganti berarti pembaca lama tidak akan pernah")
        print("menerima perubahan ini, dan tidak ada galat yang memberitahunya.")
        print("Jalankan: python tools/versi_aset.py")
        return 1

    for nama, isi in harus.items():
        if _tertinggal(nama, isi):
            (AKAR / nama).write_text(isi, encoding="utf-8", newline="\n")
            print(f"  ditulis: {nama}")

    print(f"{len(beda)} berkas diperbarui dari {len(harus)} yang diperiksa")
    for aset in BERSIDIK:
        print(f"  {aset:28} v={sidik(AKAR / aset)}")
    print(f"  pustaka peta                 folder {versi_vendor()}")
    print(f"  gambar karya                 {len(list(KARYA.glob('*.webp')))} berkas, masing masing sidiknya sendiri")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
