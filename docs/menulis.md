# Menulis tulisan blog

Sejak Fase 0, tulisan blog adalah **data**, bukan markup. Anda menulis satu
berkas Markdown, sisanya dibangkitkan: halaman tulisan, kartu di halaman
Blog, `sitemap.xml`, dan `feed.xml`.

## Langkahnya

**1.** Buat satu berkas di `content/blog/`. Namanya jadi alamatnya:

```
content/blog/kenapa-proyeksi-penting.md   ->   /blog/kenapa-proyeksi-penting
```

**2.** Isi berkasnya dengan bentuk ini:

```
---
slug: kenapa-proyeksi-penting
tanggal: 2026-09-20
tanggal_label_en: 20 Sep 2026
tanggal_label_id: 20 Sep 2026
tag_en: Map design
tag_id: Desain peta
baca_en: 4 min read
baca_id: 4 menit baca
judul_en: Why the projection matters
judul_id: Kenapa proyeksinya penting
ringkas_en: One sentence for the card on the Blog page.
ringkas_id: Satu kalimat untuk kartu di halaman Blog.
keterangan_en: One sentence for Google and for the link preview.
keterangan_id: Satu kalimat untuk Google dan untuk pratinjau tautan.
lede_en: The opening paragraph of the article itself.
lede_id: Paragraf pembuka artikelnya sendiri.
---

=== en ===

## First section

A paragraph.

> A pull quote, if the piece needs one.

=== id ===

## Bagian pertama

Satu paragraf.

> Kutipan, kalau memang perlu.
```

**3.** Bangkitkan dan periksa:

```bash
python tools/bangun_tulisan.py
python tools/build_feed.py
python -m pytest
```

**4.** `git push`. Cloudflare membangun dan menerbitkan sendiri.

## Aturan yang dijaga uji

**Dua bahasa harus punya jumlah blok yang sama.** Kalau versi Inggris punya
lima paragraf dan versi Indonesia empat, pembangkitnya berhenti dan menyebut
angkanya. Satu bahasa yang diam diam kehilangan satu paragraf adalah
kegagalan yang tidak akan pernah Anda lihat sendiri.

**Jenis bloknya juga harus sama urutannya.** Judul lawan paragraf pada
posisi yang sama akan ditolak.

**Tidak boleh ada terjemahan kosong.** Ini cerminan kolom berpasangan
`NOT NULL` di rancangan basis datanya.

**HTML blog yang di-commit harus sama persis dengan hasil pembangkitan.**
Kalau Anda menyunting `blog/*.html` dengan tangan, CI menolaknya. Suntingan
tangan akan terbit sekali lalu lenyap tanpa jejak pada pembangkitan
berikutnya, dan itu jenis kehilangan yang paling sulit dilacak.

## Markdown yang didukung

Sengaja sempit, dan yang di luar daftar ini **ditolak dengan galat yang
menyebut nomor baris**, bukan diterjemahkan seadanya.

| Ditulis | Jadi |
| --- | --- |
| `## Judul bagian` | `<h2>` |
| baris biasa | `<p>` |
| `> kutipan` | `<blockquote><p>` |
| `**tebal**` | `<strong>` |
| `*miring*` | `<em>` |
| `` `kode` `` | `<code>` |
| `[teks](/alamat)` | `<a href>` |

Yang ditolak: judul selain `##`, daftar berpoin, tabel, gambar, blok kode
berpagar, dan HTML mentah. Kalau salah satunya benar benar dibutuhkan,
tambahkan dukungannya di `tools/markah.py` beserta ujinya, jangan
menyiasatinya lewat HTML mentah.

## Kenapa berkas, bukan basis data

Untuk sekarang. Rancangan lengkapnya di
[rancangan-platform.md](rancangan-platform.md): `SumberIsi` adalah antarmuka,
dan `SumberBerkas` hanya salah satu implementasinya. Ketika basis data dan
dashboard admin sudah berdiri, `SumberApi` masuk di belakang antarmuka yang
sama dan pembangkitnya tidak berubah sama sekali.

Itu sebabnya Fase 0 tidak akan terbuang.
