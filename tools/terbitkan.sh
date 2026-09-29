#!/bin/sh

set -eu

cd "$(dirname "$0")/.."

set -- content/blog content/unggahan blog feed.xml sitemap.xml

if ! curl -sf -o /dev/null http://127.0.0.1:8000/api/v1/blog; then
  echo "Dashboard belum menyala. Jalankan tools/nyalakan_dashboard.cmd dulu, lalu ulangi." >&2
  exit 1
fi

cabang=$(git rev-parse --abbrev-ref HEAD)
if [ "$cabang" != "main" ]; then
  echo "Repositori sedang di cabang $cabang, bukan main. Tidak ada yang dikirim." >&2
  exit 1
fi

echo "menyamakan dengan GitHub"
git pull --ff-only --quiet || {
  echo "Salinan di laptop dan di GitHub sudah berbeda arah. Tidak ada yang dikirim." >&2
  exit 1
}

echo "mengambil tulisan terbit dari dashboard"
python tools/bangun_tulisan.py --sumber api

git add -A -- "$@"
if git diff --cached --quiet -- "$@"; then
  echo
  echo "Tidak ada yang baru. Situs sudah sama dengan dashboard."
  exit 0
fi

echo
echo "yang akan diterbitkan:"
git diff --cached --name-status -- "$@"

tulisan=$(git diff --cached --name-only -- content/blog | sed -n 's#^content/blog/\(.*\)\.md$#\1#p' | tr '\n' ' ')
git commit --quiet -m "tulisan: terbitkan dari dashboard ${tulisan:-(foto dan halaman)}" -- "$@"
git push --quiet origin main

echo
echo "Terkirim. Cloudflare menerbitkannya dalam sekitar dua menit."
echo "Cek di https://www.hendrokuswantoro.com/blog/"
