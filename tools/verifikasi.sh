#!/bin/sh
# Chapter 24 of the engineering standards: everything that has to pass before
# a task may be called finished. One command, so there is no excuse to skip a
# step by forgetting it.
#
#   sh tools/verifikasi.sh
#
# Exits non zero on the first failure and says which step it was. Steps that
# need a tool this machine does not have are reported as skipped rather than
# silently passed, because a check that quietly does nothing is worse than a
# check that is absent.

set -eu

cd "$(dirname "$0")/.."

LULUS=0
LEWAT=0

langkah() {
  printf '\n== %s\n' "$1"
}

lulus() {
  LULUS=$((LULUS + 1))
  printf '   ok\n'
}

lewat() {
  LEWAT=$((LEWAT + 1))
  printf '   skipped, %s\n' "$1"
}

# Node memang terpasang, hanya tidak ada di PATH milik Git Bash.
#
# Akibatnya dua langkah melaporkan "node is not installed on this machine",
# dan laporan itu tidak benar. Yang dilewati bukan hanya `node --check`,
# melainkan seluruh Type Check dan Build port Next.js, jadi selama ini satu
# satunya yang pernah membangunnya adalah CI. Berkas ini berhak melewatkan
# langkah yang memang tidak bisa dijalankan; ia tidak berhak mengatakan
# sesuatu tidak terpasang padahal terpasang.
if ! command -v node >/dev/null 2>&1; then
  for DIR in "/c/Program Files/nodejs" "/c/Program Files (x86)/nodejs"; do
    if [ -x "$DIR/node.exe" ]; then
      PATH="$DIR:$PATH"
      export PATH
      printf 'verifikasi.sh: node ditemukan di %s\n' "$DIR"
      break
    fi
  done
fi

langkah "Lint, shell scripts parse"
for berkas in tools/*.sh infrastructure/*.sh; do
  sh -n "$berkas"
done
lulus

langkah "Lint, Python compiles"
python -m compileall -q tools tests
lulus

langkah "Lint, JavaScript has no syntax error"
if command -v node >/dev/null 2>&1; then
  node --check assets/js/app.js
  node --check assets/js/peta.js
  lulus
else
  lewat "node is not installed on this machine"
fi

langkah "Type Check and Build, the Next.js port"
if command -v npm >/dev/null 2>&1; then
  (cd next && npm ci --no-audit --no-fund --silent      && npm run typecheck && npm run build >/dev/null)
  lulus
else
  lewat "npm is not installed, CI runs this instead"
fi

langkah "Lint, every text colour still passes WCAG AA"
python tools/kontras.py >/dev/null
lulus

langkah "Lint, the inline script hash matches _headers"
python tools/hash_skrip.py >/dev/null
lulus

langkah "Lint, the Next.js stylesheet is not behind"
python tools/gaya_next.py --periksa >/dev/null
lulus

langkah "Lint, the vendored font matches its record"
python tools/ambil_font.py --periksa >/dev/null
lulus

# Alur kerjanya sendiri tidak pernah diperiksa sebelum dijalankan di GitHub,
# dan satu "\n" harfiah di dalamnya membuat health check gagal tiap malam
# sambil melaporkan situsnya mati.
langkah "Lint, the GitHub workflows parse"
if python -c "import yaml" 2>/dev/null; then
  python tools/periksa_alur.py >/dev/null
  lulus
else
  lewat "pyyaml belum terpasang, pip install pyyaml"
fi

langkah "Reverse proxy, the nginx config is valid"
if command -v docker >/dev/null 2>&1; then
  sh infrastructure/periksa_nginx.sh >/dev/null
  lulus
else
  lewat "docker is not running, CI checks this instead"
fi

langkah "Lint, blog pages match their content"
python tools/bangun_tulisan.py --periksa >/dev/null
lulus

langkah "Test"
python -m pytest
lulus

langkah "E2E Test, Chromium"
# dijalankan terpisah: lihat alasannya di pytest.ini
if python -c "import playwright" 2>/dev/null; then
  python -m pytest -m peramban
  lulus
else
  lewat "playwright belum terpasang"
fi

langkah "Security Check, no credential in the repository"
POLA='pk\.eyJ[A-Za-z0-9]|sk\.eyJ[A-Za-z0-9]|BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}'
if git grep -nIE "$POLA" -- . ':!tests/test_peta.py' ':!tools/verifikasi.sh' ':!.github' >/dev/null 2>&1; then
  printf '   FAIL, a credential is tracked by git\n'
  git grep -nIE "$POLA" -- . ':!tests/test_peta.py' ':!tools/verifikasi.sh' ':!.github'
  exit 1
fi
lulus

langkah "Backup, an encrypted backup can be restored"
if [ -n "${DSN:-}" ] || grep -q '^DSN=.' .env 2>/dev/null; then
  python backend/db/cadangan.py buat >/dev/null
  python backend/db/cadangan.py uji-pulih >/dev/null
  lulus
else
  lewat "no database configured on this machine"
fi

langkah "Security Check, the token file is ignored"
if git ls-files --error-unmatch assets/js/konfigurasi.js >/dev/null 2>&1; then
  printf '   FAIL, konfigurasi.js is tracked and it carries the token\n'
  exit 1
fi
grep -q 'assets/js/konfigurasi.js' .gitignore
lulus

langkah "Build, the folder Cloudflare serves"
SIMPAN=""
if [ -f assets/js/konfigurasi.js ]; then
  SIMPAN=$(cat assets/js/konfigurasi.js)
fi
sh tools/bangun_situs.sh >/dev/null
JUMLAH=$(find dist -type f | wc -l | tr -d ' ')
if [ "$JUMLAH" -lt 30 ]; then
  printf '   FAIL, dist/ holds only %s files\n' "$JUMLAH"
  exit 1
fi
# bangun_situs.sh rewrites the token file from the environment, which on a
# developer machine means wiping the real token. Put it back.
if [ -n "$SIMPAN" ]; then
  printf '%s' "$SIMPAN" > assets/js/konfigurasi.js
fi
printf '   ok, dist/ holds %s files\n' "$JUMLAH"
LULUS=$((LULUS + 1))

langkah "Build, the upload bundle"
python tools/build_dist.py
lulus

langkah "Production Configuration Check"
grep -q 'Content-Security-Policy:' _headers
grep -q 'Strict-Transport-Security:' _headers
grep -q 'directory = "./dist"' wrangler.toml
test ! -f _redirects
lulus

printf '\n%s steps passed, %s skipped\n' "$LULUS" "$LEWAT"
