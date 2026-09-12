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
