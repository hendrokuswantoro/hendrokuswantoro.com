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
python -m pytest                 # 649, tanpa peramban, hitungan detik
python -m pytest -m peramban     # 57, Chromium sungguhan
sh tools/verifikasi.sh           # 21 langkah, seluruhnya, berurutan

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
assets/js/peta.js         peta karya, 31 lapisan di atas ubin Mapbox Streets
assets/js/konfigurasi.js  token Mapbox, TIDAK ikut git
assets/vendor/maplibre/   MapLibre GL JS, disimpan sendiri, bukan CDN
assets/fonts/             delapan woff2 Poppins, bukan dari Google
content/blog/*.md         sumber tulisan blog
content/template/         template ber-{{slot}}
backend/api/v1/           router, HTTP saja
backend/layanan/          aturan bisnis, tidak tahu SQL
backend/repositori/       satu satunya yang tahu SQL
backend/db/migrations/    0001 sampai 0005, nomornya wajib unik
next/                     port Next.js, situs dan dashboard admin
tools/                    pembangkit dan pemeriksa, lihat di bawah
tests/                    706 uji
docs/                     empat belas dokumen, alasan di balik keputusannya
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
| `feed.xml`, baris blog di `sitemap.xml` | `tools/build_feed.py` |
| `next/app/globals.css` | `tools/gaya_next.py` |
| nomor `?v=` di seluruh HTML dan `app.js` | `tools/versi_aset.py` |
| `assets/img/og-cover.png`, ikon | `tools/build_og.py`, `tools/build_icons.py` |
| `assets/img/work/*.webp` | `tools/build_work_images.py` |
| `@font-face` di `style.css` | `tools/ambil_font.py` |
| hash sha256 di `_headers` | `tools/hash_skrip.py` |
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
gagal kalau angka di komentar tidak lagi sama dengan yang dihitung. Pasangan
terendah di palet terang 4,54:1, di palet gelap 5,19:1, ambang AA 4,5:1. Tidak
ada ruang untuk menggelapkan satu nada pun tanpa memeriksa.

**Satu skala huruf untuk situs dan dashboard**, `--fs-xs` sampai `--fs-xl` di
`:root`. Ukuran huruf tidak boleh diketik langsung di
`next/app/admin/admin.module.css`; `tests/test_gaya.py` menolaknya.

Satu jebakan di CSS yang sudah memakan waktu: **`font: inherit` adalah
pemendekan yang MENYETEL ULANG `font-size`.** Longhand-nya wajib ditulis
SESUDAHNYA, kalau tidak nilainya hilang tanpa jejak dan tanpa galat. Ada uji
yang menangkap pembalikan urutannya.

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
pernah ditandai `is-ready`, dan ringkasan legenda tinggal kosong sampai ada
yang menggeser petanya. Sebab yang sama mengenai pembaca dengan sambungan
lambat, bukan hanya mesin ini. Karena itu `siap()` di kedua port dipicu oleh
yang pertama tiba di antara `load`, `styledata`, dan `idle`, ditambah jaring
pengaman berwaktu, dan isinya tidak menuntut satu ubin pun.

Alamat `#peta-<id>` membuka peta tepat di satu karya, dan tiap terbang
menuliskannya kembali dengan `replaceState`. Tautan "Lihat di peta" di tiap
kartu memakai alamat yang sama, jadi yang tersalin dari bilah alamat selalu
yang sedang dilihat. `tests/test_peta.py` menahan kedua port tetap memilikinya.

**`map.addLayer` tanpa `beforeId` menaruh lapisannya PALING ATAS**, di atas
seluruh lapisan nama. Itu yang terjadi pada `gedung3d` sampai 14 September
2026: gedung 3D menimpa nama jalan dan nama tempat, dan di tampilan miring
akibatnya nama nama itu terpotong badan gedung dan terbaca seperti saling
tumpang tindih. Tempatnya yang benar tepat sebelum lapisan simbol pertama,
yaitu `panah-searah`.

**`map.stop()` bukan sekadar membatalkan animasi.** Ia memanggil
`handlers.stop()`, yang menyetel ulang seluruh penanganan gerak termasuk
DragPan. Memanggilnya pada `dragstart` mematahkan seretan yang baru saja
dimulai peristiwa itu juga: terukur, menyeret 320 piksel cuma menggeser peta
2,5 persen dari semestinya. Jangan panggil `map.stop()` dari pendengar
peristiwa gerak; MapLibre sudah mengambil alih animasi dengan sendirinya.

**Tangga warna bangunan mengikuti tinggi yang benar benar ada di sini.**
Diukur dari 17.956 bangunan Mapbox yang termuat di Yogyakarta: median 3 m,
persentil 90 6,2 m, persentil 99 14 m, tertinggi 75 m. Tangga yang membentang
sampai 140 m membuat sembilan puluh sembilan persen bangunan keluar dengan
warna yang nyaris sama, dan kotanya tampak seperti hamparan rata.

**Roda tetikus tidak memperbesar peta kecuali Ctrl atau Cmd ditahan.**
Menggulir saja menggulir halaman. `cooperativeGestures` hanya dipasang di layar
sentuh, tempat satu jari memang harus tetap menggulir halaman.

Uji perubahan CSP dengan menyajikan situs **beserta tajuknya**, bukan dengan
`python -m http.server` saja: galat CSP tidak muncul tanpa tajuk aslinya.

`Permissions-Policy: camera=(self)` hanya dipasang pada `location = /admin`,
tidak pada seluruh situs.

Deploy sengaja tidak ada di `ci.yml`. Cloudflare membangun dan menerbitkan
sendiri ketika `main` bergerak, jadi deploy kedua di GitHub Actions berarti
memberi situs ini dua tuan.

## Yang belum selesai, dan itu milik pemilik proyek

1. **`hendrokuswantoro.com` belum terdaftar.** Otoritas `.com` menjawab
   NXDOMAIN, bukan sekadar tanpa A record. Setiap `rel=canonical`, `og:url`,
   JSON-LD, `sitemap.xml`, `feed.xml`, dan `CNAME` menunjuk ke nama yang tidak
   ada. Inilah sebabnya Health Check merah tiap malam. Langkahnya sengaja
   ditaruh paling akhir supaya kegagalan yang sudah diketahui tidak menutupi
   lima pemeriksaan lain. Situsnya sendiri sehat di alamat `.workers.dev`.
2. SMTP belum diisi di `.env`, jadi surat verifikasi ditulis ke
   `cadangan/surat/` dan tidak berangkat.
3. `KUNCI_KOLOM` belum punya salinan di luar mesin ini. Kalau hilang, kolom
   terenkripsi tidak bisa dibaca lagi.
4. Model pengenalan wajah 37 MB, tidak ikut git, diambil dengan
   `python tools/ambil_model.py`. **Verifikasi wajah belum pernah dijalankan
   dengan kamera sungguhan.**
5. `http://localhost:8099` belum ada di pembatasan URL token Mapbox, jadi peta
   tidak tergambar saat dikembangkan secara lokal dan empat uji peta dilewati.
   Buka console.mapbox.com, Tokens, pilih token `pk.`, URL restrictions,
   tambahkan baris itu persis, lalu Save changes.

   **Mapbox menolak alamat IP.** Kalimatnya tersurat di layar: "IP addresses
   are not supported in URL restrictions. Use a domain name instead." Jadi
   `http://127.0.0.1:8099` akan ditolak, dan itu sebabnya server uji di
   `tests/conftest.py` menjawab di `localhost`, bukan di `127.0.0.1`. Lihat
   `INANG_UJI` di sana. Pembatasan URL Mapbox juga **tidak boleh memakai `*`
   di bagian jalur.**

## Catatan lingkungan

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
