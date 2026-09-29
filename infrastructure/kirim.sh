#!/bin/sh

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
CADANGAN="${CADANGAN_FOLDER:-cadangan}"
case "$CADANGAN" in
  /*|[A-Za-z]:*) ;;
  *) CADANGAN="$AKAR/$CADANGAN" ;;
esac

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

daftar() {
  for f in "$CADANGAN"/hk-*.sql.gz.enc; do
    if [ -f "$f" ]; then printf '%s\n' "$f"; fi
  done
}

if [ "$SEMUA" -eq 1 ]; then
  DAFTAR=$(daftar)
else
  DAFTAR=$(daftar | tail -1)
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

UNGGAHAN="$CADANGAN/unggahan"
if [ -d "$UNGGAHAN" ]; then
  SIAP=$(mktemp)
  JUMLAH=0
  for jalur in "$UNGGAHAN"/*; do
    [ -f "$jalur" ] || continue
    berkas=${jalur##*/}
    penanda=$(head -c 6 "$UNGGAHAN/$berkas" 2>/dev/null || true)
    case "$berkas" in
      *.enc) ;;
      *) penanda="" ;;
    esac
    if [ "$penanda" != "HKCAD1" ]; then
      echo "TOLAK unggahan/$berkas: tidak terenkripsi" >&2
      GAGAL=1
      continue
    fi
    printf '%s\n' "$berkas" >> "$SIAP"
    JUMLAH=$((JUMLAH + 1))
  done

  if [ "$COBA" -eq 1 ]; then
    echo "akan dikirim: $JUMLAH berkas unggahan -> $TUJUAN/unggahan/"
  elif [ "$JUMLAH" -gt 0 ]; then
    if rclone copy --checksum --files-from "$SIAP" "$UNGGAHAN" "$TUJUAN/unggahan"; then
      echo "terkirim: $JUMLAH berkas unggahan, yang sudah ada di sana dilewati"
    else
      echo "GAGAL mengirim unggahan" >&2
      GAGAL=1
    fi
  fi
  rm -f "$SIAP"
fi

if [ "$COBA" -eq 0 ] && [ "$GAGAL" -eq 0 ]; then
  rclone delete --max-depth 1 --min-age "${CADANGAN_SIMPAN_HARI:-30}d" "$TUJUAN/" || true
fi

exit "$GAGAL"
