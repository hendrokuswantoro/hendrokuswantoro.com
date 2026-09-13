# Yang membuat situs ini ringan, dan yang sengaja tidak dikerjakan

Diukur 13 September 2026. Seluruh angka di sini keluar dari
`python -m pytest tests/test_performa.py -q -s -m peramban`, bukan dari
perkiraan, dan uji itu akan gagal kalau angkanya memburuk.

## Keadaan sekarang

| Halaman | Berat | Permintaan | Asal luar |
| --- | --- | --- | --- |
| `/` | 158 KB | 10 | tidak ada |
| `/about` | 113 KB | 7 | tidak ada |
| `/blog/` | 110 KB | 7 | tidak ada |
| `/blog/kapan-peta-diam` | 112 KB | 7 | tidak ada |
| `/project` | 1927 KB | 29 | ubin peta Mapbox |

Rincian beranda, semuanya dari asal sendiri:

| | KB |
| --- | --- |
| `style.css` | 47,8 |
| `app.js` | 21,7 |
| dokumen HTML | 20,5 |
| tiga gambar karya, 400w | 40,0 |
| empat berkas font Poppins | 31,9 |

## Dua hal yang dikerjakan

### 1. Poppins dibawa masuk

Sebelumnya font dipanggil dari `fonts.googleapis.com`. Yang dibayar untuk itu
ada tiga, dan hanya satu yang berupa bita:

1. **Dua asal tambahan di jalur render.** Peramban menyelesaikan DNS, TCP, dan
   TLS ke `fonts.googleapis.com`, menunggu sebuah stylesheet yang memblokir
   render, baru dari isinya tahu bahwa berkas fontnya ada di
   `fonts.gstatic.com`, lalu mengulang DNS, TCP, dan TLS ke sana. Dua jabat
   tangan dan satu perjalanan bolak balik tambahan sebelum huruf pertama boleh
   digambar.
2. **Bitanya tidak pernah terukur.** Resource Timing melaporkan
   `transferSize` nol untuk berkas dari asal lain yang tidak mengirim
   `Timing-Allow-Origin`, dan Google tidak mengirimnya. Jadi 32 KB font tidak
   pernah masuk anggaran performa sama sekali: selama berhari hari anggaran itu
   mengawasi halaman yang lebih ringan daripada yang benar benar dikirim.
3. **Setiap kunjungan memberi tahu pihak ketiga** alamat IP pembaca dan
   halaman yang sedang dibukanya. Itu tidak dibutuhkan untuk menggambar huruf.

Sekarang delapan berkas woff2 ada di `assets/fonts`, subset `latin` dan
`latin-ext` saja, empat tebal. Devanagari yang juga dibawa Poppins, sekitar
17 KB per tebal, tidak diambil: situs ini tidak memuat satu pun aksara itu.
Subset latin berjumlah 30,7 KB untuk empat tebal.

Tiga tebal yang dipakai di atas layar pertama, 400, 600, dan 700, dimuat awal
lewat `<link rel="preload">`. Tebal 500 tidak, sebab ia hanya dipakai label
`.tag` yang duduk di bawah layar. Alamat di `preload` **wajib sama persis**
dengan alamat di `@font-face`; selisih satu karakter membuat berkasnya diunduh
dua kali, dan hasilnya bukan lebih cepat melainkan dua kali lebih berat.
`tests/test_gaya.py` yang memeriksanya.

Nama berkasnya memuat nomor versi Google, misalnya
`poppins-v24-400-latin.woff2`. `/assets/*` disajikan dengan `immutable` selama
setahun, jadi berkas yang isinya berubah wajib berganti nama, atau pembaca
lama memegang versi basi sampai setahun ke depan.

CSP ikut menyempit: `style-src` tidak lagi menyebut `fonts.googleapis.com`,
dan `font-src` menjadi `'self'`. Dua asal yang dulu harus diizinkan sekarang
tidak diizinkan lagi.

Ongkosnya jujur: blok `@font-face` menambah 3,2 KB pada `style.css`, 0,4 KB
sesudah gzip. Halaman tanpa gambar seperti `/about` hanya membayar ongkos itu
dan tidak ikut menghemat bita, hanya menghemat dua jabat tangan. Itu sebabnya
`/about` naik di atas kertas.

`tools/ambil_font.py` yang mengunduh, mencatat sha256 tiap berkas di
`assets/fonts/sumber.json`, dan menulis blok `@font-face` di `style.css`.
`--periksa` membandingkan berkas yang ada dengan catatan itu **tanpa menyentuh
jaringan**, jadi CI tidak ikut bergantung pada Google untuk bisa lulus.
`--periksa --daring` menambahkan satu hal saja: tahu kalau Poppins naik versi.

Lisensinya OFL 1.1, yang menuntut salinan lisensi menyertai font yang
disebarkan. Salinannya ada di `assets/fonts/OFL.txt` dan ikut terbit.

### 2. Gambar karya punya tiga lebar

Sebelumnya satu berkas 800 px dipakai di semua tempat. Kotak kartunya diukur
di peramban pada dua puluh dua ukuran layar, dan hasilnya:

| Layar | Kotak di beranda | Kotak di halaman Proyek |
| --- | --- | --- |
| 390 px | 340 px | 340 px |
| 768 px | 348 px | 348 px |
| 1024 px | 310 px | 310 px |
| 1280 px | 390 px | 287 px |
| 1440 px ke atas | 443 px | 327 px |

Jadi berkas 800 px itu antara 1,8 dan 2,8 kali lebih lebar daripada yang bisa
ditampilkan layar berkerapatan 1. Sekarang ada 400, 600, dan 800, dan
`sizes` memberi tahu peramban selebar apa kotaknya sebelum tata letaknya ada.
Yang dipilih peramban, terukur: 400w di hampir semua tempat, 600w hanya pada
layar 1440 px ke atas di beranda, di mana kotaknya memang 443 px.

Beranda turun dari 114 KB gambar menjadi 40 KB.

Dua cara `sizes` bisa salah, dan keduanya tidak menimbulkan galat apa pun:
terlalu kecil membuat peramban mengambil berkas yang kurang lebar, yang hanya
terlihat di layar padat sebagai gambar sedikit kabur; terlalu besar membuat
berkas 800 px diunduh untuk kotak 289 px, dan seluruh guna `srcset` hilang.
Karena itu nilainya diturunkan dari pengukuran, bukan dikarang, dan diperiksa
kembali di peramban pada enam ukuran layar.

Yang **tidak** berubah: `src` tetap menunjuk berkas 800 px, jadi apa pun yang
tidak mengerti `srcset` tetap mendapat gambar yang benar.

## Empat hal yang diukur lalu tidak dikerjakan

Optimasi yang tidak terbukti berguna tetap menambah satu tempat lagi yang bisa
rusak. Keempat hal di bawah ini dihitung, dan angkanya tidak membenarkan
ongkosnya.

### Memecah CSS peta ke berkas sendiri

`style.css` memuat aturan peta yang hanya dipakai `/project`. Terukur:

- Aturan yang selektornya menyebut `maplibregl`, yaitu penimpa gaya vendor
  yang memang tidak berarti apa pun sebelum `maplibre-gl.css` dimuat:
  **2,1 KB mentah**, sekitar 0,6 KB sesudah gzip.
- Ditambah seluruh aturan `.peta*`: 9,7 KB mentah, sekitar 2,5 KB gzip.

Yang aman dipindahkan hanya yang pertama, dan 0,6 KB tidak sebanding dengan
satu permintaan HTTP tambahan. Yang kedua memuat `.peta__frame`, kotak yang
menentukan tinggi petanya; memindahkannya berarti kotak itu belum punya ukuran
saat halaman pertama digambar. Tidak dikerjakan.

### Meminifikasi CSS dan JavaScript

`style.css` 48,6 KB mentah menjadi 12,3 KB sesudah gzip; `app.js` 21,7 KB
menjadi 6,6 KB. Minifikasi memotong sekitar 30 persen sebelum kompresi dan
jauh lebih sedikit sesudahnya, sebab gzip sudah memakan spasi dan nama yang
berulang. Cloudflare mengompresi dengan brotli, yang lebih rapat lagi.
Gantinya: satu langkah bangun yang wajib jalan sebelum setiap terbit, dan
berkas terbit yang tidak lagi sama dengan berkas yang ditulis. Tidak
sebanding. Tidak dikerjakan.

### Mengecilkan MapLibre

1 MB, dan itu sebagian besar berat `/project`. `maplibre-gl-shared.mjs`
diunduh dua kali, sekali oleh halaman dan sekali oleh workernya yang berjalan
di konteks terpisah dengan peta modulnya sendiri. Di produksi permintaan kedua
kemungkinan besar dijawab dari cache HTTP, sebab `/assets/*` disajikan dengan
`immutable`; server uji lokal tidak mengirim header cache, jadi angka 1927 KB
itu lebih buruk daripada yang dialami pembaca sungguhan.

Mengecilkannya menuntut membangun MapLibre sendiri dengan bundler, dan itu
berarti berkas vendor yang tidak lagi bisa dibandingkan dengan rilis resminya.
Yang sudah dikerjakan dan cukup: pustakanya dimuat malas, hanya di halaman
yang berpeta, dan empat halaman lain tidak membayarnya sama sekali.
`tests/test_performa.py` yang menjaganya.

### Membuang tebal 500

Tebal 500 dipakai empat aturan CSS, paling menonjol label `.tag`. Membuangnya
menghemat 7,6 KB untuk pembaca beranda. Tetapi itu mengubah tampilan, bukan
hanya berat, dan keputusan semacam itu bukan keputusan yang boleh diambil
diam diam lewat dokumen performa. Dicatat di sini sebagai pilihan yang
tersedia, bukan sebagai rencana.

## Angka yang benar benar dialami pembaca

Tabel di atas diukur terhadap server uji lokal, yang tidak memadatkan apa pun.
Diukur terhadap situs yang benar benar terbit, dengan brotli dari Cloudflare,
beranda menjadi **92,3 KB** pada layar 626 px:

| | KB |
| --- | --- |
| `parking.webp`, 800w untuk layar berkerapatan 1,5 | 33,4 |
| empat berkas font Poppins | 31,9 |
| `style.css` | 13,5 |
| `app.js` | 7,5 |
| dokumen HTML | 6,0 |

Delapan permintaan, nol asal luar. Dua gambar lainnya dimuat malas dan belum
diminta pada saat pengukuran.

Perhatikan font tidak ikut mengecil: woff2 sudah terkompresi, dan brotli tidak
bisa menambah apa apa di atasnya. Itu juga sebabnya `gzip_types` di nginx tidak
menyebut font, dan memang tidak boleh.

## Anggaran diukur pada asal sendiri, bukan pada seluruh permintaan

Ubin peta datang dari luar dan jumlahnya diputuskan peta sendiri. `/project`
terukur 29 permintaan di mesin yang tokennya dibatasi per URL sehingga tiap
ubin dijawab 403, dan 51 di CI yang tidak punya token sehingga ubin OpenFreeMap
benar benar dimuat. Anggaran yang menghitung keduanya akan gagal karena cuaca.

Jadi yang dijadikan syarat lulus hanya berkas dari asal situs ini, yaitu satu
satunya yang bisa digemukkan oleh sebuah commit. Jumlah seluruhnya tetap
dicetak di sebelahnya.

## Yang paling berpengaruh dan belum dilakukan siapa pun di sini

Satu angka yang tidak bisa diperbaiki dari dalam repositori ini: situs ini
disajikan dari `workers.dev`, dan `www.hendrokuswantoro.com` belum terdaftar.
Lihat [status.md](status.md). Selama itu, semua pengukuran di atas berlaku
untuk alamat yang bukan alamat yang diiklankan situs ini tentang dirinya
sendiri.
