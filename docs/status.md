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
| 2 | Font seperti Google | Sudah, Poppins |
| 3 | Warna Deep Cobalt Blue | Diganti atas permintaan Anda, hijau Gojek lalu hitam putih Uber. Abu abunya kini netral seperti Uber Base, latar `#f6f6f6` |
| 4 | Menu home, about, project | Sudah, plus Blog atas permintaan Anda |
| 5 | Copyright | Sudah |
| 6 | Domain hendrokuswantoro.com | Menunggu nameserver menyebar |

## Bagian dua, tumpukan teknologi

| Lapisan | Teknologi | Status |
| --- | --- | --- |
| Frontend | TypeScript + Next.js + React | Sebagian. Port ada di `next/`, **dibangun dan lolos type check di mesin ini sejak Node terpasang**, tetapi belum diterbitkan. Versi HTML biasa yang hidup |
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
| 8 Authentication & IAM | Sudah | Passkey WebAuthn, Argon2id, JWT. 19 + 18 uji, sebagian besar menguji penolakan |
| 9 Authorization | Sudah | RBAC, `butuh_admin`, 401 dan 403 dibedakan |
| 10 Session & Token | Sudah | Refresh berputar, dicabut di Postgres, hanya SHA-256-nya yang disimpan |
| 11 Security | Sudah | Header, CSP, HSTS, penyisiran rahasia. Temuan MapLibre ditutup 12 Sep 2026, lihat [keamanan.md](keamanan.md) |
| 12 Reverse proxy | Sudah, belum hidup | `infrastructure/nginx/`, lolos `nginx -t`, header sama persis dengan `_headers`. Yang menyajikan sekarang masih Cloudflare |
| 13 CDN & WAF | Sudah | Cloudflare |
| 14 Infrastructure | Sudah, belum hidup | Compose, unit systemd yang dikeraskan, `pasang.sh` yang idempoten. Belum pernah menyentuh Ubuntu sungguhan |
| 15 CI/CD | Sudah | Lint, type check, test, security scan, build tiap push |
| 16 Testing | Sudah | 437 uji: berkas, gaya dan kontras, basis data, API, autentikasi, passkey, enkripsi cadangan, infrastruktur, peramban, performa |
| 17 Monitoring | Sudah | Log JSON terstruktur, health check harian, peringatan lewat isu |
| 18 Backup & DR | Sudah | AES-256-GCM, RPO 1 hari, RTO di bawah 15 menit, retensi 14 lokal dan 30 hari di penyedia, pemulihan diuji tiap push |
| 19 DevOps & Automation | Sudah | Deploy, build, sertifikat, pemeriksaan semuanya otomatis |
| 20 Performance | Sudah | Diukur dan dianggarkan, lihat [pengujian.md](pengujian.md) |
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

## Yang menunggu, bukan belum dikerjakan

Domain `hendrokuswantoro.com` sedang menunggu nameserver menyebar. Sesudah
aktif tinggal tiga langkah yang semuanya sudah ditulis di README: pasang dua
custom domain, pasang Redirect Rule, ganti variabel `SITUS` di GitHub supaya
health check ikut pindah alamat.
