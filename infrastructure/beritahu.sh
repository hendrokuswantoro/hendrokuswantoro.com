#!/bin/sh

set -eu

UNIT="${1:-tidak-disebut}"
WAKTU=$(date -Iseconds)
MESIN=$(hostname)

RINGKAS="[$MESIN] $UNIT gagal pada $WAKTU"

echo "$RINGKAS"

if command -v logger >/dev/null 2>&1; then
  logger -t hk-beritahu -p daemon.err "$RINGKAS"
fi

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
