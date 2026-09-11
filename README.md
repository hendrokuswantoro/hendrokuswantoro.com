# hendrokuswantoro.com

Situs pribadi Hendro Kuswantoro. HTML, CSS, dan JavaScript biasa, tanpa build
step dan tanpa dependensi. Empat menu: Home, About, Project, Blog.

- Tata letaknya mengikuti pola aplikasi Gojek: kartu, tombol pil, kisi ikon
  layanan, dan tab bar di bawah layar pada ponsel.
- **Warnanya mengikuti aplikasi Uber**: hitam, putih, abu abu, dengan satu
  aksen biru `#276ef1` untuk tautan dan keadaan aktif.
- **Hurufnya Poppins**, pengganti paling dekat untuk huruf Gojek yang memang
  tidak dilisensikan untuk umum.
- Bahasanya sengaja sederhana. Kalimat pendek, tanpa tanda strip dan titik dua.
- Dwibahasa Inggris dan Indonesia lewat tombol EN/ID.
- **Tidak ada bagian kontak.** Ini disengaja.
- Halaman Proyek memuat peta karya, MapLibre dengan ubin OpenFreeMap, yang
  baru dimuat setelah tombolnya ditekan.

## Warna dan kontras

Semua diukur terhadap putih. Ambang WCAG AA adalah 4,5:1 untuk teks biasa dan
3,0:1 untuk grafis.

Halamannya berlatar abu abu dan kartunya putih, supaya kartu terangkat dari
latar dan layar tidak menyilaukan.

| Token | Terang | Gelap | Dipakai untuk |
| --- | --- | --- | --- |
| `--bg` | `#f2f3f5` | `#17181a` | latar halaman |
| `--card` | `#ffffff` | `#1f2124` | kartu, panel, tombol putih |
| `--surface` | `#e9ebee` | `#202225` | pita seksi |
| `--ink` | `#000000` | `#f5f5f5` | judul dan tombol |
| `--ink-2` | `#4a4a4a` | `#c7c7c7` | teks isi |
| `--ink-3` | `#6b6b6b` | `#9a9a9a` | keterangan |
| `--accent` | `#276ef1` | `#6f9dff` | tautan dan keadaan aktif |

Kontras teks isi terhadap latarnya 8,0:1 pada tema terang dan 10,6:1 pada tema
gelap, keduanya di atas ambang WCAG AA.

## Mode gelap

Situs mengikuti setelan sistem pembaca lewat `prefers-color-scheme`, tanpa
tombol tambahan di sebelah tombol bahasa. Seluruh warna diambil dari token di
`:root`, jadi tema gelap hanya menimpa token, bukan menulis ulang aturan.

Kontras pada tema gelap, diukur terhadap `#0b0b0b`: teks isi 11,6:1, judul
18:1, tombol 19,7:1, keterangan 7:1. Semuanya lolos WCAG AA.

Dua hal sengaja tidak ikut berbalik. Panel ajakan tetap gelap dengan teks
putih di kedua tema, dan penanda di peta tetap hitam bergaris putih, sebab
peta dasarnya selalu terang.

## Peta karya

`assets/js/peta.js` menggambar tujuh titik karya di peta Indonesia. Pustaka
MapLibre disimpan sendiri di `assets/vendor/maplibre/`, bukan dari CDN, dan
baru diunduh ketika bagian petanya mendekati layar.

**Tiga peta dasar.** Peta memakai OpenFreeMap, gratis tanpa kunci. Satelit dan
Mapbox memakai ubin Mapbox bila tokennya ada. Tanpa token, pilihan Mapbox
disembunyikan dan Satelit jatuh ke citra Esri yang juga tanpa kunci.

**2D dan 3D.** Tombol 3D memiringkan kamera dan menyalakan relief sungguhan
dari ubin ketinggian terrarium milik AWS Open Data, gratis tanpa kunci.
Gedung ikut ditegakkan pada perbesaran tinggi bila peta dasarnya memuat tinggi
bangunan. Sumber relief hidup terpisah dari gaya peta, jadi 3D tetap menyala
waktu peta dasarnya diganti.

**Legendanya dinamis.** Angkanya menghitung penanda yang benar benar berada di
dalam layar saat itu dan berubah tiap kali peta digeser. Klik satu baris untuk
menyaring satu jenis karya, klik lagi untuk kembali.

Titik titiknya penanda lokasi, bukan batas wilayah kajian, dan itu ditulis di
bawah petanya.

### Token Mapbox

Token ada di `assets/js/konfigurasi.js`, yang **tidak ikut masuk git**.
Contohnya ada di `konfigurasi.contoh.js`. Token `pk.` memang dirancang tampil
di sumber halaman, tetapi tetap batasi pemakaiannya: di console.mapbox.com,
bagian Tokens, isi URL restriction dengan `https://www.hendrokuswantoro.com/*`
supaya kuota Anda tidak dipakai situs lain.

Kalau berkas itu hilang atau tokennya kosong, petanya tetap jalan dengan
sumber yang tidak butuh kunci.

Berkas `_headers` memuat pengecualian yang diperlukan peta: alamat
OpenFreeMap di `img-src` dan `connect-src`, serta `worker-src blob:` karena
MapLibre membuat pekerjanya sendiri saat berjalan. **Uji perubahan aturan itu
dengan menyajikan situs beserta tajuknya**, jangan hanya dengan `python -m
http.server`, sebab galat CSP tidak muncul tanpa tajuk aslinya.

## Menjalankan secara lokal

Situs ini memakai jalur absolut (`/assets/...`), jadi bukalah lewat server
kecil, bukan klik ganda berkasnya.

```bash
cd "D:/Projects/personal web"
python -m http.server 8080
```

Lalu buka `http://localhost:8080`.

## Susunan berkas

```
index.html                 Home
about.html                 About
project.html               Project
blog/index.html            daftar tulisan
blog/*.html                tulisan blog, satu berkas satu tulisan
404.html                   halaman tidak ditemukan
assets/css/style.css       seluruh gaya, token warna ada di :root
assets/js/app.js           bahasa, filter proyek, header, animasi, tahun hak cipta
assets/img/                favicon, ikon aplikasi, gambar pratayang
tools/build_og.py          pembangkit assets/img/og-cover.png
tools/build_icons.py       pembangkit ikon PNG
robots.txt                 mengizinkan perayap, menunjuk ke sitemap
sitemap.xml                tujuh alamat, termasuk tiap tulisan blog
site.webmanifest           nama, warna, ikon untuk pemasangan di ponsel
_headers                   tajuk keamanan dan cache untuk Cloudflare Pages / Netlify
CNAME                      domain untuk GitHub Pages
```

## Mengubah isi

Seluruh teks ada langsung di dalam berkas HTML. Tidak ada CMS dan tidak ada
berkas data terpisah, jadi yang Anda sunting adalah yang tampil.

### Dwibahasa

Teks Inggris ditulis sebagai isi elemen, terjemahan Indonesianya menumpang di
atribut `data-ind` pada elemen yang sama:

```html
<h2 data-ind="Tiga yang terbaru">Three recent ones</h2>
```

Mesin pencari tetap membaca teks sungguhan, bukan halaman kosong yang diisi
JavaScript. Saat pengunjung menekan ID, `app.js` menukar isinya dan menyimpan
pilihannya di `localStorage`. Pengunjung berbahasa Indonesia mendapat versi ID
otomatis pada kunjungan pertama.

Untuk teks pada atribut seperti `aria-label`, pakai `data-ind-label`.

**Elemen tanpa `data-ind` tidak akan pernah berubah bahasa.**

### Menulis tulisan blog baru

1. Salin salah satu berkas di `blog/`, misalnya `blog/kapan-peta-diam.html`,
   beri nama baru memakai tanda hubung, tanpa spasi.
2. Ganti isi `<title>`, `<meta name="description">`, `<link rel="canonical">`,
   seluruh tag `og:` dan `twitter:`, serta blok `application/ld+json` di
   bagian kepala. Tiga tempat memuat alamat halamannya, jangan ada yang
   tertinggal.
3. Ganti tanggal di dua tempat: `datePublished` pada blok JSON dan
   `<time datetime="...">` di badan tulisan.
4. Tulis isinya. Satu `<h2>` per bagian, `<blockquote>` untuk kalimat yang
   ingin ditonjolkan.
5. Tambahkan satu kartu `<a class="post">` di `blog/index.html`, paling atas,
   supaya yang terbaru ada di urutan pertama.
6. Tambahkan satu baris `<url>` di `sitemap.xml`.

Gaya bahasanya jaga tetap sederhana: kalimat pendek, kata sehari-hari,
satu gagasan per paragraf.

### Gambar karya

Gambar di kartu proyek dibangkitkan dari peta asli di `D:/Projects/Portfolio Kerja`,
yang berukuran 0,4 sampai 4,7 MB per berkas. Terlalu berat untuk peramban, jadi:

```bash
python tools/build_work_images.py
```

Hasilnya `assets/img/work/*.webp`, masing masing sekitar 40 KB, dengan seluruh
lembar peta tetap terlihat utuh. Tidak ada yang dipotong, sebab peta yang
legendanya terpotong sudah jadi dokumen lain. Kalau ada karya baru, tambahkan
satu baris di kamus `WORK` dalam berkas itu.

### Gambar dan ikon

Gambar pratayang media sosial dan ikon aplikasi dibangkitkan dari kode:

```bash
python tools/build_og.py
python tools/build_icons.py
```

Warna di kedua berkas itu harus sama dengan `assets/css/style.css`.

## Menerbitkan ke Cloudflare Pages

Situs ini tidak punya proses build, jadi yang diunggah adalah berkasnya apa
adanya. Ada dua jalan.

### A. Unggah langsung, paling cepat, tanpa GitHub

`dist-hendrokuswantoro.zip` di folder ini berisi 21 berkas yang perlu
disajikan, tanpa README, tanpa `tools/`, tanpa folder `next/`. Bangkitkan
ulang kapan saja dengan `python tools/build_dist.py`.

1. Buka `dash.cloudflare.com`, pilih **Workers & Pages**, lalu **Create**.
2. Pindah ke tab **Pages**, pilih **Upload assets**.
3. Beri nama proyek, misalnya `hendrokuswantoro`, lalu seret berkas zip itu
   ke kotak unggahan. Cloudflare membongkarnya sendiri.
4. Tekan **Deploy site**. Beberapa detik kemudian situsnya hidup di alamat
   `nama-proyek.pages.dev`.

### B. Lewat Git, supaya tiap perubahan terbit sendiri

Repositori git-nya sudah ada di folder ini, tinggal didorong ke GitHub atau
GitLab, lalu di Cloudflare pilih **Connect to Git**. Build command dikosongkan
dan build output directory diisi `/`. Untuk versi Next.js, root directory
diisi `next`, build command `npm run build`, dan output `out`.

### Memasang domainnya

1. Di proyek Pages, buka **Custom domains**, tekan **Set up a custom domain**.
2. Masukkan `www.hendrokuswantoro.com`, lalu ulangi untuk
   `hendrokuswantoro.com`.
3. Kalau domainnya sudah berada di akun Cloudflare yang sama, catatan DNS-nya
   dibuat otomatis. Kalau belum, pindahkan dulu nameserver domainnya ke
   Cloudflare, atau tambahkan CNAME `www` ke alamat `.pages.dev` di penyedia
   DNS yang sekarang.
4. Pengalihan dari tanpa www ke dengan www sudah disiapkan di berkas
   `_redirects`, dan baru aktif sesudah kedua domain terpasang.

Berkas `_headers` ikut terbaca otomatis, termasuk Content Security Policy dan
HSTS. Sertifikat TLS diterbitkan Cloudflare sendiri.

## Sesudah terbit, periksa ini

- [ ] `https://www.hendrokuswantoro.com` tampil dan `http://` dialihkan ke `https://`
- [ ] `hendrokuswantoro.com` tanpa www dialihkan ke dengan www
- [ ] Empat menu jalan di ponsel dan desktop, termasuk `/blog/`
- [ ] Tombol EN/ID mengubah seluruh teks dan pilihannya bertahan saat halaman dimuat ulang
- [ ] Filter di halaman Project menyaring kartu dengan benar
- [ ] `/sitemap.xml` dan `/robots.txt` dapat dibuka
- [ ] Pratayang tautan di WhatsApp atau LinkedIn menampilkan `og-cover.png`

## Yang sebaiknya Anda sunting sendiri

Isi situs disusun dari berkas proyek Anda di `D:/Projects`. Bagian berikut
adalah klaim tentang diri Anda, jadi mohon diperiksa:

1. Daftar keahlian dan perkakas di `about.html`. Isinya saya susun dari
   berkas proyek Anda, jadi tambah atau kurangi sesuai kenyataan.
2. Deskripsi enam proyek di `project.html`. Tidak ada nama klien, tanggal,
   maupun angka capaian, karena tidak dapat diverifikasi dari berkas yang ada.
3. Tiga tulisan blog beserta tanggalnya. Isinya saya susun dari cara kerja
   yang tampak pada proyek Anda, tetapi tulisan atas nama Anda sebaiknya
   Anda baca ulang dan akui sendiri kalimatnya.

## Dua versi dalam satu repositori

| Folder | Isi | Status |
| --- | --- | --- |
| akar repositori | HTML, CSS, JavaScript biasa | sudah teruji, siap terbit |
| `next/` | Next.js 15 + TypeScript, static export | ditulis lengkap, **belum pernah dibangun** karena Node.js belum terpasang |

Keduanya menghasilkan situs yang sama. Yang berbeda hanya cara membangunnya,
dan bentuk alamatnya: versi akar memakai `/about.html`, versi Next memakai
`/about/`. Pakai salah satu, jangan keduanya sekaligus, dan pasang pengalihan
alamat kalau suatu saat berpindah.

Petunjuk lengkap versi Next ada di `next/README.md`. Ringkasnya:

```bash
cd next
npm install
npm run typecheck
npm run build      # menghasilkan next/out/
```
