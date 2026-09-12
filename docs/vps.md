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
git clone https://github.com/hendrokuswantoro/personal-web /tmp/hk
sh /tmp/hk/infrastructure/pasang.sh
```

Idempoten: menjalankannya lagi aman dan tidak menggandakan apa pun.

Yang dikerjakannya: paket, Docker, rclone, pengguna sistem `hk` tanpa shell,
venv, berkas unit systemd, konfigurasi nginx, ufw dengan tiga porta terbuka,
fail2ban, dan pembaruan keamanan otomatis.

Yang **tidak** dikerjakannya, dengan sengaja: tidak meminta sertifikat TLS
(certbot butuh DNS sudah mengarah ke mesin itu, dan itu tidak bisa dipastikan
skrip), tidak mengisi rahasia (rahasia diketik manusia, tidak dibangkitkan
skrip yang keluarannya masuk log), dan tidak menyalakan apa pun.

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
WEBAUTHN_RP_ID=hendrokuswantoro.com
WEBAUTHN_ASAL=["https://www.hendrokuswantoro.com"]
CADANGAN_TUJUAN=r2:hk-cadangan/harian
```

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

### 5. DNS, lalu sertifikat

Arahkan `A` dan `AAAA` untuk `hendrokuswantoro.com` dan
`www.hendrokuswantoro.com` ke alamat VPS. **Tunggu sampai benar benar
menyebar**, periksa dengan `dig +short www.hendrokuswantoro.com`, baru:

```bash
sudo certbot --nginx -d hendrokuswantoro.com -d www.hendrokuswantoro.com
```

Let's Encrypt membatasi lima kegagalan per jam untuk nama yang sama. Meminta
sertifikat sebelum DNS-nya siap adalah cara paling cepat kehabisan jatah itu
lalu menunggu satu jam tanpa bisa berbuat apa apa.

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

Yang berubah hanya DNS. Konfigurasi nginx menyajikan situs statis yang sama,
dengan header keamanan yang sama persis, dijaga `tests/test_infrastruktur.py`
supaya keduanya tidak pernah bergeser satu sama lain.

Yang hilang: cache tepi di puluhan kota, perlindungan DDoS, dan sertifikat
yang mengurus dirinya sendiri. Yang didapat: satu mesin yang seluruhnya milik
Anda dan yang seluruhnya jadi tanggung jawab Anda untuk ditambal.

Susunan paling masuk akal adalah keduanya: Cloudflare di depan sebagai DNS
dan cache, VPS di belakang untuk `/api/` dan `/admin`.
