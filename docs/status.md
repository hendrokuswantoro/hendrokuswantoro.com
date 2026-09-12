# Status terhadap spesifikasi

Pemeriksaan baris demi baris terhadap `Personal web.docx`. Tiga tanda dipakai:

- **Sudah** — terpasang dan ada yang menjaganya
- **Tidak berlaku** — tidak relevan untuk situs ini, alasannya ditulis
- **Belum** — berlaku, tetapi belum dikerjakan

Terakhir diperiksa 12 September 2026, sesudah MapLibre naik ke 6.9.0.

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
| 11 Security | Sudah | Header, CSP, HSTS, penyisiran rahasia. Temuan MapLibre ditutup 12 Sep 2026, lihat [keamanan.md](keamanan.md) |
| 12 Reverse proxy | Digantikan | TLS, routing, kompresi, rate limit dikerjakan tepi Cloudflare |
| 13 CDN & WAF | Sudah | Cloudflare |
| 14 Infrastructure | Tidak berlaku | Tidak ada kontainer untuk berkas statis |
| 15 CI/CD | Sudah | Lint, type check, test, security scan, build tiap push |
| 16 Testing | Sudah | 285 uji: berkas, basis data, API, autentikasi, peramban, performa. Tidak ada uji peramban, lihat daftar di bawah |
| 17 Monitoring | Sudah | Log JSON terstruktur, health check harian, peringatan lewat isu |
| 18 Backup & DR | Sudah | RPO 1 hari, RTO di bawah 15 menit, retensi 14, pemulihan diuji tiap push |
| 19 DevOps & Automation | Sudah | Deploy, build, sertifikat, pemeriksaan semuanya otomatis |
| 20 Performance | Sudah | Diukur dan dianggarkan, lihat [pengujian.md](pengujian.md) |
| 21 Git | Sudah | Commit atomik dan deskriptif, tidak ada rahasia |
| 22 Documentation | Sudah | README plus lima dokumen. Dokumentasi API, basis data, dan autentikasi tidak berlaku |
| 23 Production Hardening | Sudah | HTTPS, rahasia, header, health check, rollback, dan pemulihan cadangan yang sudah diuji |
| 24 Final Verification | Sudah | `tools/verifikasi.sh` |

## Yang benar benar belum dikerjakan

Dari lima butir, nol yang tersisa dari daftar lama. Yang belum sekarang hanya
satu, dan bukan kelalaian melainkan keputusan yang menunggu Anda:

**Fase 7, VPS.** Nginx, deploy, cadangan terjadwal yang terenkripsi, dan
sertifikat. Semuanya menuntut server yang belum ada, dan servernya menuntut
keputusan biaya yang bukan milik saya. Rancangannya ada di
[rancangan-platform.md](rancangan-platform.md) bagian 11 dan 12.

## Yang sudah ditutup sejak pemeriksaan pertama

| | Selesai |
| --- | --- |
| MapLibre 4.7.1 dengan GHSA-jrc7-96c5-q579 | naik ke 6.9.0, diverifikasi di peramban |
| Bab 18 tanpa isi | `backend/db/cadangan.py`, RPO 1 hari, RTO di bawah 15 menit, uji pemulihan jalan di tiap push CI |
| Tidak ada peringatan | health check yang gagal membuka isu berlabel `kesehatan`, ditutup sendiri saat pulih |
| Port Next.js belum pernah dibangun | `npm run build` jalan di CI |
| Tidak ada uji peramban | 25 uji Chromium: peta menggambar, 3D menegakkan bangunan, dua bahasa, tanpa geser mendatar di ponsel |
| Performa belum pernah diukur | anggaran per halaman, angkanya tercetak tiap kali dijalankan |

## Yang menunggu, bukan belum dikerjakan

Domain `hendrokuswantoro.com` sedang menunggu nameserver menyebar. Sesudah
aktif tinggal tiga langkah yang semuanya sudah ditulis di README: pasang dua
custom domain, pasang Redirect Rule, ganti variabel `SITUS` di GitHub supaya
health check ikut pindah alamat.
