"""Membangun halaman blog dari content/blog/*.md.

    python tools/bangun_tulisan.py              # tulis
    python tools/bangun_tulisan.py --periksa    # bandingkan saja, jangan tulis
    python tools/bangun_tulisan.py --sumber api # ekspor dari dashboard dulu, lalu tulis

Yang dibangkitkan: satu halaman per tulisan, daftar di blog/index.html,
lalu sitemap.xml dan feed.xml ikut diperbarui lewat tools/build_feed.py.

--sumber api tidak membangun halaman langsung dari basis data. Ia menulis tiap
tulisan terbit menjadi content/blog/SLUG.md dan menyalin foto serta video yang
disebutnya ke content/unggahan/, lalu membangun dari berkas seperti biasa.
Jadi yang terbit selalu bisa dibangun ulang dari git, dan CI memeriksa hal
yang sama. Tulisan di content/blog yang tidak ada di dashboard dibiarkan.

Nomor versi aset tidak ditulis di template. Pembangkit membacanya dari
index.html, sehingga halaman blog tidak mungkin memakai versi yang berbeda
dari halaman lain. Pergeseran versi itu pernah terjadi dua kali dalam satu
hari dan tidak menimbulkan galat apa pun.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import markah  # noqa: E402
import unggahan_publik  # noqa: E402
from isi import IsiSalah, SumberApi, SumberBerkas, Tulisan, tulis_tulisan  # noqa: E402
from versi_aset import cap_karya  # noqa: E402

AKAR = pathlib.Path(__file__).resolve().parent.parent
ISI = AKAR / "content"
TEMPLATE = AKAR / "content" / "template"
SITUS = "https://www.hendrokuswantoro.com"
TANGGAL_SITUS = "2026-09-14"


def versi_aset() -> tuple[str, str]:
    beranda = (AKAR / "index.html").read_text(encoding="utf-8")
    css = re.search(r"/assets/css/style\.css\?v=([0-9a-z]+)", beranda)
    js = re.search(r"/assets/js/app\.js\?v=([0-9a-z]+)", beranda)
    if not css or not js:
        raise SystemExit("index.html tidak menyebut versi aset")
    return css.group(1), js.group(1)


def badan(mentah: str, lain: str) -> str:
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

        ind = markah.untuk_ind(idn.teks)
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
                    f'          <li data-ind="{markah.untuk_ind(b)}">{markah.sebaris(a)}</li>'
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
    alt = markah.polos(en.teks)
    ind_alt = markah.polos(idn.teks)
    ind = markah.untuk_ind(idn.teks)
    src = html.escape(cap_karya(en.alamat), quote=True)
    baris = ['        <figure class="tulisan__media">']

    if en.jenis == "gambar":
        ukur = markah.ukuran(en.alamat)
        sifat = f' width="{ukur[0]}" height="{ukur[1]}"' if ukur else ""
        baris.append(
            f'          <img src="{src}" alt="{alt}" data-ind-alt="{ind_alt}"'
            f'{sifat} loading="lazy" decoding="async">'
        )
    else:
        baris.append(
            f'          <video src="{src}" controls preload="metadata"'
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
        % (t.slug, markah.untuk_ind(t.judul.id), markah.sebaris(t.judul.en))
        for t in semua
        if t.slug != ini.slug
    ]
    return "\n".join(baris)


def halaman(t: Tulisan, semua: list[Tulisan], css: str, js: str) -> str:
    nilai = {
        "slug": t.slug,
        "tanggal": t.tanggal,
        "tanggal_label_en": html.escape(t.tanggal_label.en, quote=True),
        "tanggal_label_id": markah.untuk_ind(t.tanggal_label.id),
        "tag_en": html.escape(t.tag.en, quote=True),
        "tag_id": markah.untuk_ind(t.tag.id),
        "baca_en": html.escape(t.baca.en, quote=True),
        "baca_id": markah.untuk_ind(t.baca.id),
        "judul_en": html.escape(t.judul.en, quote=True),
        "judul_id": markah.untuk_ind(t.judul.id),
        "judul_json": json.dumps(t.judul.en, ensure_ascii=False)[1:-1]
        .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
        "keterangan_en": html.escape(t.keterangan.en, quote=True),
        "keterangan_id": markah.untuk_ind(t.keterangan.id),
        "lede_en": html.escape(t.lede.en, quote=True),
        "lede_id": markah.untuk_ind(t.lede.id),
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
    baris = [
        '        <a class="post" href="/blog/%s">' % t.slug,
        '          <span class="post__meta">',
        '            <span class="tag" data-ind="%s">%s</span>'
        % (markah.untuk_ind(t.tag.id), html.escape(t.tag.en, quote=True)),
        '            <time datetime="%s" data-ind="%s">%s</time>'
        % (t.tanggal, markah.untuk_ind(t.tanggal_label.id),
           html.escape(t.tanggal_label.en, quote=True)),
        '            <span data-ind="%s">%s</span>'
        % (markah.untuk_ind(t.baca.id), html.escape(t.baca.en, quote=True)),
        '          </span>',
        '          <h2 data-ind="%s">%s</h2>'
        % (markah.untuk_ind(t.judul.id), markah.sebaris(t.judul.en)),
        '          <p data-ind="%s">%s</p>'
        % (markah.untuk_ind(t.ringkas.id), markah.sebaris(t.ringkas.en)),
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

def ekspor(pangkal: str) -> None:
    dari_api = SumberApi(pangkal).tulisan()
    folder = ISI / "blog"
    for t in dari_api:
        tujuan = folder / f"{t.slug}.md"
        baru = tulis_tulisan(t)
        lama = tujuan.read_text(encoding="utf-8") if tujuan.exists() else None
        if lama != baru:
            tujuan.write_text(baru, encoding="utf-8", newline="\n")
            print(f"tulis {tujuan.relative_to(AKAR).as_posix()}")
        else:
            print(f"tetap {tujuan.relative_to(AKAR).as_posix()}")
    ada = {t.slug for t in dari_api}
    for berkas in sorted(folder.glob("*.md")):
        if berkas.stem not in ada:
            print(f"biar {berkas.relative_to(AKAR).as_posix()}: tidak ada di dashboard, tidak disentuh")

    dipakai = unggahan_publik.rujukan(SumberBerkas(ISI).tulisan())
    for nama in unggahan_publik.salin(dipakai, ISI / "unggahan", pangkal):
        print(f"salin content/unggahan/{nama}")


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true",
                        help="bandingkan saja, keluar 1 bila ada beda")
    alasan.add_argument("--sumber", default="berkas", choices=["berkas", "api"],
                        help="dari content/ atau dari API")
    alasan.add_argument("--api", default="http://127.0.0.1:8000",
                        help="pangkal API kalau --sumber api")
    pilihan = alasan.parse_args()

    if pilihan.sumber == "api":
        if pilihan.periksa:
            raise SystemExit("--periksa hanya membandingkan dengan content/, tanpa --sumber api")
        try:
            ekspor(pilihan.api)
        except IsiSalah as galat:
            raise SystemExit(f"ekspor gagal: {galat}") from galat

    css, js = versi_aset()
    semua = SumberBerkas(ISI).tulisan()
    if not semua:
        raise SystemExit("content/blog kosong")

    beda = 0
    folder_unggahan = ISI / "unggahan"
    try:
        dipakai = unggahan_publik.rujukan(semua)
    except IsiSalah as galat:
        raise SystemExit(str(galat)) from galat
    if not pilihan.periksa:
        for nama in unggahan_publik.pangkas(dipakai, folder_unggahan):
            print(f"buang content/unggahan/{nama}, tidak disebut tulisan mana pun")
    for masalah in unggahan_publik.periksa(dipakai, folder_unggahan):
        beda += 1
        print(masalah)
    if beda and not pilihan.periksa:
        raise SystemExit("unggahan belum lengkap; jalankan dengan --sumber api selagi dashboard menyala")
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
