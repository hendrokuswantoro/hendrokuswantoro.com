# hendrokuswantoro.com

Situs pribadi Hendro Kuswantoro. HTML, CSS, dan JavaScript biasa, tanpa build
step dan tanpa dependensi. Empat menu: Home, About, Project, Blog.

- Gaya antarmuka mengikuti aplikasi Gojek: warna rata tanpa gradasi, kartu
  bersudut besar, tombol pil, kisi ikon layanan, dan tab bar di bawah layar
  pada ponsel.
- Bahasanya sengaja sederhana. Kalimat pendek, kata sehari-hari, tanpa
  istilah teknis yang tidak perlu.
- Warna utama hijau Gojek `#00aa13`. Catatan: dokumen spesifikasi awal
  menyebut Deep Cobalt Blue, lalu diganti hijau atas permintaan pemilik pada
  11 September 2026. Kalau suatu saat kembali ke biru, yang diubah cukup blok
  `:root` di `assets/css/style.css` ditambah warna di dua berkas `tools/`.
- Tipografi Google Fonts: **Inter** untuk teks, **Outfit** untuk wordmark dan
  angka besar.
- Dwibahasa Inggris dan Indonesia lewat tombol EN/ID.
- **Tidak ada bagian kontak.** Ini disengaja. Tidak ada alamat surel, formulir,
  maupun nomor di seluruh halaman.

## Warna dan kontras

Hijau Gojek terang bagus untuk bidang besar, tetapi terlalu terang untuk
menyangga teks putih berukuran biasa. Karena itu ada tiga nada, dan masing
masing punya tugas sendiri. Angkanya dihitung terhadap putih.

| Token | Nilai | Kontras | Dipakai untuk |
| --- | --- | --- | --- |
| `--brand` | `#00aa13` | 3,11:1 | bidang besar, ikon, garis, keadaan aktif |
| `--brand-btn` | `#008a10` | 4,52:1 | tombol yang memuat teks putih |
| `--brand-ink` | `#00730d` | 6,07:1 | teks dan tautan hijau di atas putih |

Ambang WCAG AA adalah 4,5:1 untuk teks biasa dan 3,0:1 untuk grafis.
**Jangan menaruh teks putih berukuran biasa di atas `--brand`.** Pakai
`--brand-btn`. Kalau warnanya diganti, hitung ulang ketiganya.

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

### Gambar dan ikon

Gambar pratayang media sosial dan ikon aplikasi dibangkitkan dari kode:

```bash
python tools/build_og.py
python tools/build_icons.py
```

Warna di kedua berkas itu harus sama dengan `assets/css/style.css`.

## Menerbitkan ke https://www.hendrokuswantoro.com

Tidak ada proses build, jadi cukup unggah isi folder ini apa adanya.

**Cloudflare Pages (disarankan).** Dorong folder ini ke repositori Git, buat
project baru, build command dikosongkan, output directory diisi `/`. Lalu di
**Custom domains** tambahkan `www.hendrokuswantoro.com`, dan arahkan
`hendrokuswantoro.com` ke www. Berkas `_headers` otomatis terbaca.

**Netlify.** Sama persis: publish directory `.`, tanpa build command.

**GitHub Pages.** Berkas `CNAME` sudah berisi domainnya. Aktifkan Pages dari
cabang `main` folder root. Perlu dicatat, GitHub Pages tidak membaca
`_headers`, jadi tajuk keamanannya tidak ikut terpasang.

DNS: `www` sebagai CNAME ke host yang diberikan penyedia, dan `@` diarahkan
ke `www` memakai ALIAS, ANAME, atau A sesuai penyedia.

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
