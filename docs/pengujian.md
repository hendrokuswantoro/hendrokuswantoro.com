# Pengujian

```bash
pip install -r tests/requirements.txt
python -m pytest                 # 260 uji, di bawah sepuluh detik
python -m pytest -m peramban     # 25 uji lagi, dengan Chromium sungguhan
sh tools/verifikasi.sh           # keduanya, plus lint, build, dan security check
```

**Kenapa dipisah dua perintah.** Di Windows psycopg menolak
`ProactorEventLoop` sedangkan Playwright justru menuntutnya untuk
menjalankan subproses. Keduanya tidak bisa hidup dalam satu proses pytest.
Alasannya ditulis lengkap di `pytest.ini`, dan kebijakan event loop-nya
disetel di dalam fixture, bukan saat modul diimpor, sebab pytest mengimpor
seluruh modul uji saat mengoleksi walau tidak semuanya akan dijalankan.

Di CI keduanya berjalan di pekerjaan yang berbeda, jadi tidak ada yang
terlewat diam diam.

Kebutuhan ujinya dipisah di `tests/requirements.txt` supaya pytest tidak
pernah ikut ke mana pun situs ini diterbitkan.

## Apa yang dijaga, dan kenapa

### `test_struktur.py`

Bentuk tiap halaman. Satu `h1`, tidak ada tingkat judul yang dilompati, id
tidak kembar, tiap gambar punya `alt` yang diterjemahkan, tiap tautan dan
aset internal menunjuk berkas yang ada, tiap halaman punya `lang`, judul,
keterangan, kanonis, dan tawaran umpan RSS.

**Sudah menangkap cacat sungguhan.** Judul kartu di halaman Proyek dan Blog
dulu `h3` yang duduk langsung di bawah `h1` halaman, tanpa `h2` di antaranya.
Peramban tidak mengeluh. Pembaca layar tersesat.

### `test_dwibahasa.py`

Inggris ada di markup, Indonesia menumpang di atribut `data-ind` di
sebelahnya. Kegagalan yang dijaga di sini sifatnya diam: seseorang menyunting
kalimat Inggrisnya dan lupa atributnya, lalu separuh situs berganti bahasa
sementara separuh lagi tidak.

Uji ini juga menuntut tiap atribut Indonesia punya pasangan Inggrisnya.
Tanpa pasangan, saklar bahasa akan mengosongkan nilainya saat kembali ke
Inggris, bukan mengembalikannya.

**Sudah menangkap cacat sungguhan.** Keterangan halaman 404 tidak pernah
ikut berganti bahasa.

### `test_peta.py`

Dua port peta harus tetap sebangun: id lapisan sama, urutan sama. Urutan
bukan hiasan. MapLibre menempatkan simbol dari tumpukan paling atas ke bawah,
jadi menukar urutan diam diam mengubah label mana yang menang saat berebut
tempat.

Uji ini juga mengurung dua kesalahan yang mudah terjadi:

- id yang terdaftar di `LAYER_NAMA` tetapi tidak ada di gayanya, sehingga
  satu lapisan berhenti ikut saklar bahasa tanpa galat apa pun
- lapisan `nama-*` yang lupa didaftarkan, sehingga selamanya memakai bahasa
  yang pertama dimuat

Ditambah 38 provinsi yang koordinatnya diperiksa masih berada di dalam kotak
Indonesia, dan penyisiran token di seluruh berkas yang dilacak git.

### `test_terbit.py`

Apa yang benar benar sampai ke server, dan apakah isinya sepakat sendiri.

Uji pertamanya ada karena bug yang ditangkapnya menipu saya dua kali dalam
satu hari: nomor versi pada `style.css` dan `app.js` bergeser antar halaman,
sehingga pengunjung lama menerima HTML baru dengan stylesheet lama di semua
halaman kecuali satu. Tidak ada galat. Situsnya hanya terlihat salah bagi
sebagian orang.

Sisanya: dua pembangun (`build_dist.py` dan `bangun_situs.sh`) harus
menyalin daftar berkas yang sama, sitemap dan feed harus memuat tiap tulisan
yang ada, `_headers` harus tetap membawa kelima header keamanannya,
`_redirects` tidak boleh kembali karena Workers menolaknya dengan kode
100324, dan `wrangler.toml` harus tetap menunjuk `./dist`.

### `test_peramban.py`

Menjalankan Chromium sungguhan. Ini lubang terbesar di rangkaian uji sampai
12 September 2026: semua uji lain membaca berkas atau memanggil API, dan
tidak satu pun membuktikan halamannya benar benar tergambar.

Petanya sudah **tiga kali rusak diam diam**: sekali karena lapisan `sky` yang
tidak didukung MapLibre 4, sekali karena worker yang diblokir CSP, sekali
karena satu berkas pustaka yang kurang. Ketiganya tidak menimbulkan galat apa
pun; petanya hanya diam. Tiap kali yang menemukannya mata manusia.

Yang dijaga hanya hal yang **cuma bisa dibuktikan di peramban**: peta yang
benar benar menggambar tujuh penanda dan ubinnya, tombol 3D yang benar benar
menegakkan bangunan dengan terrain menyala, nama jalan yang muncul di zoom
kota, saklar bahasa yang mengganti seluruh teks dan bertahan antar halaman,
daftar isi yang dibangun JavaScript, dan tidak adanya geser mendatar di layar
360 piksel.

Servernya menyajikan **CSP yang sama persis** dengan yang disajikan
Cloudflare, dibaca dari `_headers`. Menguji di bawah aturan yang lebih
longgar daripada produksi berarti menguji sesuatu yang bukan situs ini. Itu
juga sebabnya penantiannya memakai `page.evaluate` dan bukan
`page.wait_for_function`: yang terakhir menyuntikkan pemantau ber-`eval`, dan
CSP situs ini menolak `unsafe-eval`.

### `test_performa.py`

Bab 20 menuntut optimasi, dan optimasi tanpa pengukuran adalah tebakan yang
kebetulan rapi. Angka yang terukur pada 13 September 2026:

| Halaman | Berat | Permintaan | Sebelumnya |
| --- | --- | --- | --- |
| `/` | 158 KB | 10 | 201 KB terukur, 233 KB sebenarnya |
| `/about` | 113 KB | 7 | 78 KB terukur, 110 KB sebenarnya |
| `/blog/` | 110 KB | 7 | 75 KB terukur, 107 KB sebenarnya |
| `/blog/kapan-peta-diam` | 112 KB | 7 | 77 KB terukur, 109 KB sebenarnya |
| `/project` | 1927 KB | 29 | 2076 KB |

Kolom terakhir memuat dua angka, dan selisihnya yang penting.

**Angka lama tidak mengukur fontnya.** Selama Poppins datang dari
`fonts.gstatic.com`, Resource Timing melaporkan `transferSize` nol untuk
berkas dari asal lain yang tidak mengirim `Timing-Allow-Origin`, dan Google
tidak mengirimnya. Jadi 32 KB font tidak pernah masuk hitungan sama sekali,
dan anggaran ini mengawasi halaman yang lebih ringan daripada yang benar benar
dikirim ke pembaca. Sekarang fontnya ada di `assets/fonts`, jadi bitanya
terhitung; itu sebabnya `/about` **naik** di atas kertas sambil menjadi lebih
cepat. Lihat [ringan.md](ringan.md).

`/` turun 75 KB, dari 233 KB menjadi 158 KB, karena dua hal sekaligus: font
dari asal sendiri dan gambar karya dalam tiga lebar. Permintaannya bertambah
tiga, dan itu memang benar: empat berkas font dari asal ini menggantikan satu
stylesheet plus empat woff2 dari dua asal lain, dan kelimanya dulu tidak
terhitung.

`/project` berat karena memuat MapLibre dan ubin peta. Pustakanya sendiri
sekitar 1 MB, sebab `maplibre-gl-shared.mjs` diunduh **dua kali**: sekali
oleh halaman, sekali oleh worker yang berjalan di konteks terpisah. Angka itu
ditulis apa adanya dan diberi anggaran sendiri, bukan disembunyikan di balik
satu anggaran besar untuk semua halaman, sebab anggaran seperti itu membuat
halaman lain bisa membengkak tanpa ketahuan.

**Yang dianggarkan berkas dari asal situs ini, bukan seluruh permintaan.**
Ubin peta datang dari Mapbox atau, kalau tokennya kosong, dari OpenFreeMap.
Jumlahnya diputuskan peta sendiri berdasarkan apa yang kebetulan terlihat, dan
berubah antar putaran pada kode yang sama persis: `/project` terukur 29
permintaan di mesin yang tokennya dibatasi per URL sehingga tiap ubin dijawab
403, dan 51 di CI yang tidak punya token sehingga ubinnya benar benar dimuat.
Anggaran yang menghitungnya akan gagal karena cuaca, bukan karena ada yang
menggemukkan situs ini.

Yang bisa digemukkan seseorang lewat sebuah commit adalah berkas dari asal
sendiri: pustaka baru, gambar yang lupa dikecilkan, CSS yang membengkak. Itu
yang dijaga. Jumlah seluruhnya tetap dicetak di sebelahnya, supaya tetap
terlihat, hanya tidak dijadikan syarat lulus. Catatan kecil yang mengikutinya:
bita ubin memang tidak pernah ikut terhitung sejak awal, sebab ia dari asal
lain tanpa `Timing-Allow-Origin`, jadi yang berubah hanya jumlah permintaannya.

Yang juga dijaga:

- **Tidak ada satu pun permintaan ke pihak ketiga.** Dulu Google Fonts
  dikecualikan; sekarang daftarnya kosong.
- Empat halaman tanpa peta tidak mengunduh MapLibre sama sekali.
- **Lebar gambar yang dipilih peramban diukur, bukan dihitung.** Enam ukuran
  layar, dua halaman, dan tiap gambar diperiksa tiga hal: berkasnya tidak
  lebih sempit daripada kotaknya, tidak lebih dari dua kali lebarnya, dan
  nilai `sizes` tidak lebih kecil daripada kotak yang sebenarnya. Yang
  terakhir tidak terlihat di layar biasa; ia hanya muncul di layar padat,
  sebagai gambar yang sedikit kabur tanpa satu pun pesan galat.

Satu catatan tentang `naturalWidth`: untuk gambar dengan `srcset`
berdeskriptor `w`, Chromium melaporkannya sebagai lebar berkas dibagi
kerapatan yang ia hitung dari `sizes`, jadi nilainya mendekati nilai `sizes`
itu sendiri dan bukan lebar berkasnya. Uji yang memperlakukannya sebagai
lebar berkas akan menuduh gambar 400 px hanya 253 px. Itu sudah terjadi di
sini; lebar berkasnya sekarang dibaca dari namanya.

Yang **tidak** diklaim: bahwa di `/project` pun MapLibre ditunda sampai
digulir. Bagian petanya duduk tinggi di halaman itu, di dalam `rootMargin`
500px milik pengamatnya, jadi memang langsung dimuat.

## Menambah uji

Satu berkas per topik, nama berkas `test_*.py`, nama fungsi menjelaskan apa
yang dijaga bukan apa yang dipanggil. Docstring-nya menyebut **kegagalan apa
yang dicegah**, bukan mengulang isi kodenya. Uji yang tidak bisa dijelaskan
kegagalannya biasanya uji yang tidak perlu ada.

Pembantu bersama ada di `tests/konftes.py`.
