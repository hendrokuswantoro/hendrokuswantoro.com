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

## Temuan yang belum selesai

### MapLibre GL JS 4.7.1, GHSA-jrc7-96c5-q579, CRITICAL

`DOM.sanitize()` menelusuri `elem.attributes`, sebuah `NamedNodeMap` yang
hidup, sambil memanggil `removeAttribute()` di dalam perulangan yang sama.
Menghapus satu atribut menggeser sisanya satu indeks, sehingga atribut
tetangganya terlewat. Muatan seperti

```html
<details open onload="1" ontoggle="...">
```

kehilangan atribut pertamanya tetapi yang kedua selamat dan berjalan begitu
disisipkan lewat `innerHTML` pada kontrol atribusi. Nol klik.

Terdampak: seluruh versi di bawah **6.4.1**.

**Seberapa terpapar situs ini.** Yang melewati `DOM.sanitize()` adalah teks
atribusi. Di situs ini teks itu dua konstanta yang ditulis tangan di
`assets/js/peta.js`, dan sumber ubinnya didefinisikan dengan daftar `tiles`
langsung sehingga MapLibre tidak pernah mengambil TileJSON pihak ketiga.
Tidak ada jalur bagi penyerang memasok atribusi.

Satu pengecualian: `FALLBACK_STYLE` menunjuk gaya OpenFreeMap, dan gaya jarak
jauh membawa atribusinya sendiri. Jalur itu hanya hidup bila token Mapbox
tidak ada.

**Kenapa muatannya tetap tidak jalan.** CSP situs ini menyetel `script-src
'self' blob:` tanpa `'unsafe-inline'`. Penangan kejadian sebaris seperti
`ontoggle="..."` adalah skrip sebaris, dan peramban menolaknya tanpa
`'unsafe-inline'`. Jadi walaupun atribut itu selamat dari sanitizer, ia tidak
akan berjalan. Ini pertahanan berlapis yang memang gunanya untuk hari seperti
ini.

**Kenapa belum diperbaiki.** Perbaikannya menuntut naik ke 6.4.1 atau lebih,
dan **MapLibre 6 hanya terbit sebagai ESM.** Sudah diperiksa: 5.24.0 masih
punya bundel UMD tetapi tetap terdampak, sedangkan 6.4.1 dan 6.9.0 hanya
punya `maplibre-gl.mjs`. Situs ini memuat pustakanya lewat `<script src>`
biasa lalu membaca `window.maplibregl`, jadi naiknya bukan tukar berkas
melainkan pindah cara muat:

1. `app.js` harus memakai `import()` dinamis, bukan menyisipkan `<script>`
2. `peta.js` harus menerima modulnya, bukan membaca global
3. seluruh peta harus diuji ulang, sebab v5 memperkenalkan proyeksi globe dan
   perilaku kamera berubah antar versi mayor. Kode 3D di situs ini justru
   sudah disetel mengelilingi kebiasaan v4: lapisan `sky` yang tidak didukung,
   `isStyleLoaded()` yang tidak pernah benar selama ubin mengalir, dan terrain
   yang membatalkan animasi kamera pada centang yang sama

**Keputusan.** Ditunda, bukan diabaikan. Risikonya nyata tetapi tidak dapat
dieksploitasi pada konfigurasi sekarang, sedangkan migrasi ESM berisiko
merusak peta yang baru saja selesai disetel. Dikerjakan sebagai tugas
tersendiri dengan pengujian ulang penuh, bukan disisipkan ke pekerjaan lain.

Sampai itu terjadi:

- CSP **tidak boleh** menerima `'unsafe-inline'` pada `script-src`. Itu yang
  menahan muatannya. Dijaga `tests/test_terbit.py`.
- `FALLBACK_STYLE` hanya hidup tanpa token. Jangan menjadikannya bawaan.
- Versi yang dibawa dikunci dan diperiksa, supaya tidak ada yang mengira
  masalah ini sudah beres padahal belum. Dijaga `tests/test_peta.py`.

### Next.js di `next/`

Port Next.js membawa kerentanannya sendiri dan jumlahnya banyak. Port itu
**tidak pernah dibangun dan tidak pernah terbit**; tidak ada satu paket npm
pun yang sampai ke pengunjung. `npm audit` di CI karena itu mencetak
laporannya tetapi tidak menggagalkan pipeline. Begitu port itu benar benar
diterbitkan, aturan ini wajib dibalik.
