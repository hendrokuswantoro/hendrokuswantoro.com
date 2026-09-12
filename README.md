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
- Halaman Proyek memuat peta karya, MapLibre di atas ubin vektor Mapbox
  Streets, yang dimuat sendiri begitu bagian petanya mendekati layar. Tidak
  ada tombol yang harus ditekan.

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

**Satu peta dasar, Mapbox.** Gayanya ditulis sendiri di berkas itu, bukan
diambil dari URL gaya Mapbox. Gaya Mapbox menunjuk sumbernya dengan alamat
`mapbox://` yang tidak bisa dibaca MapLibre, sedangkan versi rasternya tidak
membawa tinggi bangunan sama sekali. Itulah sebabnya bangunan 3D dulu tidak
pernah muncul. Membaca ubin vektornya langsung menyelesaikan keduanya.

**Bangunan 3D sungguhan.** Lapisan `building` pada Mapbox Streets menyimpan
tinggi tiap bangunan, jadi tombol 3D menegakkan bangunan dengan tinggi
aslinya, bukan tinggi tebakan. Di Jakarta terhitung 4.950 bangunan tergambar
dengan menara tertinggi 383 meter.

**Apa saja yang digambar.** Gayanya punya 31 lapisan, disusun begini:

| Kelompok | Lapisan | Muncul mulai zoom |
| --- | --- | --- |
| Dasar | latar, bayangan bukit, ruang hijau, air, sungai | 0 |
| Batas | kabupaten, provinsi, negara | 5, 0, 0 |
| Jalan | tol dan jalan nasional, arteri, tertiary, jalan kecil, masing-masing garis tepi lalu isinya | 4, 7, 10, 12 |
| Lain | apron dan landasan bandara, rel kereta beserta palangnya | 10, 11 |
| Bangunan | tapak 2D, dan `gedung3d` yang menggantikannya saat tombol 3D ditekan | 14 |
| Tanda | panah arah jalan satu arah, titik POI | 15, 15,5 |
| Nama | alam, kelurahan, kota, jalan, provinsi, negara, POI | 3 sampai 15,5 |

Empat tingkat jalan dibedakan warnanya seperti peta pengemudi: kuning amber
untuk tol dan jalan nasional, krem hangat untuk arteri, putih untuk sisanya.
Tanahnya sengaja digelapkan sedikit ke `#e8ecf1`, sebab dengan latar yang
lebih terang jalan putihnya menyatu dengan tanah dan jaringannya tidak
terbaca.

**Urutan lapisan nama itu disengaja.** MapLibre menempatkan simbol dari
tumpukan paling atas ke bawah, jadi lapisan yang ditulis paling akhir yang
menang saat berebut tempat. Karena itu namanya disusun dari yang paling kecil
ke yang paling besar. Sebelum diurutkan begitu, 959 label permukiman pada zoom
4 menutup nama negara sampai tidak satu pun tergambar. Jumlah permukiman juga
disaring memakai `filterrank` bawaan Mapbox seiring peta ditarik menjauh.

**Nama provinsi dibawa sendiri.** Lapisan `place_label` Mapbox punya kelas
`state`, tetapi untuk Indonesia isinya kosong, sudah diperiksa dari zoom 4
sampai 9 (negara bagian Australia muncul, provinsi Indonesia tidak). Karena
itu 38 nama provinsi ditulis di `PROVINSI_ID` di dalam `peta.js`.
**Koordinatnya adalah titik untuk menggantungkan label, bukan titik pusat
resmi dan bukan batas.** Garis batasnya sendiri tetap datang dari lapisan
`admin` Mapbox.

**Panah satu arah tidak ikut antre.** Lapisannya disetel
`text-allow-overlap` dan `text-ignore-placement`, jadi panahnya tidak pernah
mengambil tempat yang sedang diperebutkan nama jalan.

**Relief dan bayangan bukit.** Peta memakai DEM Mapbox untuk relief 3D dan
lapisan hillshade yang tetap terlihat di tampilan 2D.

**Jelajah.** Tombol Jelajah menerbangkan peta dari satu karya ke karya
berikutnya tiap tujuh detik, dan berhenti begitu tangan menyentuh peta.
Mengklik penanda juga menerbangkan peta ke karya itu pada perbesaran 15.

**Legendanya dinamis.** Angkanya menghitung penanda yang benar benar berada di
dalam layar saat itu dan berubah selama peta digeser. Ada baris ringkasan yang
menyebut apa saja yang sedang terlihat. Klik satu baris untuk menyaring satu
jenis karya.

**Panelnya bisa dilipat**, dan pilihan itu disimpan di `localStorage`.

**Tombol rumah** mengembalikan tampilan seperti saat peta pertama dibuka.

**Chrome petanya selalu terang.** Bilah skala, kredit, dan tombol kontrol tidak
ikut tema gelap, sebab peta dasarnya selalu terang.

Tanpa token Mapbox, peta jatuh ke OpenFreeMap tanpa kunci dan tetap jalan,
tetapi yang hilang bukan cuma bangunan 3D: batas provinsi dan kabupaten,
tingkatan jalan, nama jalan, nama tempat, rel, dan titik POI semuanya dibaca
dari ubin vektor Mapbox Streets, jadi ketiganya ikut hilang bersamaan.

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

## Pengujian dan CI

```bash
pip install -r tests/requirements.txt
python -m pytest
```

140 uji, jalannya di bawah satu detik, tanpa peramban dan tanpa jaringan.
Rinciannya di [docs/pengujian.md](docs/pengujian.md).

Tiap `git push` ke `main` menjalankan `.github/workflows/ci.yml`:

```
Lint -> Type Check -> Test -> Security Scan -> Build
```

Deploy sengaja tidak ada di pipeline itu. Cloudflare membangun dan
menerbitkan sendiri ketika `main` bergerak, jadi menaruh deploy kedua di
GitHub Actions berarti memberi situs ini dua tuan. Yang dikerjakan pipeline
itu adalah menolak membiarkan sebuah push sampai ke sana dalam keadaan rusak
tanpa ketahuan.

`Type Check` menjalankan `tsc --noEmit` pada port Next.js di runner GitHub.
Itu satu satunya tempat port kedua pernah diperiksa, sebab mesin tempat situs
ini ditulis tidak punya Node.

Health Check terpisah di `.github/workflows/kesehatan.yml`, jalan tiap hari
dan sesudah CI. Isinya memeriksa situs yang sudah terbit, bukan salinan
kerja: sepuluh halaman menjawab 200, halaman yang tidak ada menjawab 404,
kelima header keamanan masih terkirim, umpan RSS terbaca, dan token petanya
benar benar sampai. Alamat yang diperiksa diambil dari variabel repositori
`SITUS`, jadi bisa pindah ke domain asli tanpa menyunting berkasnya.

## Dokumentasi

- [docs/arsitektur.md](docs/arsitektur.md) - bentuk sistemnya, dan kenapa
  tidak ada basis data
- [docs/pengujian.md](docs/pengujian.md) - apa yang dijaga tiap uji
- [docs/pemecahan-masalah.md](docs/pemecahan-masalah.md) - yang sudah pernah
  rusak, sebabnya, dan cara mengenalinya lagi

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
tools/build_feed.py        pembangkit feed.xml, membaca berkas di blog/
tools/bangun_situs.sh      pembangun dist/, dipakai Cloudflare saat build
tools/konfigurasi.sh       penulis token dari MAPBOX_TOKEN, dipanggil di atas
assets/js/peta.js          peta karya, 31 lapisan di atas ubin vektor Mapbox
assets/vendor/maplibre/    MapLibre GL JS, disimpan sendiri, bukan dari CDN
tests/                     140 uji, tanpa peramban dan tanpa jaringan
docs/                      arsitektur, panduan uji, pemecahan masalah
.github/workflows/ci.yml   lint, type check, test, security scan, build
.github/workflows/kesehatan.yml  health check terhadap situs yang sudah terbit
wrangler.toml              menunjuk ./dist, dibaca alur Workers
robots.txt                 mengizinkan perayap, menunjuk ke sitemap
sitemap.xml                tujuh alamat, termasuk tiap tulisan blog
feed.xml                   umpan RSS, dibangkitkan, jangan disunting tangan
site.webmanifest           nama, warna, ikon untuk pemasangan di ponsel
_headers                   tajuk keamanan dan cache, dibaca Workers dan Pages
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
7. Tambahkan judul tulisan baru ke blok `rail__lain` di tiap tulisan lain,
   dan salin blok `<aside class="rail">` ke tulisan yang baru. Daftar isinya
   tidak perlu ditulis: `app.js` menyusunnya sendiri dari `<h2>` yang ada.
8. Jalankan `python tools/build_feed.py` supaya `feed.xml` ikut terbarui.

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

Repositori git-nya sudah ada di folder ini. Dorong ke GitHub, lalu di
Cloudflare pilih **Connect to Git** dan arahkan ke repositori itu.

Ada dua alur di Cloudflare, dan keduanya sudah disiapkan.

**Alur Workers yang baru** membaca `wrangler.toml` di akar repositori. Berkas
itu sudah ada, isinya cuma menunjuk `./dist` sebagai folder yang disajikan.
Tanpa berkas itu, alur ini berhenti dengan pesan *There was a problem parsing
the Wrangler configuration file*.

**Alur Pages yang lama** tidak membaca `wrangler.toml` sama sekali, cukup diisi
manual. Masuk lewat tautan **Continue to Pages**.

Isiannya sama untuk keduanya:

| Isian | Nilai |
| --- | --- |
| Framework preset | None |
| Build command | `sh tools/bangun_situs.sh` |
| Build output directory | `dist` |
| Environment variable | `MAPBOX_TOKEN` = token `pk.` Anda |

`tools/bangun_situs.sh` mengerjakan dua hal: menulis tokennya lewat
`tools/konfigurasi.sh`, lalu menyalin hanya berkas yang pantas disajikan ke
`dist/`. README, `tools/`, dan versi Next.js tidak ikut, sama persis dengan
isi zip yang dibuat `tools/build_dist.py`. Keduanya menghasilkan 34 berkas.

**Kenapa ada build command padahal situsnya statis.** Token Mapbox disimpan di
`assets/js/konfigurasi.js`, dan berkas itu tidak pernah ikut di-commit, lihat
`.gitignore`. Jadi salinan yang ada di GitHub tidak punya token, dan tanpa
token peta jatuh ke OpenFreeMap. `tools/konfigurasi.sh` menulis berkas itu
saat build dari variabel lingkungan `MAPBOX_TOKEN`, sehingga tokennya cukup
disimpan sekali di Cloudflare dan repositorinya boleh publik.

Kalau variabelnya lupa diisi, build-nya tetap berhasil dan situsnya tetap
terbit, hanya petanya yang turun ke OpenFreeMap. Cari baris
`konfigurasi.sh: MAPBOX_TOKEN is not set` di log build.

Untuk versi Next.js, root directory diisi `next`, build command
`npm run build`, output `out`, dan variabelnya bernama
`NEXT_PUBLIC_MAPBOX_TOKEN`.

### Mendorong ke GitHub pertama kali

Buat repositori kosong di <https://github.com/new>, tanpa README, tanpa
`.gitignore`, tanpa lisensi. Lalu dari folder ini:

```bash
git remote add origin https://github.com/hendrokuswantoro/NAMA-REPO.git
git push -u origin main
```

Git akan meminta izin lewat peramban sekali saja. Sesudah itu tiap perubahan
cukup `git push`.

### Memasang domainnya

1. Di proyek Pages, buka **Custom domains**, tekan **Set up a custom domain**.
2. Masukkan `www.hendrokuswantoro.com`, lalu ulangi untuk
   `hendrokuswantoro.com`.
3. Kalau domainnya sudah berada di akun Cloudflare yang sama, catatan DNS-nya
   dibuat otomatis. Kalau belum, pindahkan dulu nameserver domainnya ke
   Cloudflare, atau tambahkan CNAME `www` ke alamat `.pages.dev` di penyedia
   DNS yang sekarang.
4. Pengalihan dari tanpa www ke dengan www **tidak** memakai berkas
   `_redirects`. Berkas itu dulu ada dan sudah dihapus: Cloudflare Workers
   menolaknya dengan `Only relative URLs are allowed [code: 100324]`, sebab
   di Workers `_redirects` hanya boleh memuat jalur relatif, tidak boleh
   pindah host. Yang dipakai sekarang adalah **Redirect Rule** di dashboard,
   yang jalan di Workers maupun Pages:

   Dashboard domain `hendrokuswantoro.com` → **Rules** → **Redirect Rules** →
   **Create rule**. Kondisinya `Hostname` `equals` `hendrokuswantoro.com`,
   lalu **Dynamic redirect** ke
   `concat("https://www.hendrokuswantoro.com", http.request.uri.path)`
   dengan status **301** dan **Preserve query string** dinyalakan.

Berkas `_headers` ikut terbaca otomatis, termasuk Content Security Policy dan
HSTS. Sertifikat TLS diterbitkan Cloudflare sendiri.

## Sesudah terbit, periksa ini

- [ ] `https://www.hendrokuswantoro.com` tampil dan `http://` dialihkan ke `https://`
- [ ] `hendrokuswantoro.com` tanpa www dialihkan ke dengan www
- [ ] Empat menu jalan di ponsel dan desktop, termasuk `/blog/`
- [ ] Tombol EN/ID mengubah seluruh teks dan pilihannya bertahan saat halaman dimuat ulang
- [ ] Filter di halaman Project menyaring kartu dengan benar
- [ ] `/sitemap.xml`, `/robots.txt` dan `/feed.xml` dapat dibuka
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
