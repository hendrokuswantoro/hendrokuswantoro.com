# Rancangan platform

Gabungan dua dokumen: `Personal web.docx` dan
`Spesifikasi_Teknis_Personal_Geospatial_Platform.docx`, didamaikan dengan
situs yang sudah hidup hari ini. Dokumen ini **rancangan**, belum
implementasi. Bab 15.2 kedua dokumen menuntut arsitektur dirancang sebelum
coding, dan ini pemenuhannya.

Ditulis 12 September 2026.

## 1. Dua dokumen, dua tujuan yang berbeda

Keduanya diminta untuk situs yang sama, tetapi yang dituju tidak sama.

| | Dokumen 1 | Dokumen 2 |
| --- | --- | --- |
| Judul sendiri | permintaan situs sederhana | *Production Ready Specification* |
| Sasaran | situs pribadi yang powerful | *miniature production-grade geospatial platform* |
| Halaman | Home, About, Project, (Blog) | ditambah Maps, Contact, Admin Dashboard |
| Basis data | disebut di tabel tumpukan | DDL lengkap, PostGIS, indeks GIST |
| Tempat jalan | tidak disebut | VPS Linux + Docker Compose + Nginx |
| Backend | disebut di tabel | FastAPI, lapisan Repository, JWT, Redis |

Dokumen 1 menyebut tumpukan teknologi sebagai daftar keinginan. Dokumen 2
menuntutnya sebagai sistem yang benar benar berjalan, lengkap dengan DDL,
`docker-compose.yml`, pipeline, dan delapan fase.

**Keduanya sepakat pada satu hal yang bertentangan dengan sisanya:** bab 15.1
di kedua dokumen menulis *jangan membuat kompleksitas yang tidak diperlukan.*

Pertentangan itu tidak bisa dihindari dengan kompromi kata kata, jadi
dituliskan terang terangan di sini: **untuk situs ini, infrastrukturnya
sendiri adalah salah satu isinya.** Bukan biaya yang harus ditekan, melainkan
barang yang dipamerkan. Dokumen 2 menyebutnya di bagian 14: platform ini
harus memperlihatkan kemampuan end-to-end, bukan sekadar menampilkan CV.

Dengan pembacaan itu, PostGIS dan FastAPI berhenti jadi kompleksitas yang
tidak diperlukan, sebab yang diperlukan memang keberadaannya.

Tetapi konsekuensinya harus ditanggung sadar, dan ada di bagian 11.

## 2. Yang sudah ada hari ini

| | Isi |
| --- | --- |
| Terbit di | Cloudflare Workers, static assets, tanpa server |
| Halaman | Home, About, Project, Blog, 404 |
| Tulisan blog | 3, masing masing satu berkas HTML yang ditulis tangan |
| Proyek | 7, tertanam di markup dan di larik JavaScript |
| Titik spasial | 7 pasang lng/lat di `assets/js/peta.js` |
| Kategori proyek | app, analysis, satellite, design |
| Peta | MapLibre, 31 lapisan di atas ubin vektor Mapbox |
| Dwibahasa | 280 atribut `data-ind`, 37 label, 10 alt |
| Uji | 154, semuanya membaca berkas |
| CI/CD | GitHub Actions, lima pekerjaan |
| Basis data | tidak ada |
| Biaya jalan | nol |

**Masalah yang memicu permintaan ini:** menulis satu tulisan blog berarti
menyalin berkas HTML, menulis dua bahasa berdampingan di atribut, lalu
memperbarui `sitemap.xml` dan menjalankan pembangkit umpan. Itu bukan cara
menulis, itu cara menyunting kode.

## 3. Keputusan pokok: di mana sistemnya berjalan

Ini persimpangan yang menentukan seluruh sisanya, dan biayanya nyata.

### Pilihan A, VPS penuh seperti Dokumen 2

Satu VPS Ubuntu, Docker Compose menjalankan Postgres+PostGIS, Redis, FastAPI,
Next.js, dan Nginx. Cloudflare di depannya sebagai DNS, CDN, dan WAF.

- **Untung:** persis seperti spesifikasi. Seluruh kemampuan yang ingin
  ditunjukkan benar benar berjalan, bukan diceritakan.
- **Rugi:** ada biaya bulanan. Server itu milik Anda: menambal kernel,
  memperbarui citra, memantau disk, memulihkan saat mati, semuanya jadi
  pekerjaan Anda. Situs yang hari ini tidak pernah bisa mati karena tidak
  punya server, mulai bisa mati.

### Pilihan B, tanpa server sama sekali

Tulisan blog disimpan sebagai berkas Markdown di repositori, dibangun jadi
HTML saat `git push`.

- **Untung:** menyelesaikan masalah menulis sepenuhnya, hari ini, tanpa biaya
  dan tanpa server. Menulis jadi: buat satu berkas `.md`, `git push`.
- **Rugi:** tidak ada PostGIS, tidak ada API, tidak ada dashboard. Tujuan
  Dokumen 2 tidak tercapai sama sekali.

### Pilihan C, hibrida bertahap — **yang saya sarankan**

Basis data adalah sumber kebenaran. Situs publik tetap statis, dibangun dari
basis data itu, bukan menanyakannya saat pengunjung datang.

```
Menulis  : Admin Dashboard -> FastAPI -> PostgreSQL + PostGIS
Menerbit : build -> tarik isi dari API -> HTML statis -> Cloudflare
Membaca  : Pengunjung -> Cloudflare -> HTML statis        (tanpa menyentuh server)
Peta     : Pengunjung -> Cloudflare -> /api/v1/maps/...   (menyentuh server)
```

- **Untung:** seluruh tumpukan Dokumen 2 benar benar berjalan dan bisa
  ditunjukkan. Tetapi halaman yang dibaca orang tetap statis, jadi tetap
  secepat sekarang, dan **kalau VPS-nya mati, situsnya tetap hidup.** Yang
  hilang hanya kemampuan menulis dan titik akhir peta yang hidup.
- **Rugi:** dua sumber isi yang harus dijaga tetap sinkron, dan satu langkah
  build tambahan antara menulis dan terbit.

Pilihan C menyerap Pilihan B sebagai fase pertamanya, asalkan sumber isinya
dirancang sebagai antarmuka sejak awal. Itu yang dilakukan bagian 5.

## 4. Arsitektur yang dirancang

```
                    MENULIS (jarang, satu orang)
  Admin -> HTTPS -> Cloudflare -> Nginx -> FastAPI -> PostgreSQL + PostGIS
                                             |            Redis (sesi, laju)
                                             +---------> S3 (gambar, GeoTIFF)

                    MENERBITKAN (dipicu, otomatis)
  GitHub Actions -> GET /api/v1/... -> pembangkit -> HTML statis -> Workers

                    MEMBACA (sering, semua orang)
  Pengunjung -> Cloudflare -> Workers static assets -> selesai
  Pengunjung -> Cloudflare -> Nginx -> FastAPI -> PostGIS   (hanya /api/v1/maps)
```

Tiga jalur dipisah sengaja, dan pemisahannya punya alasan yang bisa diuji:
halaman yang dibaca tidak boleh bergantung pada server yang bisa mati,
sedangkan bagian yang memang ingin dipamerkan justru harus benar benar hidup.

Pemisahan lapisan di backend mengikuti Dokumen 2 bagian 11:

```
Router (FastAPI)
  -> Schema (Pydantic)      validasi masuk dan keluar
  -> Service                aturan bisnis, tidak tahu SQL
  -> Repository             satu satunya yang tahu SQL
  -> PostgreSQL + PostGIS
```

## 5. Sumber isi sebagai antarmuka

Supaya fase pertama tidak terbuang saat fase kedua datang, pembangkit situs
tidak boleh tahu isi datang dari mana.

```python
class SumberIsi(Protocol):
    def tulisan(self) -> list[Tulisan]: ...
    def proyek(self) -> list[Proyek]: ...

class SumberBerkas:   # fase 1, membaca content/*.md
class SumberApi:      # fase 2, membaca /api/v1/...
```

Pembangkitnya memanggil antarmuka itu. Berpindah dari berkas ke basis data
berarti mengganti satu baris yang memilih implementasi, bukan menulis ulang
pembangkitnya. Ini penerapan Repository pattern yang diminta bab 15.4 pada
sisi yang biasanya dilupakan, yaitu sisi pembangkit.

## 6. Skema basis data

Dokumen 2 memberi DDL untuk `users`, `projects`, dan `spatial_layers`, lalu
menyebut tabel pendukung tanpa merincinya. Bagian ini merinci yang kurang dan
memperbaiki satu hal yang tidak ada di dokumen mana pun: **situs ini
dwibahasa, dan skema di Dokumen 2 tidak punya tempat untuk itu sama sekali.**

### Keputusan: dua kolom, bukan tabel terjemahan

Bahasanya tepat dua, keduanya selalu wajib ada, dan tidak akan bertambah.
Tabel terjemahan akan menambah join pada tiap query demi keluwesan yang tidak
akan pernah dipakai, dan yang lebih buruk, membuat "tulisan tanpa terjemahan"
jadi keadaan yang mungkin. Dengan dua kolom `NOT NULL`, keadaan itu mustahil.

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- pencarian blog

CREATE TYPE status_terbit AS ENUM ('draf', 'terbit', 'arsip');

CREATE TABLE blog_posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(150) UNIQUE NOT NULL,

    judul_en        VARCHAR(200) NOT NULL,
    judul_id        VARCHAR(200) NOT NULL,
    ringkas_en      VARCHAR(300) NOT NULL,
    ringkas_id      VARCHAR(300) NOT NULL,
    lede_en         TEXT NOT NULL,
    lede_id         TEXT NOT NULL,
    isi_en          TEXT NOT NULL,          -- Markdown
    isi_id          TEXT NOT NULL,          -- Markdown

    tag             VARCHAR(50) NOT NULL,
    status          status_terbit NOT NULL DEFAULT 'draf',
    terbit_pada     TIMESTAMPTZ,
    menit_baca      SMALLINT NOT NULL DEFAULT 1,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    diubah_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    penulis_id      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    CONSTRAINT terbit_punya_tanggal
        CHECK (status <> 'terbit' OR terbit_pada IS NOT NULL),
    CONSTRAINT menit_masuk_akal
        CHECK (menit_baca BETWEEN 1 AND 120)
);

CREATE INDEX idx_blog_terbit  ON blog_posts (status, terbit_pada DESC);
CREATE INDEX idx_blog_slug    ON blog_posts (slug);
CREATE INDEX idx_blog_cari_en ON blog_posts USING GIN (judul_en gin_trgm_ops);
CREATE INDEX idx_blog_cari_id ON blog_posts USING GIN (judul_id gin_trgm_ops);
```

`CONSTRAINT terbit_punya_tanggal` ada karena satu hal yang sudah terbukti
memakan korban di proyek lain: keadaan yang mustahil harus dibuat mustahil
oleh basis datanya, bukan diingat oleh kodenya. Tulisan berstatus terbit
tanpa tanggal terbit akan merusak urutan umpan RSS tanpa galat apa pun.

### Proyek, disesuaikan dengan yang sudah ada

DDL Dokumen 2 dipakai apa adanya, ditambah dwibahasa dan diselaraskan dengan
empat kategori yang sudah dipakai situs sekarang.

```sql
CREATE TYPE kategori_proyek AS ENUM ('app', 'analysis', 'satellite', 'design');

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(150) UNIQUE NOT NULL,
    judul_en        VARCHAR(200) NOT NULL,
    judul_id        VARCHAR(200) NOT NULL,
    ringkas_en      TEXT NOT NULL,
    ringkas_id      TEXT NOT NULL,
    peran_en        VARCHAR(200),
    peran_id        VARCHAR(200),
    kategori        kategori_proyek[] NOT NULL,
    teknologi       TEXT[] NOT NULL,
    gambar_url      VARCHAR(255),
    gambar_alt_en   VARCHAR(300),
    gambar_alt_id   VARCHAR(300),
    demo_url        VARCHAR(255),
    github_url      VARCHAR(255),
    unggulan        BOOLEAN NOT NULL DEFAULT FALSE,
    nama_lokasi     VARCHAR(100),
    geom            GEOMETRY(Point, 4326),
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT kategori_tidak_kosong CHECK (cardinality(kategori) > 0),
    CONSTRAINT titik_di_indonesia CHECK (
        geom IS NULL OR (
            ST_X(geom) BETWEEN 94 AND 142 AND ST_Y(geom) BETWEEN -12 AND 7
        )
    )
);

CREATE INDEX idx_projects_geom ON projects USING GIST (geom);
CREATE INDEX idx_projects_kategori ON projects USING GIN (kategori);
```

`titik_di_indonesia` menyalin uji yang sudah ada di `tests/test_peta.py` ke
dalam basis datanya. Aturan yang sudah dijaga di satu tempat lebih baik
dijaga di tempat yang tidak bisa dilewati.

**Catatan penting tentang `geom` pada proyek.** Titik ini adalah tempat
menggantungkan penanda di peta, bukan koordinat survei dan bukan batas
wilayah kajian. Keterangan itu sudah tertulis di bawah peta sekarang dan
wajib ikut berpindah ke dokumentasi basis datanya, supaya tidak ada yang
memakainya sebagai data lokasi yang presisi.

### Tabel sisanya

`users`, `spatial_layers`, `contacts`, `settings` mengikuti Dokumen 2.
`experiences`, `education`, `skills`, `certifications` ditunda: halaman About
sekarang sengaja pendek atas permintaan Anda sendiri, dan membuat empat tabel
untuk isi yang belum ada adalah kompleksitas yang dilarang bab 15.1.

## 7. Permukaan API

Mengikuti Dokumen 2 bagian 7, ditambah yang dibutuhkan alur menulis.

| Method | Endpoint | Fungsi | Otorisasi |
| --- | --- | --- | --- |
| GET | `/api/v1/blog` | daftar tulisan terbit, dua bahasa | Publik |
| GET | `/api/v1/blog/{slug}` | satu tulisan | Publik |
| GET | `/api/v1/projects` | daftar proyek | Publik |
| GET | `/api/v1/projects/{slug}` | detail proyek | Publik |
| GET | `/api/v1/maps/projects-spatial` | GeoJSON FeatureCollection | Publik |
| GET | `/api/v1/health` | kesehatan proses, basis data, cache | Publik |
| POST | `/api/v1/auth/login` | masuk, terbitkan token | Publik, dibatasi laju |
| POST | `/api/v1/auth/refresh` | putar refresh token | Cookie |
| POST | `/api/v1/auth/logout` | cabut sesi | Bearer |
| GET | `/api/v1/admin/blog` | termasuk draf | Admin |
| POST | `/api/v1/admin/blog` | tulisan baru | Admin |
| PATCH | `/api/v1/admin/blog/{id}` | sunting | Admin |
| POST | `/api/v1/admin/blog/{id}/terbit` | ubah status jadi terbit | Admin |
| POST | `/api/v1/admin/terbitkan` | picu build ulang situs statis | Admin |
| POST | `/api/v1/admin/media` | unggah gambar ke S3, kembalikan URL | Admin |

Satu keputusan yang berbeda dari Dokumen 2: **tidak ada `POST /api/v1/contact`
dan tidak ada formulir kontak.** Anda sudah dua kali meminta situs ini tanpa
bagian kontak. Permintaan Anda menang atas spesifikasi, dan tabel `contacts`
di Dokumen 2 ikut tidak dibuat.

## 8. Keamanan

Dokumen 2 bagian 8 dan bab 15.8 sampai 15.11 keduanya berlaku. Yang berubah
karena penggunanya tepat satu orang:

| | Rancangan | Alasan |
| --- | --- | --- |
| Masuk utama | **Passkey, WebAuthn/FIDO2** | untuk satu admin, passkey lebih aman sekaligus lebih mudah daripada kata sandi. Tidak ada yang bisa dicuri lewat phishing |
| Cadangan | Argon2id + TOTP | dipakai bila perangkat passkey hilang |
| Pemulihan | recovery codes sekali pakai | disimpan sebagai hash Argon2id |
| Token | access JWT pendek + refresh di cookie HttpOnly Secure SameSite=Strict | bab 15.10 |
| Otorisasi | RBAC dua peran, diverifikasi di backend | visitor tidak pernah punya token |
| Laju | Redis, per IP, ketat pada `/auth/login` | bab 15.11 |
| Rahasia | `.env` di luar git, `.env.example` di dalam | sudah jadi kebiasaan repo ini |
| SQL | parameterized, tanpa pengecualian | bab 15.11 |

Keycloak **tidak** dipakai. Bab 15.8 mengizinkan OAuth2/OIDC, tetapi
menjalankan penyedia identitas penuh untuk satu akun adalah kompleksitas yang
dilarang bab 15.1. WebAuthn memenuhi maksud babnya tanpa satu kontainer
tambahan.

## 9. Alur menulis satu tulisan, dari awal sampai terbaca

Ini yang sebenarnya Anda minta. Rancangannya diuji terhadap alur ini.

```
1. Buka /admin, masuk dengan passkey
2. Tulis judul, ringkasan, dan isi. Dua kolom berdampingan, Inggris dan
   Indonesia. Isinya Markdown, pratinjau langsung di sebelahnya
3. Simpan. Status draf. Belum terlihat siapa pun
4. Tekan Terbitkan
     -> status jadi terbit, terbit_pada terisi
     -> POST /api/v1/admin/terbitkan memicu GitHub Actions
5. Pipeline berjalan:
     tarik isi dari API -> bangun HTML dwibahasa -> bangkitkan sitemap dan
     feed -> uji 154 berkas -> deploy Cloudflare
6. Dua menit kemudian tulisan itu hidup, statis, dan bisa dibaca offline
   oleh Cloudflare walaupun VPS-nya mati
```

Langkah 5 memakai pipeline yang **sudah ada hari ini**. Tidak ada yang
dibuang. Yang ditambahkan hanya sumber isinya.

Dan satu hal yang hari ini tidak mungkin jadi mungkin: `menit_baca`,
`sitemap.xml`, `feed.xml`, dan daftar di halaman Blog semuanya terisi
sendiri. Sekarang keempatnya diurus tangan.

## 10. Struktur repositori dan perpindahannya

Dokumen 2 bagian 11 meminta struktur yang berbeda dari repositori sekarang.
Perpindahannya bertahap, bukan sekali potong.

```
hendrokuswantoro.com/
├── site/                  <- situs statis yang sekarang, dipindah utuh
│   ├── assets/ blog/ *.html
│   └── tools/
├── backend/               <- baru, FastAPI
│   ├── api/ core/ models/ schemas/ services/ repositories/
│   ├── migrations/        <- Alembic
│   └── tests/
├── frontend/              <- port Next.js yang sekarang di next/
├── spatial/               <- skrip ETL, data contoh
├── infrastructure/
│   ├── nginx/ docker/
│   └── docker-compose.yml
├── content/               <- fase 1, tulisan Markdown
├── docs/                  <- sudah ada
├── tests/                 <- sudah ada, 154 uji
└── .github/workflows/     <- sudah ada
```

**Yang tidak boleh rusak saat pindah:** `wrangler.toml` menunjuk `./dist`,
`tools/bangun_situs.sh` menyalin dari akar, dan 154 uji membaca jalur yang
sekarang. Ketiganya harus ikut diperbarui dalam commit yang sama dengan
pemindahannya, dan uji yang lolos sebelum pindah wajib lolos sesudahnya.

## 11. Biaya dan konsekuensi yang harus ditanggung sadar

Ini bagian yang biasanya tidak ditulis di dokumen arsitektur, dan karena itu
biasanya jadi penyesalan.

| | Sekarang | Sesudah Pilihan C |
| --- | --- | --- |
| Biaya bulanan | nol | satu VPS, kira kira 60 sampai 150 ribu, plus object storage |
| Yang bisa mati | tidak ada | VPS, Postgres, Redis, Nginx |
| Yang harus ditambal | tidak ada | kernel, citra Docker, dependensi Python |
| Cadangan | git | git plus `pg_dump` harian yang **wajib diuji pulihkan** |
| Permukaan serangan | berkas statis | ditambah satu halaman masuk yang menghadap internet |
| Waktu rawat | mendekati nol | beberapa jam per bulan, jujur saja |

Angka rupiah di atas perkiraan, bukan harga yang saya cek hari ini.

**Yang tidak berubah:** halaman yang dibaca pengunjung tetap statis di
Cloudflare. Kalau seluruh VPS mati, situsnya tetap terbaca. Itu satu satunya
alasan Pilihan C layak dipilih di atas Pilihan A.

**Satu kewajiban baru yang tidak boleh ditawar.** Begitu ada basis data, bab
15.18 berhenti jadi teori. Cadangan yang belum pernah dipulihkan belum
terbukti apa apa, dan pemulihan pertama tidak boleh dicoba pada hari datanya
benar benar hilang. Prosedurnya harus ditulis dan diuji sebelum tulisan
pertama masuk.

## 12. Fase pengerjaan

Delapan fase Dokumen 2 diurutkan ulang supaya masalah menulis selesai lebih
dulu, dan supaya tiap fase berdiri sendiri.

| Fase | Isi | Selesai bila |
| --- | --- | --- |
| 0 | `content/*.md` plus antarmuka `SumberIsi`, pembangkit membaca berkas | menulis tulisan baru cukup satu berkas Markdown dan `git push`. Tiga tulisan lama pindah tanpa berubah tampilannya |
| 1 | Docker Compose lokal: Postgres+PostGIS, Redis. Skema, migrasi Alembic, data awal dari isi yang sekarang | `docker compose up` memberi basis data terisi 7 proyek dan 3 tulisan |
| 2 | FastAPI: Router, Schema, Service, Repository. Titik akhir publik saja | `/api/v1/blog` dan `/api/v1/projects` menjawab, terdokumentasi di `/docs` |
| 3 | Spatial: `ST_AsGeoJSON`, `/api/v1/maps/projects-spatial`, peta membaca dari API | peta menggambar tujuh titik dari PostGIS, bukan dari larik JavaScript |
| 4 | Keamanan: passkey, JWT, RBAC, rate limiting | admin bisa masuk, visitor tidak pernah bisa menulis |
| 5 | Admin Dashboard: tulis, sunting, terbitkan, unggah gambar | tulisan baru bisa ditulis tanpa menyentuh berkas |
| 6 | `SumberApi`, pipeline menarik dari API | tekan Terbitkan, dua menit kemudian hidup |
| 7 | VPS, Nginx, deploy, cadangan terenkripsi, **uji pulihkan** | pemulihan pernah benar benar dijalankan dan berhasil |
| 8 | Uji peramban, peringatan, pengukuran performa | enam hal yang belum di `status.md` tertutup |

**Fase 0 sendirian sudah menyelesaikan masalah yang Anda sebut.** Fase 1
sampai 7 yang membuat platformnya jadi platform.

## 13. Yang belum diputuskan

Tiga hal, dan semuanya milik Anda, bukan milik saya.

1. **Pilihan A, B, atau C.** Rancangan ini menganggap C. Kalau ternyata B,
   bagian 6 sampai 11 tidak dikerjakan dan fase berhenti di 0.
2. **VPS di mana.** Penyedia dalam negeri lebih murah dan latensinya lebih
   baik untuk pembaca Indonesia; penyedia luar lebih matang alatnya.
3. **Kapan.** Fase 0 bisa selesai hari ini. Fase 1 sampai 7 adalah pekerjaan
   berminggu minggu, bukan berjam jam, dan tidak perlu dikerjakan berurutan
   tanpa jeda.

Tidak ada satu pun dari ketiganya yang menghalangi Fase 0 dimulai.
