#!/bin/sh

set -eu

TUJUAN="assets/js/konfigurasi.js"

if [ -z "${MAPBOX_TOKEN:-}" ] && [ -f .env ]; then
  POLA='s/^MAPBOX_TOKEN=[^A-Za-z0-9._-]*\([A-Za-z0-9._-]*\).*/\1/p'
  DARI_ENV=$(sed -n "$POLA" .env | head -1)
  if [ -n "$DARI_ENV" ]; then
    MAPBOX_TOKEN="$DARI_ENV"
    echo "konfigurasi.sh: token read from .env"
  fi
fi

if [ -z "${MAPBOX_TOKEN:-}" ]; then
  echo "konfigurasi.sh: MAPBOX_TOKEN is not set."
  echo "konfigurasi.sh: the map will fall back to OpenFreeMap."
  TOKEN=""
else
  TOKEN="$MAPBOX_TOKEN"
  echo "konfigurasi.sh: token found, ${#TOKEN} characters."
fi

cat > "$TUJUAN" <<JS
window.HK_KONFIG = {
  mapboxToken: "$TOKEN"
};
JS

echo "konfigurasi.sh: wrote $TUJUAN"
