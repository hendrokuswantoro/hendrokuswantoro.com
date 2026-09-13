#!/bin/sh
# Mengirim cadangan ke object storage. Bab 15.18.
#
#     sh infrastructure/kirim.sh            # kirim yang terbaru
#     sh infrastructure/kirim.sh --semua    # kirim semua yang belum terkirim
#     sh infrastructure/kirim.sh --coba     # sebutkan saja, jangan kirim
#
# Cadangan yang duduk di mesin yang sama dengan basis datanya bukan cadangan.
# Ia melindungi dari perintah DELETE yang salah, dan tidak melindungi sama
# sekali dari disk yang mati, penyedia yang menutup akun, atau ransomware yang
# mengunci seluruh isi mesin sekaligus. Karena itu ada berkas ini.
#
# ATURAN YANG TIDAK BOLEH DILANGGAR: berkas yang tidak terenkripsi tidak
# pernah dikirim. Di mesin ini, cadangan yang belum terkunci masih bisa
# dimaklumi, sebab siapa pun yang bisa membacanya sudah bisa membaca basis
# datanya. Begitu ia naik ke penyedia lain, isinya yang berupa alamat email
# dan hash sandi ada di tangan orang lain. Skrip ini menolak, bukan
# memperingatkan lalu tetap mengirim.
#
# rclone yang dipakai, bukan awscli, karena satu berkas konfigurasi yang sama
# bekerja untuk S3, Backblaze B2, Cloudflare R2, Wasabi, dan idcloudhost,
# sehingga pindah penyedia tidak menuntut skrip ini berubah.

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
CADANGAN="${CADANGAN_FOLDER:-$AKAR/cadangan}"

# Nama remote rclone dan jalurnya. Keduanya dari environment: nama bucket
# bukan rahasia, tetapi ia berbeda tiap mesin dan tidak boleh dipatok di kode.
TUJUAN="${CADANGAN_TUJUAN:-}"

SEMUA=0
COBA=0
for arg in "$@"; do
  case "$arg" in
    --semua) SEMUA=1 ;;
    --coba)  COBA=1 ;;
    *) echo "argumen tidak dikenal: $arg" >&2; exit 2 ;;
  esac
done

if [ -z "$TUJUAN" ]; then
  echo "CADANGAN_TUJUAN belum diisi, pengiriman dilewati." >&2
  echo "Contoh: CADANGAN_TUJUAN=r2:hk-cadangan/harian" >&2
  exit 0
fi

# Diperiksa hanya kalau memang akan mengirim. --coba tidak menghubungi
# siapa pun, dan menuntut rclone di situ membuat pemeriksaan penolakan berkas
# polos di CI lolos karena alasan yang salah: ia akan keluar dengan 1 karena
# rclone tidak ada, bukan karena berkasnya ditolak.
if [ "$COBA" -eq 0 ] && ! command -v rclone >/dev/null 2>&1; then
  echo "rclone tidak ada. Pasang dengan: curl https://rclone.org/install.sh | sudo bash" >&2
  exit 1
fi

if [ ! -d "$CADANGAN" ]; then
  echo "tidak ada folder cadangan: $CADANGAN" >&2
  exit 1
fi

# --- pilih berkasnya ---------------------------------------------------------
# Hanya yang berakhiran .enc. Akhirannya diperiksa lagi isinya di bawah:
# nama berkas bisa diganti siapa saja, penanda di dalamnya tidak.
if [ "$SEMUA" -eq 1 ]; then
  DAFTAR=$(ls -1 "$CADANGAN"/hk-*.sql.gz.enc 2>/dev/null || true)
else
  DAFTAR=$(ls -1 "$CADANGAN"/hk-*.sql.gz.enc 2>/dev/null | tail -1 || true)
fi

if [ -z "$DAFTAR" ]; then
  echo "tidak ada cadangan terenkripsi untuk dikirim." >&2
  echo "Isi CADANGAN_KUNCI di .env lalu jalankan: python backend/db/cadangan.py buat" >&2
  exit 1
fi

# --- kirim -------------------------------------------------------------------
# IFS dipotong jadi baris baru saja, dan globbing dimatikan, sebelum
# menelusuri daftarnya. Tanpa keduanya, satu spasi di jalur folder memecah
# nama berkas jadi dua, dan yang terjadi bukan galat melainkan dua "berkas"
# yang tidak ada lalu ditolak dengan alasan yang salah. Persis itu yang
# terjadi saat skrip ini pertama dicoba, di folder bernama "personal web".
IFS_ASLI=$IFS
IFS='
'
set -f

GAGAL=0
for berkas in $DAFTAR; do
  nama=$(basename "$berkas")

  # Penanda berkas terenkripsi, tujuh bita pertama. Diperiksa dari isinya,
  # bukan dari namanya.
  penanda=$(head -c 6 "$berkas" 2>/dev/null || true)
  if [ "$penanda" != "HKCAD1" ]; then
    echo "TOLAK $nama: isinya tidak terenkripsi meski namanya berakhiran .enc" >&2
    GAGAL=1
    continue
  fi

  if [ "$COBA" -eq 1 ]; then
    echo "akan dikirim: $nama -> $TUJUAN/"
    continue
  fi

  if rclone copyto --checksum "$berkas" "$TUJUAN/$nama"; then
    echo "terkirim: $nama"
  else
    echo "GAGAL mengirim: $nama" >&2
    GAGAL=1
  fi
done

set +f
IFS=$IFS_ASLI

# --- retensi di sisi penyedia ------------------------------------------------
# Sama dengan retensi lokal. Cadangan yang menumpuk selamanya adalah tagihan
# yang tumbuh selamanya, dan cadangan tiga tahun lalu tidak berguna untuk
# basis data yang skemanya sudah tiga kali berubah.
if [ "$COBA" -eq 0 ] && [ "$GAGAL" -eq 0 ]; then
  rclone delete --min-age "${CADANGAN_SIMPAN_HARI:-30}d" "$TUJUAN/" || true
fi

exit "$GAGAL"
