# Pengujian

```bash
pip install -r tests/requirements.txt
python -m pytest
```

140 uji, jalannya di bawah satu detik. Tidak ada peramban, tidak ada server,
tidak ada jaringan. Semuanya membaca berkas yang benar benar akan disajikan.

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

## Menambah uji

Satu berkas per topik, nama berkas `test_*.py`, nama fungsi menjelaskan apa
yang dijaga bukan apa yang dipanggil. Docstring-nya menyebut **kegagalan apa
yang dicegah**, bukan mengulang isi kodenya. Uji yang tidak bisa dijelaskan
kegagalannya biasanya uji yang tidak perlu ada.

Pembantu bersama ada di `tests/konftes.py`.
