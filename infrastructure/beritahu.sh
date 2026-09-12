#!/bin/sh
# Memberitahukan kegagalan sebuah unit systemd.
#
#     sh infrastructure/beritahu.sh hk-cadangan.service
#
# Dipanggil hk-cadangan-gagal@.service lewat OnFailure=. Dipisah jadi skrip
# sendiri supaya cara memberitahunya bisa berganti tanpa menyentuh berkas
# unit, dan supaya bisa dicoba dengan tangan.
#
# Isi pesannya hanya nama unit, waktunya, dan sepuluh baris terakhir dari
# journal. **Sepuluh baris itu tidak boleh dianggap aman untuk dikirim ke
# mana pun**: log bisa memuat pesan galat yang menyebut alamat atau nama
# berkas. Karena itu yang dikirim hanya ringkasannya, dan journal lengkapnya
# tetap di mesin, dibaca dengan `journalctl -u <unit> -n 200`.

set -eu

UNIT="${1:-tidak-disebut}"
WAKTU=$(date -Iseconds)
MESIN=$(hostname)

RINGKAS="[$MESIN] $UNIT gagal pada $WAKTU"

echo "$RINGKAS"

# Selalu tercatat di journal mesin itu sendiri, apa pun jalur lainnya.
if command -v logger >/dev/null 2>&1; then
  logger -t hk-beritahu -p daemon.err "$RINGKAS"
fi

# --- Telegram ----------------------------------------------------------------
# Dipilih karena satu satunya yang sampai ke saku dalam hitungan detik tanpa
# server surel sendiri, tanpa langganan, dan tanpa mempercayakan kunci apa pun
# ke pihak ketiga selain token bot yang bisa dicabut kapan saja.
#
# Kalau tokennya tidak diisi, skrip ini diam dan keluar dengan 0. Pemberitahuan
# yang belum dikonfigurasi bukan alasan menggagalkan lagi unit yang sudah gagal.
if [ -n "${TELEGRAM_TOKEN:-}" ] && [ -n "${TELEGRAM_TUJUAN:-}" ]; then
  PESAN="$RINGKAS

Sepuluh baris terakhir ada di mesin:
  journalctl -u $UNIT -n 200 --no-pager"

  curl -sS --max-time 20 \
    -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_TUJUAN}" \
    --data-urlencode "text=${PESAN}" \
    -o /dev/null || echo "pemberitahuan Telegram gagal dikirim" >&2
fi

exit 0
