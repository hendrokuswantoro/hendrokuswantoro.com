# Keamanan

Bab 11 dan 22 dokumen standar. Isinya apa yang sudah terpasang, satu temuan
yang belum selesai, dan alasan kenapa belum.

## Yang sudah terpasang

| | Nilai | Diperiksa oleh |
| --- | --- | --- |
| TLS | dipaksa Cloudflare, HSTS 2 tahun, preload | `kesehatan.yml` |
| CSP | `script-src 'self' blob:`, tanpa `unsafe-inline` | `test_terbit.py` |
| Clickjacking | `X-Frame-Options: DENY`, `frame-ancestors 'none'` | `test_terbit.py` |
| MIME sniffing | `X-Content-Type-Options: nosniff` | `test_terbit.py` |
| Referrer | `strict-origin-when-cross-origin` | `test_terbit.py` |
| Izin peramban | geolocation, camera, microphone, payment semuanya ditutup | `_headers` |
| Rahasia | tidak ada satu pun di git, disisir tiap push | `ci.yml`, `test_peta.py` |

Situs ini tidak menerima masukan dari siapa pun. Tidak ada formulir, tidak ada
login, tidak ada komentar, tidak ada basis data. Seluruh permukaan serangan
yang biasa dibahas di bab 11 — injeksi SQL, CSRF, brute force, SSRF — tidak
punya pintu masuk di sini. Yang tersisa hanya dua: berkas yang disajikan, dan
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

## Temuan yang belum selesai

### Next.js di `next/`

Port Next.js membawa kerentanannya sendiri dan jumlahnya banyak. Port itu
**tidak pernah dibangun dan tidak pernah terbit**; tidak ada satu paket npm
pun yang sampai ke pengunjung. `npm audit` di CI karena itu mencetak
laporannya tetapi tidak menggagalkan pipeline. Begitu port itu benar benar
diterbitkan, aturan ini wajib dibalik.
