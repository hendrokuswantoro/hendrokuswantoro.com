#!/bin/sh

set -u

cd "$(dirname "$0")/.." || exit 1
mkdir -p cadangan
CATATAN=cadangan/harian.log
PAKSA_UJI=0
[ "${1:-}" = "--uji-pulih" ] && PAKSA_UJI=1

jalankan() {
  echo "== $(date '+%Y-%m-%d %H:%M')"

  if ! docker info >/dev/null 2>&1; then
    echo "GAGAL: Docker Desktop tidak menyala, cadangan dilewati"
    return 1
  fi

  if [ "$(docker inspect -f '{{.State.Running}}' hk_db 2>/dev/null)" != "true" ]; then
    echo "basis data mati, dinyalakan dulu"
    (cd infrastructure && docker compose --env-file ../.env up -d db >/dev/null) || return 1
    for _ in $(seq 1 60); do
      docker exec hk_db pg_isready -q >/dev/null 2>&1 && break
      sleep 1
    done
  fi

  python backend/db/cadangan.py buat || return 1

  if [ "$PAKSA_UJI" = "1" ] || [ "$(date +%u)" = "7" ]; then
    echo "membuktikan cadangan terbaru bisa dipulihkan"
    python backend/db/cadangan.py uji-pulih || return 1
  fi
  echo "selesai"
}

jalankan < /dev/null >> "$CATATAN" 2>&1
hasil=$?

tail -n 400 "$CATATAN" > "$CATATAN.baru" && mv "$CATATAN.baru" "$CATATAN"

if [ "$hasil" -ne 0 ] && [ -x /c/Windows/System32/msg.exe ]; then
  /c/Windows/System32/msg.exe "*" "Cadangan harian hendrokuswantoro.com GAGAL. Lihat cadangan/harian.log di folder proyek." < /dev/null
fi
exit "$hasil"
