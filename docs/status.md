# Status terhadap spesifikasi

Pemeriksaan baris demi baris terhadap `Personal web.docx`. Tiga tanda dipakai:

- **Sudah** — terpasang dan ada yang menjaganya
- **Tidak berlaku** — tidak relevan untuk situs ini, alasannya ditulis
- **Belum** — berlaku, tetapi belum dikerjakan

Terakhir diperiksa 12 September 2026.

## Bagian satu, permintaan situsnya

| | Permintaan | Status |
| --- | --- | --- |
| 1 | UI/UX seperti Gojek | Sudah |
| 2 | Font seperti Google | Sudah, Poppins |
| 3 | Warna Deep Cobalt Blue | Diganti atas permintaan Anda, hijau Gojek lalu hitam putih Uber |
| 4 | Menu home, about, project | Sudah, plus Blog atas permintaan Anda |
| 5 | Copyright | Sudah |
| 6 | Domain hendrokuswantoro.com | Menunggu nameserver menyebar |

## Bagian dua, tumpukan teknologi

| Lapisan | Teknologi | Status |
| --- | --- | --- |
| Frontend | TypeScript + Next.js + React | Sebagian. Port ada di `next/`, lolos type check di CI, tetapi belum pernah dibangun maupun diterbitkan |
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
| Authentication | OAuth2/OIDC + Keycloak | Tidak berlaku |
| Reverse proxy | Nginx / Traefik | Digantikan lapisan tepi Cloudflare |
| Container | Docker | Tidak berlaku |
| Orchestration | Kubernetes | Tidak berlaku |
| CI/CD | GitHub Actions | Sudah |
| Monitoring | Prometheus + Grafana | Sebagian. Health check harian ada, metrik dan peringatan belum |
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
| 4 Backend | Tidak berlaku | Tidak ada backend |
| 5 Database | Tidak berlaku | Tidak ada basis data |
| 6 Redis | Tidak berlaku | Tidak ada sesi maupun antrean |
| 7 Object storage | Tidak berlaku | Tidak ada unggahan |
| 8 Authentication & IAM | Tidak berlaku | Tidak ada yang login |
| 9 Authorization | Tidak berlaku | Tidak ada peran |
| 10 Session & Token | Tidak berlaku | Tidak ada sesi |
| 11 Security | Sebagian | Header, CSP, HSTS, penyisiran rahasia semuanya ada. Satu temuan terbuka, lihat [keamanan.md](keamanan.md) |
| 12 Reverse proxy | Digantikan | TLS, routing, kompresi, rate limit dikerjakan tepi Cloudflare |
| 13 CDN & WAF | Sudah | Cloudflare |
| 14 Infrastructure | Tidak berlaku | Tidak ada kontainer untuk berkas statis |
| 15 CI/CD | Sudah | Lint, type check, test, security scan, build tiap push |
| 16 Testing | Sebagian | 154 uji berkas. Tidak ada uji peramban, lihat daftar di bawah |
| 17 Monitoring | Sebagian | Health check harian ada, peringatan belum |
| 18 Backup & DR | Belum | Git dan zip adalah cadangannya, tetapi RPO, RTO, dan prosedur pemulihan belum ditulis dan belum pernah diuji |
| 19 DevOps & Automation | Sudah | Deploy, build, sertifikat, pemeriksaan semuanya otomatis |
| 20 Performance | Sebagian | Sudah dioptimalkan, tetapi belum pernah diukur |
| 21 Git | Sudah | Commit atomik dan deskriptif, tidak ada rahasia |
| 22 Documentation | Sudah | README plus lima dokumen. Dokumentasi API, basis data, dan autentikasi tidak berlaku |
| 23 Production Hardening | Sebagian | HTTPS, rahasia, header, health check, rollback sudah. Pemulihan cadangan belum diuji |
| 24 Final Verification | Sudah | `tools/verifikasi.sh` |

## Yang benar benar belum dikerjakan

Enam, urut dari yang paling berdampak.

**1. MapLibre masih di 4.7.1, membawa GHSA-jrc7-96c5-q579 yang CRITICAL.**
Tidak dapat dieksploitasi pada konfigurasi sekarang, dan CSP menahan
muatannya, tetapi tetap belum diperbaiki. Perbaikannya menuntut migrasi ke
ESM, bukan tukar berkas. Analisis lengkapnya di [keamanan.md](keamanan.md).

**2. Tidak ada uji peramban.** 154 uji itu membaca berkas, bukan menjalankan
situsnya. Yang tidak dijaga siapa pun: petanya benar benar tergambar, tombol
3D benar benar menegakkan bangunan, saklar bahasa benar benar mengganti
seluruh teks, dan halaman tidak berantakan di ponsel. Semua itu sejauh ini
saya periksa dengan tangan. Sebuah pekerjaan Playwright di CI akan
menutupnya, dan itu satu satunya cara menahan peta kembali rusak diam diam
seperti yang sudah tiga kali terjadi.

**3. Bab 18 belum ada isinya.** Cadangannya memang sudah nyata: seluruh situs
ada di git, di GitHub, dan di zip. Tetapi RPO, RTO, dan prosedur pemulihannya
belum ditulis, dan yang lebih penting, pemulihannya belum pernah diuji. Bab
18 menuntut *regular restore testing*, dan cadangan yang belum pernah
dipulihkan belum terbukti apa apa.

**4. Peringatan belum ada.** Health check berjalan tiap hari, tetapi kalau
situsnya mati, kegagalannya hanya duduk di halaman GitHub Actions sampai ada
yang membukanya. Bab 17 menuntut alerting.

**5. Performa belum pernah diukur.** Gambar sudah webp, MapLibre dimuat
malas, aset diberi versi dan disimpan setahun. Semuanya masuk akal, tetapi
tidak satu pun angkanya pernah dilihat. Bab 20 menuntut optimasi, dan optimasi
tanpa pengukuran adalah tebakan yang kebetulan rapi.

**6. Port Next.js belum pernah dibangun.** CI menjalankan `tsc --noEmit`,
jadi tipenya terbukti benar, tetapi `next build` tidak pernah dijalankan.
Port itu bisa saja gagal dibangun tanpa ada yang tahu.

## Yang menunggu, bukan belum dikerjakan

Domain `hendrokuswantoro.com` sedang menunggu nameserver menyebar. Sesudah
aktif tinggal tiga langkah yang semuanya sudah ditulis di README: pasang dua
custom domain, pasang Redirect Rule, ganti variabel `SITUS` di GitHub supaya
health check ikut pindah alamat.
