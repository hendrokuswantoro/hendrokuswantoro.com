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

## Lewat dashboard

Sejak Fase 5 ada cara kedua, dan ini yang sebenarnya Anda minta: menulis di
formulir, bukan di berkas.

```bash
cd infrastructure && docker compose --env-file ../.env up -d
cd .. && python backend/jalan.py
```

Lalu buka <http://127.0.0.1:8000/admin>.

**Sekali saja**, pasang sandi admin:

```bash
python backend/db/buat_admin.py
```

### Alurnya

1. Masuk. Kalau cookie sesi masih hidup, sandinya tidak ditanya lagi.
2. **Tulisan baru**, isi kolomnya. Inggris dan Indonesia berdampingan.
3. Isinya Markdown, dengan penghitung blok di bawah tiap kolom dan pratinjau
   di bawahnya. Kalau jumlah bloknya tidak sama, peringatannya muncul
   **sebelum** Anda menekan Simpan.
4. **Simpan.** Statusnya draf. Belum terlihat siapa pun.
5. **Terbitkan.** Statusnya berubah, dan tulisannya muncul di jalur publik API.
6. Bangkitkan halamannya lalu dorong:

```bash
python tools/bangun_tulisan.py --sumber api
```

lalu `python tools/build_feed.py`, `python -m pytest`, `git push`.

### Dua dashboard, dan cara memilihnya

Ada dua, dan keduanya memakai API yang sama persis.

| | Di mana | Menuntut |
| --- | --- | --- |
| HTML biasa | `backend/admin/index.html` | tidak apa apa |
| Next.js | `next/app/admin/` | `npm run build` lebih dulu |

Bawaannya yang HTML. Ia satu berkas, tanpa langkah build yang bisa lupa
dijalankan, dan itu sifat yang berharga untuk alat yang dipakai saat sesuatu
sedang rusak.

Versi Next.js dinyalakan dengan sengaja:

```bash
cd next && npm ci && npm run build
cd .. && ADMIN_NEXT=1 python backend/jalan.py
```

Kalau hasil buildnya belum ada, yang HTML tetap keluar, bukan 404.

Versi Next.js inilah yang diminta spesifikasi, dan sampai Node terpasang pada
12 September 2026 ia memang tidak ada. Isinya: masuk dengan sandi atau
passkey, daftar tulisan termasuk draf, penyunting dua bahasa yang menghitung
blok tiap bahasa sambil diketik, dan panel passkey.

Ia hidup di luar route group `(situs)`, jadi ia tidak ikut memakai kepala,
kaki, dan bilah tab milik halaman publik. Sebelum pemisahan itu halaman admin
punya dua `<header>` sekaligus, lengkap dengan saklar bahasa yang tidak
berarti apa apa di sana; yang menemukannya uji peramban, bukan mata.

Token akses disimpan di variabel biasa, bukan `localStorage`. Token di
`localStorage` bisa diambil satu XSS; yang di memori ikut hilang saat tab
ditutup. Yang bertahan antar kunjungan adalah cookie refresh yang HttpOnly,
yang tidak bisa dibaca JavaScript sama sekali.

Pratinjaunya dirakit dengan `createElement`, bukan `innerHTML`. Isi yang Anda
tulis sendiri memang tidak berbahaya, tetapi kebiasaan merakit lewat
`innerHTML` itu yang suatu saat dipakai untuk isi yang datang dari luar.
