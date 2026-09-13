# Pemecahan masalah

Yang sudah pernah terjadi, sebabnya, dan cara mengenalinya lagi.

## Peta polos abu abu, tanpa nama jalan dan batas wilayah

Tokennya tidak sampai. Peta jatuh ke OpenFreeMap, yang tidak membawa
bangunan, batas wilayah, tingkatan jalan, maupun nama tempat.

Periksa log build Cloudflare. Kalau tertulis

```
konfigurasi.sh: MAPBOX_TOKEN is not set.
```

berarti variabelnya belum ada di **Settings, Build variables**, atau ada
tetapi sebagai variabel runtime. Yang dibaca skrip build hanya variabel build.

Kalau lognya menyebut `token found` tetapi petanya tetap polos, sebabnya
pembatasan URL di console.mapbox.com tidak memuat alamat yang sedang dibuka.
Alamat `.workers.dev` dan `www.hendrokuswantoro.com` adalah dua alamat
berbeda bagi Mapbox.

## Deploy gagal di tahap Deploying

```
Invalid _redirects configuration: Line 4: Only relative URLs are allowed.
[code: 100324]
```

Cloudflare Pages menerima aturan lintas host di `_redirects`. Cloudflare
Workers tidak. Berkas itu sudah dihapus dan pengalihan tanpa www ke dengan
www pindah ke Redirect Rule di dashboard. Kalau berkas itu kembali, deploy
akan gagal lagi di tempat yang sama. Dijaga `tests/test_terbit.py`.

## Deploy berhenti sebelum sampai ke pengaturan build

```
There was a problem parsing the Wrangler configuration file.
```

Alur Workers yang baru menuntut `wrangler.toml` di akar repositori. Berkas
itu tidak mendeklarasikan kode Worker sama sekali, hanya menunjuk `./dist`.

## Perubahan tidak kelihatan di peramban padahal sudah terbit

`_headers` menyetel `/assets/*` jadi `immutable` selama setahun. Itu memang
yang diinginkan, dan itulah gunanya `?v=` di belakang tiap aset. Kalau
nomornya tidak ikut dinaikkan, peramban lama menyajikan berkas lama.

Naikkan nomor versinya di **semua** halaman sekaligus. Kalau hanya sebagian,
pengunjung menerima campuran lama dan baru. Dijaga
`tests/test_terbit.py::test_versi_seragam`.

Selama pengujian lokal, server ujinya menyetel `Cache-Control: no-store`.

## Nama jalan tidak muncul di zoom kota

Bukan soal data. `road` di Mapbox Streets membawa 1.617 ruas bernama di pusat
Yogyakarta pada zoom 14; yang tergambar dulu cuma 4.

Sebabnya urutan lapisan. MapLibre menempatkan simbol dari tumpukan paling
atas ke bawah, dan `nama-jalan` dulu berada paling bawah sehingga kalah
terus. Sekarang urutannya dari kecil ke besar.

## Nama negara hilang di zoom pulau

Sebab yang sama dari arah berbeda: 959 label permukiman pada zoom 4 memenuhi
seluruh kisi tabrakan sampai tidak satu pun nama negara kebagian tempat.
Sekarang jumlah permukiman disaring memakai `filterrank` bawaan Mapbox
seiring peta ditarik menjauh.

## Nama provinsi tidak ada

Bukan bug. Lapisan `place_label` Mapbox punya kelas `state`, tetapi untuk
Indonesia isinya kosong, sudah diperiksa dari zoom 4 sampai 9. Negara bagian
Australia muncul, provinsi Indonesia tidak.

Karena itu 38 nama provinsi dibawa sendiri di `PROVINSI_ID`. Koordinatnya
titik untuk menggantungkan label, bukan pusat resmi dan bukan batas. Garis
batasnya tetap dari lapisan `admin` Mapbox.

## Bangunan 3D tidak berdiri

Pernah terjadi karena tiga sebab berbeda, berurutan:

1. lapisan `sky` tidak didukung MapLibre 4 dan melemparkan galat yang
   membatalkan seluruh pengaktifan 3D
2. `isStyleLoaded()` tidak pernah benar selama ubin masih mengalir, sehingga
   menunggu nilainya berarti menunggu selamanya
3. menyalakan terrain membatalkan animasi kamera yang dimulai pada centang
   yang sama, jadi kemiringannya harus ditunda satu `requestAnimationFrame`

Sekarang polanya coba lalu ulangi, tidak pernah menunggu satu penanda.

## Uji gagal di CI tetapi lolos di komputer

Periksa akhiran barisnya. `.gitattributes` memaksa LF di repositori,
sedangkan Windows menulis CRLF di salinan kerja. Kalau sebuah uji
membandingkan teks mentah, tulis ujinya supaya tidak peduli akhiran baris.

## Uji peta gagal dengan "peta melaporkan galat", 13 September 2026

**Gejalanya.** Empat uji peramban gagal sekaligus. Pesannya `peta melaporkan
galat, assert 14 == 0`. Tidak menyebut galat apa, tidak menyebut dari mana.

**Sebabnya dua, bertumpuk.**

Pertama, `assets/js/konfigurasi.js` berisi token kosong. Berkas itu tidak ikut
git, dan `tools/konfigurasi.sh` menulis ulang isinya dari `$MAPBOX_TOKEN`.
Di mesin pengembangan variabel itu tidak ada di shell, ia ada di `.env`, dan
skrip itu satu satunya alat di repositori ini yang tidak pernah membaca
`.env`. Jadi tiap kali `tools/bangun_situs.sh` dijalankan, tokennya tertimpa
kosong, diam diam, dan peta jatuh ke OpenFreeMap.

Sekarang `konfigurasi.sh` membaca `.env` kalau environment tidak menyediakan.

Kedua, dan ini yang sebenarnya: **tokennya dibatasi per URL**. Pembatasan itu
mencocokkan asal, dan `http://127.0.0.1:<porta acak>` tidak ada di daftarnya,
jadi tiap ubin dijawab **403**. Bukan cacat kode. Bukan token kedaluwarsa.
Setelan yang bekerja sebagaimana mestinya.

**Kenapa lama ditemukan.** Peta tanpa ubin dan peta yang rusak tampak sama
persis: kosong. Pesan gagalnya menuduh kodenya.

**Yang diperbaiki supaya tidak terulang.**

1. `tools/konfigurasi.sh` membaca `.env`.
2. Server uji memakai porta tetap 8099, bukan acak, sehingga satu baris
   `http://127.0.0.1:8099` di console.mapbox.com cukup untuk selamanya. Porta
   acak berarti asal yang tidak pernah bisa didaftarkan.
3. `butuh_ubin()` di `tests/test_peramban.py` membedakan tiga keadaan:
   token kosong, ubin ditolak 403, dan peta yang benar benar rusak. Dua yang
   pertama **dilewati** dengan alasan yang menyebut langkah perbaikannya;
   yang ketiga tetap menggagalkan uji.
4. `pytest.ini` memakai `-rs`, jadi alasan tiap uji yang dilewati selalu
   tercetak. Uji yang dilewati diam diam adalah uji yang berhenti menjaga apa
   pun tanpa ada yang tahu.
5. Fixture halaman mencatat alamat tiap jawaban yang ditolak. Pesan konsol
   untuk berkas yang gagal dimuat tidak menyebut alamatnya sama sekali,
   sehingga 403 dari Mapbox tidak bisa dibedakan dari 403 yang benar benar
   salah.

**Yang masih perlu Anda kerjakan.** Tambahkan `http://127.0.0.1:8099` pada
URL restrictions token Mapbox di console.mapbox.com. Sampai itu dilakukan,
empat uji peta dilewati, dan ia tidak menjaga apa apa.
