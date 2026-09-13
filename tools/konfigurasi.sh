#!/bin/sh
# Writes assets/js/konfigurasi.js from the MAPBOX_TOKEN environment variable.
#
# This is the build command for Cloudflare Pages when the site is deployed
# from GitHub. The token never enters the repository: it lives in the Pages
# project under Settings, Environment variables, and this script pours it
# into the one file the map reads at runtime.
#
# In Cloudflare Pages set:
#   Build command:      sh tools/konfigurasi.sh
#   Output directory:   /
#   Environment var:    MAPBOX_TOKEN = pk....
#
# Without the variable the script still finishes and the site still works.
# The map falls back to OpenFreeMap and loses the buildings, boundaries,
# road hierarchy and names that only the Mapbox vector tiles carry, so the
# warning below is worth reading in the build log.

set -eu

TUJUAN="assets/js/konfigurasi.js"

# On a developer machine the token lives in .env, not in the shell. Without
# this fallback the script quietly wrote an empty token over the working one,
# the map fell back to OpenFreeMap, and four browser tests failed with
# messages about missing layers that said nothing about the real cause. That
# happened. Every other tool in this repository already reads .env; this one
# was the exception.
#
# Satu sed, bukan rangkaian tr dengan tanda kutip bertumpuk. Percobaan
# pertama memakai `tr -d` untuk membuang tanda kutip dan carriage return,
# dan tumpukan kutipnya menyelundupkan satu bita CR ke dalam berkas ini.
# Bash memaafkannya, dash tidak, jadi `sh -n` di runner gagal sementara di
# mesin ini lolos. Token Mapbox hanya memuat huruf, angka, titik, garis
# bawah, dan tanda hubung, jadi cukup ambil yang itu saja: tanda kutip,
# spasi, dan CR ikut tertinggal dengan sendirinya.
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
/* Written by tools/konfigurasi.sh at build time. Do not edit by hand and do
   not commit: the value comes from the MAPBOX_TOKEN environment variable. */
window.HK_KONFIG = {
  mapboxToken: "$TOKEN"
};
JS

echo "konfigurasi.sh: wrote $TUJUAN"
