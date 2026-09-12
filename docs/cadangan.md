# Cadangan dan pemulihan

Bab 15.18. Berlaku sejak ada basis data, tidak sebelumnya.

## Perintahnya

```bash
python backend/db/cadangan.py buat       # buat cadangan
python backend/db/cadangan.py daftar     # lihat yang ada
python backend/db/cadangan.py uji-pulih  # buktikan yang terbaru bisa dipulihkan
python backend/db/cadangan.py pulihkan cadangan/hk-2026-09-12-1855.sql.gz.enc
python backend/db/enkripsi.py kunci      # buat kunci enkripsi, sekali saja
```

## Apa yang dicadangkan, dan apa yang tidak perlu

| | Cadangannya | Kenapa |
| --- | --- | --- |
| Skema dan isi basis data | `pg_dump` terkompres | satu satunya data yang tidak ada di tempat lain |
| Isi tulisan dan proyek | `content/` di git dan GitHub | sudah tercadangkan tiga tempat |
| Kode, gaya, gambar | git dan GitHub | sama |
| Situs yang terbit | dibangun ulang dari keduanya | tidak perlu dicadangkan sendiri |

Itu sebabnya cadangannya kecil. Sebagian besar situs ini memang sudah hidup
di git, dan menyalinnya lagi ke tempat lain hanya menambah barang yang bisa
kedaluwarsa.

## RPO dan RTO

| | Nilai | Artinya |
| --- | --- | --- |
| RPO | **1 hari** | paling banyak satu hari tulisan yang hilang, karena cadangannya harian |
| RTO | **di bawah 15 menit** | terukur: pemulihan penuh ke basis data kosong selesai dalam hitungan detik pada ukuran sekarang, sisanya waktu manusia mengetik perintah |

RPO bisa dibuat lebih ketat dengan menjalankan cadangan lebih sering. Untuk
situs yang tulisannya beberapa kali sebulan, harian sudah lebih rapat
daripada lajunya berubah.

**Retensi 14 cadangan terakhir.** Yang lebih tua dibuang otomatis saat
membuat yang baru. Retensi yang tidak disebut berarti disk yang penuh diam
diam.

## Enkripsi

Cadangan dipadatkan lalu **dikunci dengan AES-256-GCM**, lihat
`backend/db/enkripsi.py`. Urutannya begitu dan bukan sebaliknya: keluaran AES
tidak bisa dipadatkan sama sekali.

Tidak ada protokol buatan sendiri. Satu panggilan ke pustaka `cryptography`,
tanpa pemotongan berbingkai buatan sendiri, dan bentuk berkasnya sesederhana
yang bisa:

```
HKCAD1
   7 bita penanda, supaya berkasnya bisa dikenali tanpa dicoba dibuka
nonce      12 bita acak, tidak pernah dipakai dua kali dengan kunci yang sama
ciphertext sisanya, sudah termasuk tag autentikasi 16 bita
```

GCM memberi kerahasiaan **sekaligus** keutuhan. Itu yang membedakannya dari
mode yang sekadar menyandi: berkas yang berubah satu bit gagal dibuka, bukan
terbuka jadi sampah yang dikira data lalu dipulihkan ke basis data sungguhan.
Diuji dengan benar benar membalik satu bit di empat posisi berbeda,
`tests/test_cadangan.py`.

### Kuncinya

```bash
python backend/db/enkripsi.py kunci
```

Salin barisnya ke `.env`. Kuncinya tidak pernah ada di dalam kode, dan tidak
pernah ada nilai bawaan: kunci bawaan adalah kunci yang sudah bocor.

**Simpan salinannya di tempat yang bukan mesin ini.** Kunci yang hilang berarti
seluruh cadangan yang sudah terenkripsi tidak akan pernah bisa dibuka lagi,
dan Anda akan menyadarinya persis pada hari Anda membutuhkannya.

### Kalau `CADANGAN_KUNCI` kosong

Cadangannya tetap dibuat, hanya tanpa enkripsi, dan perintahnya mengatakan
begitu. Cadangan yang tidak jadi dibuat karena kuncinya belum disiapkan lebih
buruk daripada cadangan yang belum terenkripsi di mesin sendiri.

`daftar` menandai mana yang belum terkunci, dan `infrastructure/kirim.sh`
**menolak** mengirimnya keluar. Di mesin ini, cadangan polos masih bisa
dimaklumi: siapa pun yang bisa membacanya sudah bisa membaca basis datanya.
Begitu ia naik ke penyedia lain, alamat email dan hash sandi ada di tangan
orang lain.

Penolakan itu dibaca dari penanda di dalam berkas, bukan dari akhiran
namanya. Nama berkas bisa diganti siapa saja.

### Berkas lama tetap bisa dibuka

`pulihkan` dan `uji-pulih` mengenali sendiri mana yang terkunci dari
penandanya, jadi cadangan yang dibuat sebelum ada enkripsi tidak jadi sampah.

## Pengujian pemulihan

Ini bagian yang paling sering ditulis dan paling jarang dijalankan.

```bash
python backend/db/cadangan.py uji-pulih
```

Yang dikerjakannya:

1. menghitung isi basis data yang asli
2. membuat basis data sementara `hk_uji_pulih`
3. memulihkan cadangan terbaru **ke sana**, bukan ke yang asli
4. menghitung isinya lalu membandingkan
5. membuang basis data sementara itu

Dipulihkan ke basis data sementara dengan sengaja. Uji pemulihan yang menimpa
data sungguhan bukan uji, itu taruhan.

**Ini berjalan di CI pada tiap push**, bukan hanya tersedia untuk dijalankan
manual. Cadangan yang belum pernah dipulihkan belum terbukti apa apa, dan
pemulihan pertama tidak boleh dicoba pada hari datanya benar benar hilang.

Terakhir terbukti: 12 September 2026, dari berkas **terenkripsi**
`hk-2026-09-12-1855.sql.gz.enc`. 3 tulisan, 7 proyek, 1 pengguna, 3 migrasi,
seluruhnya cocok.

## Penjadwalan

Di mesin pengembangan tidak perlu. Di VPS, `hk-cadangan.timer` menyala 02:40
waktu setempat dengan sebaran acak sampai 20 menit, lalu menjalankan tiga
langkah berurutan: buat, **uji-pulih**, kirim.

Langkah kedua itu yang paling penting, dan ia dijalankan tiap malam, bukan
sesekali. `Persistent=true` membuat jadwal yang terlewat karena mesinnya mati
dikejar begitu ia hidup lagi, bukan dilewati diam diam sampai besok.

Kalau salah satunya gagal, `hk-cadangan-gagal@.service` memanggil
`infrastructure/beritahu.sh`, yang mengirim pesan ke Telegram kalau tokennya
diisi. Kegagalan yang hanya duduk di journal sampai ada yang kebetulan
membukanya sama saja dengan tidak ada pemeriksaan.

Berkasnya ada dan lolos pemeriksaan yang bisa dilakukan tanpa server, lihat
[vps.md](vps.md). **Belum pernah dijalankan systemd sungguhan**, sebab
servernya belum ada.

Retensi di sisi penyedia 30 hari, diatur `CADANGAN_SIMPAN_HARI`.
