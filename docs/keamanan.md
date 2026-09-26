# Keamanan

Bab 11 dan 22 dokumen standar. Isinya apa yang sudah terpasang, satu temuan
yang belum selesai, dan alasan kenapa belum.

## Yang sudah terpasang

| | Nilai | Diperiksa oleh |
| --- | --- | --- |
| TLS | dipaksa Cloudflare, HSTS 2 tahun, preload | `kesehatan.yml` |
| CSP | `script-src 'self' blob:` plus satu hash sha256, tanpa `unsafe-inline` | `test_terbit.py`, `test_gaya.py` |
| Clickjacking | `X-Frame-Options: DENY`, `frame-ancestors 'none'` | `test_terbit.py` |
| MIME sniffing | `X-Content-Type-Options: nosniff` | `test_terbit.py` |
| Referrer | `strict-origin-when-cross-origin` | `test_terbit.py` |
| Izin peramban | geolocation, microphone, payment ditutup. Kamera ditutup di seluruh situs kecuali `= /admin`, tempat verifikasi wajah memerlukannya | `_headers`, `test_infrastruktur.py` |
| Rahasia | tidak ada satu pun di git, disisir tiap push | `ci.yml`, `test_peta.py`, `test_infrastruktur.py` |
| Masuk | Passkey WebAuthn, atau Argon2id + JWT, plus faktor kedua | `test_passkey.py`, `test_auth.py` |
| Faktor kedua | TOTP RFC 6238, kode email, kode pemulihan, verifikasi wajah. Batas masing masing di [keamanan-akun.md](keamanan-akun.md) | `test_keamanan_akun.py`, `test_keamanan_alur.py`, `test_wajah.py` |
| Sesi | refresh berputar, dicabut di Postgres, hanya SHA-256-nya disimpan | `test_auth.py` |
| Cadangan | AES-256-GCM, satu bit yang berubah gagal dibuka | `test_cadangan.py` |
| Layanan di VPS | systemd yang dikeraskan, soket Unix bukan porta | `test_infrastruktur.py` |
| Jalur tulis | menuntut sesi yang lahir lewat faktor kedua atau passkey | `test_faktor_kedua_wajib.py` |
| Cabut sesi | token akses ikut mati seketika, bukan 15 menit kemudian | `test_cabut_sesi.py` |
| Unggahan | jenis dari bita pertamanya, kuota ruang, dan pembuang EXIF | `test_berkas.py`, `test_metadata.py` |
| CSP | tiap halaman disajikan dengan tajuk produksinya lalu dibuka Chromium | `test_csp.py` |
| Kabar | surat saat ada yang masuk dari perangkat baru | `test_kabar_keamanan.py` |

**Permukaan serangannya sudah tidak sekecil dulu.** Kalimat di tempat ini dulu
berbunyi: tidak ada formulir, tidak ada login, tidak ada basis data, jadi
injeksi SQL, CSRF, dan brute force tidak punya pintu masuk. Itu benar sampai
Fase 1. Sekarang ada basis data, ada yang login, dan ada jalur yang menulis.

Yang menggantikannya bukan kalimat yang lebih menenangkan melainkan daftar
yang bisa diperiksa:

| Pintu yang terbuka | Yang menjaganya |
| --- | --- |
| Injeksi SQL | seluruh kueri berparameter, dan SQL hanya ada di lapisan repositori, dijaga `test_api.py` |
| CSRF | cookie refresh `SameSite=Strict`, dan seluruh jalur tulis menuntut header `Authorization`, yang tidak ikut terkirim sendiri |
| Tebak sandi | lima kegagalan per 15 menit lalu 429, plus pembatas laju nginx 10 per menit di `/api/v1/auth/` |
| Halaman palsu | passkey terikat pada `rp_id`; tanda tangan untuk alamat lain tidak berlaku |
| Token yang bocor | access token mati dalam 15 menit, refresh diputar dan yang lama langsung mati |
| Berkas cadangan yang bocor | terenkripsi sebelum keluar dari mesin |

Yang tersisa sama seperti dulu, dan tidak hilang: berkas yang disajikan, dan
pustaka pihak ketiga yang ikut terunduh ke peramban.

## Pengerasan 19 September 2026

Delapan hal, dan yang pertama bukan pengerasan melainkan perbaikan.

### 1. CSP mematikan seluruh dashboard, dan tidak ada yang tahu

Halaman `/admin` disajikan beserta tajuk CSP produksinya sendiri lalu dibuka
Chromium. Hasilnya:

    Refused to execute inline script because it violates the following
    Content Security Policy directive: "script-src 'self' blob: 'sha256-...'"

Skrip dashboard sebaris 44 KB. Hash itu milik skrip tema tiga baris di situs
publik. Dashboard mati total di balik nginx: tombol Masuk diam, tidak ada
pesan apa pun di layar, dan jejaknya hanya di konsol.

Belum merusak apa pun sebab VPS-nya belum pernah ada. Ia pasti terjadi di hari
pertama ia ada.

Gaya dan skripnya sekarang berkas sendiri, ketujuh belas atribut `style=` di
markup diganti kelas, dan CSP dashboard jadi lebih ketat daripada CSP situs
publik: tanpa hash, tanpa `'unsafe-inline'`, tanpa satu pun asal ubin peta.

`style-src` di seluruh situs juga tidak lagi menyebut `'unsafe-inline'`.
Kalimat lama di `_headers` mengatakan MapLibre menulis gaya sebaris ke
kontrolnya sendiri sehingga izin itu wajib. Itu keliru untuk MapLibre 6: ia
menulis lewat CSSOM, dan CSSOM tidak dijaga `style-src`. Terukur nol
pelanggaran di lima halaman, peta terbuka penuh.

**Yang seharusnya sudah ada sejak dulu:** `tests/test_csp.py`. CLAUDE.md sudah
melarang menguji CSP tanpa tajuknya, dan larangan tanpa uji cuma kalimat.

### 2. Jalur tulis menuntut faktor kedua

Sebelumnya faktor kedua sepenuhnya pilihan: kalau TOTP belum dinyalakan, sandi
saja membuka jalur yang menerbitkan tulisan dan mengunggah berkas.

Sekarang sesi mencatat apakah ia lahir lewat faktor kedua, klaim `f2` di dalam
token membawanya, dan `butuh_admin_kuat` menjaga router tulis. Passkey dihitung
setara: ia terikat perangkat dan terikat alamat situs, jadi menuntut TOTP di
atasnya berarti menuntut faktor yang lebih lemah untuk menjaga yang lebih kuat.

**Halaman keamanan sengaja tidak ikut dijaga penjaga yang kuat.** Kalau ia ikut
ditutup, pemilik yang belum punya TOTP tidak akan pernah bisa memasangnya.
`FAKTOR_KEDUA_WAJIB=false` ada untuk pemulihan: mesin baru, TOTP hilang, kode
pemulihan ikut hilang.

### 3. Sesi yang dicabut mematikan token aksesnya sekarang

Access token adalah JWT dan tidak pernah ditanyakan ke basis data. Mencabut
sesi dulu hanya mematikan refresh token-nya; token aksesnya tetap sah sampai
lima belas menit berikutnya. Lima belas menit terdengar pendek sampai diingat
kapan tombolnya ditekan: "keluarkan perangkat lain" ditekan justru saat
pemiliknya curiga.

Token sekarang membawa `sid`, dan tiap sesi yang dicabut masuk daftar cabut di
Redis selama sisa umur token. Satu pembacaan Redis per permintaan, di jalur
yang sudah memanggil Redis untuk pembatas laju.

**Tanpa Redis, pemendekan ini tidak berlaku,** dan halaman keamanan
mengatakannya alih alih mendiamkannya.

### 4. Kunci jaringan untuk /admin

`map $admin_boleh` di konfigurasi nginx, mati secara bawaan. Isi daftarnya,
lalu hilangkan tanda pagar pada `if ($admin_boleh = 0) { return 404; }`.
Menjawab 404, bukan 403: 403 memberi tahu bahwa ada sesuatu di sana.

Untuk kebanyakan orang yang alamat rumahnya berganti, yang lebih cocok adalah
Cloudflare Access di depannya, yang memakai identitas dan bukan alamat.

### 5. Kabar yang datang sendiri

Jejak keamanan hanya terbaca kalau ada yang membukanya, dan orang yang akunnya
diambil orang lain tidak sedang membukanya. Sekarang ada surat untuk masuk dari
perangkat yang belum pernah terlihat, dan untuk tiap perubahan pada jalan masuk
itu sendiri.

Isinya tidak memuat alamat IP, token, maupun kode apa pun: surat bisa nyasar,
dan yang nyasar tidak boleh jadi hadiah. Kegagalan mengirim tidak pernah
menggagalkan yang memicunya.

Tertahan `SMTP_HOST` yang masih kosong. Sampai itu diisi, suratnya ditulis ke
`cadangan/surat/` dan `terkirim=False`, seperti seluruh surat lain di sini.

### 6. Batas ruang unggahan, dan pembuang metadata foto

Batas per berkas tidak menjaga apa apa terhadap yang mengunggah seribu berkas,
dan cakram yang penuh mematikan PostgreSQL. Sekarang ada batas total, batas
jumlah, dan batas per hari, diperiksa **sebelum** berkasnya ditulis.

Metadata EXIF bisa dibuang lewat kotak centang, mati secara bawaan. Yang bisa
dibuang JPEG, PNG, dan WebP; GIF dan AVIF **ditolak** kalau pembuangan diminta,
sebab membuang setengah lalu mengaku sudah bersih lebih berbahaya daripada
tidak membuang sama sekali.

### 7. Pengguna basis data dengan hak terkecil

`infrastructure/postgres/hak_terkecil.sql`. `hk_app` boleh SELECT, INSERT,
UPDATE, DELETE, dan tidak boleh CREATE, DROP, ALTER, atau TRUNCATE. Migrasi
dijalankan pemilik skemanya, lewat DSN yang berbeda.

Injeksi SQL sudah dijaga kueri berparameter dan oleh `test_api.py`. Ini lapis
kedua, dan gunanya justru pada hari lapis pertama ternyata bocor: yang
membedakan gangguan dari bencana biasanya bukan apakah ada yang masuk,
melainkan seberapa jauh ia bisa melangkah.

### 8. Memutar JWT_SECRET tanpa mengeluarkan semua orang

```
# 1. pindahkan yang lama, isi yang baru
JWT_SECRET_LAMA=<nilai lama>
JWT_SECRET=<nilai baru>

# 2. muat ulang layanannya
sudo systemctl restart hk-api

# 3. tunggu lima belas menit, yaitu umur token akses

# 4. KOSONGKAN JWT_SECRET_LAMA, lalu muat ulang sekali lagi
```

Langkah empat bukan kerapian. Medan yang dibiarkan terisi berarti rahasia lama
tetap berlaku selamanya, dan rotasinya tidak menutup apa apa.

Yang lama **hanya** dipakai memeriksa, tidak pernah untuk menandatangani, jadi
rotasinya selalu bergerak satu arah.

## Audit 26 September 2026

Audit pra peluncuran, sepuluh temuan, semuanya diperbaiki hari itu juga.
Tidak ada yang Critical. Uji untuk tiap temuan ada di
`tests/test_temuan_audit.py`.

| # | Tingkat | Temuan | Perbaikannya |
| --- | --- | --- | --- |
| 1 | High | Akun berpasskey bisa diambil alih dengan sandi saja: masuk dengan sandi, hapus passkey pemiliknya, daftarkan passkey sendiri | Passkey ikut dihitung sebagai faktor. `butuh_admin_pendaftar` hanya mengizinkan faktor pertama dari sesi lemah. Menghapus faktor menuntut sesi kuat |
| 2 | Medium | Lewat soket Unix, uvicorn tidak punya alamat klien, jadi pembatas laju aplikasi mati dan jejak keamanan memakai satu alamat untuk semua orang | `--forwarded-allow-ips='*'`, dan nginx menimpa `X-Forwarded-For` dengan `$remote_addr` |
| 3 | Medium | TOTP dan kode pemulihan boleh ditebak tanpa batas selama tiketnya hidup | Lima kali salah per akun dalam lima belas menit, dicatat di `gagal_masuk` |
| 4 | Medium | Wajah, yang bisa ditembus rekaman video, menerbitkan sesi kuat | Masuk lewat wajah menerbitkan sesi lemah |
| 5 | Medium | Siapa pun yang tahu email admin bisa menguncinya di luar dengan lima sandi salah tiap lima belas menit | Batas ketat per pasangan email dan alamat, batas per email dua puluh kali lebih longgar |
| 6 | Low | Kode TOTP yang sudah dipakai diterima lagi, padahal keterangan di `totp.py` berjanji menolaknya | Kolom `totp_langkah_terakhir`, migrasi 0008 |
| 7 | Low | Tag, label tanggal, lama baca, judul, dan paragraf pembuka masuk halaman blog tanpa escape, dan escape `data-ind` dibatalkan `innerHTML` | Semua kolom di-escape, `data-ind` dua kali lewat `markah.untuk_ind()`, JSON-LD lewat `json.dumps` |
| 8 | Low | Token verifikasi email di query string, jadi tercatat di log akses nginx | Tokennya di fragmen `#`, yang tidak pernah dikirim ke server |
| 9 | Low | Nilai bawaan CORS memuat alamat pengembangan http | Bawaannya hanya situs yang terbit |
| 10 | Low | Isi tulisan dan pratinjau tanpa batas panjang | 200.000 karakter untuk isi, 2.000 untuk paragraf pembuka |

Yang tidak bisa ditutup kode: akun yang belum punya faktor sama sekali tetap
bisa dipasangi faktor pertama oleh siapa pun yang tahu sandinya. Satu satunya
penutupnya adalah pemilik yang memasang passkey atau TOTP lebih dulu.

Yang diperiksa dan bersih: secret di berkas dan di seluruh riwayat git, SQL
injection, command injection, IDOR, cookie, header keamanan, dependensi
(`pip-audit` dan `npm audit`, nol kerentanan), dan kebocoran di log serta
jawaban galat selain temuan 8.

## Temuan yang sudah ditutup

### MapLibre GL JS, GHSA-jrc7-96c5-q579, CRITICAL — **selesai 12 September 2026**

`DOM.sanitize()` menelusuri `elem.attributes`, sebuah `NamedNodeMap` yang
hidup, sambil memanggil `removeAttribute()` di dalam perulangan yang sama,
sehingga atribut tetangga terlewat. Muatan seperti
`<details open onload="1" ontoggle="...">` kehilangan atribut pertamanya
tetapi yang kedua selamat dan berjalan. Terdampak: seluruh versi di bawah
**6.4.1**.

Situs ini sekarang membawa **6.9.0**.

**Kenapa naiknya tidak sekadar tukar berkas.** MapLibre 6 terbit sebagai ES
module saja. Sudah diperiksa: 5.24.0 masih punya bundel UMD tetapi tetap
terdampak; 6.4.1 dan 6.9.0 hanya punya `.mjs`. Yang berubah:

1. `app.js` memuatnya dengan `import()` dinamis lalu menaruh namespace-nya di
   `window.maplibregl`, tepat di tempat global lama berada, sehingga
   `peta.js` tidak berubah sama sekali
2. pustakanya kini **empat berkas**, bukan satu: `maplibre-gl.mjs`,
   `maplibre-gl-shared.mjs`, `maplibre-gl-worker.mjs`, dan CSS-nya
3. CSP `worker-src` harus menerima `'self'`

**Jebakan nomor tiga memakan waktu paling lama, dan patut dicatat.** MapLibre
4 membangun workernya dari blob, jadi `worker-src blob:` cukup. MapLibre 6
memuat workernya sebagai modul dari origin sendiri lewat `import.meta.url`.
Dengan aturan lama, gayanya termuat, `style.load` menyala, lalu **peta diam
selamanya**: tidak satu pun ubin diminta, `isStyleLoaded()` tetap false, dan
tidak ada satu pun galat, di konsol maupun di penangan `error` peta.
Pelanggaran CSP di dalam worker menyala di global worker itu, bukan di
dokumen, jadi pendengar `securitypolicyviolation` di halaman tidak
melihatnya.

Diverifikasi di peramban sesudah naik: 31 lapisan, gaya termuat, nol galat.
Pada zoom 16 terhitung 3.281 bangunan, 16 nama jalan, 11 titik POI, 11 panah
satu arah. Tombol 3D menegakkan 5.838 bangunan dengan terrain menyala.
Saklar bahasa tetap mengganti `text-field`. Kelima kontrol peta ada, tujuh
penanda karya ada.

Tiga uji menjaga supaya ini tidak mundur: keempat berkas pustaka wajib ada,
versinya wajib di atas 6.4.1, dan `worker-src` wajib memuat `'self'`.

**Yang tetap berlaku sesudah ditutup.** `script-src` tetap tidak boleh
menerima `'unsafe-inline'`. Sekarang alasannya bukan lagi menambal satu
celah tertentu, melainkan menahan seluruh keluarga serangan yang sama pada
celah berikutnya yang belum diketahui. Dijaga `tests/test_terbit.py`.
`FALLBACK_STYLE` juga tetap hanya hidup tanpa token, dan jangan dijadikan
bawaan: gaya jarak jauh membawa atribusi pihak ketiga.

### postcss di `next/`, GHSA-qx2v-qp2m-jg93 dan tiga lainnya, HIGH — **selesai 14 September 2026**

Empat advisory pada `postcss` di bawah 8.5.23, satu di antaranya high: XSS
lewat `</style>` yang tidak dilolos, dan tiga soal `sourceMappingURL` yang
bisa membaca berkas `.map` sembarangan. Semuanya masuk lewat `next@15.5.25`
yang membawa `postcss@8.4.31`.

`npm audit fix --force` menawarkan `next@16.3.5`, sebuah lompatan versi
mayor. Itu tidak dikerjakan. Yang dikerjakan `overrides` di
`next/package.json`:

```json
"overrides": { "postcss": "^8.5.28" }
```

8.5.28 masih satu mayor dengan 8.4.31, jadi ongkosnya jauh lebih kecil
daripada risiko menaikkan kerangka kerjanya. Sesudah itu `npm audit`
menjawab **nol**, dan port-nya tetap lolos `tsc --noEmit` serta `npm run
build`, ketiganya dijalankan, bukan diperkirakan.

Karena temuannya nol, langkah audit npm di CI **sekarang memblokir** pada
tingkat high. Sebelumnya ia mencetak laporan lalu selalu lolos, dengan alasan
port itu belum diterbitkan. Alasan itu masih benar, tetapi pemeriksaan yang
sudah gratis tidak ada gunanya dibiarkan tidak menjaga apa apa.

## Temuan yang belum selesai

Tidak ada.
