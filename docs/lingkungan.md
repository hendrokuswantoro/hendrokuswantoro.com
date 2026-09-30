# Variabel lingkungan

`.env.example` hanya memuat nama variabel dan nilai contohnya. Salin menjadi
`.env`, lalu isi:

```bash
cp .env.example .env
```

`.env` tidak pernah ikut git. Di VPS, `infrastructure/pasang.sh` menyalin
berkas yang sama ke `/etc/hendrokuswantoro/env`. Tidak ada rahasia di dalam
kode; berkas contoh hanya menyebut nama variabelnya, tidak pernah nilai yang
sungguhan.

Sampai 30 September 2026 keterangan di bawah ini tertulis sebagai komentar di
`.env.example`. Sejak itu berkasnya tanpa komentar, dan keterangannya di sini.

## Basis data

`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, dan `POSTGRES_PORT`
dipakai Docker Compose untuk membuat basis datanya. `DSN` dipakai aplikasi,
skrip migrasi, dan pemuat data; cocokkan dengan keempat nilai itu.

## Cache dan pembatas laju

`REDIS_PORT` dan `REDIS_URL` menunjuk Redis, tempat pembatas laju menghitung.

Pembatas laju di aplikasi berlaku per alamat klien. nginx punya batasnya
sendiri di depan aplikasi. Bawaannya `LAJU_JUMLAH=120` permintaan per
`LAJU_JENDELA_DETIK=60` detik, dan `LAJU_MASUK_JUMLAH=15` di antaranya boleh
ke `/api/v1/auth/`. Batas kedua menggantikan batas masuk nginx saat dashboard
dibuka lewat terowongan, yang tanpa nginx.

`KOLAM_MIN` dan `KOLAM_MAKS` adalah ukuran kolam sambungan PostgreSQL,
bawaannya 1 sampai 8.

## Asal yang boleh memanggil API

`ASAL_DIIZINKAN` adalah daftar JSON asal peramban yang boleh memanggil API.
Bawaannya hanya `https://www.hendrokuswantoro.com`, tempat situs, dashboard,
dan API tinggal bersama di VPS. Di mesin pengembangan, tambahkan server
Next.js-nya, misalnya `["http://127.0.0.1:8081","https://www.hendrokuswantoro.com"]`.

## Peta

`MAPBOX_TOKEN` adalah token publik Mapbox. Ia ikut terunduh ke peramban, jadi
batasi lewat pembatasan URL di console.mapbox.com, bukan dengan
menyembunyikannya.

## Autentikasi

`JWT_SECRET` minimal 32 karakter. Buat dengan:

```bash
python -c "import secrets;print(secrets.token_urlsafe(48))"
```

Tanpa rahasia itu seluruh jalur admin menjawab 503, bukan terbuka dengan
rahasia bawaan. Rahasia bawaan adalah rahasia yang sudah bocor.

`AKSES_UMUR_MENIT`, `REFRESH_UMUR_HARI`, `MASUK_GAGAL_MAKS`, dan
`MASUK_JENDELA_MENIT` mengatur umur token dan kunci setelah salah sandi.
`SESI_MAKS_HARI` adalah umur mutlak sebuah sesi; memutar refresh token tidak
memperpanjangnya. `COOKIE_AMAN=false` hanya untuk pengembangan lokal tanpa
HTTPS.

`DOKUMEN_API=1` membuka dokumentasi API interaktif di `/docs`, `/redoc`, dan
`/openapi.json`. Bawaannya tertutup. Dokumentasi itu memberi peta lengkap
permukaan API kepada siapa pun yang membukanya: berguna saat mengembangkan,
tidak ada gunanya di produksi.

### Memutar `JWT_SECRET` tanpa mengeluarkan semua orang

Pindahkan nilai lama ke `JWT_SECRET_LAMA`, isi `JWT_SECRET` dengan yang baru,
muat ulang, tunggu lima belas menit, lalu KOSONGKAN lagi `JWT_SECRET_LAMA`.
Membiarkannya terisi berarti rahasia lama berlaku selamanya dan rotasinya
tidak menutup apa apa. Ia hanya dipakai memeriksa, tidak pernah untuk
menandatangani.

### Faktor kedua wajib untuk jalur tulis

`FAKTOR_KEDUA_WAJIB=true` secara bawaan. Sandi saja membuka dashboard yang bisa
menerbitkan tulisan dan mengunggah berkas, dan permukaan itu tidak pantas
dijaga satu rahasia yang bisa ditebak, dipakai ulang, atau dipancing halaman
palsu. Halaman keamanan TIDAK ikut dituntut, supaya faktor kedua masih bisa
dipasang oleh yang belum punya. Matikan hanya untuk pemulihan: mesin baru,
TOTP hilang, dan kode pemulihan ikut hilang.

## Passkey, WebAuthn

`WEBAUTHN_RP_ID` adalah nama host saja: tanpa skema, tanpa porta, tanpa garis
miring. Ia tidak boleh ditebak dari header Host, sebab header itu datang dari
peramban dan penyerang bisa memilihnya sendiri. Kosongkan untuk mematikan
jalur passkey; jalurnya akan menjawab 503, bukan terbuka dengan nilai bawaan.
`WEBAUTHN_ASAL` adalah daftar JSON asal lengkap yang boleh.

```
Lokal    : WEBAUTHN_RP_ID=localhost
Produksi : WEBAUTHN_RP_ID=www.hendrokuswantoro.com
           WEBAUTHN_ASAL=["https://www.hendrokuswantoro.com"]
Terowongan: WEBAUTHN_RP_ID=admin.hendrokuswantoro.com
           WEBAUTHN_ASAL=["https://admin.hendrokuswantoro.com"]
```

Produksi memakai `www`, bukan `hendrokuswantoro.com`, supaya passkey hanya
berlaku di nama tempat dashboard tinggal dan tidak di subdomain lain.

JANGAN memakai alamat IP seperti `127.0.0.1`, dan jangan pula memasukkannya ke
`WEBAUTHN_ASAL`. WebAuthn menuntut rp_id berupa nama domain; `127.0.0.1` bukan
nama domain, melainkan alamat. Peramban menolaknya sebelum satu pun
permintaan dikirim, dengan `SecurityError` berbunyi "This is an invalid
domain", dan rp_id `127.0.0.1` ditolak sama persis. Tidak ada nilai mana pun
yang membuat `127.0.0.1` bekerja. Bukalah `http://localhost:8000/admin`:
mesinnya sama, hanya namanya yang berbeda, dan hanya nama yang diterima
WebAuthn.

## Cadangan

`CADANGAN_KUNCI` adalah kunci AES-256 untuk mengunci berkas cadangan, ditulis
base64. Buat dengan `python backend/db/enkripsi.py kunci`. Kalau kosong,
cadangan tetap dibuat tanpa enkripsi dan perintahnya mengatakan begitu.
Kunci ini wajib diisi sebelum cadangan dikirim keluar dari mesin; skrip
pengirimnya menolak berkas yang tidak terenkripsi. Simpan salinan kuncinya di
tempat yang BUKAN mesin ini: kunci yang hilang berarti seluruh cadangan yang
terenkripsi tidak akan pernah terbuka.

`CADANGAN_FOLDER` adalah folder cadangan basis data dan unggahan; jalur
relatif dihitung dari akar repositori. Di VPS `pasang.sh` mengisinya dengan
`/srv/hendrokuswantoro/cadangan`, satu satunya folder yang boleh ditulis unit
cadangan. Di dalam `app/` folder itu ditolak `ProtectSystem=strict`, dan
cadangan malam gagal.

`CADANGAN_TUJUAN` adalah tujuan rclone untuk salinan di luar mesin, misalnya
`r2:hk-cadangan/harian`. Kosong berarti cadangan hanya disimpan di mesin ini;
lihat `docs/cadangan.md`. `CADANGAN_SIMPAN_HARI` adalah berapa hari cadangan
basis data disimpan di penyedia.

`TELEGRAM_TOKEN` dan `TELEGRAM_TUJUAN` mengirim pemberitahuan kalau cadangan
malam gagal. Keduanya kosong berarti kegagalan hanya dicatat di journal.

## Penyandian kolom

`KUNCI_KOLOM` adalah kunci AES-256 untuk menyandikan rahasia TOTP dan ciri
wajah sebelum masuk basis data. Bentuknya sama dengan `CADANGAN_KUNCI` dan
dibuat dengan perintah yang sama, tetapi sengaja BERBEDA: cadangan dan kolom
basis data tidak seharusnya bisa dibuka satu kunci yang sama, sebab yang
memegang cadangan belum tentu berhak membuka rahasia yang masih hidup.

Kalau kosong, aplikasi authenticator tidak bisa dipasang sama sekali, dan
halaman keamanannya mengatakan begitu. Rahasianya TIDAK disimpan apa adanya
sebagai gantinya: faktor kedua yang ikut bocor bersama hash sandinya bukan
faktor kedua.

## Surat

`SMTP_HOST`, `SMTP_PORTA`, `SMTP_PENGGUNA`, `SMTP_SANDI`, dan `SURAT_DARI`
dipakai verifikasi alamat email, kode masuk enam angka, dan pemberitahuan
keamanan.

Kalau kosong, surat TIDAK dikirim. Ia ditulis ke `cadangan/surat/` sebagai
berkas `.eml`, dan setiap layar yang memintanya mengatakan bahwa suratnya
tidak berangkat. Aplikasi ini tidak pernah membalas "kode sudah dikirim" untuk
surat yang tidak pernah ada.

`SURAT_WAJIB=1` membuatnya melempar galat alih alih menulis berkas. Pasang itu
di produksi: di sana, surat yang diam diam mendarat di folder adalah surat
yang hilang.

## Unggahan foto dan video

`UNGGAHAN_DIR` adalah folder berkas yang diunggah lewat dashboard; jalur
relatif dihitung dari akar repositori, dan folder bawaannya ada di
`.gitignore`. Berkasnya TIDAK masuk basis data, hanya catatannya: satu video
dua puluh megabita di dalam baris membuat setiap cadangan basis data ikut
membawanya.

`UNGGAHAN_GAMBAR_MAKS_MB` dan `UNGGAHAN_VIDEO_MAKS_MB` adalah batas per
berkas. Di atas angka itu yang menunggu adalah pembaca dengan kuota ponsel,
bukan cakram yang penuh.

`UNGGAHAN_TOTAL_MAKS_MB`, `UNGGAHAN_JUMLAH_MAKS`, dan `UNGGAHAN_PER_HARI_MAKS`
membatasi seluruh ruang unggahan. Batas per berkas tidak menjaga apa apa
terhadap yang mengunggah seribu berkas, dan cakram yang penuh mematikan
PostgreSQL, lalu seluruh situs.

## Dashboard

`ADMIN_NEXT=1` membuat `/admin` menyajikan dashboard Next dari `next/out`,
yang dibangun alur Deploy VPS. Kalau `next/out` belum ada, dashboard HTML yang
tampil.

## Dashboard lewat Cloudflare Tunnel

`TEROWONGAN_HOST`, `ACCESS_TIM`, dan `ACCESS_AUD` dipakai selama VPS belum
ada, saat dashboard di laptop dibuka dari mana saja lewat Cloudflare Tunnel di
balik Cloudflare Access. Langkahnya di `docs/terowongan.md`.

Permintaan yang datang lewat terowongan WAJIB membawa token Cloudflare Access
yang sah untuk `ACCESS_AUD`; tanpa itu ia ditolak, bukan dibuka. Ketiganya
kosong berarti terowongan ditolak seluruhnya, dan `localhost` tetap bekerja.
