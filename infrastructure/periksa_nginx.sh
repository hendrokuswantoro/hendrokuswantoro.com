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
    apk add --no-cache openssl curl >/dev/null 2>&1

    SITUS=/srv/hendrokuswantoro/situs
    mkdir -p /etc/ssl/hendrokuswantoro "$SITUS/assets/css" /run/hk-api

    openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
      -subj "/CN=hendrokuswantoro.com" \
      -keyout /etc/ssl/hendrokuswantoro/origin.key \
      -out    /etc/ssl/hendrokuswantoro/origin.pem \
      >/dev/null 2>&1

    nginx -t

    echo "<h1>about</h1>" > "$SITUS/about.html"
    echo "tidak ada" > "$SITUS/404.html"
    echo "a{}" > "$SITUS/assets/css/style.css"
    nginx -g "error_log /dev/null crit;" 2>/dev/null

    kepala() {
      curl -sk -o /dev/null -D - --resolve "$1:443:127.0.0.1" "https://$1$2" | tr -d "\r" | tr "A-Z" "a-z"
    }
    gagal=0
    tuntut() {
      if printf "%s\n" "$2" | grep -q "$3"; then echo "ok    $1"; else echo "GAGAL $1"; gagal=1; fi
    }
    tolak() {
      if printf "%s\n" "$2" | grep -q "$3"; then echo "GAGAL $1"; gagal=1; else echo "ok    $1"; fi
    }
    satu() {
      if [ "$(printf "%s\n" "$2" | grep -c "$3")" = "1" ]; then echo "ok    $1"; else echo "GAGAL $1"; gagal=1; fi
    }

    h=$(kepala www.hendrokuswantoro.com /about.html)
    tuntut "alamat .html dialihkan ke alamat bersih" "$h" "^location: https://www.hendrokuswantoro.com/about$"

    h=$(kepala www.hendrokuswantoro.com "/%5Cevil.com/x.html")
    tolak "garis miring terbalik tidak menjadi pengalihan ke situs lain" "$h" "^location:"

    h=$(kepala www.hendrokuswantoro.com /about)
    satu "halaman HTML membawa satu cache-control, divalidasi ulang" "$h" "^cache-control: public, max-age=0, must-revalidate$"
    tuntut "halaman HTML membawa CSP" "$h" "^content-security-policy: "
    tuntut "versi nginx tidak disebut" "$h" "^server: nginx$"

    h=$(kepala www.hendrokuswantoro.com /assets/css/style.css)
    satu "aset membawa tepat satu cache-control" "$h" "^cache-control:"
    tuntut "aset dijanjikan immutable" "$h" "^cache-control: public, max-age=31536000, immutable$"
    tuntut "aset tetap membawa HSTS" "$h" "^strict-transport-security: "

    h=$(kepala hendrokuswantoro.com /about)
    tuntut "nama tanpa www mengalihkan ke www" "$h" "^location: https://www.hendrokuswantoro.com/about$"
    tuntut "nama tanpa www mengirim HSTS, syarat daftar preload" "$h" "^strict-transport-security: max-age=63072000; includesubdomains; preload$"

    exit "$gagal"
  '

echo "konfigurasi nginx lolos"
