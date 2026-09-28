#!/bin/sh

set -eu

cd "$(dirname "$0")/.."

sh tools/konfigurasi.sh

rm -rf dist
mkdir -p dist

for berkas in index.html about.html project.html parkir-jogja.html 404.html \
              robots.txt sitemap.xml feed.xml site.webmanifest \
              _headers CNAME; do
  cp "$berkas" dist/
done

cp -r assets dist/assets
mkdir -p dist/.well-known
cp .well-known/security.txt dist/.well-known/
cp -r blog dist/blog

JUMLAH=$(find dist -type f | wc -l | tr -d ' ')
echo "bangun_situs.sh: dist/ holds $JUMLAH files"
