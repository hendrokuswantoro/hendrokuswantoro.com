# Arsitektur

Situs ini statis. Tidak ada basis data, tidak ada sesi, tidak ada server
aplikasi. Keputusan itu diambil sadar, dan pantas ditulis alasannya supaya
tidak ada yang membongkarnya tanpa sebab.

## Jalur sebuah permintaan

```
Pengunjung
   -> DNS Cloudflare
   -> Jaringan tepi Cloudflare, sekaligus CDN dan WAF
   -> Worker hendrokuswantoro-com, mode static assets
   -> berkas dari dist/
```

Tidak ada reverse proxy, load balancer, maupun origin server di belakangnya.
Yang di dokumen standar disebut CDN, WAF, TLS termination, dan load balancing
semuanya dikerjakan lapisan tepi Cloudflare. Menambahkan Nginx di belakangnya
berarti menambah satu titik gagal untuk pekerjaan yang sudah selesai.

## Kenapa statis

Situs ini punya empat halaman dan tiga tulisan. Isinya tidak berubah kecuali
penulisnya mengubahnya. Tidak ada yang login, tidak ada yang mengirim
formulir, tidak ada data pengunjung yang disimpan.

Basis data untuk isi yang tidak berubah adalah biaya tanpa imbalan: satu
proses lagi yang harus hidup, dicadangkan, ditambal, dan dibayar. PostgreSQL,
Redis, Keycloak, dan Kubernetes di dokumen standar itu untuk aplikasi kerja,
bukan untuk brosur empat halaman.

**Kalau suatu saat situs ini butuh yang berikut, keputusan di atas gugur:**
bagian kontak yang menerima kiriman, komentar di blog, halaman yang hanya
bisa dibuka setelah login, atau isi yang datang dari sumber luar saat halaman
dibuka. Sebelum salah satu itu ada, menambah backend adalah kompleksitas yang
dilarang bab 1 dokumen standar.

## Dua port, satu situs

| | Statis | Next.js |
| --- | --- | --- |
| Letak | akar repositori | `next/` |
| Yang terbit | ya, ini yang hidup | belum pernah dibangun |
| Perlu Node | tidak | ya |
| Peta | `assets/js/peta.js` | `next/components/WorkMap.tsx` |

Versi statis yang terbit. Versi Next.js ada karena diminta di spesifikasi dan
disimpan tetap sejalan, tetapi tidak pernah dibangun sekali pun: mesin tempat
situs ini ditulis tidak punya Node. Karena itu `tests/test_peta.py` memaksa
kedua port memuat lapisan peta yang sama persis dengan urutan sama, dan
pekerjaan `Type Check` di CI menjalankan `tsc --noEmit` di runner GitHub yang
punya Node. Itu satu satunya hal yang sejauh ini menjaga port kedua tidak
diam diam rusak.

## Rahasia

Hanya ada satu: token Mapbox.

```
GitHub  : tidak ada
Cloudflare : build variable MAPBOX_TOKEN
Build   : tools/konfigurasi.sh menulis assets/js/konfigurasi.js
Peramban: token ikut terunduh, memang begitu sifatnya
```

Token `pk.` Mapbox memang dirancang untuk hidup di peramban. Yang menahannya
disalahgunakan bukan kerahasiaan, melainkan pembatasan URL di
console.mapbox.com. Itu sebabnya token ini tetap tidak boleh masuk git:
bukan karena isinya rahasia, tetapi karena repositorinya publik dan token di
dalam repositori publik adalah undangan bagi pemindai otomatis.

## Peta

Peta dasarnya ditulis tangan di atas ubin vektor Mapbox Streets v8, bukan
diambil dari URL gaya Mapbox. Dua alasannya ada di README, dan keduanya
ditemukan lewat kegagalan, bukan lewat dokumentasi.

31 lapisan, disusun dari tanah sampai nama. Urutan lapisan nama sengaja dari
yang terkecil ke yang terbesar, sebab MapLibre menempatkan simbol dari
tumpukan paling atas ke bawah.
