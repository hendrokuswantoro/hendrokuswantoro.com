# VPS, Nginx, deploy, dan cadangan terjadwal

Fase 7. Semua berkasnya ada dan sudah diuji sejauh yang bisa diuji tanpa
server. Yang belum ada servernya, dan itu keputusan biaya yang bukan milik
saya.

**Yang sudah terbukti di mesin ini**

| | |
| --- | --- |
| Konfigurasi nginx | Lolos `nginx -t` di dalam kontainer nginx 1.27 |
| Berkas unit systemd | Terbaca, pengerasannya dijaga 7 uji |
| Skrip shell | Lolos `sh -n`, semuanya memakai `set -e` |
| Enkripsi cadangan | 20 uji, termasuk kunci salah dan satu bit yang berubah |
| Cadangan terenkripsi | Dibuat, dikunci, **dipulihkan**, jumlah barisnya cocok |
| Alur kerja deploy | YAML-nya sah, 6 uji atas isinya |

**Yang belum pernah dijalankan, dan alasannya**

`pasang.sh` belum pernah menyentuh Ubuntu sungguhan. `hk-api.service` belum
pernah dinyalakan systemd. `kirim.sh` belum pernah menghubungi object storage.
Ketiganya menuntut mesin yang belum ada. Saya tidak bisa mengujinya, jadi saya
tidak mengatakan ia bekerja.

---

## Apakah VPS-nya memang perlu

Jawaban jujurnya: **untuk situsnya, tidak.** Empat halaman statis disajikan
Cloudflare dengan sangat baik, gratis, dari puluhan kota, tanpa ada yang perlu
ditambal tiap bulan.

VPS baru berarti untuk tiga hal yang tidak bisa dikerjakan Cloudflare:

1. Menulis tulisan blog lewat `/admin` dari mana saja, bukan hanya dari
   laptop ini.
2. PostGIS, kalau suatu saat ada peta yang datanya berubah tanpa Anda
   menerbitkan ulang situsnya.
3. Passkey dan API, yang butuh proses yang hidup.

Selama menulis blog masih nyaman dikerjakan dari laptop ini lalu di-push ke
git, VPS itu Rp75.000 sampai Rp150.000 sebulan untuk kenyamanan yang belum
tentu terasa. Itu bukan pendapat tentang uang Anda; itu supaya keputusannya
diambil dengan angka, bukan karena daftarnya belum semua tercentang.

### Kalau memang jadi

| Penyedia | Spesifikasi | Perkiraan per bulan |
| --- | --- | --- |
| Hetzner CX22 | 2 vCPU, 4 GB, 40 GB | sekitar Rp70.000 |
| DigitalOcean | 1 vCPU, 2 GB, 50 GB | sekitar Rp190.000 |
| Biznet Gio | 1 vCPU, 2 GB | sekitar Rp100.000 |
| IDCloudHost | 1 vCPU, 2 GB | sekitar Rp120.000 |

2 GB memori adalah batas bawah yang masuk akal: PostGIS, Redis, dan dua
pekerja uvicorn muat di 1 GB, tetapi tanpa ruang sisa untuk apa pun.

Penyedia Indonesia berarti latensi lebih rendah untuk pembaca di sini dan
tagihan dalam rupiah. Hetzner lebih murah dan lebih cepat mesinnya, dengan
tambahan sekitar 180 ms untuk pengunjung dari Indonesia, yang untuk API
tidak terasa dan untuk halaman statis tidak berlaku karena halamannya tetap
dari Cloudflare.

---

## Pemasangan

### 1. Mesin kosong

Ubuntu 24.04 LTS. Yang pertama dilakukan, sebelum apa pun:

```bash
ssh-copy-id root@ALAMAT           # dari laptop Anda
ssh root@ALAMAT
passwd -l root                    # kunci sandi root, sisakan kunci SSH saja
```

Lalu matikan masuk dengan sandi, di `/etc/ssh/sshd_config`:

```
PermitRootLogin prohibit-password
PasswordAuthentication no
```

`systemctl restart ssh`. **Jangan tutup sesi SSH yang sedang terbuka sebelum
membuktikan sesi baru bisa masuk.** Kesalahan di berkas itu mengunci Anda dari
mesin sendiri, dan satu satunya jalan kembali adalah konsol darurat penyedia.

### 2. Jalankan pemasangnya

```bash
git clone https://github.com/hendrokuswantoro/hendrokuswantoro.com /tmp/hk
sh /tmp/hk/infrastructure/pasang.sh
```

Idempoten: menjalankannya lagi aman dan tidak menggandakan apa pun.

Yang dikerjakannya: paket, Docker, rclone, pengguna sistem `hk` tanpa shell,
venv, berkas unit systemd, konfigurasi nginx, ufw, fail2ban, dan pembaruan
keamanan otomatis. Firewall-nya membuka SSH untuk semua orang dan porta 443
HANYA untuk jaringan Cloudflare di `infrastructure/cloudflare-ip.txt`. Porta 80
tertutup.

Yang **tidak** dikerjakannya, dengan sengaja: tidak memasang sertifikat TLS
(sertifikatnya dibuat di dasbor Cloudflare, lihat langkah 5), tidak mengisi
rahasia (rahasia diketik manusia, tidak dibangkitkan skrip yang keluarannya
masuk log), dan tidak menyalakan apa pun.

### 3. Isi rahasianya

```bash
sudo nano /etc/hendrokuswantoro/env
```

Yang wajib:

```
POSTGRES_PASSWORD=...
DSN=postgresql://hendro:...@127.0.0.1:5433/hendrokuswantoro
JWT_SECRET=...                 # python -c "import secrets;print(secrets.token_urlsafe(48))"
CADANGAN_KUNCI=...             # python backend/db/enkripsi.py kunci
MAPBOX_TOKEN=pk....
WEBAUTHN_RP_ID=admin.hendrokuswantoro.com
WEBAUTHN_ASAL=["https://admin.hendrokuswantoro.com"]
CADANGAN_TUJUAN=r2:hk-cadangan/harian
KUNCI_KOLOM=...                # SALINAN dari laptop, bukan kunci baru; lihat di bawah
SMTP_HOST=...
SMTP_PORTA=587
SMTP_PENGGUNA=...
SMTP_SANDI=...
SURAT_DARI=...
SURAT_WAJIB=1
```

`KUNCI_KOLOM` wajib sama dengan yang dipakai saat rahasia TOTP dan ciri wajah
disandikan. Kalau basis datanya dipindah dari laptop, kuncinya ikut dipindah;
kunci baru tidak bisa membuka rahasia lama. Kalau basis datanya baru, buat
kunci baru dengan `python backend/db/enkripsi.py kunci` dan simpan salinannya
di luar mesin ini sama seperti `CADANGAN_KUNCI`.

Berkas itu milik root dengan izin 0640 dan grup `hk`. Ia tidak pernah ada di
git, dan tidak pernah ikut rsync.

**Simpan salinan `CADANGAN_KUNCI` di tempat yang bukan mesin ini.** Kunci
yang hilang berarti seluruh cadangan yang sudah terenkripsi tidak akan pernah
bisa dibuka lagi, dan pada saat Anda menyadarinya, itu justru hari Anda
membutuhkannya.

### 4. Basis data, skema, admin

```bash
cd /srv/hendrokuswantoro/app/infrastructure
sudo -u hk docker compose --env-file /etc/hendrokuswantoro/env up -d

cd /srv/hendrokuswantoro/app
sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/migrasi.py
sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/muat_awal.py
sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/buat_admin.py
```

### 5. DNS dan sertifikat, di dasbor Cloudflare

Situs publik tetap di Worker Cloudflare, di `www`. Dashboard dan API tinggal
di `admin.hendrokuswantoro.com`, di VPS. Pemilik memilih susunan ini pada 28
September 2026. Alasannya:

- Situs publik tidak ikut mati kalau VPS mati.
- Beda nama berarti beda asal bagi peramban. Skrip yang lolos ke `www` tidak
  bisa membaca jawaban API admin, sebab CORS hanya mengizinkan `admin.`.
- `/admin` bisa dikunci terpisah, misalnya dengan Cloudflare Access.

Di dasbor Cloudflare, zona `hendrokuswantoro.com`:

1. **DNS**: record `A` (dan `AAAA` kalau VPS-nya punya IPv6) bernama `admin`
   ke alamat VPS, **Proxied** (awan oranye). Awan abu abu membuka alamat VPS
   ke dunia, dan firewall di atas akan menolak semua orang.
2. **SSL/TLS, Overview**: **Full (strict)**. Worker di `www` tidak
   terpengaruh, sebab ia tidak punya origin.
3. **SSL/TLS, Origin Server, Create Certificate**, untuk
   `hendrokuswantoro.com` dan `*.hendrokuswantoro.com`, 15 tahun. Tempel
   sertifikatnya ke `/etc/ssl/hendrokuswantoro/origin.pem` dan kuncinya ke
   `origin.key` di folder yang sama, lalu `chmod 0600` kuncinya. Kuncinya
   hanya ditampilkan sekali; kalau hilang, buat sertifikat baru.

Sertifikat origin Cloudflare hanya dipercaya Cloudflare, bukan peramban. Itu
disengaja: tidak ada yang boleh menghubungi VPS tanpa lewat Cloudflare. Ini
juga menghapus certbot sama sekali. Certbot butuh porta 80 terbuka untuk Let's
Encrypt, dan porta itu justru ditutup.

### Alamat asli pengunjung

Di balik Cloudflare, nginx melihat alamat Cloudflare, bukan alamat orangnya.
Tanpa perbaikan, pembatas masuk sepuluh kali per menit berlaku untuk SEMUA
orang sekaligus, jadi satu penyerang bisa membuat pemilik tidak bisa masuk.
Kunci `admin_boleh` per alamat juga tidak berguna, dan jejak keamanan mencatat
alamat Cloudflare.

Karena itu nginx membaca `CF-Connecting-IP`, tetapi HANYA dari jaringan
Cloudflare (`set_real_ip_from`). Tajuk yang sama dari alamat lain diabaikan,
dan firewall memang tidak membiarkan alamat lain masuk. Daftar jaringannya
tinggal di `infrastructure/cloudflare-ip.txt` dan dibangkitkan oleh
`tools/ip_cloudflare.py`:

```bash
python tools/ip_cloudflare.py --ambil     # ambil daftar terbaru, tulis ulang nginx
python tools/ip_cloudflare.py --banding   # bandingkan dengan api.cloudflare.com
```

Pemeriksaan kesehatan malam menjalankan `--banding`. Kalau Cloudflare menambah
jaringan, jalankan `--ambil`, commit, lalu di VPS jalankan ulang `pasang.sh`
supaya firewall ikut. Jaringan yang DIHAPUS Cloudflare tidak ikut hilang dari
ufw dengan sendirinya; hapus aturannya dengan `sudo ufw status numbered` lalu
`sudo ufw delete <nomor>`.

Server bawaan nginx menolak jabat tangan TLS untuk nama apa pun selain nama
milik situs ini (`ssl_reject_handshake`). Lapisan tambahan yang belum dipasang
adalah Authenticated Origin Pulls: Cloudflare menunjukkan sertifikat klien dan
nginx menolak yang tidak membawanya. Ia butuh sakelar di dasbor, dan kalau
nginx menuntutnya sebelum sakelarnya menyala, seluruh dashboard menjawab 400.

### Cloudflare Access, disarankan

Akun admin di VPS lahir tanpa faktor kedua. Selama itu, siapa pun yang tahu
sandinya bisa memasang faktor PERTAMA miliknya sendiri. Sebelum record DNS
`admin` dibuat, pasang aplikasi Cloudflare Access (Zero Trust,
gratis untuk sedikit pemakai) untuk `admin.hendrokuswantoro.com`, dengan
aturan yang hanya mengizinkan `kuswantoro.hendro01@gmail.com`. Lalu masuk dan
pasang authenticator serta passkey hari itu juga.

### 6. Nyalakan

```bash
sudo systemctl start hk-api
sudo systemctl start hk-cadangan.timer
sudo nginx -t && sudo systemctl reload nginx
```

### 7. Buktikan cadangannya, sekarang

```bash
sudo systemctl start hk-cadangan.service
sudo journalctl -u hk-cadangan -n 40 --no-pager
```

Yang dicari di keluarannya: baris `BERHASIL: ... pulih utuh, seluruh jumlah
baris cocok`. Kalau baris itu tidak ada, cadangannya belum terbukti apa apa,
dan tidak ada gunanya melanjutkan sampai ia ada.

---

## Deploy otomatis

`.github/workflows/vps.yml` berjalan sesudah CI hijau, dan **hanya** kalau
variabel repositori `VPS_AKTIF` berisi `1`. Selama VPS-nya belum ada, seluruh
pekerjaannya dilewati; alur kerja yang gagal tiap push adalah lampu merah yang
berhenti dibaca.

Yang harus diisi di **Settings > Secrets and variables > Actions**:

| Jenis | Nama | Isi |
| --- | --- | --- |
| Secret | `VPS_HOST` | alamat IP |
| Secret | `VPS_PENGGUNA` | akun SSH untuk deploy |
| Secret | `VPS_SSH_KUNCI` | kunci privat OpenSSH, khusus deploy |
| Secret | `VPS_PORTA` | opsional, bawaannya 22 |
| Variable | `VPS_AKTIF` | `1` |
| Variable | `SITUS` | `https://www.hendrokuswantoro.com` |
| Variable | `ADMIN` | opsional, bawaannya `https://admin.hendrokuswantoro.com` |

`VPS_HOST` adalah alamat asli VPS, bukan `admin.hendrokuswantoro.com`: nama
itu menunjuk Cloudflare, dan Cloudflare tidak meneruskan SSH.

Buat kunci khusus untuk ini, jangan pakai kunci pribadi Anda:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/hk-deploy -C "deploy hendrokuswantoro" -N ""
```

Akun deploy perlu `sudo systemctl restart hk-api` tanpa sandi, dan tidak
perlu apa apa lagi. Di `/etc/sudoers.d/hk-deploy`:

```
deploy ALL=(root) NOPASSWD: /bin/systemctl restart hk-api
```

Satu baris itu, bukan `NOPASSWD: ALL`. Kunci deploy yang bocor lalu bisa
menjalankan apa saja sebagai root adalah mesin yang bocor seluruhnya.

Urutan langkahnya: bangun situs, kirim `dist/`, kirim kodenya, pasang
dependensi, **migrasi**, baru nyalakan ulang. Migrasi sebelum restart, bukan
sesudah: urutan sebaliknya membuat kode baru sempat berjalan di atas skema
lama.

Yang tidak dikerjakannya: pengembalian otomatis. Deploy yang gagal
mengembalikan dirinya sendiri terdengar bagus sampai ia mengembalikan
kodenya tanpa mengembalikan skemanya. Kalau gagal, langkah terakhir mencetak
apa yang harus dilakukan.

---

## Cadangan terjadwal

`hk-cadangan.timer` menyala 02:40 waktu setempat, dengan sebaran acak sampai
20 menit. Bukan jam bulat, sebab jam bulat adalah saat seluruh dunia
menjalankan tugas terjadwalnya sekaligus.

`Persistent=true` yang membedakannya dari cron: kalau mesinnya mati semalam,
cadangannya dijalankan begitu ia hidup lagi, bukan dilewati diam diam.

Tiga langkah, dan yang kedua yang paling penting:

```
cadangan.py buat        pg_dump, gzip, AES-256-GCM
cadangan.py uji-pulih   pulihkan ke basis data sementara, hitung barisnya
kirim.sh                naikkan ke object storage
```

Kalau salah satu gagal, unitnya gagal, dan `hk-cadangan-gagal@.service`
memanggil `beritahu.sh`. Isi `TELEGRAM_TOKEN` dan `TELEGRAM_TUJUAN` di
`/etc/hendrokuswantoro/env` supaya pesannya sampai ke saku, bukan berhenti di
journal yang tidak pernah dibuka.

`kirim.sh` **menolak** berkas yang tidak terenkripsi, dan memeriksanya dari
penanda di dalam berkas, bukan dari akhiran namanya. Di mesin ini, cadangan
yang belum terkunci masih bisa dimaklumi; begitu ia naik ke penyedia lain,
alamat email dan hash sandi ada di tangan orang lain.

Retensi 14 berkas di mesin, 30 hari di penyedia. Keduanya bisa diatur:
`SIMPAN_TERAKHIR` di `cadangan.py`, `CADANGAN_SIMPAN_HARI` di environment.

### Memulihkan sungguhan

```bash
sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/cadangan.py daftar
sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/cadangan.py \
    pulihkan cadangan/hk-2026-09-12-0240.sql.gz.enc
```

Ia akan meminta Anda mengetik `PULIHKAN` dengan huruf besar. Itu bukan
formalitas: perintah itu menimpa seluruh isi basis data yang sekarang.

---

## Kalau nanti pindah sepenuhnya dari Cloudflare

nginx masih memuat server untuk `www` yang menyajikan situs statis yang sama,
dengan header keamanan yang sama persis, dijaga `tests/test_infrastruktur.py`
supaya keduanya tidak pernah bergeser. Tetapi pindah tidak lagi cukup dengan
mengganti DNS: sertifikat origin hanya dipercaya Cloudflare, firewall hanya
menerima Cloudflare, dan `set_real_ip_from` hanya berarti di balik Cloudflare.
Ketiganya harus diganti bersamaan, ditambah sertifikat Let's Encrypt.

Yang hilang kalau pindah: cache tepi di puluhan kota, perlindungan DDoS, dan
sertifikat yang mengurus dirinya sendiri. Yang didapat: satu mesin yang
seluruhnya milik Anda dan yang seluruhnya jadi tanggung jawab Anda untuk
ditambal.

## Gambar unggahan di situs publik

Foto dan video dari dashboard disimpan di VPS dan disajikan di
`https://admin.hendrokuswantoro.com/unggahan/...`. Situs publik di Cloudflare
belum membangun tulisan dari basis data (`bangun_tulisan.py --sumber api`
belum dipakai build Cloudflare), jadi hari ini belum ada tulisan terbit yang
menunjuk unggahan. Saat jalur itu dipasang, berkas unggahan yang disebut
tulisan wajib ikut disalin ke `dist/unggahan/` saat build. Jangan menunjuk
`admin.` langsung dari situs publik: itu membuka CSP situs ke subdomain admin
dan membuat tiap pembaca menyambung ke VPS.
