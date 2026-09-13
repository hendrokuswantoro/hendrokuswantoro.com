# Penyisiran keamanan, 13 September 2026

Permintaannya: uji dari segala penjuru, jangan ada celah. Berkas ini hasilnya,
lengkap dengan yang **tidak** aman dan yang tidak bisa diamankan.

Satu kalimat lebih dulu, supaya tidak ada salah paham. Tidak ada yang bisa
berkata sebuah situs "tidak punya celah". Yang bisa dikatakan adalah: ini yang
diperiksa, ini caranya, ini yang ditemukan, ini yang sudah ditutup, dan ini
yang sengaja dibiarkan beserta alasannya. Siapa pun yang menjanjikan lebih
dari itu sedang menjual sesuatu.

---

## Yang ditemukan dan sudah ditutup

### 1. Tautan `javascript:` di dalam tulisan — XSS tersimpan

**Berat.** `tools/markah.py` meng-escape seluruh HTML dengan benar, dan
menolak HTML mentah di awal baris. Tetapi alamat di dalam `[label](alamat)`
hanya di-escape, tidak pernah diperiksa skemanya:

```
[klik](javascript:alert(1))   ->  <a href="javascript:alert(1">klik</a>
[klik](data:text/html,...)    ->  <a href="data:text/html,...">klik</a>
```

Tautan pertama menjalankan JavaScript di dalam asal situs ini begitu diklik.
Yang kedua membuka halaman karangan penulisnya, juga di atas asal situs ini,
yang berarti ia bisa meminta sandi dengan tampilan yang meyakinkan.

Penulisnya memang hanya pemilik situs. **Itu alasan memperbaikinya, bukan
alasan membiarkannya**: "hanya admin yang bisa" adalah anggapan yang gugur
pada hari ada penulis kedua, atau pada hari satu akun diambil orang.

Yang diperbaiki: skema dibatasi `https:`, `http:`, `mailto:`, dan alamat
relatif. Selain itu **ditolak**, bukan dibersihkan diam diam; tautan yang
dibersihkan tanpa sepengetahuan penulisnya akan terbit menuju tempat lain
daripada yang dimaksudnya.

Diperiksa di dua tempat: saat HTML dibangkitkan, **dan** saat API menerima
tulisan. Kalau hanya di tempat pertama, tulisan bertautan `javascript:` akan
diterima API dengan tenang, tersimpan di basis data, lalu meledak berhari hari
kemudian saat situsnya dibangun ulang, jauh dari orang yang menulisnya.

### 2. Dua puluh empat temuan di paket Python

`pip-audit` pada `backend/requirements.txt`:

| Paket | Lama | Temuan | Sekarang |
| --- | --- | --- | --- |
| pyjwt | 2.10.1 | 12 | **2.14.0** |
| starlette | 0.48.0 | 12 | **1.6.0** |

`pyjwt` adalah pustaka yang memverifikasi tiap token masuk. starlette adalah
yang menerima tiap permintaan.

Satu catatan tentang starlette: ia dependensi FastAPI, dan FastAPI hanya
menuntut `>=0.46.0` tanpa batas atas. Artinya pip boleh memasang 0.48.0 yang
bermasalah, dan memang itu yang terjadi. Karena itu versinya sekarang disebut
tersurat di `requirements.txt`. **Batas bawah dependensi bukan pilihan
versi.**

Sesudah dinaikkan: `No known vulnerabilities found`, dan 406 uji tetap lolos.

`pip-audit --strict` sekarang **memblokir** CI, tidak seperti `npm audit` yang
hanya dilaporkan. Bedanya nyata: paket Python berjalan di server yang
menghadap internet dan memegang basis data; paket di `next/` belum pernah
diterbitkan.

### 3. `/docs`, `/redoc`, dan `/openapi.json` terbuka

**Ringan, tetapi tidak ada gunanya dibiarkan.** Ketiganya menyerahkan peta
lengkap permukaan API kepada siapa pun yang membukanya, termasuk nama tiap
titik akhir admin dan bentuk persis badan permintaannya.

Itu bukan kerentanan dengan sendirinya. Alamat yang tidak diketahui bukan
pengaman, dan yang menjaga jalur admin tetap token, bukan ketidaktahuan. Tetapi
peta cuma cuma untuk orang yang tidak punya urusan di sana adalah pemberian
yang tidak perlu.

Sekarang tertutup kecuali `DOKUMEN_API=1`. Dinyalakan dengan sengaja, bukan
dimatikan dengan sengaja: yang bawaannya terbuka akan tetap terbuka di
produksi pada hari ada yang lupa mematikannya.

### 4. Draf tidak bisa dibuka, dan tanggal tidak bisa diubah

Bukan temuan keamanan, tetapi ditemukan dalam penyisiran yang sama dan
diperbaiki sekalian.

Penyunting membuka tulisan lewat jalur publik `/api/v1/blog/{slug}`, yang
hanya menjawab kalau statusnya sudah terbit. Jadi draf yang baru dibuat tidak
pernah bisa dibuka lagi; satu satunya jalan keluar adalah menerbitkannya lebih
dulu, yaitu kebalikan dari gunanya draf. Sekarang ada
`GET /api/v1/admin/blog/{slug}` di belakang `butuh_admin`.

Dan `PATCH` dengan kolom `tanggal` menjawab 200 tanpa mengubah apa apa:
skemanya menyebut `tanggal`, kolomnya bernama `terbit_pada`, dan terjemahan di
antara keduanya tidak pernah ada. Tersaring diam diam oleh daftar kolom yang
boleh diubah. Sekarang diterjemahkan, dan dibuktikan berubah.

---

## Yang diperiksa dan ternyata sudah benar

| | Cara memeriksanya | Hasil |
| --- | --- | --- |
| Injeksi SQL | seluruh kueri berparameter; nama kolom dinamis disaring terhadap daftar tetap | aman, dijaga `test_api.py` |
| CORS | preflight dari `https://jahat.example` | **400**, tanpa `Access-Control-Allow-Origin` |
| CORS, asal sah | preflight dari `https://www.hendrokuswantoro.com` | ACAO benar |
| Path traversal | `/api/v1/blog/../../etc/passwd`, `/admin/../backend/main.py` | 404 keduanya |
| Admin tanpa token | `GET /api/v1/admin/blog` | 401 |
| XSS di isi tulisan | `<script>` dan `<img onerror>` di dalam Markdown | di-escape |
| HTML mentah | `<div>` di awal baris | ditolak dengan nomor baris |
| Alg confusion JWT | `algorithms=["HS256"]` dipatok | tidak menerima `none` maupun RS256 |
| Token dari penerbit lain | uji dengan `iss` dan `aud` asing | ditolak |
| Sandi apa adanya | `SELECT sandi_hash` | `$argon2id$`, bergaram |
| Waktu jawaban masuk | hash umpan dihitung walau penggunanya tidak ada | email asing dan sandi salah sama |
| Tebak sandi | 6 kali salah berturut turut | 429 pada yang keenam |
| Alamat IP | kolom `alamat_hash` | SHA-256, 64 karakter, tanpa titik |
| Refresh token | isi tabel `sesi` | hanya SHA-256-nya |
| Token bekas pakai | dipakai ulang sesudah diputar | 401 |
| Cookie | header `set-cookie` | HttpOnly, Secure, SameSite=Strict |
| IDOR passkey | mencabut kunci milik orang lain | 404, bukan 403 |
| Passkey dari asal lain | tanda tangan untuk `hendrokuswantoro.com.jahat.id` | ditolak |
| Tantangan diputar ulang | tantangan bekas pakai | ditolak |
| Mass assignment | `TulisanUbah` hanya kolom yang disebut; `status` lewat titik akhir sendiri | aman |
| Galat membocorkan isi | penangan galat global | hanya "kesalahan di server" |
| Rahasia di git | `git grep` pola kredensial, dan `test_infrastruktur.py` | bersih |
| Header keamanan | `_headers` dan nginx | enam header, sama persis di keduanya |
| CSP | `script-src` | tanpa `unsafe-inline`, tanpa `unsafe-eval`, satu hash |
| Basis data menghadap internet | `docker-compose.yml` | terikat 127.0.0.1 saja |
| Redis | sama | terikat 127.0.0.1 saja |
| `X-Forwarded-For` | `--forwarded-allow-ips='127.0.0.1'` | hanya percaya nginx setempat |

---

## Yang sengaja dibiarkan, dan alasannya

### Tangkapan layar tidak bisa dicegah

Diminta, dan tidak bisa dikerjakan. **Tidak ada satu pun cara di web untuk
mencegah tangkapan layar.** Tidak ada API-nya, dan tidak akan ada: yang
menggambar layar adalah sistem operasi, bukan halaman.

Trik yang beredar, seperti mengaburkan halaman saat jendelanya kehilangan
fokus, tidak menghalangi tombol Print Screen sama sekali, tidak menghalangi
kamera ponsel, dan merusak halaman bagi pembaca yang jujur. Jadi tidak
dipasang.

Yang **dipasang** ada di `assets/js/app.js` bagian perlindungan isi, dan
batasnya disebut di sana juga:

- **bisa** menghentikan blok teks, Ctrl+C, klik kanan, seret teks keluar, dan
  cetak ke PDF
- **tidak bisa** menghentikan Lihat Sumber, JavaScript yang dimatikan, mode
  baca, `curl`, atau umpan RSS situs ini sendiri

Teksnya memang ada di dalam HTML, sebab di situlah mesin pencari dan pembaca
layar membacanya. Isi yang benar benar tidak boleh disalin adalah isi yang
tidak diterbitkan. Yang ini menaikkan ongkosnya, bukan menutup pintunya.

### npm audit tidak memblokir

Empat temuan `postcss` lewat `next`, dan menutupnya menuntut `next@16`, yang
merupakan perubahan besar. Ketiganya soal `sourceMappingURL` di dalam CSS yang
dikendalikan penyerang; CSS di sini seluruhnya milik sendiri, dan postcss
hanya berjalan saat membangun, tidak pernah di peramban pengunjung. Port
`next/` juga belum pernah diterbitkan.

Ini dicatat, bukan disembunyikan. Begitu port itu jadi versi yang dilihat
pengunjung, `|| true` di CI wajib dicabut.

### MapLibre di `assets/vendor/`

Versi 6.9.0, di atas 6.4.1 yang menutup GHSA-jrc7-96c5-q579. Ia tidak terlihat
`npm audit` karena memang tidak dipasang lewat npm; yang menjaganya langkah CI
tersendiri yang menuntut nomor versinya dan catatannya bergerak bersamaan.

---

## Yang belum diuji, dan saya tidak akan berpura pura sudah

- **Uji tembus oleh manusia.** Seluruh yang di atas saya kerjakan sendiri
  terhadap kode yang saya tulis sendiri. Itu punya titik buta yang menurut
  definisinya tidak saya lihat.
- **Perilaku di bawah beban.** Pembatas laju diuji benar setelannya, bukan
  diuji menahan serangan sungguhan.
- **Nginx dan systemd di server sungguhan.** Konfigurasinya lolos `nginx -t`
  dan berkas unitnya lolos pemeriksaan, tetapi keduanya belum pernah hidup.
- **Rantai pasok.** Paketnya diperiksa terhadap basis data kerentanan yang
  sudah diketahui. Paket yang jahat sejak lahir tidak akan muncul di sana.

## Menjalankan ulang penyisirannya

```bash
pip-audit -r backend/requirements.txt --strict
cd next && npm audit
python -m pytest                      # 406
python -m pytest -m peramban          # 43
sh tools/verifikasi.sh                # seluruhnya
```

Yang pertama sekarang memblokir CI. Temuan berikutnya akan ketahuan pada hari
ia diumumkan, bukan berbulan bulan kemudian.
