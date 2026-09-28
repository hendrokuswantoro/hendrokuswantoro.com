#!/bin/sh

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
  node --check assets/js/parkir.js
  for berkas in backend/admin/*.js; do
    node --check "$berkas"
  done
  node -e "const fs=require('fs'),vm=require('vm');const t=fs.readFileSync('backend/admin/index.html','utf8');const s=[...t.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');new vm.Script(s);"
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

langkah "Lint, asset versions match their contents"
python tools/versi_aset.py --periksa >/dev/null
lulus

langkah "Lint, the face model matches its record"
if [ -f assets/model/sumber.json ]; then
  python tools/ambil_model.py --periksa >/dev/null
  lulus
else
  lewat "model wajah belum diunduh, python tools/ambil_model.py"
fi

langkah "Lint, the GitHub workflows parse"
if python -c "import yaml" 2>/dev/null; then
  python tools/periksa_alur.py >/dev/null
  lulus
else
  lewat "pyyaml belum terpasang, pip install pyyaml"
fi

langkah "Reverse proxy, the nginx config is valid"
if ! command -v docker >/dev/null 2>&1; then
  lewat "docker is not installed, CI checks this instead"
elif ! docker info >/dev/null 2>&1; then
  lewat "docker daemon is not answering, CI checks this instead"
else
  sh infrastructure/periksa_nginx.sh >/dev/null
  lulus
fi

langkah "Lint, blog pages match their content"
python tools/bangun_tulisan.py --periksa >/dev/null
lulus

langkah "Test"
python -m pytest
lulus

langkah "E2E Test, Chromium"
if ! python -c "import playwright" 2>/dev/null; then
  lewat "playwright belum terpasang"
elif ! python tools/peramban_siap.py; then
  lewat "chromium belum diunduh, jalankan: python -m playwright install chromium"
else
  python -m pytest -m peramban
  lulus
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
if [ -z "${DSN:-}" ] && ! grep -q '^DSN=.' .env 2>/dev/null; then
  lewat "no database configured on this machine"
elif ! python tools/basis_data_hidup.py; then
  lewat "the database is configured but nothing answers on its port"
else
  python backend/db/cadangan.py buat >/dev/null
  python backend/db/cadangan.py uji-pulih >/dev/null
  lulus
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
