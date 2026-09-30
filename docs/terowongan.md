# Dashboard lewat Cloudflare Tunnel

Selama VPS belum ada, dashboard berjalan di laptop pemilik dan dibuka dari
mana saja di `https://admin.hendrokuswantoro.com/admin`. Pemilik memilihnya
pada 29 September 2026, sesudah VPS ditunda karena kartunya ditolak.

Yang perlu diketahui sebelum memakainya:

- **Dashboard hanya hidup selama laptopnya menyala** dan servernya berjalan.
  Situs publik tidak terpengaruh sama sekali: ia dilayani Cloudflare, dan
  tulisan dari dashboard terbit lewat git.
- Laptop tidak membuka porta apa pun. `cloudflared` menyambung KELUAR ke
  Cloudflare, dan permintaan masuk lewat sambungan itu.

## Lapisannya

```
pembaca -> Cloudflare Access (kode email) -> terowongan -> cloudflared
        -> 127.0.0.1:8000 -> Terowongan (backend/core/terowongan.py)
        -> sandi + TOTP atau passkey
```

`backend/core/terowongan.py` menggantikan pekerjaan nginx untuk permintaan
yang datang lewat terowongan. Ia mengenalinya dari nama host
`TEROWONGAN_HOST` ATAU dari header Cloudflare mana pun (`cf-ray`,
`cf-connecting-ip`, `cf-access-jwt-assertion`), jadi terowongan yang salah
disetel dengan host `localhost` tetap dijaga.

1. **Token Cloudflare Access wajib.** Tanda tangannya diperiksa terhadap
   kunci publik tim di `https://TIM.cloudflareaccess.com/cdn-cgi/access/certs`,
   beserta `aud`, `iss`, dan umurnya. Aplikasi Access yang terhapus atau salah
   jalur tidak membuka dashboard: permintaannya ditolak 403. Kalau salah satu
   dari `TEROWONGAN_HOST`, `ACCESS_TIM`, atau `ACCESS_AUD` kosong, seluruh
   permintaan lewat terowongan ditolak 503 dan pesannya menyebut yang kurang.
2. **Hanya `/admin`, `/_next/`, `/api/`, dan `/unggahan/`** yang dibuka.
3. **Alamat pembaca dibaca dari `cf-connecting-ip`**, dan hanya kalau
   permintaannya datang dari loopback, tempat `cloudflared` berjalan. Tanpa
   itu seluruh pembaca tampak sebagai `127.0.0.1`, dan pembatas masuk sepuluh
   kali per menit berlaku untuk semua orang sekaligus.
   Batas masuk itu sendiri milik nginx, jadi di sini digantikan batas aplikasi
   untuk `/api/v1/auth/`: `LAJU_MASUK_JUMLAH`, 15 permintaan per menit per
   alamat.
4. **Header keamanan yang sama dengan nginx**, termasuk CSP dashboard Next yang
   dihitung aplikasi. `tests/test_terowongan.py` membandingkannya dengan
   `infrastructure/nginx/hendrokuswantoro.conf`. Jawaban API memakai CSP
   `default-src 'none'`, lebih ketat dari nginx, sebab di nama host ini tidak
   ada situs publik.

Permintaan ke `localhost` tidak disentuh sama sekali.

## Memasangnya, sekali saja

Token terowongan adalah rahasia. Jangan menempelnya ke obrolan atau ke git.

1. Pasang cloudflared dari PowerShell:
   `winget install --id Cloudflare.cloudflared`
2. Di `one.dash.cloudflare.com`: **Networks > Tunnels > Create a tunnel**, pilih
   **Cloudflared**, beri nama `hk-laptop`, lalu pilih **Windows**. Salin
   perintah `cloudflared.exe service install ...` yang ditampilkan dan jalankan
   di PowerShell **sebagai Administrator**. cloudflared lalu menyala sendiri
   tiap Windows menyala.
3. Masih di terowongan itu, **Public Hostname > Add a public hostname**:
   subdomain `admin`, domain `hendrokuswantoro.com`, path kosong, service
   `HTTP`, URL `localhost:8000`. Kalau Cloudflare menolak karena record DNS
   `admin` sudah ada, hapus record lamanya di DNS lebih dulu.
4. **Access > Applications**: pastikan ada aplikasi yang menjaga
   `admin.hendrokuswantoro.com` SELURUHNYA, tanpa path, dengan kebijakan Allow
   untuk email pemilik saja. Salin **Application Audience (AUD) Tag**-nya.
5. **Settings > General**: nama tim adalah bagian sebelum
   `.cloudflareaccess.com` di **Team domain**.
6. Isi `.env` di laptop:

   ```
   TEROWONGAN_HOST=admin.hendrokuswantoro.com
   ACCESS_TIM=<nama tim>
   ACCESS_AUD=<AUD tag>
   WEBAUTHN_RP_ID=admin.hendrokuswantoro.com
   WEBAUTHN_ASAL=["https://admin.hendrokuswantoro.com"]
   COOKIE_AMAN=true
   ```

   `ADMIN_NEXT` tidak perlu ditulis di sini: `tools/nyalakan_dashboard.sh`
   menyetelnya ke `1` bila belum ada, sehingga yang tampil dashboard Next.

   Sesudah `WEBAUTHN_RP_ID` diganti, passkey yang didaftarkan di `localhost`
   tidak berlaku lagi; daftarkan passkey baru dari alamat terowongan. Sandi,
   TOTP, dan kode pemulihan tidak terpengaruh. Chrome menerima cookie
   `Secure` di `http://localhost`, jadi `COOKIE_AMAN=true` tidak mematikan
   dashboard lokal.

## Tiap kali ingin membuka dashboard

1. Buka Docker Desktop.
2. Klik dua kali `tools/nyalakan_dashboard.cmd` di File Explorer, atau jalankan
   `sh tools/nyalakan_dashboard.sh` dari Git Bash. Keduanya menyalakan basis
   data, menjalankan migrasi, lalu server. Biarkan jendelanya terbuka. Kalau
   dashboard ternyata sudah menyala, skripnya berhenti dengan pesan bahwa
   porta 8000 sudah dipakai.
3. Buka `https://admin.hendrokuswantoro.com/admin`, masuk ke Cloudflare Access
   dengan kode email, lalu masuk ke dashboard seperti biasa.

Kalau yang tampil halaman galat Cloudflare 1033 atau 502, terowongannya hidup
tetapi server di laptop belum berjalan: jalankan langkah 2.

## Menerbitkan tulisan dari dashboard

Menandai tulisan terbit di dashboard belum membuatnya tampil di situs. Situs
dibangun Cloudflare dari git, jadi tulisannya harus masuk git lebih dulu.

1. Pastikan dashboard menyala.
2. Klik dua kali `tools/terbitkan.cmd`, atau jalankan `sh tools/terbitkan.sh`.
3. Tunggu sekitar dua menit, lalu buka `https://www.hendrokuswantoro.com/blog/`.

Skripnya menyamakan laptop dengan GitHub (`git pull --ff-only`), mengambil
tulisan terbit beserta fotonya lewat `bangun_tulisan.py --sumber api`, lalu
membuat satu commit yang HANYA memuat `content/blog`, `content/unggahan`,
`blog/`, `feed.xml`, dan `sitemap.xml`, dan mengirimnya. Perubahan lain yang
kebetulan ada di laptop tidak ikut. Kalau tidak ada yang baru, ia berhenti
tanpa membuat commit. Kalau laptop dan GitHub sudah berbeda arah, ia berhenti
tanpa mengirim apa pun.

Tulisan yang dijadikan draf lagi atau dihapus di dashboard TIDAK ikut hilang
dari situs; berkasnya di `content/blog/` harus dihapus sendiri.

## Saat VPS menyala

Terowongan tidak dibutuhkan lagi. Hapus public hostname `admin`, kosongkan
ketiga variabel di atas, dan ikuti `docs/vps.md`.

Di VPS, Cloudflare tetap memasang `CF-Ray`, `CF-Connecting-IP`, dan
`Cf-Access-Jwt-Assertion` di setiap permintaan. Aplikasi yang melihatnya
mengira dirinya di balik terowongan, dan dengan ketiga variabel kosong ia
menjawab 503. Karena itu tiap blok `proxy_pass` di nginx mengosongkan ketiganya.
Blok baru yang lupa melakukannya ketahuan di `tests/test_terowongan.py`.
