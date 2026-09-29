#!/bin/sh

set -eu

cd "$(dirname "$0")/.."

if ! docker info >/dev/null 2>&1; then
  echo "Docker belum menyala. Buka Docker Desktop, tunggu sampai ikonnya diam, lalu ulangi." >&2
  exit 1
fi

echo "menyalakan basis data dan cache"
(cd infrastructure && docker compose --env-file ../.env up -d db cache >/dev/null)

for _ in $(seq 1 60); do
  if docker exec hk_db pg_isready -q >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec hk_db pg_isready -q || { echo "basis data tidak menjawab dalam 60 detik" >&2; exit 1; }

python backend/db/migrasi.py
echo "dashboard: http://localhost:8000/admin, dan lewat terowongan bila TEROWONGAN_HOST diisi"
exec python backend/jalan.py
