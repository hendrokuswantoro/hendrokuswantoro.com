# Keamanan akun: apa yang menjaga jalan masuk, dan sejauh mana

Dipasang 13 September 2026. Dokumen ini menyebut apa yang setiap lapisan
kerjakan **dan apa yang tidak**, sebab lapisan keamanan yang batasnya tidak
tertulis akan dipercaya melebihi kemampuannya, dan itu justru menurunkan
keamanan.

## Ringkasnya

| Lapisan | Menahan apa | Tidak menahan apa |
| --- | --- | --- |
| Sandi Argon2id | tebakan dari daftar sandi bocor | halaman palsu, sandi yang dipakai ulang |
| Passkey WebAuthn | halaman palsu, sandi yang bocor, sandi yang dipakai ulang | perangkat yang hilang tanpa passkey kedua |
| TOTP | sandi yang bocor | halaman palsu yang meneruskan kodenya saat itu juga |
| Kode lewat email | sandi yang bocor | orang yang juga menguasai kotak suratnya |
| Kode pemulihan | ponsel yang hilang | kertas yang ikut hilang |
| Verifikasi wajah | orang yang tahu sandinya tetapi tidak bisa hadir di depan kamera | rekaman video wajah pemiliknya |

Yang paling kuat tetap **passkey**, dan itu bukan pendapat: kunci privatnya
tidak pernah meninggalkan perangkat, dan tanda tangannya terikat pada alamat
situs ini, sehingga halaman palsu tidak akan pernah mendapat tanda tangan yang
berlaku. Semua lapisan lain bisa diteruskan oleh halaman palsu yang meminta
kodenya lalu memakainya saat itu juga.

## Urutan yang terjadi saat masuk

```
sandi benar ──► ada faktor kedua? ──tidak──► sesi terbit
                      │ ya
                      ▼
              tiket lima menit  (BUKAN sesi)
                      │
        totp / wajah / email / kode pemulihan
                      │ lolos
                      ▼
                  sesi terbit
```

**Tiket, bukan sesi setengah jadi.** Antara "sandinya benar" dan "sesinya
terbit" ada keadaan yang harus dibawa entah di mana. Menerbitkan sesi lalu
menandainya belum lengkap berarti kunci yang sudah jadi, dan apa pun yang lupa
memeriksa tandanya akan menerimanya. Tiketnya JWT dengan audiens yang berbeda,
jadi pustaka JWT-nya sendiri yang menolaknya di setiap pintu selain pintu
faktor kedua. Dijaga dua uji yang mencobanya dari kedua arah.

Passkey tidak lewat jalur ini, dan itu benar: passkey sudah dua faktor pada
dirinya sendiri, yaitu perangkatnya dan sidik jari atau PIN yang membukanya.

## Sidik jari

Yang orang sebut "masuk pakai sidik jari" di web adalah WebAuthn dengan
`authenticatorAttachment: platform` dan `userVerification: required`. Itu yang
dipakai di sini.

**Sidik jarinya tidak pernah sampai ke server ini, dan tidak akan pernah.**
Perangkatnya yang memeriksa, lalu menandatangani dengan kunci privat yang tidak
pernah keluar dari sana. Yang diterima server cuma tanda tangan dan satu bendera
bahwa pemiliknya sudah diperiksa.

Itu bukan kekurangan melainkan justru rancangannya. Tidak ada data biometrik
yang disimpan di sini, jadi tidak ada yang bisa bocor dari sini, dan sidik jari
yang bocor tidak bisa diganti seperti kata sandi. Di perangkat tanpa sensor,
yang diminta PIN perangkat itu, dan jaminannya sama.

Kunci fisik USB tetap bisa didaftarkan lewat tombol terpisah. Memaksa salah
satunya berarti menutup yang lain.

## TOTP

RFC 6238, ditulis di `backend/layanan/totp.py`, tiga puluh baris, dan keenam
vektor uji resmi RFC-nya ada di `tests/test_keamanan_akun.py`. Itu bukan
protokol buatan sendiri: TOTP standar terbuka yang dipakai Google
Authenticator, Aegis, dan 1Password sejak 2011.

Yang **tidak** ditulis sendiri: penyandian rahasianya. Rahasia TOTP disandikan
AES-256-GCM dengan kunci dari `KUNCI_KOLOM` sebelum masuk basis data, memakai
implementasi yang sama dengan cadangan. Alasannya langsung: faktor kedua yang
ikut bocor bersama hash sandinya bukan faktor kedua.

Kode QR-nya digambar di server ini. Alamat `otpauth://` **memuat rahasianya**,
jadi mengirimnya ke pembuat QR mana pun berarti menyerahkan faktor kedua kepada
pihak yang tidak pernah diminta menjaganya.

Delapan kode pemulihan dicetak sekali saat TOTP dinyalakan dan tidak pernah
bisa dilihat lagi; yang tersimpan cuma sidiknya. Tanpa itu, ponsel yang hilang
berarti akun yang terkunci selamanya, dan akun yang terkunci selamanya membuat
orang mematikan faktor keduanya.

## Verifikasi wajah

**Dinyalakan sendiri, mati secara bawaan.** Ini bagian yang paling perlu
dibaca sampai habis sebelum dipakai.

### Yang ia kerjakan

Server meminta tiga bingkai dengan urutan gerakan yang baru diputuskan saat itu
juga, misalnya lurus lalu kiri lalu kanan. Tiap bingkai harus memuat tepat satu
wajah, arah hadapnya harus sesuai yang diminta, dan ketiganya harus cocok
dengan wajah yang terdaftar. Tantangannya sekali pakai dan berlaku dua menit.

Deteksi dan pengenalannya memakai YuNet dan SFace lewat `cv2.FaceDetectorYN`
dan `cv2.FaceRecognizerSF`, dua API OpenCV yang memang dibuat untuk kedua model
itu. Ambang kemiripan 0,363 adalah angka yang disebut penulis SFace, bukan
angka yang dipilih di sini.

### Yang ia TIDAK kerjakan

**Ia tidak membuktikan bahwa yang di depan kamera adalah orang hidup.** Rekaman
video wajah pemiliknya akan lolos, termasuk urutan gerakannya kalau rekamannya
cukup panjang. Deteksi kehidupan yang sungguhan menuntut model tersendiri, dan
yang dipakai penyedia identitas komersial pun masih bisa ditipu.

Jadi ia menaikkan ongkos bagi orang yang sudah tahu kata sandi Anda. Ia tidak
menutup pintunya, dan ia bukan pengganti passkey.

Satu hal lagi yang pantas dipertimbangkan sebelum menyalakannya: wajah bisa
difoto dari jauh, dan tidak bisa diganti kalau bocor. Passkey bisa dicabut
dalam satu klik.

### Yang disimpan dan yang tidak

| | |
| --- | --- |
| disimpan | 128 angka hasil penyandian wajah, disandikan AES-256-GCM dengan `KUNCI_KOLOM` |
| TIDAK disimpan | fotonya. Satu pun tidak, tidak saat mendaftar dan tidak saat masuk |

Gambar yang tidak pernah tersimpan adalah gambar yang tidak bisa bocor.
`tests/test_wajah.py` memeriksanya dari kodenya: tidak ada satu pun penulisan
berkas di lapisan wajah.

UU 27/2022 menggolongkan data biometrik sebagai data pribadi yang bersifat
spesifik. Pemilik akun ini adalah subjek datanya sendiri, ia yang memilih
menyalakannya, dan tombol hapusnya benar benar menghapus barisnya, bukan
menandainya nonaktif.

### Kamera hanya diizinkan di satu alamat

`Permissions-Policy` di blok server nginx mematikan kamera untuk **seluruh**
situs. Pengecualiannya dibuat di satu alamat saja, `location = /admin`, dengan
`camera=(self)`. Halaman yang tidak bisa menyalakan kamera tidak bisa disuruh
menyalakannya oleh skrip yang diselundupkan ke dalamnya.

Kelima header lain diulang di blok itu, sebab satu `add_header` di dalam
`location` menghapus seluruh `add_header` induknya. Tanpa mengulang, halaman
admin justru jadi satu satunya halaman tanpa CSP dan tanpa nosniff.

## Surat

Verifikasi email dan kode masuk enam angka menuntut SMTP. **Kalau SMTP belum
dikonfigurasi, suratnya tidak dianggap terkirim.** Ia ditulis ke
`cadangan/surat/` sebagai berkas `.eml`, dan setiap layar yang memintanya
mengatakan bahwa ia tidak berangkat.

Yang tidak akan pernah terjadi: membalas "kode sudah dikirim" untuk surat yang
tidak pernah ada. Verifikasi email yang emailnya tidak pernah sampai bukan
verifikasi apa apa, dan lebih buruk daripada tidak ada verifikasi, sebab
sesudahnya ada kolom di basis data yang mengatakan alamat itu sudah terbukti.

Di produksi pasang `SURAT_WAJIB=1`, yang membuatnya melempar galat alih alih
menulis berkas. Di sana, surat yang diam diam mendarat di folder adalah surat
yang hilang.

## Jejak

Halaman keamanan menampilkan aktivitas terakhir, **termasuk yang gagal**.
Daftar yang hanya memuat keberhasilan cuma memberi tahu pemiliknya apa yang
sudah ia lakukan sendiri; yang gagal memberi tahu bahwa ada orang lain sedang
mencoba.

Alamat IP tidak disimpan apa adanya, hanya ringkasan SHA-256-nya, sama seperti
pembatas laju. Jejak keamanan yang berubah jadi catatan tempat pembacanya
berada adalah jejak yang menciptakan risiko baru sambil menutup yang lama.

## Yang harus diisi sebelum semuanya hidup

| Variabel | Untuk apa | Tanpa itu |
| --- | --- | --- |
| `KUNCI_KOLOM` | menyandikan rahasia TOTP dan ciri wajah | TOTP dan wajah tidak bisa dipasang sama sekali, dan halamannya mengatakan begitu |
| `SMTP_HOST` dkk | verifikasi email dan kode masuk | surat ditulis ke berkas, tidak dikirim, dan layarnya mengatakan begitu |
| model wajah | verifikasi wajah | verifikasi wajah tidak ditawarkan saat masuk |

Tidak satu pun dari ketiganya membuat sistem ini diam diam melewatkan siapa
pun. Fitur yang menurunkan jaminannya sendiri ketika konfigurasinya kurang
adalah fitur yang jaminannya tidak pernah bisa dipercaya.

```bash
python backend/db/enkripsi.py kunci   # lalu tulis sebagai KUNCI_KOLOM di .env
python tools/ambil_model.py           # 37 MB, sekali saja
```

## Apa yang diuji, dan apa yang tidak

62 uji baru. Yang penting dari daftar ini bukan jumlahnya melainkan apa yang
**sengaja tidak** ada di dalamnya.

Diuji: vektor RFC 6238, kode yang tidak pernah tersimpan apa adanya, rahasia
TOTP yang tersandi, tiket yang tidak bisa dipakai sebagai token akses dan
sebaliknya, kode pemulihan yang ditolak saat dipakai kedua kali, tautan
verifikasi sekali pakai, tantangan wajah sekali pakai, arah hadap yang dihitung
dari lima titik penanda, bingkai yang bukan gambar, gambar tanpa wajah, dan
satu bingkai tidak cocok yang menolak semuanya.

**Tidak diuji: ketepatan pengenalan wajahnya.** Untuk mengujinya dibutuhkan
foto wajah orang sungguhan, dan foto wajah orang sungguhan tidak akan masuk
repositori ini. Ketepatan YuNet dan SFace adalah klaim terukur penulisnya di
atas kumpulan data yang memang dibuat untuk itu. Yang diuji di sini sambungan
di sekelilingnya, dan itu disebut apa adanya di kepala `tests/test_wajah.py`.

**Tidak pernah dijalankan dengan kamera sungguhan.** Mesin tempat ini dibangun
tidak punya kamera, dan Browser pane menolak akses kamera. Yang sudah terbukti
di peramban: komponennya tampil, arah yang diminta tertulis di layar, tombolnya
hidup, dan izin yang ditolak memunculkan pesan yang benar dalam bahasa
Indonesia. Yang belum pernah terjadi: satu wajah sungguhan masuk dan diterima.
Itu langkah pertama Anda, bukan klaim saya.
