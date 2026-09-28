#!/bin/sh

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
KONFIG="$AKAR/infrastructure/nginx/hendrokuswantoro.conf"
CITRA=nginx:1.27-alpine

if command -v cygpath >/dev/null 2>&1; then
  KONFIG=$(cygpath -m "$KONFIG")
fi

if [ ! -f "$KONFIG" ]; then
  echo "tidak ada: $KONFIG" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker tidak ada, pemeriksaan dilewati" >&2
  exit 0
fi

echo "memeriksa $KONFIG dengan $CITRA"

docker run --rm \
  -v "$KONFIG:/etc/nginx/conf.d/hendrokuswantoro.conf:ro" \
  "$CITRA" sh -eu -c '
    apk add --no-cache openssl >/dev/null 2>&1

    mkdir -p /etc/ssl/hendrokuswantoro /srv/hendrokuswantoro/situs /run/hk-api

    openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
      -subj "/CN=hendrokuswantoro.com" \
      -keyout /etc/ssl/hendrokuswantoro/origin.key \
      -out    /etc/ssl/hendrokuswantoro/origin.pem \
      >/dev/null 2>&1

    nginx -t
  '

echo "konfigurasi nginx lolos"
