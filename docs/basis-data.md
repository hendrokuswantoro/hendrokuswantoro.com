# Basis data

Bab 15.22 menuntut dokumentasi basis data. Ini isinya: cara menjalankannya,
apa isi skemanya, dan kenapa beberapa keputusannya diambil begitu.

## Menjalankan

```bash
cp .env.example .env        # lalu isi kata sandinya
cd infrastructure && docker compose --env-file ../.env up -d
```

Lalu dari akar repositori:

```bash
pip install -r backend/requirements.txt
python backend/db/migrasi.py
python backend/db/muat_awal.py
```

Hasilnya PostgreSQL 16 dengan PostGIS 3.4 di `127.0.0.1:5433`, Redis di
`6380`, berisi 3 tulisan dan 7 proyek yang dibaca dari `content/`.

Keduanya **hanya mendengar di localhost**. Basis data tidak pernah menghadap
internet, bahkan di mesin pengembangan.

## Migrasi

SQL bernomor di `backend/db/migrations/`, dijalankan
`backend/db/migrasi.py`. Yang sudah diterapkan dicatat di tabel
`skema_migrasi` beserta sidik SHA-256 isinya.

**Menyunting migrasi yang sudah jalan akan ditolak**, bukan diterapkan diam
diam separuh. Kalau skemanya perlu berubah, buat berkas dengan nomor
berikutnya.

Kenapa bukan Alembic: skema ini dibaca jauh lebih sering daripada diubah, dan
SQL yang bisa dibaca langsung lebih jujur daripada Python yang membangkitkan
SQL. Proyek Parkir Jogja memakai pola yang sama.

## Tabel

| Tabel | Isi |
| --- | --- |
| `users` | pemilik situs. Satu baris. `sandi_hash` boleh NULL sebab passkey jadi jalur utama |
| `blog_posts` | tulisan, dua bahasa, isinya Markdown |
| `projects` | tujuh karya, dengan `geom` titik |
| `spatial_layers` | lapisan spasial umum, belum dipakai |
| `settings` | pasangan kunci nilai |
| `berkas` | catatan foto dan video yang diunggah. **Berkasnya sendiri di cakram**, bukan di sini |
| `skema_migrasi` | catatan migrasi yang sudah jalan |

Tabel `berkas` sengaja tidak menyimpan bitanya. PostgreSQL bisa, dan tetap
tidak dipakai begitu: satu video dua puluh megabita di dalam baris membuat
setiap cadangan basis data ikut membawanya, setiap replikasi mengirimnya lagi,
dan setiap pembacaan halaman melewati kolam koneksi untuk sesuatu yang bisa
dilayani berkas statis tanpa satu pun kueri. Yang tersimpan namanya, jenisnya,
ukurannya, sidik sha256 isinya, dan siapa yang mengunggahnya.

Sidiknya `UNIQUE`, dan itu yang membuat satu foto yang dipakai di tiga tulisan
tetap satu berkas di cakram. `CHECK` di tabelnya menahan gambar tanpa ukuran
dan video yang punya ukuran: gambar tanpa lebar dan tinggi akan terbit sebagai
halaman yang melompat, dan ukuran video di sini hanya bisa datang dari
tebakan, sebab tidak ada yang mengukurnya.

## Dua keputusan yang perlu dijelaskan

### Kolom berpasangan, bukan tabel terjemahan

Tiap teks punya sepasang kolom `_en` dan `_id`, keduanya `NOT NULL`.

Bahasanya tepat dua, keduanya selalu wajib ada, dan tidak akan bertambah.
Tabel terjemahan akan menambah join pada tiap kueri demi keluwesan yang tidak
akan pernah dipakai, dan yang lebih buruk, membuat "tulisan tanpa terjemahan"
jadi keadaan yang **mungkin**. Dengan dua kolom `NOT NULL`, keadaan itu
mustahil.

### Keadaan mustahil ditutup oleh basis datanya

```sql
CONSTRAINT terbit_punya_tanggal
    CHECK (status <> 'terbit' OR terbit_pada IS NOT NULL)
```

Tulisan berstatus terbit tanpa tanggal terbit akan merusak urutan umpan RSS
**tanpa galat apa pun**. Kode bisa lupa memeriksanya; basis data tidak.

Empat batasan lain dengan alasan yang sama:

| Batasan | Menahan |
| --- | --- |
| `titik_di_indonesia` | proyek yang koordinatnya mendarat di Paris |
| `slug_bentuknya_benar` | slug berspasi atau berhuruf besar, yang jadi alamat rusak |
| `kategori_tidak_kosong` | proyek yang tidak muncul di filter mana pun |
| `idx_projects_urut` unik | dua proyek berebut posisi yang sama |

Kelimanya diuji di `tests/test_basis_data.py` dengan cara **mencoba
melanggarnya**. Batasan yang tidak pernah diuji adalah batasan yang mungkin
saja tidak pernah menyala.

## Data awal

`backend/db/muat_awal.py` membaca `content/` lewat `tools/isi.py`, sumber
yang sama persis dengan yang dipakai membangun situs statis. Kalau pemuat ini
punya salinan datanya sendiri, dua salinan itu pasti berpisah jalan.

Aman dijalankan berkali kali: baris yang sudah ada diperbarui, bukan
digandakan. Ada ujinya.

## Yang belum

Cadangan dan pemulihan, bab 15.18. Sampai itu ditulis dan **diuji**, basis
data ini belum boleh menyimpan apa pun yang tidak ada salinannya di
`content/`.

## Catatan migrasi

Sampai 30 September 2026 alasan di balik tiap migrasi ditulis sebagai komentar
`--` di berkas SQL-nya. Sejak itu berkas migrasi tidak berkomentar, dan
alasannya tinggal di sini, berurutan seperti di berkasnya. Keterangan kolom
yang disimpan di katalog lewat `COMMENT ON` tetap di berkas SQL, sebab itu
perintah, bukan komentar.

### `0001_awal.sql`

Skema awal.

Dua keputusan yang tidak ada di spesifikasi mana pun dan dirancang di sini, alasannya di docs/rancangan-platform.md bagian 6:

1. Situs ini dwibahasa. Tiap kolom teks berpasangan dan NOT NULL, bukan tabel terjemahan. Dua bahasa, keduanya selalu wajib, tidak akan bertambah. Dengan begini "tulisan tanpa terjemahan" mustahil, bukan sekadar tidak dianjurkan.

2. Keadaan yang mustahil dibuat mustahil oleh basis datanya, bukan diingat oleh kodenya. Tulisan berstatus terbit tanpa tanggal terbit akan merusak urutan umpan RSS tanpa galat apa pun.

salinan uji yang sudah ada di tests/test_peta.py, ditaruh di tempat yang tidak bisa dilewati

### `0002_sesi.sql`

Sesi refresh token.

Disimpan di Postgres, bukan Redis. Bab 15.10 menuntut sesi bisa dicabut dan bisa "keluar dari semua perangkat"; keduanya tidak ada artinya kalau daftarnya lenyap setiap kali cache dinyalakan ulang. Redis tetap dipakai untuk pembatas laju, tempat kehilangan data memang tidak berbahaya.

Yang disimpan hanya ringkasan tokennya, bukan tokennya. Basis data yang bocor tidak boleh memberi siapa pun kunci masuk.

Percobaan masuk yang gagal, untuk menahan tebak sandi. Bab 15.11. Alamat IP tidak disimpan apa adanya, hanya ringkasannya.

### `0003_passkey.sql`

Passkey, yaitu WebAuthn. Bab 15.8 menyebutnya jalur masuk utama.

Sandi yang disimpan sebagai Argon2id tetap ada dan tetap aman, tetapi ia punya satu cacat yang tidak bisa ditambal dari sisi server: sandi bisa diketikkan ke halaman palsu. Passkey tidak bisa. Kunci privatnya tidak pernah meninggalkan perangkat, dan tanda tangannya terikat pada rp_id, jadi halaman yang alamatnya bukan alamat ini tidak akan pernah mendapat tanda tangan yang berlaku. Itu alasan sebenarnya, bukan karena passkey lebih praktis.

Yang disimpan di sini hanya kunci PUBLIK. Tidak ada satu pun rahasia di tabel ini: basis data yang bocor seluruhnya tidak memberi siapa pun cara masuk, berbeda dengan tabel sandi yang bocor.

Diberikan authenticator, bukan dibuat di sini. Panjangnya bebas menurut spesifikasi, tetapi 16 bita ke bawah bukan kredensial yang masuk akal.

Penghitung tanda tangan. Authenticator menaikkannya tiap dipakai, dan nilai yang tidak naik menandakan kredensialnya disalin. Tidak semua authenticator memakainya; yang memakai nol selamanya memang sah.

Diisi pemiliknya supaya ia tahu kunci mana yang sedang dicabutnya.

Tantangan WebAuthn, disimpan di server.

Ini bagian yang paling mudah salah. Tantangan yang dibuat lalu dipercaya kembali dari peramban apa adanya berarti penyerang boleh memilih sendiri tantangannya, dan seluruh jaminan kesegaran tanda tangan hilang. Jadi tantangan lahir di sini, sekali pakai, dan berumur pendek.

Mendaftar selalu atas nama seseorang yang sudah masuk. Masuk belum tahu siapa: passkey yang discoverable menyebut pemiliknya sendiri.

### `0004_keamanan.sql`

Verifikasi email, kode sekali pakai, TOTP, kode pemulihan, dan jejak keamanan. Bab 15.8 dan 15.10.

Sampai migrasi ini, jalan masuk ke dashboard ada dua: sandi Argon2id dan passkey. Keduanya kuat, dan keduanya punya lubang yang sama bentuknya: tidak ada satu pun jejak tentang apa yang terjadi pada akun itu, dan tidak ada cara memastikan bahwa alamat email pemiliknya memang alamat yang ia kuasai. Akun yang emailnya tidak pernah dibuktikan adalah akun yang jalur pemulihannya menuju entah ke mana.

Empat hal ditambahkan di sini, dan satu aturan berlaku untuk semuanya: yang disimpan hanya sidiknya, tidak pernah nilainya. Kode OTP yang tersimpan apa adanya sama saja dengan sandi yang tersimpan apa adanya, hanya umurnya lebih pendek. Basis data yang bocor seluruhnya tidak boleh memberi siapa pun satu pun kode yang masih bisa dipakai.

Rahasia yang ada tetapi belum pernah diaktifkan adalah rahasia yang sedang dipasang dan belum dibuktikan bisa dibaca perangkatnya. Yang mustahil: aktif tanpa rahasia.

Dipakai dua hal yang bentuknya sama: tautan verifikasi email, dan kode enam angka yang dikirim ke email saat masuk. Keduanya lahir, dipakai sekali, lalu mati. Dijadikan satu tabel karena aturannya memang satu.

sha256 heksa. Bukan kodenya. Lihat komentar di kepala berkas ini.

Tebakan yang gagal dihitung di baris kodenya sendiri, bukan per alamat IP. Penebak yang berpindah pindah IP tetap membakar jatah kode yang sama, dan kode itu mati sebelum ruang tebakannya habis.

Delapan kode sekali pakai yang dicetak saat TOTP dinyalakan, dan tidak pernah bisa dilihat lagi sesudah itu.

Tanpa ini, ponsel yang hilang berarti akun yang terkunci selamanya, dan akun yang terkunci selamanya membuat orang mematikan faktor keduanya. Faktor kedua yang dimatikan tidak menjaga apa pun.

Yang membuat halaman "aktivitas terakhir" milik Google dan Meta berguna bukan daftarnya, melainkan bahwa yang GAGAL pun tercatat. Masuk yang berhasil hanya memberi tahu pemiliknya apa yang sudah ia lakukan; masuk yang gagal memberi tahu bahwa ada orang lain sedang mencoba.

Yang TIDAK disimpan: alamat IP apa adanya. Hanya ringkasannya, digaram per proses, sama seperti pembatas laju. Jejak keamanan yang berubah jadi catatan lokasi pembacanya adalah jejak yang menciptakan risiko baru sambil menutup yang lama.

### `0005_wajah.sql`

Verifikasi wajah sebagai faktor kedua.

Sebelum apa pun yang lain, apa yang lapisan ini bisa dan tidak bisa kerjakan, supaya tidak ada yang menganggapnya lebih kuat daripada yang sebenarnya. Hal yang sama ditulis di layar tempat ia dinyalakan.

BISA  : menaikkan ongkos masuk bagi orang yang sudah tahu kata sandinya. Ia harus hadir di depan kamera dengan wajah yang cocok, mengikuti urutan gerakan yang baru diminta server saat itu juga. TIDAK : menghentikan orang yang punya rekaman video wajah pemiliknya. Pencocokan wajah bukan pembuktian kehadiran, dan urutan gerakan hanya menyulitkan, bukan menutup. TIDAK : menggantikan passkey. Passkey menandatangani dengan kunci yang tidak pernah meninggalkan perangkat dan terikat pada alamat situs ini; wajah tidak terikat pada apa pun.

Karena itu ia ditawarkan sebagai tambahan yang dinyalakan sendiri, bukan sebagai bawaan, dan bukan sebagai pengganti apa pun yang sudah ada.

Yang disimpan dan yang tidak:

disimpan      : 128 angka hasil penyandian wajah, disandikan AES-256-GCM dengan kunci dari KUNCI_KOLOM, sama seperti rahasia TOTP TIDAK disimpan: fotonya. Satu pun tidak, tidak saat mendaftar dan tidak saat masuk. Gambar yang tidak pernah tersimpan adalah gambar yang tidak bisa bocor.

UU 27/2022 menggolongkan data biometrik sebagai data pribadi yang bersifat spesifik. Pemilik akun ini adalah subjek datanya sendiri, ia yang memilih menyalakannya, dan ia bisa menghapusnya kapan saja lewat satu tombol yang benar benar menghapus barisnya, bukan menandainya nonaktif.

Urutan gerakan diputuskan server, bukan klien, dan hanya berlaku sekali.

Tanpa ini, "kirim tiga foto wajah Anda" bisa dijawab dengan tiga berkas yang sudah disiapkan sejak lama. Dengan ini, tiga berkas itu harus kebetulan memuat urutan gerakan yang baru saja diminta, dan urutannya berganti tiap kali. Itu menyulitkan, dan perlu dikatakan terus terang bahwa menyulitkan bukan menutup: rekaman video yang cukup panjang tetap memuat semuanya.

### `0006_berkas.sql`

Foto dan video yang diunggah lewat dashboard admin.

Berkasnya sendiri TIDAK disimpan di sini. Yang di sini catatannya: nama berkas di cakram, jenisnya, ukurannya, dan siapa yang mengunggahnya. PostgreSQL bisa menyimpan bita, dan tetap tidak dipakai begitu: satu video dua puluh megabita di dalam baris membuat setiap cadangan basis data ikut membawanya, setiap replikasi mengirimnya lagi, dan setiap pembacaan halaman melewati kolam koneksi untuk sesuatu yang bisa dilayani berkas statis tanpa satu pun kueri.

Nama berkasnya tidak pernah datang dari pengunggahnya. Yang dipakai nama acak enam belas heksa, ditambah ukuran gambarnya, ditambah akhiran yang ditentukan dari bita pertama berkasnya, bukan dari nama yang dikirim. Nama kiriman bisa berbunyi "../../etc/passwd" atau "laporan.pdf.exe", dan keduanya pernah jadi kerentanan di tempat lain. Nama aslinya tetap dicatat di kolom terpisah supaya pengunggahnya bisa mengenali berkasnya lagi, dan ia tidak pernah dipakai untuk membentuk jalur.

Ukuran gambar ikut ke dalam nama berkasnya, misalnya "9f3c1a7b2d4e5f60-1600x900.webp". Itu membuat pembangkit halaman tahu lebar dan tingginya tanpa membuka berkasnya dan tanpa bertanya ke basis data, sehingga tulisan di bawah gambar tidak melompat saat gambarnya tiba.

Nama di cakram, sekaligus bagian terakhir alamatnya di /unggahan/.

Nama yang dikirim pengunggahnya, hanya untuk dilihat orang.

'gambar' atau 'video'. Ditentukan dari bita pertama berkasnya.

Hanya terisi untuk gambar. Video tidak diukur: mengukurnya menuntut ffmpeg, dan menebaknya berarti menuliskan angka yang tidak diukur.

sha256 isi berkasnya. Dipakai mengenali unggahan yang sama dua kali, supaya satu foto yang dipakai di tiga tulisan tetap satu berkas.

Gambar punya ukuran, video tidak. Dijaga di sini supaya tidak ada baris gambar yang lolos tanpa ukuran dan berakhir sebagai halaman yang melompat.

### `0007_sesi_kuat.sql`

Dua hal yang dicatat per sesi, dan keduanya soal jalan masuk.

1. Apakah sesi ini lahir lewat faktor kedua.

Sampai 19 September 2026 faktor kedua sepenuhnya pilihan. Kalau pemiliknya belum menyalakan TOTP, sandi saja membuka dashboard yang bisa menerbitkan tulisan dan mengunggah berkas. Itu keadaan yang boleh, dan halaman keamanannya memang menyebutnya terus terang, tetapi ia bukan keadaan yang pantas jadi bawaan untuk permukaan tulis.

Sekarang jalur tulis menuntut sesi yang lahir lewat faktor kedua, dan kolom inilah yang mencatatnya. Dicatat di sesi, bukan disimpulkan ulang tiap permintaan, sebab yang benar adalah keadaan saat ia masuk: menyalakan TOTP sesudah masuk tidak boleh diam diam menguatkan sesi yang sudah terbit, dan mematikannya tidak boleh melemahkan sesi yang sedang berjalan.

Passkey dihitung faktor kedua dengan sendirinya. Ia menandatangani dengan kunci yang tidak pernah meninggalkan perangkat dan terikat pada alamat situs ini; tidak ada yang bisa ditipu untuk menyerahkannya lewat halaman palsu. Menuntut TOTP di atasnya berarti menuntut faktor yang lebih lemah untuk menjaga faktor yang lebih kuat.

Nilai bawaannya false, dan itu disengaja: sesi yang sudah terbit sebelum migrasi ini tidak pernah membuktikan faktor kedua, jadi menandainya true berarti mengarang bukti. Pemiliknya cukup masuk sekali lagi.

2. Kapan sesi ini dicabut, dan siapa yang mencabutnya, sudah ada di kolom dicabut_pada. Yang belum ada: cara mematikan access token yang sudah terlanjur terbit dari sesi itu.

Access token adalah JWT dan tidak pernah ditanyakan ke basis data, jadi mencabut sesi hanya mematikan refresh token-nya. Token aksesnya tetap sah sampai lima belas menit berikutnya. Itu jendela yang pendek dan tetap nyata: tombol "keluarkan perangkat lain" ditekan justru ketika orangnya curiga, dan lima belas menit adalah waktu yang panjang untuk dicurigai.

Yang menutupnya bukan kolom baru melainkan daftar cabut di Redis, dan token membawa `sid` berisi id sesi ini. Lihat backend/core/cabut.py. Indeks di bawah dipakai membersihkan daftar itu, dan tidak lebih.

### `0008_totp_langkah.sql`

Nomor jendela TOTP terakhir yang berhasil dipakai.

Sampai 26 September 2026 keterangan di backend/layanan/totp.py sudah berjanji bahwa kode yang sudah dipakai ditolak sampai jendelanya lewat, tetapi nomor jendelanya dibuang begitu saja dan tidak pernah disimpan. Kode yang terlihat orang lain tetap berlaku sampai sekitar sembilan puluh detik. Kolom ini yang membuat janji itu benar.

### `0009_setelan_keamanan.sql`

Setelan keamanan yang dipilih pemilik akun sendiri.

kabar_masuk dan kabar_perubahan menentukan surat pemberitahuan mana yang dikirim. Mematikan salah satunya selalu dikabarkan lewat surat, apa pun setelannya, supaya orang yang mengambil alih akun tidak bisa membungkam pemiliknya dengan diam diam.

mode_ketat menutup cara masuk yang lemah: wajah tidak lagi diterima sebagai faktor kedua selama akun punya authenticator atau passkey.

Tantangan WebAuthn untuk membuka kunci layar dashboard. Selalu atas nama orang yang sedang masuk, jadi pengguna_id wajib ada.

### `0010_sesi_ketat.sql`

Umur mutlak sesi dan alasan pencabutannya.

`awal` adalah saat orangnya masuk, dan ikut diwariskan setiap kali refresh token diputar. Sebelum kolom ini ada, tiap putaran memberi umur baru, jadi sesi yang terus dipakai tidak pernah berakhir.

`dicabut_karena` membedakan token yang dicabut karena diputar dari yang dicabut karena keluar atau dikeluarkan. Hanya token yang sudah DIPUTAR lalu dipakai lagi yang menandakan pencurian: pemilik sahnya sudah memegang token penggantinya, jadi yang memakai token lama adalah salinan. Perangkat yang dikeluarkan lalu mencoba memperpanjang bukan pencuri, dan tidak boleh memicu pencabutan seluruh sesi.
