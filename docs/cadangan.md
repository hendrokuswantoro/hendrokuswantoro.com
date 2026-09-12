# Cadangan dan pemulihan

Bab 15.18. Berlaku sejak ada basis data, tidak sebelumnya.

## Perintahnya

```bash
python backend/db/cadangan.py buat       # buat cadangan
python backend/db/cadangan.py daftar     # lihat yang ada
python backend/db/cadangan.py uji-pulih  # buktikan yang terbaru bisa dipulihkan
python backend/db/cadangan.py pulihkan cadangan/hk-2026-09-12-1654.sql.gz
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

Cadangan dikompresi, **belum dienkripsi**. Selama berkasnya hanya ada di
mesin Anda sendiri, enkripsi tidak menambah apa apa: penyerang yang bisa
membaca `cadangan/` juga bisa membaca `.env` yang memuat kata sandinya.

**Begitu cadangan dikirim ke object storage atau ke mesin lain, enkripsi jadi
wajib**, sebab saat itu berkasnya melewati tempat yang tidak Anda kendalikan.
Itu bagian dari Fase 7 dan belum dikerjakan.

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

Terakhir terbukti: 12 September 2026, 3 tulisan, 7 proyek, 1 pengguna,
2 migrasi, seluruhnya cocok.

## Yang belum

Penjadwalan otomatis. Di mesin pengembangan tidak perlu; di VPS nanti
dijalankan cron harian yang mengunggah hasilnya ke object storage terpisah,
terenkripsi. Itu Fase 7.
