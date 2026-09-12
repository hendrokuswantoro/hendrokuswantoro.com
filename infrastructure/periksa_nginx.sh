#!/bin/sh
# Memeriksa konfigurasi nginx tanpa punya VPS dan tanpa memasang nginx.
#
#     sh infrastructure/periksa_nginx.sh
#
# Dijalankan di dalam kontainer nginx resmi, jadi yang memeriksanya adalah
# nginx sungguhan dengan versi yang sama dengan yang akan dipakai server.
# Tanpa ini, salah ketik satu titik koma baru ketahuan saat `systemctl reload
# nginx` di server menolak menyala, dan pada saat itu situsnya sudah mati.
#
# Sertifikat TLS tidak ada di mesin ini, dan nginx menolak konfigurasi yang
# menyebut berkas sertifikat yang tidak ada. Jadi skrip ini membuat
# sertifikat tanda tangan sendiri di dalam kontainer, hanya untuk pemeriksaan
# ini, lalu membuangnya bersama kontainernya. Yang diperiksa susunan
# konfigurasinya; sertifikat sungguhan datang dari certbot di server.

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
KONFIG="$AKAR/infrastructure/nginx/hendrokuswantoro.conf"
CITRA=nginx:1.27-alpine

# Di Git Bash pada Windows, pwd menjawab /d/Projects/... yang tidak dikenal
# Docker Desktop, dan mountnya gagal tanpa pesan yang jelas. cygpath ada
# persis di lingkungan itu dan tidak ada di mana pun lainnya, jadi ia sekaligus
# jadi cara mendeteksinya.
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
    # Citra nginx resmi tidak membawa openssl. Tanpa baris ini kegagalannya
    # hanya berupa kode keluar 127 yang tidak menyebut apa apa.
    apk add --no-cache openssl >/dev/null 2>&1

    mkdir -p /etc/letsencrypt/live/hendrokuswantoro.com /var/www/certbot \
             /srv/hendrokuswantoro/situs /run/hk-api

    # Sertifikat sementara, hanya supaya nginx mau membaca berkasnya.
    openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
      -subj "/CN=hendrokuswantoro.com" \
      -keyout /etc/letsencrypt/live/hendrokuswantoro.com/privkey.pem \
      -out    /etc/letsencrypt/live/hendrokuswantoro.com/fullchain.pem \
      >/dev/null 2>&1

    # Dua berkas yang biasanya dipasang certbot.
    printf "ssl_session_cache shared:le_nginx_SSL:10m;\nssl_session_timeout 1440m;\nssl_protocols TLSv1.2 TLSv1.3;\nssl_prefer_server_ciphers off;\n" \
      > /etc/letsencrypt/options-ssl-nginx.conf
    openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048 >/dev/null 2>&1

    nginx -t
  '

echo "konfigurasi nginx lolos"
