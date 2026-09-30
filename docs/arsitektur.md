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
| Yang terbit | ya, ini yang hidup | tidak, meski sudah bisa dibangun |
| Perlu Node | tidak | ya |
| Peta | `assets/js/peta.js` | `next/components/WorkMap.tsx`, `peta/gaya.ts`, `peta/bangun.ts` |

Versi statis yang terbit. Versi Next.js ada karena diminta di spesifikasi dan
disimpan tetap sejalan.

Sampai 13 September 2026 port itu **tidak pernah dibangun sekali pun**, sebab
mesin tempat situs ini ditulis tidak punya Node, dan kalimat itu berdiri di
sini berhari hari sesudah berhenti benar. Sekarang Node 24 terpasang,
`npm run build` sudah dijalankan di mesin ini, dan `next/out/` ada. Yang
belum berubah cuma satu: keluarannya tetap tidak diterbitkan.

Yang menjaga port kedua tidak diam diam rusak ada tiga: `tests/test_peta.py`
memaksa keduanya memuat lapisan peta yang sama persis dengan urutan sama,
`tools/gaya_next.py` membangkitkan CSS-nya dari `assets/css/style.css`
sehingga sistem desainnya tidak bisa bercabang, dan pekerjaan `Type Check` di
CI menjalankan `tsc --noEmit` beserta `npm run build`.

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

38 lapisan, disusun dari tanah sampai nama. Urutan lapisan nama sengaja dari
yang terkecil ke yang terbesar, sebab MapLibre menempatkan simbol dari
tumpukan paling atas ke bawah.

## Alasan di balik berkas konfigurasi

Sampai 30 September 2026 alasan di bawah ini tertulis sebagai komentar di
berkasnya masing masing. Sejak itu `tools/cari_komentar.py` juga memeriksa
berkas requirements, `.gitignore`, `.gitattributes`, `_headers`,
`_redirects`, `.env.example`, skrip PowerShell, dan berkas batch, jadi
alasannya tinggal di sini. Keterangan tiap variabel di `.env.example` ada di
`docs/lingkungan.md`.

### `backend/requirements.txt`

Kebutuhan uji dipisah ke `tests/requirements.txt` supaya pytest tidak pernah
ikut ke server. Versinya dinaikkan 13 September 2026 sesudah pip-audit
menemukan 24 temuan pada dua paket; rinciannya di `docs/audit-keamanan.md`.

- **starlette** disebut tersurat meski ia dependensi fastapi. Tanpa baris itu
  pip memasang starlette mana pun yang memenuhi `>=0.46.0`, termasuk 0.48.0
  yang membawa sembilan temuan. Batas bawah dependensi bukan pilihan versi.
- **email-validator** dituntut `EmailStr` di `backend/api/v1/auth.py`.
  Pydantic baru mengimpornya saat modelnya dibangun, jadi ketiadaannya tidak
  terlihat sampai aplikasi dimuat. Di pemasangan bersih, termasuk CI,
  `import backend.main` langsung gagal. Ketahuan lewat CI yang gagal tiga kali
  berturut turut, bukan lewat membaca kode.
- **webauthn** membawa cryptography, cbor2, asn1crypto, dan pyOpenSSL, supaya
  tidak ada satu baris pun kriptografi buatan sendiri di jalur masuk.
- **qrcode** menggambar kode QR authenticator tanpa Pillow; yang dipakai hanya
  matriksnya, dan SVG-nya digambar sendiri di `backend/layanan/totp.py`. Ia
  menggantikan layanan "buat QR gratis" mana pun: alamat otpauth MEMUAT
  rahasia TOTP-nya, jadi mengirimnya ke pembuat QR pihak ketiga berarti
  menyerahkan faktor kedua.
- **opencv-python-headless** untuk verifikasi wajah yang opsional, tanpa GTK
  dan tanpa jendela sebab server tidak punya layar. Modelnya (37 MB) tidak ikut;
  ia diunduh `tools/ambil_model.py` dan dicatat sidiknya. Tanpa model,
  verifikasi wajah mati dan halaman keamanannya mengatakan begitu.
- **python-multipart** dituntut jalur unggah foto dan video. Ia dependensi
  opsional FastAPI, jadi ketiadaannya baru terlihat saat `import backend.main`,
  sama seperti email-validator. Batas bawahnya bukan selera: 0.0.18 menutup
  penolakan layanan lewat multipart yang disusun khusus, dan jalur unggah
  justru menerima multipart dari luar.

### `tests/requirements.txt`

Hanya untuk uji, supaya pelari uji tidak pernah sampai ke server. PyYAML
dipakai `tools/periksa_alur.py` untuk membaca `.github/workflows`; CI
memasangnya sendiri di langkah Lint, yang tidak memasang berkas ini.

### `.gitignore`

- `.env` dan `.env.*` tidak pernah masuk git, kecuali `!.env.example`. Tanpa
  pengecualian itu `.env.example` ikut terjaring, dan satu satunya keterangan
  variabel apa saja yang dibutuhkan hanya ada di mesin penulisnya. Sudah
  pernah terjadi.
- `assets/js/konfigurasi.js` dan `cadangan/` memuat kunci atau salinannya.
- `assets/model/`, model pengenalan wajah 39 MB, diunduh `tools/ambil_model.py`.
- `/unggahan/` berisi foto dan video dari dashboard: milik satu pemasangan,
  bukan milik kode. Garis miring di depannya disengaja; alasannya di myweb.md.
- `.claude/worktrees/` adalah worktree sementara sesi Claude Code, berisi
  salinan seluruh repositori.
- `dist-*.zip` dibangun ulang kapan saja oleh `tools/build_dist.py`.

### `.gitattributes`

Satu jenis akhir baris di repositori (`eol=lf`), mesin apa pun penulisnya.
Gambar, font, arsip, dan ubin `.pbf` ditandai `binary` supaya tidak pernah
diubah. Berkas batch Windows (`*.cmd`) tetap CRLF: cmd.exe membaca berkas
batch dengan anggapan CRLF, dan pada berkas ber-LF label serta `goto` dikenal
meleset.

### `next/public/_headers` dan `next/public/_redirects`

Keduanya milik port Next, dibaca Cloudflare Pages atau Netlify kalau port itu
kelak diterbitkan di sana. CSP-nya memberi peta karya empat pengecualian:
host ubin dan gaya peta, pekerja `blob:` karena MapLibre membangun pekerjanya
saat berjalan, `blob:` dan `data:` untuk tekstur kanvasnya, dan gaya sebaris
yang ditulis MapLibre ke kontrol dan penandanya sendiri. Skrip tetap dibatasi
ke asal ini. Aturan di `_redirects` baru menyala setelah nama tanpa `www` dan
dengan `www` sama sama dipasang sebagai custom domain proyeknya.

### `next/eslint.config.mjs`

Dua aturan Next dimatikan per berkas, bukan lewat komentar `eslint-disable`
di kodenya. `@next/next/no-img-element` mati di empat komponen yang
menampilkan gambar unggahan dan gambar karya: port ini diekspor statis dengan
`images: { unoptimized: true }` di `next.config`, jadi `next/image` tidak
mengoptimalkan apa pun dan hanya menambah pembungkus. `@next/next/no-html-link-for-pages` mati di dua tempat di
dashboard yang menautkan ke `/`: situs publik bukan halaman aplikasi Next ini,
jadi tautannya wajib memuat halaman penuh, bukan navigasi klien.
