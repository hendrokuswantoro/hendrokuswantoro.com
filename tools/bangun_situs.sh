#!/bin/sh
# Builds dist/, the folder Cloudflare actually serves.
#
# Two jobs, in this order:
#
#   1. write assets/js/konfigurasi.js from the MAPBOX_TOKEN environment
#      variable, because that file is gitignored and a clone has no token
#   2. copy only the files that belong on a web server into dist/
#
# What it leaves out: the README, tools/, the Next.js port, and the git
# metadata. None of those belong in front of a visitor.
#
# Cloudflare Workers (wrangler.toml present):
#   Build command: sh tools/bangun_situs.sh
#   Assets are read from ./dist, declared in wrangler.toml
#
# Cloudflare Pages (legacy workflow):
#   Build command:           sh tools/bangun_situs.sh
#   Build output directory:  dist

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
cp -r blog dist/blog

JUMLAH=$(find dist -type f | wc -l | tr -d ' ')
echo "bangun_situs.sh: dist/ holds $JUMLAH files"
