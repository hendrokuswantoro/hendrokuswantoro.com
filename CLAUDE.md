# hendrokuswantoro.com

Panduan untuk agen pengembang. Baca bagian Kaidah sebelum mengubah apa pun.

Situs pribadi Hendro Kuswantoro. Dua port dalam satu repositori: HTML, CSS,
dan JavaScript biasa di akar, plus Next.js di `next/`. Yang terbit versi akar.
Ada backend FastAPI dan dashboard admin yang tidak ikut terbit ke Cloudflare.

Latar lengkapnya di [README.md](README.md) dan `docs/`. Berkas ini hanya
memuat yang perlu diketahui sebelum menyentuh kode, terutama yang sudah
pernah rusak.

## Menjalankan

```bash
# situs statis, jalur asetnya absolut jadi jangan klik ganda berkasnya
python -m http.server 8080

# uji
pip install -r tests/requirements.txt
python -m pytest                 # 1067, tanpa peramban, hitungan detik
python -m pytest -m peramban     # 115, Chromium sungguhan
sh tools/verifikasi.sh           # 22 langkah, seluruhnya, berurutan

# backend dan dashboard admin
cd infrastructure && docker compose --env-file ../.env up -d
cd .. && pip install -r backend/requirements.txt
python backend/db/migrasi.py && python backend/db/muat_awal.py
python backend/jalan.py
```

**Jangan memanggil `uvicorn` langsung di Windows.** Uvicorn membuat
`ProactorEventLoop`, psycopg menolak bekerja di atasnya, dan gagalnya
berbentuk `PoolTimeout: pool initialization incomplete` yang tidak menyebut
sebabnya sama sekali. `backend/jalan.py` membuat loop yang benar lebih dulu
lalu menyuruh uvicorn memakai yang sudah ada.

Sebab yang sama memisahkan uji peramban dari jalankan bawaan: uji basis data
menyetel `WindowsSelectorEventLoopPolicy`, dan sesudah itu Playwright gagal
dengan `NotImplementedError` di proses yang sama. Keduanya tidak bisa hidup
berdampingan dalam satu proses pytest di Windows, jadi dipisah lewat tanda
`peramban`, bukan dihilangkan.

## Susunan berkas

```
index.html about.html project.html blog/ 404.html   situs yang terbit
assets/css/style.css      seluruh gaya, token warna dan huruf di :root
assets/js/app.js          bahasa, tema, filter proyek, header, animasi
assets/js/peta.js         peta karya ala Google Maps, 38 lapisan di atas ubin Mapbox
assets/js/parkir.js       peta tarif parkir Yogyakarta, memakai gaya peta.js
assets/js/parkir-data.js  data parkir, DIBANGKITKAN dari content/parkir/
assets/js/konfigurasi.js  token Mapbox, TIDAK ikut git
assets/vendor/maplibre/   MapLibre GL JS, disimpan sendiri, bukan CDN
assets/fonts/             delapan woff2 Poppins, bukan dari Google
content/blog/*.md         sumber tulisan blog
content/template/         template ber-{{slot}}
content/parkir/           ruas kawasan, tarif, aset provinsi, batas cakupan
backend/api/v1/           router, HTTP saja
backend/layanan/          aturan bisnis, tidak tahu SQL
backend/repositori/       satu satunya yang tahu SQL
backend/db/migrations/    0001 sampai 0010, nomornya wajib unik
backend/admin/            dashboard HTML, gaya dan skripnya berkas sendiri
unggahan/                 foto dan video dari dashboard, TIDAK ikut git
next/                     port Next.js, situs dan dashboard admin
next/components/peta/     gaya.ts dan bangun.ts, cermin peta.js untuk port Next
tools/                    pembangkit dan pemeriksa, lihat di bawah
tests/                    1182 uji
docs/                     lima belas dokumen, alasan di balik keputusannya
_headers                  tajuk keamanan dan cache, dibaca Workers dan Pages
dist/                     keluaran build, jangan disunting
```

## Kaidah yang tidak boleh dilanggar

**Berkas yang dibangkitkan jangan disunting tangan.** Yang disunting adalah
pembangkitnya, lalu dijalankan ulang. Hampir semuanya punya `--periksa` yang
dipakai CI, jadi menyunting hasilnya akan ketahuan, tetapi baru di CI.

| Hasil | Pembangkit |
| --- | --- |
| `blog/*.html`, `blog/index.html` | `tools/bangun_tulisan.py` |
| `content/unggahan/`, dan `content/blog/*.md` milik tulisan dashboard | `tools/bangun_tulisan.py --sumber api` |
| `feed.xml`, baris blog di `sitemap.xml` | `tools/build_feed.py` |
| `next/app/globals.css` | `tools/gaya_next.py` |
| nomor `?v=` di seluruh HTML, `app.js`, dan gambar karya di port Next | `tools/versi_aset.py` |
| `assets/img/og-cover.png`, ikon | `tools/build_og.py`, `tools/build_icons.py` |
| `assets/img/work/*.webp`, salinannya di `next/public/assets/img/work/` | `tools/build_work_images.py` |
| `@font-face` di `style.css` | `tools/ambil_font.py` |
| `assets/js/parkir-data.js`, `next/content/parkir-data.json` | `tools/bangun_parkir.py` |
| hash sha256 di `_headers` | `tools/hash_skrip.py` |
| baris `set_real_ip_from` di nginx | `tools/ip_cloudflare.py`, dari `infrastructure/cloudflare-ip.txt` |
| `dist/`, `dist-hendrokuswantoro.zip` | `tools/bangun_situs.sh`, `tools/build_dist.py` |

**Nomor `?v=` dihitung dari isi berkasnya, bukan dinaikkan dengan tangan.**
`/assets/*` dijanjikan `immutable, max-age=31536000`. Janji itu berarti
peramban menyimpan berkasnya setahun penuh dan tidak pernah menanyakannya
lagi, bahkan tidak dengan permintaan bersyarat. Janji itu hanya sah kalau
alamatnya berganti setiap kali isinya berganti. Sampai 13 September 2026 janji
itu diberikan tanpa dipenuhi, dan akibatnya peta hilang sama sekali bagi
pembaca yang pernah berkunjung, tanpa satu pun galat di mana pun. Jalankan
`python tools/versi_aset.py` setiap kali isi berkas di `assets/` berubah.

Impor relatif di dalam modul ES tidak mewarisi query string induknya, jadi
untuk pustaka bermodul banyak **yang diberi versi adalah nama foldernya**,
bukan query-nya. Itu sebabnya MapLibre duduk di `assets/vendor/maplibre/6.9.0/`.

**Cloudflare MENGGABUNGKAN aturan `_headers` yang cocok, tidak
menggantinya.** Menulis `/assets/*` lalu menimpanya dengan aturan khusus
untuk satu berkas tidak bekerja, dan gagalnya sunyi: berkasnya disajikan
dengan `Cache-Control: public, max-age=31536000, immutable, public,
max-age=0, must-revalidate` dan peramban membaca `immutable` yang datang
lebih dulu. Karena itu `_headers` memuat daftar folder satu per satu.
Ketahuan dengan `curl` terhadap situs yang sudah terbit, bukan dengan membaca
berkasnya, jadi **periksa perubahan `_headers` terhadap situs yang terbit.**

Di nginx aturannya berbeda dan sama sama menjebak: satu `add_header` di dalam
sebuah `location` MENGHAPUS seluruh `add_header` induknya. Karena itu
`infrastructure/nginx/hendrokuswantoro.conf` mengulang kelima header
keamanan di tiap `location` yang menambah satu header.

**Rahasia tidak pernah masuk git, dan tidak pernah diketik ke dalam kode.**

- `assets/js/konfigurasi.js` memuat token Mapbox dan ada di `.gitignore`.
  Contohnya `konfigurasi.contoh.js`. Saat build, `tools/konfigurasi.sh`
  menulisnya dari variabel lingkungan `MAPBOX_TOKEN`.
- `.env` tidak pernah di-commit. Aplikasi web **tidak pernah** memuat `.env`
  ke `os.environ`; nilainya dibaca lewat `pengaturan()` di
  `backend/core/konfigurasi.py`. Menyetel variabel di shell lalu berharap
  kode membacanya lewat `os.environ` sudah pernah memakan waktu satu jam.
- Jangan mencatat sandi, token, kunci, atau data pribadi ke log.
  `backend/core/surat.py` sengaja hanya mencatat `type(galat).__name__`,
  tidak pernah `str(galat)`, supaya kode verifikasi tidak ikut tercetak.
- Jangan mengarang protokol kriptografi sendiri.

**Berkas yang diunggah tidak pernah dipercaya namanya.** Jenis foto dan video
ditentukan dari bita pertama berkasnya di `backend/layanan/berkas.py`, bukan
dari `filename` dan bukan dari `Content-Type`. Keduanya datang dari pengirim.
Nama di cakram dibuat sendiri: enam belas heksa acak, ditambah ukuran
gambarnya, ditambah akhiran yang ditentukan dari isinya. Nama kiriman hanya
dicatat untuk dilihat orang dan tidak pernah dipakai membentuk jalur.

Ukurannya dibaca dari kepala berkasnya dengan pengurai kecil, bukan dengan
pustaka gambar. Membuka gambar dengan pustaka berarti mengurai seluruh isinya
di jalur yang menerima berkas dari luar.

**Kode sumber tidak berkomentar, sejak 26 September 2026.** Alasan di balik
tiap keputusan tinggal di berkas ini, di `docs/`, dan di pesan commit. Yang
sengaja dipertahankan hanya yang punya fungsi: arahan alat seperti `noqa`,
`type: ignore`, `pragma: no cover`, dan `eslint-disable`; shebang; penanda
blok font yang dicari `ambil_font.py` dan `gaya_next.py`, beserta atribusi
lisensi OFL di dalamnya; docstring modul di skrip yang memakai `__doc__`
sebagai teks bantuan baris perintah; berkas migrasi SQL, yang sidiknya
disimpan `migrasi.py`; isi heredoc yang dicetak atau ditulis ke berkas lain;
dan sakelar `# if ($admin_boleh = 0)` di nginx, yang tanda pagarnya disuruh
dihapus pemiliknya di `docs/keamanan.md`. Sejak 29 September 2026 kaidah ini
ditegakkan `tools/cari_komentar.py` dan `tests/test_tanpa_komentar.py`, yang
membaca komentar JS/TS lewat pengurai TypeScript, bukan regex, supaya regex
`/\//g` dan alamat `https://` tidak dikira komentar.

**Uji CSP dengan menyajikan halamannya beserta tajuknya, dan jalankan
skripnya.** Ini sudah tertulis di berkas ini sejak lama sebagai kalimat, dan
tanpa uji ia cuma kalimat: sampai 19 September 2026 CSP untuk `/admin`
menolak SELURUH skrip dashboard, dan tidak ada satu pun uji yang tahu.
Skripnya sebaris 44 KB, `script-src` di sana `'self'` ditambah satu hash milik
skrip tema di situs publik. Dashboard mati total, tombol Masuk diam, dan
jejaknya hanya di konsol peramban. `tests/test_csp.py` sekarang menyajikan
tiap halaman dengan tajuk yang dibaca dari `_headers` dan dari konfigurasi
nginx, lalu menuntut nol `securitypolicyviolation` **dan** skripnya benar
benar jalan. Halaman yang seluruh skripnya ditolak tetap tergambar rapi.

Akibatnya: **jangan menulis `<script>` atau `<style>` sebaris di
`backend/admin/`, dan jangan memakai atribut `style=` di markupnya.** Gaya dan
skripnya ada di `dasbor.css` dan lima berkas `dasbor*.js`, dimuat berurutan
dengan `dasbor.js` paling akhir sebab ia yang memasang seluruh tombolnya.
Berkas skrip baru di sana wajib ditambahkan ke `ASET_ADMIN` di
`backend/main.py`; daftarnya tertutup dengan sengaja.

**CSP dashboard Next dihitung aplikasinya, dipasang nginx.** Ekspor statis
Next menaruh sembilan skrip sebaris di `admin/index.html`, dan isinya berganti
tiap build. Hash yang diketik tangan di nginx pasti tertinggal. Karena itu
`backend/core/csp_admin.py` menghitung hash dari berkas yang benar benar
disajikan dan mengirimnya lewat tajuk `X-HK-CSP`; nginx memetakannya ke
`$csp_admin`, menyembunyikan tajuk aslinya, dan memakai kebijakan dashboard
HTML bila tajuk itu tidak ada. `tests/test_csp.py` menjalankan dashboard Next
di balik kebijakan itu, dan membuktikan kebalikannya juga: tanpa hash,
skripnya memang ditolak.

**Jalur tulis menuntut `butuh_admin_kuat`, bukan `butuh_admin`.** Yang
membedakan: sesinya lahir lewat faktor kedua atau passkey. Router baru yang
mengubah isi situs wajib memakainya di tingkat router, bukan per rute, dan
`tests/test_faktor_kedua_wajib.py` menolak kalau lupa. Halaman keamanan
sengaja TIDAK memakainya: kalau ia ikut ditutup, pemilik yang belum punya
faktor kedua tidak akan pernah bisa memasangnya, dan aturannya berubah jadi
pintu yang dikunci dari dalam.

**Memasang faktor memakai `butuh_admin_pendaftar`, menghapusnya memakai
`butuh_admin_kuat`.** Sesi yang lahir dari sandi saja boleh memasang faktor
PERTAMA, tidak boleh memasang faktor tambahan. Sampai 26 September 2026
keduanya boleh, dan akibatnya sandi saja cukup untuk mengambil alih akun
berpasskey: masuk dengan sandi, hapus passkey pemiliknya, daftarkan passkey
sendiri, lalu masuk lewat passkey itu dengan sesi kuat. Untuk alasan yang sama,
akun yang hanya punya passkey tidak bisa masuk dengan sandi, dan wajah tidak
pernah menerbitkan sesi kuat. `tests/test_temuan_audit.py` menahan ketiganya.

**Dashboard wajib tahu kekuatan sesinya sendiri, bukan menebak dari 403.**
`next/app/admin/page.tsx` membaca `GET /api/v1/keamanan` sekali, dan
`aksesDari()` di `next/components/admin/akses.ts` menurunkannya jadi tiga
keadaan: penuh, terkunci (punya faktor tetapi sesinya lemah, misalnya lewat
wajah), dan perlu faktor. Tiap tombol yang pasti ditolak server dimatikan
beserta alasannya, dan spanduk di atas menawarkan masuk ulang. Sampai 27
September 2026 dashboard memanggil jalur kuat dari sesi wajah, menerima 403,
dan daftar tulisannya hilang tanpa satu kalimat pun.

`tests/conftest.py` mematikan aturan itu untuk seluruh uji lain, supaya uji
yang masuk dengan sandi saja tetap bisa menulis. Mematikan sebuah penjaga di
dalam uji hanya sah selama ada uji lain yang menguji penjaganya sendiri.

Uji memakai akun admin pemilik yang sungguhan, sebab situs ini hanya punya
satu. Selama sesi uji, sandinya ditukar dan seluruh faktornya (TOTP, kode
pemulihan, passkey, wajah) disingkirkan, lalu dikembalikan persis di akhir.
Titipannya ditulis ke `cadangan/` lebih dulu, jadi sesi uji yang mati di
tengah jalan dipulihkan oleh sesi berikutnya. Sampai 27 September 2026
passkey buatan autentikator tiruan tidak ikut dibuang: empat puluh menumpuk,
dan karena `punya_faktor()` menghitungnya, pemilik ditolak saat memasang
faktor pertamanya.

**Setelan keamanan akun ada dua jenis, dan jangan dicampur.** Sejak 28
September 2026 halaman keamanan di dashboard Next disusun seperti WhatsApp:
Verifikasi dua langkah, Notifikasi keamanan, Kunci aplikasi, Lanjutan, dan
Aktivitas akun.

- Yang tersimpan di server, kolom `kabar_masuk`, `kabar_perubahan`, dan
  `mode_ketat` di `users` (migrasi 0009), diubah lewat `PATCH
  /api/v1/keamanan/setelan` yang menuntut `butuh_admin_kuat`. Mematikan
  notifikasi SELALU dikabarkan lewat surat (`paksa=True`), apa pun
  setelannya, supaya pengambil alih akun tidak bisa membungkam pemiliknya.
  Mode ketat menolak wajah sebagai faktor kedua, tetapi hanya selama akun
  punya authenticator atau passkey; tanpa itu ia tidak menutup satu satunya
  pintu.
- Yang tersimpan di perangkat, `localStorage["hk-admin-perangkat"]`: kunci
  aplikasi dan keluar otomatis. Kunci aplikasi hanya menutup LAYAR di
  perangkat itu, persis seperti kunci aplikasi WhatsApp, dan layarnya
  mengatakan begitu. Membukanya lewat `/api/v1/auth/passkey/buka/*`, yang
  memeriksa tanda tangan passkey milik orang yang sedang masuk dan tidak
  pernah menerbitkan sesi. Tantangannya bertujuan `buka`, jadi tidak bisa
  dipakai untuk masuk, dan tantangan masuk tidak bisa dipakai untuk membuka.

Dashboard HTML di `backend/admin/` punya menu yang sama sejak 28 September
2026, di `dasbor-keamanan.js`, dengan kunci setelan perangkat yang sama
(`hk-admin-perangkat`), jadi pilihan di satu dashboard berlaku di yang lain.
Satu yang sengaja tidak disalin: mendaftarkan wajah butuh kamera, jadi dashboard
HTML hanya bisa menghapusnya, dan layarnya mengatakan begitu. Ujinya,
`tests/test_dasbor_keamanan_peramban.py`, memakai API tiruan lewat
`page.route`, jadi tidak menyentuh basis data maupun akun pemilik.
`tests/conftest.py` menitipkan ketiga kolom
setelan bersama faktor lain dan mengembalikannya di akhir sesi uji.

**Refresh token lama yang dipakai lagi dianggap curian.** Sejak 28 September
2026 tiap baris `sesi` mencatat `awal`, saat orangnya masuk, dan
`dicabut_karena`. Token yang sudah DIPUTAR lalu dipakai lagi lebih dari
`TENGGANG_PUTAR_DETIK` (30 detik) sesudahnya mencabut seluruh sesi pemiliknya,
dicatat sebagai `refresh_dipakai_ulang`, dan dikabarkan lewat surat. Tenggang
itu ada karena dua tab yang memperpanjang bersamaan bukan pencurian. Token
yang dicabut karena keluar atau dikeluarkan TIDAK memicunya: perangkat yang
dikeluarkan lalu mencoba memperpanjang bukan pencuri, dan kalau memicu
pencabutan massal, menekan "keluarkan perangkat lain" akan mengeluarkan
pemiliknya sendiri. Umur mutlak sesi `SESI_MAKS_HARI` (30), karena sebelum
ini tiap putaran memberi umur baru dan sesi yang terus dipakai tidak pernah
berakhir. `tests/test_pengerasan.py` menahan keempatnya, dan sudah dibuktikan
gagal ketika perbaikannya dimatikan.

Jawaban di bawah `/api/v1/auth`, `/api/v1/keamanan`, dan `/api/v1/admin`
dikirim dengan `Cache-Control: no-store` oleh `backend/core/tanpa_simpan.py`.
Hanya itu yang dipasang aplikasi; header keamanan lain tetap urusan nginx,
sebab blok `/api/` di nginx mewarisi header induknya dan memasang yang sama
dua kali membuat nilainya ganda.

`/.well-known/security.txt` berlaku sampai akhir 2099. RFC 9116 menyarankan
`Expires` kurang dari setahun, tetapi itu saran (SHOULD), bukan kewajiban, dan
pemiliknya memilih pada 28 September 2026 agar berkasnya berlaku terus tanpa
diperbarui tiap tahun. Akibatnya validator seperti internet.nl memberi
peringatan, bukan galat. Kalau alamat kontaknya berganti, berkas ini yang
diganti, sebab tanggalnya tidak akan pernah mengingatkan.

**Yang mencabut sesi wajib mencatatnya di `backend/core/cabut.py`.** Access
token adalah JWT dan tidak pernah ditanyakan ke basis data, jadi mencabut sesi
tanpa mencatatnya hanya mematikan refresh token-nya dan menyisakan token akses
yang hidup sampai lima belas menit berikutnya. Tombol "keluarkan perangkat
lain" ditekan justru saat orangnya curiga.

**Nilai `data-ind` di-escape dua kali, lewat `markah.untuk_ind()`.**
Peramban membuka satu lapis saat atribut dibaca, dan `app.js` memasangnya
lewat `innerHTML`, yang membuka lapis kedua. Dengan satu lapis, `&lt;a&gt;` di
atribut kembali jadi tag sungguhan di halaman berbahasa Indonesia. Untuk
`data-ind-alt` dan atribut lain yang dipasang lewat `setAttribute`, pakai
`markah.polos()`.

**Metadata foto dibuang hanya kalau diminta, dan tidak pernah setengah.**
`backend/layanan/metadata.py` mendukung JPEG, PNG, dan WebP. GIF dan AVIF
DITOLAK ketika pembuangan diminta, bukan diterima diam diam: membuang setengah
lalu mengaku sudah bersih membuat orang berhenti hati hati, dan itu lebih
berbahaya daripada tidak membuang sama sekali.

**Lapisan backend ditegakkan oleh uji, bukan oleh niat baik.**

```
Router      backend/api/v1/     HTTP, kode status, parameter
Schema      backend/skema/      validasi dua arah, Pydantic
Service     backend/layanan/    aturan bisnis, tidak tahu SQL
Repository  backend/repositori/ satu satunya yang tahu SQL
```

`tests/test_api.py` menolak SQL di luar `repositori/` dan menolak router yang
mengimpor `backend.repositori`. Router yang butuh sesuatu dari repositori
memanggilnya lewat fungsi di lapisan layanan.

**Jangan pernah mengaku sesuatu terjadi padahal tidak.** Ini kaidah kode,
bukan kaidah laporan. `backend/core/surat.py` mengembalikan `terkirim=False`
dan menulis `.eml` ke `cadangan/surat/` ketika SMTP belum dikonfigurasi; ia
tidak pernah berpura pura suratnya berangkat. Kalau sebuah fitur belum bisa
dipakai, layarnya menyebutkan apa yang kurang, misalnya `SMTP_HOST`,
`KUNCI_KOLOM`, atau `ambil_model.py`, bukan gagal diam diam.

Hal yang sama berlaku untuk batas sebuah fitur. Verifikasi wajah **tidak**
membuktikan ada orang hidup di depan kamera dan bisa ditembus rekaman video.
Kalimat itu wajib ada di layar tempat fiturnya dinyalakan, bukan hanya di
`docs/keamanan-akun.md`, dan `tests/test_bahasa_admin.py` menggagalkan uji
kalau kata "rekaman video", "sidik jari", atau "tidak disimpan" hilang dari
`PanelKeamanan.tsx`.

**Warna tidak boleh diganti tanpa menghitung ulang seluruh matriksnya.**

```bash
python tools/kontras.py
```

Angkanya dibaca dari `style.css`, bukan diketik ulang, dan `tests/test_gaya.py`
gagal kalau angka yang tercatat di uji tidak lagi sama dengan yang dihitung. Pasangan
terendah di palet terang 4,54:1, di palet gelap 5,19:1, ambang AA 4,5:1. Tidak
ada ruang untuk menggelapkan satu nada pun tanpa memeriksa.

**Satu skala huruf untuk situs dan dashboard**, `--fs-xs` sampai `--fs-xl` di
`:root`. Ukuran huruf tidak boleh diketik langsung di
`next/app/admin/admin.module.css`; `tests/test_gaya.py` menolaknya.

Satu jebakan di CSS yang sudah memakan waktu: **`font: inherit` adalah
pemendekan yang MENYETEL ULANG `font-size`.** Longhand-nya wajib ditulis
SESUDAHNYA, kalau tidak nilainya hilang tanpa jejak dan tanpa galat. Ada uji
yang menangkap pembalikan urutannya.

Jebakan kedua: **`aspect-ratio` bersama `min-height` menurunkan lebar
minimum lewat rasionya.** `.peta__frame` memakai 21/9 dan `min-height`
sekitar 504 piksel, jadi lebar minimumnya 1.176 piksel. Sampai 27 September
2026 halaman Project meluber sampai 1.200 piksel di setiap layar antara 720
dan 1.200 piksel, dan uji geser mendatar hanya memeriksa lebar 360.
`width: 100%` yang menahannya; ujinya sekarang berjalan di 360, 768, dan
1.024.

**Skrip sebaris di `<head>` diizinkan lewat hash sha256, bukan
`unsafe-inline`.** Skrip tiga baris itu memasang tema sebelum bingkai
pertama, jadi ia tidak bisa pindah ke `app.js` yang ber-`defer`. Tiap kali ia
berubah satu byte pun, jalankan `python tools/hash_skrip.py`.

**Dwibahasa lewat atribut, bukan lewat berkas terjemahan.** Teks Inggris
ditulis sebagai isi elemen, Indonesianya menumpang di `data-ind` pada elemen
yang sama, dan untuk atribut memakai `data-ind-label` atau `data-ind-alt`.
Elemen tanpa `data-ind` tidak akan pernah berubah bahasa. Pilihan pembaca
disimpan di `localStorage["hk-lang"]`, temanya di `localStorage["hk-tema"]`.

**Bahasanya sederhana, dan itu berlaku di dashboard admin juga.** Kalimat
pendek, satu gagasan per paragraf, **tanpa tanda strip panjang**. Di
`next/components/admin/` batasnya ditegakkan uji: paragraf maksimal 45 kata,
kalimat maksimal 28 kata. Alasan panjang tinggal di `docs/`.

**Dua port wajib sejalan.** `tests/test_peta.py` memaksa keduanya memuat
lapisan peta yang sama persis dengan urutan yang sama, dan `tools/gaya_next.py`
membangkitkan CSS port Next dari `style.css`. Salinan sistem desain yang kedua
sudah pernah tertinggal berhari hari.

**Migrasi bernomor unik dan tidak pernah disunting ulang.** CI memeriksa
nomornya tidak kembar.

## Konvensi teknis

Peta karya memakai MapLibre di atas ubin vektor Mapbox Streets v8, dengan gaya
yang **ditulis tangan** di `peta.js`, bukan diambil dari URL gaya Mapbox. Gaya
Mapbox menunjuk sumbernya dengan alamat `mapbox://` yang tidak terbaca
MapLibre, sedangkan versi rasternya tidak membawa tinggi bangunan.

Urutan lapisan nama dari yang terkecil ke yang terbesar, sebab MapLibre
menempatkan simbol dari tumpukan paling atas ke bawah dan yang ditulis paling
akhir yang menang saat berebut tempat. Sebelum diurutkan begitu, 959 label
permukiman menutup seluruh nama negara pada zoom 4.

38 nama provinsi ditulis sendiri di `PROVINSI_ID` karena kelas `state` pada
`place_label` Mapbox kosong untuk Indonesia. **Koordinatnya titik untuk
menggantungkan label, bukan pusat resmi dan bukan batas.**

Tanpa token Mapbox peta jatuh ke OpenFreeMap tanpa kunci dan tetap jalan,
tetapi batas wilayah, tingkatan jalan, nama jalan, nama tempat, rel, POI, dan
bangunan 3D semuanya ikut hilang bersamaan, sebab semuanya dibaca dari ubin
vektor Mapbox.

Pustaka MapLibre dimuat sendiri begitu bagian petanya mendekati layar lewat
`IntersectionObserver`. Tidak ada tombol yang harus ditekan.

**Jangan menggantungkan penataan peta pada peristiwa `load`.** Diukur pada 14
September 2026: dengan ubin Mapbox yang dijawab 403 karena alamatnya belum ada
di pembatasan token, `load` dan `idle` **tidak menyala satu kali pun** dalam
tujuh detik, padahal petanya tergambar dan `map.loaded()` menjawab `true`.
`styledata` menyala dua kali, dan pada saat itu `map.isStyleLoaded()` masih
`false`, lalu berubah jadi `true` belakangan tanpa satu pun peristiwa yang
mengabarkannya. Akibatnya relief tidak pernah dipasang, `.peta__frame` tidak
pernah ditandai `is-ready`, dan hitungan di chip kategori tinggal nol sampai ada
yang menggeser petanya. Sebab yang sama mengenai pembaca dengan sambungan
lambat, bukan hanya mesin ini. Karena itu `siap()` di kedua port dipicu oleh
yang pertama tiba di antara `load`, `styledata`, dan `idle`, ditambah jaring
pengaman berwaktu, dan isinya tidak menuntut satu ubin pun.

Alamat `#peta-<id>` membuka peta tepat di satu karya, dan tiap terbang
menuliskannya kembali dengan `replaceState`. Tautan "Lihat di peta" di tiap
kartu memakai alamat yang sama, jadi yang tersalin dari bilah alamat selalu
yang sedang dilihat. `tests/test_peta.py` menahan kedua port tetap memilikinya.

**Tiap mode peta adalah gaya yang dibangun ulang, bukan lapisan yang
ditambal.** Peta, Satelit, Medan, 3D, tema gelap, dan bahasa semuanya masukan
bagi satu fungsi, `mapboxStyle()`, dan hasilnya dipasang dengan
`map.setStyle(gaya, { diff: true })`. MapLibre menghitung bedanya sendiri,
termasuk `terrain` dan `sky`. Lapisan yang ditambahkan lewat `map.addLayer`
akan dibuang diff berikutnya, jadi `tests/test_peta.py` menolak `addLayer`
di kedua port. `gedung3d` dan `citra` selalu ada di gaya, hanya
`visibility`-nya yang berganti.

`gedung3d` duduk tepat sebelum `panah-searah`, lapisan simbol pertama. Sampai
14 September 2026 ia ditambahkan tanpa `beforeId`, jadi jatuh PALING ATAS dan
menimpa seluruh nama: di tampilan miring nama jalan terpotong badan gedung.

Ikon POI tidak datang dari sprite. Tiap ikon digambar di kanvas saat MapLibre
memintanya lewat `styleimagemissing`, jadi ikonnya selalu ada sesudah diff
maupun muat ulang penuh. Palet, ikon, dan daftar lapisan nama wajib sama di
`peta.js` dan `next/components/peta/gaya.ts`; ujinya membandingkan teksnya.

**`map.stop()` bukan sekadar membatalkan animasi.** Ia memanggil
`handlers.stop()`, yang menyetel ulang seluruh penanganan gerak termasuk
DragPan. Memanggilnya pada `dragstart` mematahkan seretan yang baru saja
dimulai peristiwa itu juga. Terukur pada 14 September 2026 di zoom 15,2:
menyeret 320 piksel menggeser peta 0,000149 derajat bujur, sekitar 16 meter,
sedangkan semestinya sekitar 1.500 meter. Yang menahannya tetap sama adalah uji seretan di
`tests/test_peramban.py`. Jangan panggil `map.stop()` dari pendengar peristiwa
gerak; MapLibre sudah mengambil alih animasi dengan sendirinya.

**Tangga warna bangunan mengikuti tinggi yang benar benar ada di sini.**
Diukur dari 17.956 bangunan Mapbox yang termuat di Yogyakarta: median 3 m,
persentil 90 6,2 m, persentil 99 14 m, tertinggi 75 m. Tangga yang membentang
sampai 140 m membuat sembilan puluh sembilan persen bangunan keluar dengan
warna yang nyaris sama, dan kotanya tampak seperti hamparan rata.

**Roda tetikus tidak memperbesar peta kecuali Ctrl atau Cmd ditahan.**
Menggulir saja menggulir halaman. `cooperativeGestures` hanya dipasang di layar
sentuh, tempat satu jari memang harus tetap menggulir halaman. Layar hitam
bertulisan "Use two fingers to move the map" yang menyertainya disembunyikan
dengan CSS sejak 27 September 2026 atas permintaan pemilik; perilaku dua
jarinya tetap.

**Peta parkir di `/parkir-jogja#coba` membawa kaidah proyek asalnya.**
Sumbernya `D:\Projects\Portfolio Kerja\sistem parkir yogyakarta`, aplikasi
FastAPI dengan GeoPackage. Karena situs ini statis, kawasan dan tarif dihitung
di peramban oleh `parkir.js`, dengan rumus yang disalin dari `api/layanan.py`
proyek itu. `tests/parkir_rujukan.py` menyalin rumus yang sama dalam Python,
dan `tests/test_parkir_peramban.py` menuntut keduanya sepakat di lebih dari
650 titik dan 660 kombinasi tarif. Port Next menyalin rumus yang sama di
`next/components/peta/parkir-hitung.ts`, dan `tests/test_parkir_next.py`
menerjemahkannya dengan TypeScript milik port itu lalu menjalankannya di node
terhadap rujukan yang sama. Kalau rumusnya berubah, keempatnya diubah bersama.

- Di luar `content/parkir/cakupan.json` kawasannya kosong dan tarifnya
  kosong, bukan Kawasan III. Batas itu selubung jaringan jalan, bukan batas
  administrasi kota, dan tidak boleh dikarang ulang.
- Tidak ada satu tempat pun yang dilabeli ilegal, liar, atau tidak resmi.
  Hijau hanya untuk aset parkir Pemda DIY. Ruas usulan digambar putus putus
  dan memunculkan peringatan.
- Warna kawasan dihitung ulang untuk palet situs ini, bukan disalin: warna
  Kawasan II asli `#a86a00` hanya 2,61:1 di atas air. Tiap ruas digambar di
  atas halo, dan uji menuntut 3:1 terhadap halonya di kedua tema.
- Pencarian hanya mencari nama ruas di data sendiri. Tidak ada geokode luar,
  jadi ketikan pembaca tidak pernah meninggalkan peramban.
- Lapisan parkir disisipkan ke gaya dari `HK_PETA.gaya()` sebelum lapisan
  simbol pertama, bukan lewat `addLayer`, supaya ikut diff tema dan bahasa.
  Legenda juga sakelar: menyembunyikan satu kategori mengubah `filter` atau
  `visibility` di gaya yang dibangun ulang, bukan menambal lapisannya.
- Tata letaknya satu untuk semua layar. Di 860 piksel ke atas panel melayang di
  kiri peta dan peta diberi `padding` selebar panel, jadi pin dan pusat peta
  tetap sama. Di bawahnya pencarian melayang di atas peta, kartunya di bawah
  peta, dan di layar penuh kartunya jadi lembar bawah. Pin, legenda, dan
  padding membaca `--parkir-kiri`, `--parkir-tepi`, dan `--parkir-atas` yang
  dihitung `aturLetak()`. Uji menahannya di 320, 375, 768, 1.024, dan 1.440.
- Legenda terbuka sendiri hanya di 1.200 piksel ke atas. Pilihan membuka
  legenda dan meringkas kartu disimpan di `localStorage["hk-parkir"]`; itu
  kenyamanan per pembaca, jadi gagal membacanya tidak boleh merusak peta.

Port Next memuat peta yang sama lewat `next/components/peta/parkir.ts`.
Tabel teks, kendaraan, layanan, warna, dan ikonnya disalin apa adanya dari
`parkir.js`, dan ujinya menolak kalau satu kalimat saja berbeda. Kerangka
`.parkir__bungkus` dirender React, bukan dibuat skripnya, sebab React tidak
boleh kehilangan simpul yang ia pasang sendiri.

**Peta di port Next butuh alamat pekerja MapLibre yang disetel sendiri.**
Webpack mengganti `import.meta.url` di dalam MapLibre dengan alamat berkas di
cakram, jadi MapLibre tidak menemukan `maplibre-gl-worker.mjs`. Akibatnya ubin
vektor dan GeoJSON tidak pernah diproses dan petanya kosong, tanpa satu galat
pun. Sampai 28 September 2026 peta karya port Next begitu sejak awal. Sekarang
`pustakaPeta()` di `next/components/peta/pustaka.ts` memanggil
`setWorkerUrl` ke salinan di `next/public/assets/vendor/maplibre/6.9.0/`, dan
versi MapLibre di `next/package.json` dikunci persis sama dengan folder itu.

**Hanya ada satu pengurai markah, dan ia di server.** `tools/markah.py`
dipakai pembangkit situs statis, validator skema API, dan sejak 18 September
2026 juga pratinjau di kedua dashboard lewat `POST /api/v1/admin/pratinjau`.
Sampai hari itu tiap dashboard punya pengurai kecilnya sendiri di peramban.
Itu aman, dan tetap salah: dua pengurai untuk satu bahasa markah akan
berpisah, dan yang berpisah membuat layar pratinjau berbohong. Jangan
menambahkan pengurai ketiga; `tests/test_penyunting.py` menolaknya.

Yang memanggil `badan()` dari dalam permintaan HTTP **wajib** menangkap
`SystemExit`. `badan()` alat baris perintah, dan `SystemExit` bukan turunan
`Exception`: kalau ia naik, yang berhenti bukan permintaannya melainkan
pekerjanya.

**Gambar dan video hanya boleh menunjuk berkas yang diunggah ke sini**, yaitu
`/unggahan/` atau `/assets/img/`. Ditegakkan di pengurai, bukan di
antarmukanya. Gambar dari server orang lain mengirimkan alamat IP tiap pembaca
ke sana tanpa pernah diminta, dan CSP situs ini memang sudah menolaknya, jadi
yang terbit kotak kosong.

Ukuran gambar dititipkan di nama berkasnya, misalnya
`9f3c1a7b2d4e5f60-1600x900.webp`, supaya pembangkit halaman tahu lebar dan
tingginya tanpa membuka berkasnya dan tanpa bertanya ke basis data. Tanpa itu,
tulisan di bawah gambar melompat saat gambarnya tiba.

**`subprocess.PIPE` yang tidak pernah dikuras akan menggantung prosesnya.**
Terukur 18 September 2026 di `tests/conftest.py`: server uji dijalankan dengan
`stdout=PIPE`, backend mencatat tiap permintaan satu baris JSON, dan pipanya
hanya dibaca kalau prosesnya mati lebih awal. Begitu penyangga pipa penuh,
tulisan berikutnya memblokir, dan yang memblokir adalah servernya sendiri: ia
berhenti menjawab tanpa mati, tanpa galat, dan tanpa satu baris pun di mana
pun. Inilah sebab kegagalan acak di `test_dasbor_peramban.py` yang lama
tidak ketemu. Sekarang pipanya dikuras utas latar ke `deque` berbatas.

**Halaman web tidak bisa mencegah tangkapan layar**, dengan cara apa pun.
Tangkapannya diambil sistem operasi, di luar jangkauan halaman. Jangan
menambahkan skrip yang mengaku menghalangi tangkapan layar. Dari 26 sampai 29
September 2026 tiap gambar karya membawa label nama situs di pojok kanan
bawah; pemilik memintanya dihapus, sebab lembar petanya sendiri sudah memuat
nama dan hak ciptanya. `tools/build_work_images.py` sekarang juga menyalin
hasilnya ke `next/public/assets/img/work/`, yang sebelumnya disalin tangan.

**Di balik nginx, uvicorn mendengarkan lewat soket Unix, dan di sana ia
tidak punya alamat klien sama sekali.** `--forwarded-allow-ips='127.0.0.1'`
tidak pernah cocok dengan alamat yang kosong, jadi sampai 26 September 2026
seluruh permintaan terbaca tanpa alamat: pembatas laju di aplikasi meloloskan
semuanya, dan jejak keamanan memakai satu ringkasan alamat untuk semua orang.
Sekarang uvicorn mempercayai `'*'`, dan nginx wajib MENIMPA `X-Forwarded-For`
dengan `$remote_addr`, bukan menambahkannya lewat
`$proxy_add_x_forwarded_for`: dengan `'*'`, uvicorn memakai alamat paling
kiri, dan yang paling kiri itu karangan klien.

Uji perubahan CSP dengan menyajikan situs **beserta tajuknya**, bukan dengan
`python -m http.server` saja: galat CSP tidak muncul tanpa tajuk aslinya.

`Permissions-Policy: camera=(self)` hanya dipasang pada `location = /admin`,
tidak pada seluruh situs.

**Selama VPS belum ada, dashboard di laptop dibuka lewat Cloudflare Tunnel**
di `admin.hendrokuswantoro.com`, pilihan pemilik pada 29 September 2026.
Langkahnya di `docs/terowongan.md`. Tanpa nginx di depannya,
`backend/core/terowongan.py` yang menjaga: permintaan lewat terowongan
dikenali dari nama host ATAU header Cloudflare apa pun, wajib membawa token
Cloudflare Access yang sah, hanya boleh ke `/admin`, `/_next/`, `/api/`, dan
`/unggahan/`, alamat pembacanya dibaca dari `cf-connecting-ip`, dan header
keamanannya sama dengan nginx. Konfigurasi yang setengah jadi menolak (503),
tidak pernah membuka. Ia wajib middleware PALING LUAR, supaya pembatas laju
dan catatan membaca alamat yang sudah diganti. `tests/test_terowongan.py`
membandingkan header-nya dengan nginx, dan sudah dibuktikan gagal saat
pemeriksaan tokennya dimatikan.

Akibatnya di VPS: nginx WAJIB mengosongkan `CF-Ray`, `CF-Connecting-IP`, dan
`Cf-Access-Jwt-Assertion` di tiap blok `proxy_pass`. Cloudflare memasang
ketiganya di setiap permintaan, dan tanpa `TEROWONGAN_HOST` aplikasi yang
melihatnya menjawab 503. Sampai 30 September 2026 nginx meneruskannya, jadi
seluruh API di VPS akan mati sejak permintaan pertama.

Lewat terowongan tidak ada nginx, jadi batas masuk sepuluh kali per menit milik
nginx juga tidak ada. Sejak 30 September 2026 `backend/core/laju.py` memberi
`/api/v1/auth/` batas sendiri, `LAJU_MASUK_JUMLAH` (15 per jendela), di samping
batas umum 120.

Menandai tulisan terbit di dashboard TIDAK menerbitkannya ke situs. Selama
dashboard di laptop, jalannya `tools/terbitkan.cmd`: ekspor lewat
`--sumber api`, lalu satu commit yang hanya memuat berkas tulisan, lalu push.
Sampai 29 September 2026 dashboard Next menjawab "Tulisan sudah terbit." padahal
situsnya belum berubah; `tests/test_admin_next.py` kini menolak kalimat itu.

Kerja sinkron yang lama (SMTP, OpenCV, Argon2) wajib lewat
`asyncio.to_thread` di lapisan layanan. Dipanggil langsung dari fungsi async,
ia membekukan SELURUH server, bukan hanya permintaannya: terukur empat detik
tiap surat Gmail. `tests/test_tidak_membekukan.py` menolaknya.

**Situs, dashboard, dan API akan tinggal di satu VPS, di `www`.** Pemilik
memilihnya pada 29 September 2026, sehari sesudah memilih subdomain `admin.`
untuk dashboard, supaya tulisan dari dashboard bisa terbit di mesin yang sama
dan foto unggahan tampil tanpa disalin. Dashboard di `/admin`, Cloudflare tetap
di depan. Sampai VPS menyala dan langkah 8 di `docs/vps.md` dikerjakan, `www`
tetap dilayani Worker Cloudflare, dan `wrangler.toml` tetap memuat kedua custom
domain; mengubahnya lebih dulu mematikan situs.

Yang diterima dengan sadar: dashboard dan situs publik satu asal bagi
peramban, jadi skrip yang lolos ke situs publik bisa memakai sesi admin.
Penjaganya CSP situs tanpa skrip sebaris kecuali satu hash, dan Cloudflare
Access di depan jalur `/admin` dan `/api`. CORS dan `WEBAUTHN_RP_ID` produksi
menyebut `www`, bukan `hendrokuswantoro.com`, supaya passkey tidak berlaku di
subdomain lain. Cookie refresh tetap TANPA atribut `Domain`.
`tests/test_vps_cloudflare.py` menahan susunan nginx dan cookienya.

**Di balik Cloudflare, nginx melihat alamat Cloudflare.** Tanpa
`set_real_ip_from`, pembatas masuk sepuluh kali per menit berlaku untuk semua
orang sekaligus, dan satu penyerang cukup untuk mengunci pemiliknya di luar.
nginx membaca `CF-Connecting-IP` HANYA dari jaringan di
`infrastructure/cloudflare-ip.txt`, dan ufw hanya membuka porta 443 untuk
jaringan yang sama; porta 80 tertutup dan sertifikatnya sertifikat origin
Cloudflare, bukan certbot. Jangan pernah membaca alamat dari
`X-Forwarded-For` di nginx: tajuk itu bisa dikarang pengirimnya. Kalau daftar
Cloudflare berubah, `python tools/ip_cloudflare.py --ambil`; pemeriksaan
kesehatan malam menjalankan `--banding` terhadap `api.cloudflare.com`.

**Di VPS, yang mengirim kode dan yang menjalankannya adalah dua akun.**
`deploy` memiliki `app/`, `situs/`, dan `venv/`; `hk` menjalankan API dan
hanya membaca ketiganya. Unggahan tinggal di `/srv/hendrokuswantoro/unggahan`,
di luar `app/`, sebab `rsync --delete` menghapus apa pun di sana dan
`ProtectSystem=strict` menguncinya. Soket API milik grup `hk-soket`
(`hk`, `deploy`, `www-data`); jangan pernah memasukkan `www-data` ke grup
`hk`, grup itu membaca `/etc/hendrokuswantoro/env`. Semuanya dipasang
`infrastructure/izin.sh`, dan `infrastructure/periksa_izin.sh` mencobanya
sungguhan di Ubuntu dalam Docker. Sampai 29 September 2026 izin ini hanya
kalimat di `docs/vps.md`, dan deploy pertama akan gagal di tiga tempat.

**Cadangan unggahan dikunci per berkas, sekali, dan tidak pernah disinkronkan.**
`cadangan.py buat` menyalin tiap unggahan yang belum punya cadangan ke
`CADANGAN_FOLDER/unggahan/NAMA.enc`, membukanya lagi untuk membandingkan
sidiknya, dan memindahkan yang dihapus ke `terhapus/TANGGAL/` selama 30 hari.
Folder unggahan yang kosong padahal cadangannya berisi adalah galat, bukan
alasan menyapu cadangan. `kirim.sh` memakai `rclone copy`, bukan `sync`, dan
retensi penyedianya `--max-depth 1`; tanpa itu retensi 30 hari menghapus
cadangan unggahan yang masih dipakai. `tests/test_cadangan_unggahan.py`
menahannya, dan sudah dibuktikan gagal saat pengamannya dimatikan.

**Tulisan dari dashboard terbit lewat berkas, bukan langsung dari basis data.**
`bangun_tulisan.py --sumber api` menulis tiap tulisan terbit ke
`content/blog/SLUG.md` dan menyalin foto serta video yang disebutnya ke
`content/unggahan/`, lalu membangun dari berkas; `bangun_situs.sh` menaruh
foto itu di `/unggahan/` situs, dengan alamat yang sama seperti di dashboard.
Sampai 29 September 2026 mode itu membangun langsung dari basis data, jadi
tulisan dashboard pertama yang di-push akan membuat CI merah dan hilang lagi
pada pembangunan berikutnya. Batas per berkas 25 MB, batas berkas statis
Cloudflare. `/unggahan/` di `.gitignore` sengaja berawalan garis miring:
tanpa itu `content/unggahan/` ikut diabaikan dan fotonya tidak pernah sampai.

**Keamanan diuji dengan alat, bukan dengan niat.** Hasil audit 29 September
2026 dan batasnya ada di `docs/keamanan.md`. Yang wajib dijaga:

- Tiap `uses:` di workflow dikunci ke hash commit 40 heksa, bukan tag;
  `tests/test_lapisan_keamanan.py` menolak tag. Hash tag beranotasi berbeda
  dari hash commitnya; ambil yang `^{}` dari `git ls-remote`.
- gitleaks (`.gitleaks.toml`) dan bandit berjalan di job Security Scan.
- `tools/uji_keamanan.sh` membangun tiruan produksi di Docker lalu
  menyerangnya dengan OWASP ZAP, termasuk seluruh API dengan token admin.
  Batas laju nginx sengaja dilonggarkan HANYA di tiruan itu; tanpa itu ZAP
  melaporkan SQL injection palsu dari jawaban 429.
- ESLint port Next berjalan dengan `--max-warnings 0`, dan knip menolak berkas,
  export, dan dependensi yang tidak terpakai. Salinan MapLibre di
  `next/public/assets/vendor/` dikecualikan dari keduanya: itu kode pihak
  ketiga yang dimuat lewat alamat, bukan lewat import.
- zizmor, gixy (`-ll`), dan shellcheck berjalan di Security Scan. Tiap
  checkout memakai `persist-credentials: false`, dan nilai `vars`, `inputs`,
  atau keluaran langkah masuk ke skrip shell lewat `env`, tidak pernah lewat
  `${{ }}` di dalam `run:`. Workflow `workflow_run` hanya berjalan untuk push
  ke repositori ini; pengecualiannya di `.github/zizmor.yml` hanya untuk
  kedua workflow itu.
- `periksa_nginx.sh` menyalakan nginx sungguhan dan memeriksa perilakunya.
  Jangan menulis `expires` di samping `add_header Cache-Control`: keduanya
  menjadi dua header. Pola pengalih `.html` sengaja sempit; `(/.+)` membuatnya
  pengalih ke situs lain lewat `/%5C`.
- Deploy menyematkan kunci host VPS dari secret `VPS_KUNCI_HOST`, bukan
  `ssh-keyscan`, dan mengambil commit yang lolos CI (`workflow_run.head_sha`),
  bukan ujung `main`.

Deploy sengaja tidak ada di `ci.yml`. Cloudflare membangun dan menerbitkan
sendiri ketika `main` bergerak, jadi deploy kedua di GitHub Actions berarti
memberi situs ini dua tuan.

## Yang belum selesai, dan itu milik pemilik proyek

1. **`hendrokuswantoro.com` terdaftar lewat Cloudflare Registrar sejak 28
   September 2026**, berlaku sampai 27 September 2027 dengan perpanjangan
   otomatis. Kedua nama dipasang sebagai custom domain di `wrangler.toml`,
   bukan lewat dasbor, supaya tercatat di git; `tests/test_terbit.py`
   menahannya, termasuk jebakan TOML: `routes` yang ditulis di bawah
   `[assets]` masuk ke tabel itu dan diabaikan tanpa galat. `workers_dev = true`
   wajib ada: begitu `routes` diisi, Wrangler mematikan alamat `workers.dev`
   diam diam, dan pada 28 September 2026 alamat lama itu sempat menjawab galat
   1042 beberapa menit. Pengalihan dari
   nama tanpa `www` ke `www` adalah Redirect Rule di dasbor, milik pemilik.
   Pembayaran pertamanya gagal belasan kali di halaman checkout dasbor, lewat
   Google Pay, kartu, maupun PayPal, tanpa OTP dari bank; yang berhasil adalah
   halaman tagihan Stripe (`invoice.stripe.com`) dengan kartu diketik langsung.
   Ingat itu saat perpanjangan pertama gagal. Pemeriksaan kesehatan malam kini
   memeriksa `https://www.hendrokuswantoro.com`, bukan alamat `workers.dev`.
   Di dasbor sudah menyala: Always Use HTTPS, TLS minimal 1.2, DNSSEC, dan
   tiga record penolak email (`v=spf1 -all`, DKIM kosong, DMARC `p=reject`),
   sebab domain ini tidak mengirim email. Kalau kelak memakai Email Routing,
   SPF dan DMARC itu wajib diganti lebih dulu, kalau tidak surat sah ikut ditolak.
   Sejak 29 September 2026 HSTS dinyalakan juga di dasbor (12 bulan,
   includeSubDomains, preload), sebab Redirect Rule nama tanpa `www` menjawab
   sebelum Worker dan `_headers`, jadi nama itu tidak pernah mengirim HSTS.
   Cloudflare MENGGANTI nilai `_headers` di `www` dengan miliknya, bukan
   menggandakannya: yang terkirim `max-age=31536000`, bukan 63072000. Web
   Analytics (RUM) dimatikan di hari yang sama; skripnya ditolak CSP dan
   tidak pernah mengumpulkan apa pun.
   Hari itu juga pemilik mendaftarkan `hendrokuswantoro.com` ke daftar HSTS
   preload (hstspreload.org, status `pending`). Akibatnya berlaku selamanya:
   jangan pernah mematikan HSTS, memendekkan `max-age` di bawah setahun, atau
   membuat subdomain yang tidak HTTPS, sebab domain yang berhenti memenuhi
   syarat dicoret dari daftar dan keluar darinya butuh berbulan bulan.
   Pemeriksaan kesehatan malam menagih ketiga syaratnya.
   Record CAA `0 issue "letsencrypt.org"` ditambahkan hari itu juga.
   Cloudflare lalu menambah sendiri `issue` dan `issuewild` untuk pki.goog,
   ssl.com, digicert.com, dan comodoca.com; record tambahan itu TIDAK tampil
   di dasbor, hanya terlihat lewat kueri DNS. Jangan hapus record CAA itu
   dengan anggapan izin Cloudflare ikut hilang: justru tanpanya semua penerbit
   boleh.
2. VPS belum dibuat, jadi workflow "Deploy VPS" selalu dilewati dan backend,
   dashboard, serta konfigurasi nginx belum pernah berjalan di server
   sungguhan. Langkahnya ada di `docs/vps.md`. Sejak 28 September 2026 yang
   terbit di VPS adalah dashboard Next: `.env.example`, yang menjadi
   `/etc/hendrokuswantoro/env`, menyetel `ADMIN_NEXT=1`, `vps.yml` membangun `next/out` di GitHub Actions lalu
   mengirimnya, dan nginx menyajikan `/_next/` langsung dari cakram.
   Situs dan dashboard akan tinggal di `www` di VPS itu (Proxied, SSL Full
   (strict) yang sudah menyala, sertifikat origin Cloudflare); pemindahannya,
   termasuk cara membatalkannya, di `docs/vps.md` langkah 8. Basis data di sana mulai dari
   nol, jadi akun adminnya lahir TANPA faktor kedua, dan selama itu siapa pun
   yang tahu sandinya bisa memasang faktor PERTAMA miliknya sendiri, karena
   `butuh_admin_pendaftar` sengaja mengizinkannya. Cloudflare Access sudah
   dipasang pada 29 September 2026; tujuannya diganti ke `www/admin` dan
   `www/api` sebelum situs dipindah. Pasang TOTP dan passkey segera sesudah
   situs pindah. Ini satu satunya temuan audit yang tidak bisa ditutup dengan
   kode. Pada 29 September 2026 pemilik MENUNDA VPS sesudah Oracle Cloud
   Free menolak kartunya; catatan untuk mencobanya lagi ada di `docs/vps.md`,
   "Kalau memang jadi". Tulisan dari dashboard belum punya jalan ke situs publik; lihat
   bagian terakhir `docs/vps.md`.

## Catatan lingkungan

`KUNCI_KOLOM` dan `CADANGAN_KUNCI` di `.env` mesin ini punya salinan di luar
laptop sejak 26 September 2026, di brankas KeePassXC pemiliknya, beserta
dua belas heksa pertama sha256 masing masing sebagai sidik. **Jangan pernah
menjalankan `enkripsi.py kunci` untuk `.env` ini.** Kunci baru tidak bisa
membuka rahasia TOTP dan ciri wajah yang sudah tersimpan, dan salinannya
tidak akan ikut berganti.

Akun admin di basis data laptop memakai TOTP sejak 27 September 2026, dan
kode pemulihannya disimpan pemilik di brankas yang sama dengan kuncinya.

Sejak 29 September 2026 `.env` laptop memakai `WEBAUTHN_RP_ID` dan
`WEBAUTHN_ASAL` milik `admin.hendrokuswantoro.com`, sebab dashboard dibuka
lewat terowongan. Passkey pemilik ("Laptop ini") terdaftar untuk alamat itu
dan tidak berlaku di `localhost`; mode ketat dan kunci aplikasi menyala.
Salinan `.env` sebelum perubahan ada di `cadangan/env-sebelum-terowongan`.

Laptop mencadangkan basis datanya sendiri tiap hari pukul 21.00 lewat tugas
terjadwal Windows yang dipasang `tools/pasang_cadangan_harian.ps1`, dan
membuktikan pemulihannya tiap Minggu. Kegagalannya muncul sebagai jendela
`msg`, bukan di Task Scheduler, yang selalu melaporkan 0; alasannya di
`docs/cadangan.md`.

Verifikasi wajah dijalankan dengan kamera sungguhan untuk pertama kalinya pada
27 September 2026. Model 37 MB-nya tidak ikut git; ambil dengan
`python tools/ambil_model.py` di mesin baru. Percobaan pertama menolak
pemiliknya dua kali: YuNet memberi mata KANAN orangnya, yang di gambar kamera
duduk di sisi KIRI, dan `arah_hadap()` membaca arah menurut gambar. Uji lama
tidak menangkapnya karena ia hanya memeriksa kode terhadap dirinya sendiri.
Sesudah diperbaiki, kemiripan pemilik terukur 0,75 dan 0,80, jauh di atas
ambang 0,363.

Sesi uji mengosongkan `SMTP_HOST`, `SMTP_PENGGUNA`, `SMTP_SANDI`, dan
`SURAT_DARI` di `tests/conftest.py` sebelum `.env` dibaca. Sampai 27 September
2026 tidak, dan sejak SMTP diisi tiap putaran uji yang memasang TOTP atau masuk
lewat kode email mengirim surat sungguhan ke kotak masuk pemilik.

SMTP di `.env` mesin ini memakai Gmail dengan sandi aplikasi sejak 26
September 2026, dan surat uji pertamanya terkirim. `SURAT_WAJIB` sengaja
kosong di laptop; di VPS isinya `1`. Surat di `cadangan/surat/` yang lebih tua
dari tanggal itu ditulis selama SMTP belum ada dan tidak pernah berangkat.

Pembatasan URL token Mapbox sudah memuat `http://localhost:8099` sejak 26
September 2026, jadi uji peta lokal tidak lagi dilewati. **Mapbox menolak
alamat IP.** Kalimatnya tersurat di layar: "IP addresses are not supported in
URL restrictions. Use a domain name instead." Jadi `http://127.0.0.1:8099`
akan ditolak, dan itu sebabnya server uji di `tests/conftest.py` menjawab di
`localhost`, bukan di `127.0.0.1`. Lihat `INANG_UJI` di sana. Pembatasan URL
Mapbox juga **tidak boleh memakai `*` di bagian jalur.**

Node v24 terpasang, tetapi tidak selalu ada di PATH milik Git Bash.
`tools/verifikasi.sh` mencarinya sendiri di `/c/Program Files/nodejs`. Port
Next.js sudah pernah dibangun, `next/out/` ada, tetapi tidak diterbitkan.

Docker Desktop terpasang di `%LOCALAPPDATA%\Programs\DockerDesktop`, bukan di
`C:\Program Files`. Menjalankan aplikasinya saja tidak cukup: pada 14
September 2026 mesin WSL `docker-desktop` tetap berhenti dan `docker info`
menjawab `npipe:////./pipe/dockerDesktopLinuxEngine` tidak ada, sehingga
basis datanya tidak bisa dinyalakan tanpa orang membuka jendelanya. Uji yang
memerlukan basis data akan dilewati, dan `tests/test_api.py` justru **galat**
alih alih dilewati dengan rapi.

Nilai lingkungan yang diawali `/` akan diubah MSYS menjadi jalur Windows saat
lewat Git Bash. Ini sudah pernah merusak satu kunci enkripsi secara diam diam.

**Perintah yang meminta ketikan rahasia tidak bekerja di Git Bash.** MinTTY
bukan konsol Windows, jadi `getpass` tidak pernah menerima satu huruf pun dan
prompt-nya tampak menggantung. Ini mengenai `backend/db/buat_admin.py`.
Jalankan lewat `winpty python ...`, atau dari PowerShell, atau pakai
`--stdin`. Jangan pernah memindahkannya ke argumen baris perintah: argumen
terlihat di daftar proses dan tersimpan di riwayat shell.
