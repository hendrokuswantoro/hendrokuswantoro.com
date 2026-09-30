from __future__ import annotations

import html
import pathlib
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import markah
from isi import SumberBerkas, Tulisan
from versi_aset import cap_karya

SITUS = "https://www.hendrokuswantoro.com"
AKAR = pathlib.Path(__file__).resolve().parent.parent
PENULIS = "Hendro Kuswantoro"


def waktu(t: Tulisan) -> str:
    return format_datetime(datetime.fromisoformat(t.tanggal).replace(tzinfo=timezone.utc))


def blok_html(b: markah.Blok) -> str:
    if b.jenis == "h2":
        return "<h2>%s</h2>" % markah.sebaris(b.teks)
    if b.jenis == "quote":
        return "<blockquote><p>%s</p></blockquote>" % markah.sebaris(b.teks)
    if b.jenis in ("ul", "ol"):
        butir = "".join("<li>%s</li>" % markah.sebaris(x) for x in b.butir)
        return "<%s>%s</%s>" % (b.jenis, butir, b.jenis)
    if b.jenis in ("gambar", "video"):
        src = html.escape(cap_karya(b.alamat), quote=True)
        if b.jenis == "gambar":
            media = '<img src="%s" alt="%s">' % (src, markah.polos(b.teks))
        else:
            media = '<video src="%s" controls></video>' % src
        judul = "<figcaption>%s</figcaption>" % markah.sebaris(b.teks) if b.teks else ""
        return "<figure>%s%s</figure>" % (media, judul)
    return "<p>%s</p>" % markah.sebaris(b.teks)


def isi(t: Tulisan) -> str:
    bagian = ["<p>%s</p>" % html.escape(t.lede.en)]
    bagian += [blok_html(b) for b in markah.blok(t.isi_en)]
    teks = re.sub(r'(href|src)="/', r'\1="%s/' % SITUS, "".join(bagian))
    if "]]>" in teks:
        raise SystemExit("%s: isinya memuat ]]>, CDATA akan patah" % t.slug)
    return teks


def umpan(semua: list[Tulisan]) -> str:
    baris = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"'
        ' xmlns:content="http://purl.org/rss/1.0/modules/content/"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/">',
        "  <channel>",
        "    <title>%s</title>" % PENULIS,
        "    <link>%s/blog/</link>" % SITUS,
        "    <description>Notes on maps, spatial data and the systems around them.</description>",
        "    <language>en</language>",
        '    <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>' % SITUS,
        "    <lastBuildDate>%s</lastBuildDate>" % waktu(semua[0]),
    ]
    for t in semua:
        alamat = html.escape("%s/blog/%s" % (SITUS, t.slug))
        baris += [
            "    <item>",
            "      <title>%s</title>" % html.escape(t.judul.en),
            "      <link>%s</link>" % alamat,
            '      <guid isPermaLink="true">%s</guid>' % alamat,
            "      <dc:creator>%s</dc:creator>" % PENULIS,
            "      <category>%s</category>" % html.escape(t.tag.en),
            "      <description>%s</description>" % html.escape(t.keterangan.en),
            "      <content:encoded><![CDATA[%s]]></content:encoded>" % isi(t),
            "      <pubDate>%s</pubDate>" % waktu(t),
            "    </item>",
        ]
    baris += ["  </channel>", "</rss>", ""]
    return "\n".join(baris)


def main() -> None:
    semua = SumberBerkas(AKAR / "content").tulisan()
    if not semua:
        raise SystemExit("content/blog kosong")
    (AKAR / "feed.xml").write_text(umpan(semua), encoding="utf-8", newline="\n")
    print("wrote feed.xml: %d posts" % len(semua))


if __name__ == "__main__":
    main()
