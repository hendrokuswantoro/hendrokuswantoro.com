# API

Bab 15.22 menuntut dokumentasi API. Dokumentasi yang selalu benar dibangkitkan
FastAPI sendiri dari kode dan skemanya:

```
http://127.0.0.1:8000/docs        antarmuka Swagger
http://127.0.0.1:8000/openapi.json
```

Berkas ini menjelaskan hal yang tidak bisa dibangkitkan: bentuk lapisannya
dan alasan beberapa keputusannya.

## Menjalankan

```bash
cd infrastructure && docker compose --env-file ../.env up -d
cd .. && pip install -r backend/requirements.txt
python backend/db/migrasi.py && python backend/db/muat_awal.py
python backend/jalan.py
```

**Jangan panggil `uvicorn` langsung di Windows.** Uvicorn membuat
`ProactorEventLoop`, psycopg menolak bekerja di atasnya, dan gagalnya
berbentuk `PoolTimeout: pool initialization incomplete` yang tidak menyebut
sebabnya. `backend/jalan.py` membuat loop yang benar lebih dulu. Di Linux
tidak ada bedanya.

## Lapisan

```
Router      backend/api/v1/     HTTP, kode status, parameter
Schema      backend/skema/      validasi dua arah, Pydantic
Service     backend/layanan/    aturan bisnis, tidak tahu SQL
Repository  backend/repositori/ satu satunya yang tahu SQL
            PostgreSQL + PostGIS
```

**Dua uji menegakkannya**, sebab pemisahan yang hanya ditulis di dokumen akan
runtuh pada hari pertama seseorang menulis satu kueri di tempat yang salah
karena sedang buru buru:

- `test_sql_hanya_ada_di_lapisan_repositori` menyisir seluruh `backend/`
- `test_router_tidak_memanggil_repositori_langsung` menahan router melompat

Aturannya tanpa pengecualian. Waktu health check menyimpan `SELECT 1` di
`core/basis_data.py`, ujinya gagal dan kuerinya dipindah, bukan ujinya yang
dilonggarkan. Daftar pengecualian selalu bertambah.

## Titik akhir

| Method | Jalur | Otorisasi |
| --- | --- | --- |
| GET | `/health` | publik |
| GET | `/api/v1/blog` | publik |
| GET | `/api/v1/blog/{slug}` | publik |
| GET | `/api/v1/projects` | publik |
| GET | `/api/v1/projects/{slug}` | publik |
| GET | `/api/v1/maps/projects-spatial` | publik |
| GET | `/api/v1/maps/nearby` | publik |

Yang bertanda admin di rancangan belum ada. Itu Fase 4 dan 5.

## Keputusan yang perlu dijelaskan

### Dua bahasa dikirim sekaligus

Tiap teks keluar sebagai `{"en": ..., "id": ...}`, bukan disaring lewat
parameter bahasa. Alasannya situs ini mengganti bahasa **di peramban**, tanpa
memuat ulang halaman. Kalau API menyaring, tiap pergantian bahasa jadi
perjalanan jaringan baru.

### GeoJSON dirakit PostGIS, bukan Python

`ST_AsGeoJSON` menulis bentuk yang benar menurut RFC 7946 termasuk urutan
sumbunya. Merakitnya sendiri di Python adalah cara klasik menukar bujur
dengan lintang tanpa ada yang sadar sampai peta menggambar Indonesia di
Somalia. Hasilnya tetap divalidasi ulang Pydantic sebelum keluar, supaya
perubahan skema yang merusak bentuknya gagal di sini, bukan di peta orang
lain berminggu minggu kemudian.

### Jarak dihitung di geography

`ST_DWithin(geom::geography, ...)` memberi meter. Derajat bukan satuan jarak:
satu derajat bujur di Sabang dan di Merauke panjangnya berbeda, dan radius
dalam derajat menghasilkan lingkaran yang bentuknya berubah menurut lintang.
Ujinya memaksa jarak Peta Parkir dari Tugu Yogyakarta di bawah 5 km, bukan
sekadar "ada angkanya".

### ENUM dicor ke `text` di kueri

psycopg tidak mengenal tipe ENUM buatan, jadi `kategori` kembali sebagai
string mentah `{app}` dan Pydantic mengurainya huruf per huruf. Corannya ada
di lapisan repositori, satu satunya lapisan yang memang tahu SQL.

## Keamanan yang sudah ada

| | |
| --- | --- |
| CORS | daftar asal disebut satu satu, tidak pernah `*` |
| Rate limit | Redis, per IP, IP-nya diringkas SHA-256 bergaram acak per proses |
| SQL injection | seluruh kueri berparameter, tanpa pengecualian |
| Kebocoran galat | 500 hanya mengirim kalimat umum, rinciannya ke log |
| Log | JSON terstruktur, **tanpa query string**, tempat rahasia paling sering bocor |

Redis mati tidak menutup situs: pembatas laju meneruskan permintaan. Pembatas
yang mematikan layanan saat cache-nya mati merugikan lebih banyak daripada
yang dicegahnya.

Autentikasi belum ada. Sampai Fase 4 selesai, **seluruh titik akhir publik dan
tidak satu pun bisa menulis**.

## Autentikasi

Fase 4. Sudah jalan dan diuji.

| Method | Jalur | Otorisasi |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | publik, dibatasi laju |
| POST | `/api/v1/auth/refresh` | cookie refresh |
| POST | `/api/v1/auth/logout` | cookie refresh |
| POST | `/api/v1/auth/logout-semua` | admin |
| GET | `/api/v1/auth/saya` | admin |

Memasang sandi:

```bash
python backend/db/buat_admin.py
```

Sandinya diminta lewat prompt, tidak pernah lewat argumen. Argumen tersimpan
di riwayat shell dan terlihat di daftar proses.

### Yang dijaga

| | Cara |
| --- | --- |
| Sandi | Argon2id, parameter RFC 9106, di-hash ulang diam diam saat parameternya naik |
| Access token | JWT HS256, umur 15 menit. Tidak bisa dicabut, jadi dibuat cepat mati |
| Refresh token | cookie HttpOnly Secure SameSite=Strict, **tidak pernah masuk badan jawaban** |
| Putaran | tiap refresh menerbitkan token baru dan mematikan yang lama |
| Token bekas pakai | ditolak 401 |
| Pencabutan | di Postgres, bukan Redis, supaya tidak lenyap saat cache dinyalakan ulang |
| Yang disimpan | hanya SHA-256 tokennya. Basis data yang bocor tidak memberi kunci masuk |
| Tebak sandi | lima kegagalan per 15 menit lalu 429 |
| Alamat IP | diringkas SHA-256, tidak pernah disimpan apa adanya |
| Waktu jawaban | email asing dan sandi salah dijawab sama, termasuk lamanya |

Baris terakhir itu bukan hiasan. Kalau email yang tidak terdaftar dijawab
lebih cepat, selisih waktunya saja sudah memberi tahu penebak email mana
yang ada, dan itu separuh pekerjaannya. Karena itu hash umpan yang sungguhan
tetap dihitung walau penggunanya tidak ada.

**Tanpa `JWT_SECRET`, seluruh jalur admin menjawab 503**, bukan terbuka
dengan rahasia bawaan. Rahasia bawaan adalah rahasia yang sudah bocor.

### Yang belum: passkey

Rancangan menyebut WebAuthn sebagai jalur masuk utama dan sandi sebagai
cadangan. Yang terpasang sekarang baru cadangannya. Passkey menuntut pustaka
tersendiri dan alur pendaftaran perangkat, dan bab 15.8 melarang membuat
protokol kriptografi sendiri, jadi itu pekerjaan tersendiri dengan ujinya
sendiri, bukan tempelan.
