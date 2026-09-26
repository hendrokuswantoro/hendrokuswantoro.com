#!/bin/sh

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
CADANGAN="${CADANGAN_FOLDER:-$AKAR/cadangan}"

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

if [ "$COBA" -eq 0 ] && ! command -v rclone >/dev/null 2>&1; then
  echo "rclone tidak ada. Pasang dengan: curl https://rclone.org/install.sh | sudo bash" >&2
  exit 1
fi

if [ ! -d "$CADANGAN" ]; then
  echo "tidak ada folder cadangan: $CADANGAN" >&2
  exit 1
fi

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

IFS_ASLI=$IFS
IFS='
'
set -f

GAGAL=0
for berkas in $DAFTAR; do
  nama=$(basename "$berkas")

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

if [ "$COBA" -eq 0 ] && [ "$GAGAL" -eq 0 ]; then
  rclone delete --min-age "${CADANGAN_SIMPAN_HARI:-30}d" "$TUJUAN/" || true
fi

exit "$GAGAL"
