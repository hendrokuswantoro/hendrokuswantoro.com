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
