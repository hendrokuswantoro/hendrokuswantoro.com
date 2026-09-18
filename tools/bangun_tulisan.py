"""Membangun halaman blog dari content/blog/*.md.

    python tools/bangun_tulisan.py            # tulis
    python tools/bangun_tulisan.py --periksa  # bandingkan saja, jangan tulis

Yang dibangkitkan: satu halaman per tulisan, daftar di blog/index.html,
lalu sitemap.xml dan feed.xml ikut diperbarui lewat tools/build_feed.py.

Nomor versi aset tidak ditulis di template. Pembangkit membacanya dari
index.html, sehingga halaman blog tidak mungkin memakai versi yang berbeda
dari halaman lain. Pergeseran versi itu pernah terjadi dua kali dalam satu
hari dan tidak menimbulkan galat apa pun.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import markah  # noqa: E402
from isi import SumberApi, SumberBerkas, SumberIsi, Tulisan  # noqa: E402

AKAR = pathlib.Path(__file__).resolve().parent.parent
ISI = AKAR / "content"
TEMPLATE = AKAR / "content" / "template"
SITUS = "https://www.hendrokuswantoro.com"
# tanggal halaman yang isinya tidak datang dari content/
TANGGAL_SITUS = "2026-09-14"


def versi_aset() -> tuple[str, str]:
    beranda = (AKAR / "index.html").read_text(encoding="utf-8")
    # Nomornya sidik isi berkasnya, sepuluh heksa, bukan angka desimal.
    # Lihat tools/versi_aset.py.
    css = re.search(r"/assets/css/style\.css\?v=([0-9a-z]+)", beranda)
    js = re.search(r"/assets/js/app\.js\?v=([0-9a-z]+)", beranda)
    if not css or not js:
        raise SystemExit("index.html tidak menyebut versi aset")
    return css.group(1), js.group(1)


def badan(mentah: str, lain: str) -> str:
    """Markdown dua bahasa jadi HTML dengan atribut data-ind.

    Bentuk keluarannya mengikuti berkas yang sudah ada persis, termasuk
    barisnya: paragraf memecah teksnya ke baris sendiri, kutipan tidak.
    """
    blok_en = markah.blok(mentah)
    blok_id = markah.blok(lain)
    if len(blok_en) != len(blok_id):
        raise SystemExit(
            f"jumlah blok tidak sama: Inggris {len(blok_en)}, Indonesia {len(blok_id)}"
        )

    keluar: list[str] = []
    for nomor, (en, idn) in enumerate(zip(blok_en, blok_id)):
        if en.jenis != idn.jenis:
            raise SystemExit(
                f"blok ke {nomor + 1} beda jenis: {en.jenis} lawan {idn.jenis}"
            )
        # Gambar dan video wajib menunjuk berkas yang sama di kedua bahasa.
        #
        # Kalau tidak dijaga, pembaca Indonesia dan pembaca Inggris melihat
        # dua foto berbeda di tempat yang sama, dan tidak ada satu pun yang
        # mengadu. Keterangannya memang boleh, dan memang harus, berbeda.
        if en.alamat != idn.alamat:
            raise SystemExit(
                f"blok ke {nomor + 1} menunjuk berkas berbeda: "
                f"{en.alamat} lawan {idn.alamat}"
            )
        if len(en.butir) != len(idn.butir):
            raise SystemExit(
                f"blok ke {nomor + 1} beda jumlah butir: "
                f"Inggris {len(en.butir)}, Indonesia {len(idn.butir)}"
            )

        ind = markah.polos(idn.teks)
        isi = markah.sebaris(en.teks)

        if en.jenis == "h2":
            if keluar:
                keluar.append("")
            keluar.append(f'        <h2 data-ind="{ind}">{isi}</h2>')
        elif en.jenis == "quote":
            keluar.append("        <blockquote>")
            keluar.append(f'          <p data-ind="{ind}">{isi}</p>')
            keluar.append("        </blockquote>")
        elif en.jenis in ("ul", "ol"):
            keluar.append(f'        <{en.jenis} class="tulisan__daftar">')
            for a, b in zip(en.butir, idn.butir):
                keluar.append(
                    f'          <li data-ind="{markah.polos(b)}">{markah.sebaris(a)}</li>'
                )
            keluar.append(f"        </{en.jenis}>")
        elif en.jenis in ("gambar", "video"):
            keluar.extend(media(en, idn))
        else:
            keluar.append(f'        <p data-ind="{ind}">')
            keluar.append(f"          {isi}")
            keluar.append("        </p>")

    return "\n".join(keluar)


def media(en: markah.Blok, idn: markah.Blok) -> list[str]:
    """Satu gambar atau satu video, dengan keterangannya dua bahasa.

    Keterangan merangkap teks alternatif, dan itu kompromi yang disebut
    terus terang: keduanya memang berbeda tugas, satu untuk pembaca yang
    melihat gambarnya dan satu untuk yang tidak. Menuntut penulisnya
    menuliskan empat kalimat untuk satu foto akan berakhir dengan dua di
    antaranya disalin dari dua lainnya.

    Yang tetap dijaga: gambar tanpa keterangan keluar dengan alt kosong,
    yaitu pernyataan "ini hiasan", bukan alt berisi nama berkasnya.
    """
    alt = markah.polos(en.teks)
    ind = markah.polos(idn.teks)
    baris = ['        <figure class="tulisan__media">']

    if en.jenis == "gambar":
        ukur = markah.ukuran(en.alamat)
        # Tanpa ukuran, peramban baru tahu tinggi gambarnya sesudah
        # mengunduhnya, dan tulisan di bawahnya melompat. Gambar yang tidak
        # punya ukuran di namanya tetap terbit, hanya tanpa janji itu.
        sifat = f' width="{ukur[0]}" height="{ukur[1]}"' if ukur else ""
        baris.append(
            f'          <img src="{en.alamat}" alt="{alt}" data-ind-alt="{ind}"'
            f'{sifat} loading="lazy" decoding="async">'
        )
    else:
        # preload="metadata": yang diambil lebih dulu cuma durasi dan
        # ukurannya, bukan seluruh videonya. Video yang mengunduh dirinya
        # sendiri di halaman yang mungkin tidak pernah digulir sampai ke sana
        # adalah kuota pembaca yang dipakai tanpa pernah dimintai izin.
        baris.append(
            f'          <video src="{en.alamat}" controls preload="metadata"'
            ' playsinline></video>'
        )

    if en.teks:
        baris.append(
            f'          <figcaption data-ind="{ind}">'
            f'{markah.sebaris(en.teks)}</figcaption>'
        )
    baris.append("        </figure>")
    return baris


def tautan_lain(ini: Tulisan, semua: list[Tulisan]) -> str:
    baris = [
        '            <a href="/blog/%s" data-ind="%s">%s</a>'
        % (t.slug, markah.polos(t.judul.id), markah.sebaris(t.judul.en))
        for t in semua
        if t.slug != ini.slug
    ]
    return "\n".join(baris)


def halaman(t: Tulisan, semua: list[Tulisan], css: str, js: str) -> str:
    nilai = {
        "slug": t.slug,
        "tanggal": t.tanggal,
        "tanggal_label_en": t.tanggal_label.en,
        "tanggal_label_id": t.tanggal_label.id,
        "tag_en": t.tag.en,
        "tag_id": t.tag.id,
        "baca_en": t.baca.en,
        "baca_id": t.baca.id,
        "judul_en": t.judul.en,
        "judul_id": t.judul.id,
        "keterangan_en": t.keterangan.en,
        "keterangan_id": t.keterangan.id,
        "lede_en": t.lede.en,
        "lede_id": t.lede.id,
        "isi": badan(t.isi_en, t.isi_id),
        "lain": tautan_lain(t, semua),
        "versi_css": css,
        "versi_js": js,
    }
    keluar = (TEMPLATE / "tulisan.html").read_text(encoding="utf-8")
    for kunci, teks in nilai.items():
        keluar = keluar.replace("{{%s}}" % kunci, teks)
    sisa = re.findall(r"\{\{(\w+)\}\}", keluar)
    if sisa:
        raise SystemExit(f"slot template belum terisi: {sorted(set(sisa))}")
    return keluar


def kartu(t: Tulisan) -> str:
    """Satu kartu di halaman Blog.

    Ditulis sebagai daftar baris, bukan satu f-string panjang: bentuk
    keluarannya harus sama persis dengan berkas tulis tangan, dan indentasi
    yang salah satu spasi pun akan terlihat di pembandingan.
    """
    baris = [
        '        <a class="post" href="/blog/%s">' % t.slug,
        '          <span class="post__meta">',
        '            <span class="tag" data-ind="%s">%s</span>'
        % (markah.polos(t.tag.id), t.tag.en),
        '            <time datetime="%s" data-ind="%s">%s</time>'
        % (t.tanggal, markah.polos(t.tanggal_label.id), t.tanggal_label.en),
        '            <span data-ind="%s">%s</span>'
        % (markah.polos(t.baca.id), t.baca.en),
        '          </span>',
        '          <h2 data-ind="%s">%s</h2>'
        % (markah.polos(t.judul.id), markah.sebaris(t.judul.en)),
        '          <p data-ind="%s">%s</p>'
        % (markah.polos(t.ringkas.id), markah.sebaris(t.ringkas.en)),
        '          <span class="post__more" data-ind="Baca selengkapnya">Read more</span>',
        '        </a>',
    ]
    return "\n".join(baris)


def daftar(semua: list[Tulisan], css: str, js: str) -> str:
    keluar = (TEMPLATE / "blog.html").read_text(encoding="utf-8")
    isi_daftar = "\n\n".join(kartu(t) for t in semua)
    for kunci, teks in (("daftar", isi_daftar), ("versi_css", css), ("versi_js", js)):
        keluar = keluar.replace("{{%s}}" % kunci, teks)
    sisa = re.findall(r"\{\{(\w+)\}\}", keluar)
    if sisa:
        raise SystemExit("slot template blog belum terisi: %s" % sorted(set(sisa)))
    return keluar


TETAP = [
    ("/", "monthly", "1.0"),
    ("/about", "monthly", "0.8"),
    ("/project", "monthly", "0.8"),
    ("/parkir-jogja", "monthly", "0.8"),
    ("/blog/", "weekly", "0.9"),
]


def sitemap(semua: list[Tulisan]) -> str:
    """Sitemap dibangkitkan, bukan disunting tangan.

    Tulisan yang tidak terdaftar di sitemap adalah tulisan yang tidak akan
    ditemukan siapa pun. Selama daftarnya diurus tangan, lupa satu baris
    tidak menimbulkan galat apa pun.
    """
    diubah = max((t.tanggal for t in semua), default="")
    baris = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for jalur, sering, bobot in TETAP:
        stempel = diubah if jalur == "/blog/" else TANGGAL_SITUS
        baris.append(
            "  <url><loc>%s%s</loc><lastmod>%s</lastmod>"
            "<changefreq>%s</changefreq><priority>%s</priority></url>"
            % (SITUS, jalur, stempel, sering, bobot)
        )
    for t in semua:
        baris.append(
            "  <url><loc>%s/blog/%s</loc><lastmod>%s</lastmod>"
            "<changefreq>yearly</changefreq><priority>0.7</priority></url>"
            % (SITUS, t.slug, t.tanggal)
        )
    baris += ["</urlset>", ""]
    return "\n".join(baris)

def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true",
                        help="bandingkan saja, keluar 1 bila ada beda")
    alasan.add_argument("--sumber", default="berkas", choices=["berkas", "api"],
                        help="dari content/ atau dari API")
    alasan.add_argument("--api", default="http://127.0.0.1:8000",
                        help="pangkal API kalau --sumber api")
    pilihan = alasan.parse_args()

    # Seluruh alasan SumberIsi dibuat antarmuka sejak Fase 0 ada di dua baris
    # ini: berpindah dari berkas ke basis data tidak menyentuh satu pun baris
    # di bawahnya.
    sumber: SumberIsi = (
        SumberApi(pilihan.api) if pilihan.sumber == "api" else SumberBerkas(ISI)
    )

    css, js = versi_aset()
    semua = sumber.tulisan()
    if not semua:
        raise SystemExit("content/blog kosong")

    beda = 0
    for t in semua:
        tujuan = AKAR / "blog" / f"{t.slug}.html"
        baru = halaman(t, semua, css, js)
        lama = tujuan.read_text(encoding="utf-8") if tujuan.exists() else None

        if pilihan.periksa:
            if lama != baru:
                beda += 1
                print(f"BEDA  {tujuan.relative_to(AKAR).as_posix()}")
            else:
                print(f"sama  {tujuan.relative_to(AKAR).as_posix()}")
            continue

        if lama != baru:
            tujuan.write_text(baru, encoding="utf-8")
            print(f"tulis {tujuan.relative_to(AKAR).as_posix()}")
        else:
            print(f"tetap {tujuan.relative_to(AKAR).as_posix()}")

    indeks = AKAR / "blog" / "index.html"
    baru = daftar(semua, css, js)
    lama = indeks.read_text(encoding="utf-8")
    if pilihan.periksa:
        if lama != baru:
            beda += 1
            print("BEDA  blog/index.html")
        else:
            print("sama  blog/index.html")
    elif lama != baru:
        indeks.write_text(baru, encoding="utf-8")
        print("tulis blog/index.html")
    else:
        print("tetap blog/index.html")

    peta_situs = AKAR / "sitemap.xml"
    baru = sitemap(semua)
    lama = peta_situs.read_text(encoding="utf-8")
    if pilihan.periksa:
        if lama != baru:
            beda += 1
            print("BEDA  sitemap.xml")
        else:
            print("sama  sitemap.xml")
    elif lama != baru:
        peta_situs.write_text(baru, encoding="utf-8")
        print("tulis sitemap.xml")
    else:
        print("tetap sitemap.xml")

    if pilihan.periksa and beda:
        print(f"\n{beda} berkas berbeda")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
