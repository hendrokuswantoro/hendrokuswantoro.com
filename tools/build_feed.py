"""Writes feed.xml from the posts in blog/.

The posts are the source of truth. Nothing is typed twice: the title, the
summary, the date and the address all come out of the HTML that is already
published, so a feed can never drift from the page it points at.

Run from the project root:

    python tools/build_feed.py
"""

from __future__ import annotations

import html
import pathlib
import re
from email.utils import format_datetime
from datetime import datetime, timezone

SITUS = "https://www.hendrokuswantoro.com"
AKAR = pathlib.Path(__file__).resolve().parent.parent
BLOG = AKAR / "blog"


def ambil(pola: str, teks: str, berkas: str) -> str:
    cocok = re.search(pola, teks, re.S)
    if not cocok:
        raise SystemExit("%s: tidak menemukan %s" % (berkas, pola))
    return html.unescape(cocok.group(1)).strip()


def baca(berkas: pathlib.Path) -> dict:
    teks = berkas.read_text(encoding="utf-8")
    tanggal = ambil(r'<time datetime="([^"]+)"', teks, berkas.name)
    return {
        "judul": ambil(r'<meta property="og:title" content="([^"]*)"', teks, berkas.name),
        "ringkas": ambil(r'<meta property="og:description" content="([^"]*)"', teks, berkas.name),
        "alamat": ambil(r'<link rel="canonical" href="([^"]*)"', teks, berkas.name),
        "tanggal": datetime.fromisoformat(tanggal).replace(tzinfo=timezone.utc),
    }


def main() -> None:
    tulisan = [baca(p) for p in sorted(BLOG.glob("*.html")) if p.name != "index.html"]
    if not tulisan:
        raise SystemExit("blog/ kosong")
    tulisan.sort(key=lambda t: t["tanggal"], reverse=True)

    baris = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>Hendro Kuswantoro</title>",
        "    <link>%s/blog/</link>" % SITUS,
        "    <description>Notes on maps, spatial data and the systems around them.</description>",
        "    <language>en</language>",
        '    <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>' % SITUS,
        "    <lastBuildDate>%s</lastBuildDate>" % format_datetime(tulisan[0]["tanggal"]),
    ]
    for t in tulisan:
        baris += [
            "    <item>",
            "      <title>%s</title>" % html.escape(t["judul"]),
            "      <link>%s</link>" % html.escape(t["alamat"]),
            '      <guid isPermaLink="true">%s</guid>' % html.escape(t["alamat"]),
            "      <description>%s</description>" % html.escape(t["ringkas"]),
            "      <pubDate>%s</pubDate>" % format_datetime(t["tanggal"]),
            "    </item>",
        ]
    baris += ["  </channel>", "</rss>", ""]

    (AKAR / "feed.xml").write_text("\n".join(baris), encoding="utf-8")
    print("wrote feed.xml: %d posts" % len(tulisan))


if __name__ == "__main__":
    main()
