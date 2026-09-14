# Status terhadap spesifikasi

Pemeriksaan baris demi baris terhadap `Personal web.docx`. Tiga tanda dipakai:

- **Sudah** — terpasang dan ada yang menjaganya
- **Tidak berlaku** — tidak relevan untuk situs ini, alasannya ditulis
- **Belum** — berlaku, tetapi belum dikerjakan

Terakhir diperiksa 13 September 2026, sesudah passkey, enkripsi cadangan,
dan berkas VPS masuk.

## Bagian satu, permintaan situsnya

| | Permintaan | Status |
| --- | --- | --- |
| 1 | UI/UX seperti Gojek | Sudah |
| 2 | Font seperti Google | Sudah, Poppins, dan sejak 13 September 2026 disimpan sendiri di `assets/fonts`, bukan dipanggil dari Google |
| 3 | Warna Deep Cobalt Blue | Diganti atas permintaan Anda, hijau Gojek lalu hitam putih Uber. Abu abunya kini netral seperti Uber Base, latar `#f6f6f6` |
| 4 | Menu home, about, project | Sudah, plus Blog atas permintaan Anda |
| 5 | Copyright | Sudah |
| 7 | Keamanan dashboard seperti Meta dan Google | Lambang, rata kiri kanan, verifikasi email, kode OTP, dan sidik jari lewat WebAuthn sudah dan sudah dijalankan. Verifikasi wajah terpasang dan **belum pernah dijalankan dengan kamera sungguhan**, lihat [keamanan-akun.md](keamanan-akun.md) |
| 6 | Domain hendrokuswantoro.com | **Belum terdaftar.** Otoritas .com menjawab NXDOMAIN, bukan delegasi yang sedang menyebar. Situsnya hidup di workers.dev. Lihat bagian Domain di bawah |

## Bagian dua, tumpukan teknologi

| Lapisan | Teknologi | Status |
| --- | --- | --- |
| Frontend | TypeScript + Next.js + React | Sebagian. Port dibangun dan lolos type check; **halaman admin Next.js sudah dipakai sungguhan** lewat ADMIN_NEXT=1. Halaman publik yang terbit masih versi HTML |
| Map UI | MapLibre GL JS | Sudah, 31 lapisan di atas ubin vektor Mapbox |
| Advanced 3D | CesiumJS | Tidak berlaku |
| Visualisation | Deck.gl | Tidak berlaku |
| API | Python + FastAPI | Tidak berlaku |
| High performance | Go | Tidak berlaku |
| Spatial DB | PostgreSQL + PostGIS | Tidak berlaku |
| Cache | Redis | Tidak berlaku |
| Object storage | S3 / MinIO | Tidak berlaku |
| GIS engine | GDAL + PROJ + GEOS | Tidak berlaku |
| Vector processing | GeoPandas + Shapely | Tidak berlaku |
| Raster processing | Rasterio + Xarray | Tidak berlaku |
| Distributed | Dask | Tidak berlaku |
| Map server | GeoServer | Tidak berlaku |
| Tile | PMTiles / vector tiles | Sebagian. Ubin vektor Mapbox dipakai, PMTiles dan GeoServer tidak |
| Authentication | OAuth2/OIDC + Keycloak | Diganti. Passkey WebAuthn sebagai jalur utama, Argon2id + JWT sebagai cadangan. Keycloak adalah satu proses lagi untuk satu pengguna |
| Reverse proxy | Nginx / Traefik | Berkas nginx lengkap ada dan lolos `nginx -t`. Yang hidup sekarang tetap lapisan tepi Cloudflare |
| Container | Docker | PostGIS dan Redis lewat Compose |
| Orchestration | Kubernetes | Tidak berlaku |
| CI/CD | GitHub Actions | Sudah |
| Monitoring | Prometheus + Grafana | Sebagian. Health check harian, peringatan lewat isu GitHub dan Telegram. Metrik belum |
| Logging | Loki / OpenSearch | Tidak berlaku |

**Kenapa begitu banyak "tidak berlaku".** Situs ini empat halaman dan tiga
tulisan. Tidak ada yang login, tidak ada yang mengirim formulir, tidak ada
data pengunjung yang disimpan, tidak ada isi yang berubah tanpa penulisnya
mengubahnya. Basis data untuk isi yang tidak berubah adalah satu proses lagi
yang harus hidup, dicadangkan, ditambal, dan dibayar, tanpa imbalan apa pun.

Aturan nomor satu di dokumen yang sama melarangnya: *jangan membuat
kompleksitas yang tidak diperlukan.* Tumpukan itu untuk aplikasi kerja Anda,
bukan untuk brosur empat halaman. Syarat kapan keputusan ini gugur ada di
[arsitektur.md](arsitektur.md).

## Bagian tiga, 24 bab standar

| Bab | Status | Keterangan |
| --- | --- | --- |
| 1 General | Sudah | Clean code, SOLID, modular, tanpa kompleksitas berlebih |
| 2 Development Workflow | Sudah | Analisis, rancang, bertahap, uji sebelum selesai |
| 3 Frontend | Sudah | Responsif, komponen dipakai ulang, aksesibilitas, SEO, keadaan kosong dan gagal. Dijaga `test_struktur.py` |
| 4 Backend | Sudah | FastAPI berlapis, Router - Skema - Layanan - Repositori |
| 5 Database | Sudah | PostgreSQL + PostGIS, migrasi bernomor, batasan diuji dengan cara dilanggar |
| 6 Redis | Sudah | Pembatas laju. Sesi sengaja di Postgres, bukan di sini |
| 7 Object storage | Tidak berlaku | Tidak ada unggahan |
| 8 Authentication & IAM | Sudah | Passkey WebAuthn dengan sensor perangkat, Argon2id, JWT, plus faktor kedua: TOTP RFC 6238, kode email, kode pemulihan, verifikasi wajah. Batas masing masing di [keamanan-akun.md](keamanan-akun.md) |
| 9 Authorization | Sudah | RBAC, `butuh_admin`, 401 dan 403 dibedakan |
| 10 Session & Token | Sudah | Refresh berputar, dicabut di Postgres, hanya SHA-256-nya yang disimpan |
| 11 Security | Sudah | Header, CSP, HSTS, penyisiran rahasia. Penyisiran penuh 13 Sep 2026 menutup empat temuan, lihat [audit-keamanan.md](audit-keamanan.md) |
| 12 Reverse proxy | Sudah, belum hidup | `infrastructure/nginx/`, lolos `nginx -t`, header sama persis dengan `_headers`. Yang menyajikan sekarang masih Cloudflare |
| 13 CDN & WAF | Sudah | Cloudflare |
| 14 Infrastructure | Sudah, belum hidup | Compose, unit systemd yang dikeraskan, `pasang.sh` yang idempoten. Belum pernah menyentuh Ubuntu sungguhan |
| 15 CI/CD | Sudah | Lint, type check, test, security scan, build tiap push |
| 16 Testing | Sudah | 706 uji: berkas, gaya dan kontras, basis data, API, autentikasi, passkey, enkripsi cadangan, infrastruktur, peramban, performa |
| 17 Monitoring | Sudah | Log JSON terstruktur, health check harian, peringatan lewat isu. Health check-nya sendiri pernah gagal tiap malam karena cacatnya sendiri, lihat bawah |
| 18 Backup & DR | Sudah | AES-256-GCM, RPO 1 hari, RTO di bawah 15 menit, retensi 14 lokal dan 30 hari di penyedia, pemulihan diuji tiap push |
| 19 DevOps & Automation | Sudah | Deploy, build, sertifikat, pemeriksaan semuanya otomatis |
| 20 Performance | Sudah | Diukur dan dianggarkan. Beranda 158 KB dari 233 KB, nol asal luar. Lihat [ringan.md](ringan.md) |
| 21 Git | Sudah | Commit atomik dan deskriptif, tidak ada rahasia |
| 22 Documentation | Sudah | README plus sebelas dokumen, termasuk API, basis data, autentikasi, cadangan, dan VPS |
| 23 Production Hardening | Sudah | HTTPS, rahasia, header, health check, rollback, dan pemulihan cadangan yang sudah diuji |
| 24 Final Verification | Sudah | `tools/verifikasi.sh` |

## Yang benar benar belum dikerjakan

Nol butir yang bisa dikerjakan di sini. Yang tersisa menuntut mesin yang
belum Anda sewa, dan saya menyebutnya terus terang, bukan mencentangnya:

**Fase 7 sudah ditulis seluruhnya dan belum pernah dijalankan di server.**
Konfigurasi nginx lolos `nginx -t` di dalam kontainer nginx 1.27. Berkas unit
systemd terbaca dan pengerasannya dijaga tujuh uji. Skrip shell lolos `sh -n`.
Alur kerja deploy sah dan dijaga enam uji. Cadangan terenkripsi benar benar
dibuat, dikunci, lalu **dipulihkan** dengan jumlah baris yang cocok.

Yang belum pernah terjadi: `pasang.sh` menyentuh Ubuntu sungguhan,
`hk-api.service` dinyalakan systemd, dan `kirim.sh` menghubungi object
storage. Ketiganya menuntut VPS. Langkah demi langkahnya, beserta angka
biayanya dan alasan kenapa VPS itu mungkin belum perlu sama sekali, ada di
[vps.md](vps.md).

## Tiga cacat yang ditemukan 13 September 2026, dan semuanya ditutup

Ketiganya punya satu sifat yang sama: tidak satu pun menimbulkan galat di
tempat yang dilihat orang.

### 1. Health check gagal tiap malam, dan situsnya sehat

`kesehatan.yml` memuat baris ini:

```sh
for jalur in / /about /project /blog/ \n                       /blog/kapan-peta-diam \n ...
```

`\n` di situ bukan baris baru, melainkan dua karakter yang dibaca shell
sebagai satu kata bernilai `n`. Jadi pemeriksaannya meminta `$situs/n`,
dijawab 404, dan gagal. Karena langkah gagal membuka isu otomatis, ia juga
melaporkan bahwa situsnya mati. Sepuluh alamat yang sebenarnya diperiksa
semuanya menjawab 200 sepanjang waktu itu.

`bash -n` tidak bisa menangkapnya: sintaksnya sah sempurna. Yang menangkapnya
sekarang `tools/periksa_alur.py`, yang memparse tiap berkas alur, menjalankan
`bash -n` pada tiap blok `run`, dan menolak `\n` harfiah di luar `printf`,
`echo`, atau `sed`. Dipanggil CI. Empat uji di `test_infrastruktur.py`
memberi pemeriksanya kembali baris aslinya dan gagal kalau ia meloloskannya.

### 2. Uji peramban gagal di CI karena menunggu jaringan diam

`buka()` memakai `wait_until="networkidle"`. Untuk setiap halaman kecuali satu
itu sama saja dengan menunggu `app.js` selesai. Pada `/project` tidak: peta
terus meminta ubin selama masih terlihat, jaringannya tidak pernah diam selama
500 ms, dan `Page.goto` berjalan sampai batas 30 detik lalu gagal dengan pesan
yang hanya menyebut timeout.

Di mesin pengembangan ia lolos, dan alasannya memalukan: token Mapbox di sini
dibatasi per URL, tiap ubin dijawab 403 dalam sekejap, jaringannya diam, dan
ujinya hijau **karena petanya rusak**. Di CI tanpa rahasia token, peta jatuh
ke OpenFreeMap yang menjawab sungguhan, ubinnya mengalir, dan ujinya gagal.

Sekarang `app.js` memasang `data-siap` pada `<html>` di akhir `boot()`, dan
`buka()` menunggu atribut itu. Pernyataan dari kode yang menyiapkan halaman,
bukan tebakan dari perilaku jaringan.

### 3. Nginx mengirim aset tanpa header keamanan

Blok `location /assets/` memasang `add_header Cache-Control`. Satu `add_header`
di dalam `location` **menghapus seluruh** `add_header` milik blok server, jadi
sejak baris itu dipasang, setiap berkas JavaScript, SVG, dan font dikirim tanpa
`nosniff`, tanpa HSTS, dan tanpa CSP. Jebakan ini sudah dijelaskan panjang di
blok `/api/` pada berkas yang sama, lalu tetap memakan blok sebelahnya.

Cloudflare tidak punya jebakan ini: `_headers` menumpuk aturan `/*` dan
`/assets/*`, tidak menggantinya. Jadi nginx dan Cloudflare menyajikan dua situs
dengan aturan berbeda, persis keadaan yang `test_infrastruktur.py` mengaku
menjaganya. Keenam header kini diulang di blok itu, dan dua uji baru menolak
blok `/assets/` yang memasang `add_header` tanpa mengulangnya.

## Yang sudah ditutup sejak pemeriksaan pertama

| | Selesai |
| --- | --- |
| MapLibre 4.7.1 dengan GHSA-jrc7-96c5-q579 | naik ke 6.9.0, diverifikasi di peramban |
| Bab 18 tanpa isi | `backend/db/cadangan.py`, RPO 1 hari, RTO di bawah 15 menit, uji pemulihan jalan di tiap push CI |
| Tidak ada peringatan | health check yang gagal membuka isu berlabel `kesehatan`, ditutup sendiri saat pulih |
| Port Next.js belum pernah dibangun | `npm run build` jalan di CI |
| Tidak ada uji peramban | 31 uji Chromium: peta menggambar, 3D menegakkan bangunan, dua bahasa, tema, tanpa geser mendatar di ponsel |
| Performa belum pernah diukur | anggaran per halaman, angkanya tercetak tiap kali dijalankan |
| Passkey belum ada | WebAuthn terpasang, diuji dengan authenticator tiruan yang benar benar menandatangani |
| Cadangan belum dienkripsi | AES-256-GCM, dan berkas terenkripsinya sudah dipulihkan sekali |
| Node.js belum terpasang | terpasang, port Next.js dibangun dan lolos type check |
| Palet gelap memaksa diri lewat setelan sistem | tema jadi pilihan pembaca, bawaannya terang |
| `.env.example` tidak pernah sampai ke git | terjaring `.env.*` di `.gitignore`, sekarang dikecualikan |
| Font dipanggil dari dua asal Google | disimpan sendiri di `assets/fonts`, CSP menutup keduanya, beranda turun 75 KB |
| Satu berkas gambar 800 px untuk kotak 287 px | tiga lebar plus `sizes` yang diturunkan dari pengukuran, bukan dikarang |
| Alur kerja GitHub tidak pernah diperiksa | `tools/periksa_alur.py`, dipanggil CI, diuji dengan baris yang dulu lolos |
| Health check gagal tiap malam sementara situsnya sehat | `
` harfiah di daftar jalur, diganti here-doc |
| Aset dikirim nginx tanpa header keamanan | keenamnya diulang di blok `/assets/` |
| `verifikasi.sh` mengaku Node tidak terpasang padahal terpasang | mencari node di jalur Windows yang biasa, dua langkah tidak lagi dilewati |
| Dashboard tanpa faktor kedua | TOTP, kode email, kode pemulihan, dan verifikasi wajah, semuanya lewat tiket berumur lima menit |
| Alamat email tidak pernah dibuktikan | tautan sekali pakai, 24 jam, dan surat yang tidak terkirim tidak pernah mengaku terkirim |
| Tidak ada jejak siapa pun masuk | peristiwa keamanan, termasuk yang gagal, tanpa menyimpan alamat IP apa adanya |

## Domain, dan satu klaim di dokumen ini yang ternyata salah

Sampai 13 September 2026 baris di atas berbunyi "sedang menunggu nameserver
menyebar". Itu tidak benar, dan ini hasil pengukurannya:

```
$ curl -H 'accept: application/dns-json' \
    'https://cloudflare-dns.com/dns-query?name=hendrokuswantoro.com&type=NS'
{"Status":3, ... "Authority":[{"name":"com","type":6, ...}]}
```

`Status: 3` adalah NXDOMAIN, dan yang menjawabnya otoritas `com` sendiri, bukan
nameserver domainnya. Artinya **namanya belum terdaftar sama sekali**. Nama yang
sedang menyebar punya delegasi yang bisa dilihat; nama ini tidak punya apa apa.
Dua keadaan itu tampak sama dari peramban, yaitu situsnya tidak terbuka, dan
hanya yang pertama akan selesai sendiri dengan menunggu.

Yang ikut terkena, dan tidak satu pun menimbulkan galat di mana pun:

- `rel="canonical"` di setiap halaman menunjuk `https://www.hendrokuswantoro.com/...`
- `sitemap.xml`, `feed.xml`, `og:url`, dan JSON-LD memakai alamat yang sama
- `robots.txt` menunjuk sitemap di alamat itu

Mesin pencari mengindeks alamat kanonik. Selama nama itu tidak ada, situs ini
boleh sehat sempurna dan tetap tidak bisa ditemukan, dan tiap tautan di umpan
RSS-nya mati. Situsnya sendiri hidup dan menjawab 200 di sepuluh alamat, hanya
di `hendrokuswantoro-com.kuswantoro-hendro01.workers.dev`.

Sekarang ada yang memeriksanya. `kesehatan.yml` punya langkah **The canonical
address exists**: ia membaca `rel="canonical"` dari beranda yang benar benar
terbit, menanyakannya ke DNS, dan gagal dengan menyebut kedua jalan keluarnya.
Selama namanya belum ada, langkah itu akan gagal setiap malam. Itu memang
maksudnya.

Dua jalan keluarnya:

1. Daftarkan `hendrokuswantoro.com`, arahkan nameserver-nya ke Cloudflare,
   pasang dua custom domain, pasang Redirect Rule, lalu ganti variabel `SITUS`
   di GitHub supaya health check ikut pindah alamat. Langkahnya ada di README.
2. Atau ganti `CNAME` beserta setiap `rel="canonical"`, `sitemap.xml`,
   `feed.xml`, dan `og:url` ke alamat `workers.dev` yang memang dipakai, lalu
   kembalikan nanti.

Yang pertama yang Anda maksud. Yang kedua membuat situs ini bisa diindeks
hari ini.
