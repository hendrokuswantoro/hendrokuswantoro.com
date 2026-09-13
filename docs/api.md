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

## Passkey, WebAuthn

Jalur masuk utama menurut rancangan. Sandi tetap ada sebagai jalan pulang:
perangkat bisa hilang, dan akun yang satu satunya kunci ikut hilang bersama
ponselnya adalah akun yang terkunci selamanya.

| Method | Jalur | Butuh |
| --- | --- | --- |
| GET | `/api/v1/auth/passkey/siap` | tidak ada |
| POST | `/api/v1/auth/passkey/daftar/mulai` | admin |
| POST | `/api/v1/auth/passkey/daftar/selesai` | admin |
| POST | `/api/v1/auth/passkey/masuk/mulai` | tidak ada |
| POST | `/api/v1/auth/passkey/masuk/selesai` | tidak ada |
| GET | `/api/v1/auth/passkey` | admin |
| DELETE | `/api/v1/auth/passkey/{id}` | admin |

Verifikasinya seluruhnya lewat pustaka `webauthn`. Tidak ada satu baris pun
kriptografi buatan sendiri, sesuai larangan bab 15.8.

### Kenapa passkey, sebenarnya

Bukan karena lebih praktis. Sandi bisa diketikkan ke halaman palsu; passkey
tidak bisa. Kunci privatnya tidak pernah meninggalkan perangkat, dan tanda
tangannya terikat pada `rp_id`, jadi halaman yang alamatnya bukan alamat ini
tidak akan pernah mendapat tanda tangan yang berlaku. Sebanyak apa pun sandi
di-hash, ia tidak punya pertahanan yang setara.

### Yang dijaga

| | Cara |
| --- | --- |
| Tantangan | lahir di server, sekali pakai, umur 5 menit |
| Sekali pakai | `UPDATE ... RETURNING` satu pernyataan, bukan baca lalu tandai |
| Tujuan tantangan | ikut disimpan; tantangan pendaftaran tidak bisa dipakai untuk masuk |
| Tantangan mana | dibaca dari `clientDataJSON`, bagian yang ikut ditandatangani |
| rp_id dan origin | dari environment, tidak pernah ditebak dari header `Host` |
| Penghitung | nilai yang mundur ditolak: kredensialnya disalin |
| Yang disimpan | hanya kunci publik. Tabelnya bocor seluruhnya pun tidak memberi jalan masuk |
| Mendaftar | menuntut sudah masuk. Titik akhir pendaftaran yang terbuka adalah pintu belakang |
| Verifikasi pengguna | `required`, bukan `preferred` |
| Mencabut milik orang lain | 404, bukan 403 |

`allow_credentials` sengaja dikosongkan saat masuk. Menyebutkan daftar
kredensial milik sebuah email berarti memberi tahu siapa pun yang bertanya
bahwa email itu terdaftar dan punya berapa kunci. Passkey discoverable tidak
membutuhkannya: perangkatnya sendiri yang tahu kunci mana yang cocok.

### Konfigurasi

```
WEBAUTHN_RP_ID=hendrokuswantoro.com
WEBAUTHN_ASAL=["https://www.hendrokuswantoro.com"]
```

`rp_id` adalah nama host saja, tanpa skema dan tanpa porta. Tanpa keduanya
seluruh jalur passkey menjawab 503, bukan menebak nilainya dari permintaan:
header `Host` datang dari peramban, dan memercayainya berarti membiarkan
penyerang memilih `rp_id` sendiri.

### Bagaimana ini diuji tanpa menyentuh kunci keamanan

`tests/otentikator.py` adalah authenticator tiruan yang benar benar membuat
pasangan kunci P-256 dan benar benar menandatangani, dan tanda tangannya
diverifikasi pustaka yang sama dengan yang dipakai produksi. Ia juga sengaja
bisa berbohong: `tanda_tangan_palsu` dan `mundurkan_penghitung` ada supaya
ada yang membuktikan servernya menolak.

Sembilan belas uji di `tests/test_passkey.py`, dan sebagian besarnya menguji
penolakan, bukan keberhasilan.

## Jalur admin

Fase 5. Seluruhnya di belakang `butuh_admin`, tanpa pengecualian.

| Method | Jalur | Fungsi |
| --- | --- | --- |
| GET | `/api/v1/admin/blog` | semua tulisan, termasuk draf |
| POST | `/api/v1/admin/blog` | tulisan baru, mulai sebagai draf |
| PATCH | `/api/v1/admin/blog/{slug}` | sunting sebagian |
| POST | `/api/v1/admin/blog/{slug}/status` | draf, terbit, atau arsip |
| DELETE | `/api/v1/admin/blog/{slug}` | hapus |

Tulisan baru **selalu** mulai sebagai draf. Tidak ada jalur yang menerbitkan
dan membuat sekaligus: menerbitkan harus jadi tindakan tersendiri yang
disengaja.

### Aturan yang sama ditegakkan dua kali

Dua bahasa harus punya jumlah dan urutan blok yang sama. Aturan itu sudah
dijaga pembangkit situs statis sejak Fase 0, dan sekarang dijaga lagi di
skema masuk API.

Itu bukan pengulangan yang sia sia. Keduanya pintu masuk yang berbeda: satu
dari berkas, satu dari dashboard. Aturan yang hanya dijaga di satu pintu
adalah aturan yang bisa dilewati lewat pintu satunya.

Panjang teks juga dibatasi di skema masuk, bukan diserahkan ke lebar kolom
basis data. Kalau yang menolak cuma PostgreSQL, yang sampai ke penulis adalah
500 tanpa penjelasan.

## Fase 6: isi dari API

`tools/isi.py` sekarang punya dua implementasi `SumberIsi`:

```bash
python tools/bangun_tulisan.py                 # dari content/*.md
python tools/bangun_tulisan.py --sumber api    # dari basis data lewat API
```

**Keduanya menghasilkan HTML yang sama persis, sampai ke byte.** Itu bukti
bahwa `SumberIsi` benar benar antarmuka, dan bahwa Fase 0 tidak terbuang
saat basis datanya datang. Ada ujinya di `tests/test_admin.py`.

`SumberApi` memakai `urllib` dari pustaka standar, bukan requests atau httpx.
Pembangkit situs berjalan di mesin build Cloudflare, dan menambah dependensi
di sana berarti menambah satu hal lagi yang bisa gagal saat menerbitkan.
