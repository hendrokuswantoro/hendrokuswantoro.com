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
| `- butir` | `<ul><li>` |
| `1. butir` | `<ol><li>` |
| `![keterangan](/unggahan/x.webp)` | `<figure><img>` |
| `!video[keterangan](/unggahan/x.mp4)` | `<figure><video>` |
| `**tebal**` | `<strong>` |
| `*miring*` | `<em>` |
| `` `kode` `` | `<code>` |
| `[teks](/alamat)` | `<a href>` |

Yang ditolak: judul selain `##`, tabel, blok kode berpagar, dan HTML mentah.
Kalau salah satunya benar benar dibutuhkan, tambahkan dukungannya di
`tools/markah.py` beserta ujinya, jangan menyiasatinya lewat HTML mentah.

### Gambar dan video

Alamatnya **wajib** menunjuk berkas yang diunggah ke situs ini, yaitu diawali
`/unggahan/` atau `/assets/img/`. Gambar dari server orang lain ditolak
dengan galat, dan itu bukan kerewelan:

- Tiap pembaca yang membuka tulisannya mengirimkan alamat IP-nya ke server itu
  tanpa pernah diminta.
- Gambarnya hilang pada hari pemiliknya merapikan berkasnya.
- `Content-Security-Policy` situs ini memang sudah menolaknya, jadi yang
  terbit kotak kosong. Ditolak saat menulis berarti Anda tahu sekarang, bukan
  sesudah halamannya terbit.

Ukuran gambarnya dititipkan di nama berkasnya, misalnya
`9f3c1a7b2d4e5f60-1600x900.webp`. Yang menuliskannya mesin pengunggah, bukan
orang. Dari situ pembangkit halaman tahu lebar dan tingginya tanpa membuka
berkasnya, sehingga tulisan di bawah gambar tidak melompat saat gambarnya
tiba. Video tidak diukur: mengukurnya menuntut ffmpeg, dan menebaknya berarti
menuliskan angka yang tidak pernah diukur.

Keterangannya merangkap teks alternatif. Keterangan kosong, yaitu `![]( ... )`
tanpa isi di dalam kurung siku, terbit dengan `alt=""`, yang berarti "ini
hiasan". Itu pernyataan yang sah, dan lebih jujur daripada `alt` yang diisi
nama berkas.

**Gambar yang sama harus disebut di kedua bahasa.** Keterangannya boleh, dan
memang harus, berbeda; berkasnya tidak. Pembangkitnya berhenti kalau keduanya
menunjuk berkas berbeda.

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
3. Isinya Markdown, dengan **bilah format** di atasnya: tebal, miring, judul
   bagian, kutipan, daftar butir, daftar bernomor, kode, dan tautan.
   Pintasannya sama dengan yang sudah Anda hafal: Ctrl+B, Ctrl+I, Ctrl+K.
   Menekan tombol daftar dua kali mencabut tandanya lagi.
4. **Foto / video** membuka pustaka berkas. Seret berkasnya ke sana atau pilih
   dari komputer, lalu klik gambarnya untuk menyisipkannya. Ia masuk ke
   **kedua** bahasa sekaligus, sebab dua bahasa wajib sebangun blok demi blok.
5. Di bawahnya penghitung blok tiap bahasa dan pratinjau. Kalau jumlah bloknya
   tidak sama, peringatannya muncul **sebelum** Anda menekan Simpan.
6. **Simpan.** Statusnya draf. Belum terlihat siapa pun.
7. **Terbitkan.** Statusnya berubah, dan tulisannya muncul di jalur publik API.
8. Selagi dashboard masih menyala, bangkitkan halamannya lalu dorong:

```bash
python tools/bangun_tulisan.py --sumber api
```

lalu `python tools/build_feed.py`, `python -m pytest`, `git add content blog
sitemap.xml feed.xml`, `git commit`, `git push`.

Perintah pertama tidak membangun halaman langsung dari basis data. Ia menulis
tiap tulisan terbit menjadi `content/blog/SLUG.md`, menyalin foto dan video
yang disebutnya ke `content/unggahan/`, lalu membangun dari berkas seperti
biasa. Sampai 29 September 2026 ia membangun langsung dari basis data, dan
akibatnya dua: CI, yang memeriksa halaman terhadap `content/blog`, akan merah
begitu tulisan dashboard pertama di-push, dan pembangunan berikutnya dari
`content/` diam diam menghapus tulisan itu dari daftar blog.

Tulisan yang dikelola lewat dashboard disunting di dashboard. Menyunting
berkas `.md`-nya dengan tangan akan tertimpa ekspor berikutnya. Tulisan di
`content/blog` yang tidak ada di dashboard dibiarkan, tidak dihapus.

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

### Pratinjaunya dibangun server

Sampai 18 September 2026 tiap dashboard punya pengurai Markdown kecilnya
sendiri di peramban, dan pratinjaunya dirakit dengan `createElement`. Itu
aman, dan tetap salah: dua pengurai untuk satu bahasa markah akan berpisah,
dan yang berpisah diam diam membuat layar pratinjau berbohong. Pratinjau yang
menerima apa yang Simpan tolak lebih buruk daripada tidak ada pratinjau.

Sekarang keduanya memanggil `POST /api/v1/admin/pratinjau`, yang menjalankan
`tools/bangun_tulisan.badan()`, yaitu fungsi yang sama persis yang membangun
halaman blog yang sudah terbit. Kalau pratinjaunya berhasil, yang terbit akan
sama; kalau ia menolak, Simpan akan menolak dengan kalimat yang sama.

HTML jawabannya dipasang dengan `innerHTML`, dan itu aman justru karena
sumbernya: ia dibangun `tools/markah.py`, yang meng-escape seluruh teks,
menolak HTML mentah dengan galat, dan menolak skema tautan selain `http`,
`https`, dan `mailto`. Membersihkannya lagi di peramban berarti dua aturan
untuk satu hal, dan dua aturan akan berpisah. Yang tetap ditulis sebagai teks:
kalimat penolakannya, sebab ia memuat potongan baris yang baru saja diketik.

## Mengunggah foto dan video

Ada di kedua dashboard, di balik tombol **Foto / video** pada bilah format.

| | |
| --- | --- |
| Diterima | PNG, JPEG, WebP, GIF, AVIF, MP4, WebM |
| Batas | foto 10 MB, video 80 MB |
| Tersimpan di | folder `UNGGAHAN_DIR`, bawaannya `unggahan/` di akar repositori |
| Dilayani di | `/unggahan/<nama>` |
| Di basis data | hanya catatannya, tabel `berkas`. Berkasnya di cakram |

**Jenisnya ditentukan dari isi berkasnya, bukan dari namanya dan bukan dari
`Content-Type` kirimannya.** Keduanya datang dari pengirim, jadi keduanya bisa
berbunyi apa saja. Berkas HTML bernama `foto.jpg` yang diterima lalu disajikan
lagi dari alamat situs ini adalah skrip milik pengirimnya yang jalan di atas
asal situs ini.

Nama di cakram tidak pernah datang dari pengunggahnya. Yang dipakai nama acak
enam belas heksa, ditambah ukuran gambarnya, ditambah akhiran yang ditentukan
dari bita pertama berkasnya. Nama aslinya tetap dicatat supaya Anda mengenali
berkasnya lagi, dan ia tidak pernah dipakai membentuk jalur.

Berkas dengan isi yang sama persis tidak digandakan. Yang dikembalikan yang
lama, dan layarnya mengatakan begitu.

Menghapus berkas yang masih disebut sebuah tulisan **ditolak** dengan 409,
beserta slug tulisannya. Menghapusnya adalah kegagalan yang tidak bersuara:
tulisannya tetap terbit, hanya gambarnya jadi kotak kosong, dan yang
menyadarinya pembaca.

### Yang TIDAK dikerjakan, dan perlu Anda tahu

- **Metadata EXIF tidak dibuang.** Foto dari ponsel bisa membawa koordinat
  tempat pemotretannya, dan koordinat itu ikut terbit. Kalimat ini ada di
  layar unggahnya, bukan hanya di sini. Buang dulu di ponsel kalau tempatnya
  bukan untuk umum.
- **Tidak ada pengubahan ukuran atau pemampatan.** Foto delapan megabita akan
  terbit sebagai foto delapan megabita.
- **Tidak ada pemindaian malware.** Berkas yang lolos bentuknya tetap bisa
  berisi apa saja di dalamnya.

### Dua port, dan batas yang jujur di antaranya

Yang ditulis lewat dashboard hidup di PostgreSQL dan dilayani API. Yang terbit
ke Cloudflare berkas statis, dan sejak 29 September 2026 fotonya ikut ke sana
dengan sendirinya: `bangun_tulisan.py --sumber api` menyalin tiap berkas yang
disebut tulisan terbit ke `content/unggahan/`, yang ikut git, dan
`bangun_situs.sh` menaruhnya di `/unggahan/` situs. Alamatnya tidak diubah,
jadi halaman yang sama benar di Cloudflare maupun di VPS kelak.

- Hanya berkas yang **disebut tulisan terbit** yang ikut. Draf dan unggahan
  yang belum dipakai tetap di laptop.
- Berkas yang tidak lagi disebut tulisan mana pun dibuang dari
  `content/unggahan/` saat membangun. Aslinya tetap di folder unggahan
  laptop dan di cadangannya.
- **Batasnya 25 MB per berkas.** Cloudflare menolak berkas statis yang lebih
  besar, jadi ekspor berhenti dengan nama berkas dan tulisannya. Perkecil
  videonya lalu unggah ulang. Batas unggah dashboard sendiri 80 MB; video di
  atas 25 MB baru bisa terbit kalau situsnya disajikan VPS.
- `bangun_tulisan.py --periksa`, yang dijalankan CI, menolak tulisan yang
  menyebut berkas yang tidak ada di `content/unggahan/`, dan berkas di sana
  yang tidak disebut siapa pun. `tests/test_ekspor_tulisan.py` menahannya.
