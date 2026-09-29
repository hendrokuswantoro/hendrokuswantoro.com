#!/bin/sh

set -eu

cd "$(dirname "$0")/.."
AKAR=$(pwd)
TUMPUKAN="infrastructure/uji-keamanan/compose.yml"
JARINGAN=hk-uji-keamanan_default
HASIL="${1:-$AKAR/hasil-uji-keamanan}"
MODE="${UJI_MODE:-penuh}"

jalur() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi
}

SEMENTARA=$(mktemp -d)
bersihkan() {
  MSYS_NO_PATHCONV=1 docker compose -f "$TUMPUKAN" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$SEMENTARA"
}
trap bersihkan EXIT INT TERM

mkdir -p "$HASIL" cadangan "$SEMENTARA/sertifikat"
chmod 777 "$HASIL"

python - "$(jalur "$SEMENTARA/env")" <<'PY'
import base64, secrets, sys
kunci = lambda: base64.b64encode(secrets.token_bytes(32)).decode()
baris = {
    "DSN": "postgresql://hendro:uji@db:5432/hendrokuswantoro",
    "REDIS_URL": "redis://cache:6379/0",
    "JWT_SECRET": secrets.token_urlsafe(48),
    "KUNCI_KOLOM": kunci(),
    "CADANGAN_KUNCI": kunci(),
    "WEBAUTHN_RP_ID": "www.hendrokuswantoro.com",
    "WEBAUTHN_ASAL": '["https://www.hendrokuswantoro.com"]',
    "ASAL_DIIZINKAN": '["https://www.hendrokuswantoro.com"]',
    "COOKIE_AMAN": "true",
    "ADMIN_NEXT": "1",
    "DOKUMEN_API": "1",
    "FAKTOR_KEDUA_WAJIB": "false",
    "AKSES_UMUR_MENIT": "240",
    "UNGGAHAN_DIR": "/srv/hendrokuswantoro/unggahan",
    "CADANGAN_FOLDER": "/srv/hendrokuswantoro/app/cadangan",
    "HK_UJI_SANDI": secrets.token_urlsafe(24),
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.writelines(f"{k}={v}\n" for k, v in baris.items())
PY
: > "$SEMENTARA/kosong.env"
sed -e 's/rate=[0-9]*r\/[sm]/rate=10000r\/s/' -e 's/limit_conn sambungan [0-9]*/limit_conn sambungan 10000/' \
  infrastructure/nginx/hendrokuswantoro.conf > "$SEMENTARA/nginx.conf"

MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
  -subj "/CN=www.hendrokuswantoro.com" \
  -addext "subjectAltName=DNS:www.hendrokuswantoro.com,DNS:hendrokuswantoro.com" \
  -keyout "$(jalur "$SEMENTARA/sertifikat/origin.key")" \
  -out "$(jalur "$SEMENTARA/sertifikat/origin.pem")" 2>/dev/null >/dev/null \
  || { echo "openssl gagal membuat sertifikat uji" >&2; exit 1; }
chmod 644 "$SEMENTARA/sertifikat/origin.key"

[ -f dist/index.html ] || sh tools/bangun_situs.sh >/dev/null
[ -f next/out/admin/index.html ] || { echo "next/out belum dibangun: cd next && npm run build" >&2; exit 1; }

export HK_UJI_ENV HK_UJI_KOSONG HK_UJI_SERTIFIKAT HK_UJI_NGINX
HK_UJI_NGINX=$(jalur "$SEMENTARA/nginx.conf")
HK_UJI_ENV=$(jalur "$SEMENTARA/env")
HK_UJI_KOSONG=$(jalur "$SEMENTARA/kosong.env")
HK_UJI_SERTIFIKAT=$(jalur "$SEMENTARA/sertifikat")

echo "menyalakan tiruan produksi"
MSYS_NO_PATHCONV=1 docker compose -f "$TUMPUKAN" up -d --build --quiet-pull >/dev/null

siap=0
for _ in $(seq 1 90); do
  kode=$(MSYS_NO_PATHCONV=1 docker run --rm --network "$JARINGAN" curlimages/curl:latest \
    -sk -o /dev/null -w '%{http_code}' https://www.hendrokuswantoro.com/api/v1/blog 2>/dev/null || true)
  if [ "$kode" = "200" ]; then siap=1; break; fi
  sleep 2
done
if [ "$siap" -ne 1 ]; then
  echo "tiruan produksi tidak menjawab" >&2
  MSYS_NO_PATHCONV=1 docker compose -f "$TUMPUKAN" logs --tail 40 api nginx >&2
  exit 1
fi
echo "tiruan produksi menjawab"

zap() {
  MSYS_NO_PATHCONV=1 docker run --rm --network "$JARINGAN" \
    -v "$(jalur "$HASIL"):/zap/wrk:rw" ghcr.io/zaproxy/zaproxy:stable "$@" || true
}

MSYS_NO_PATHCONV=1 docker compose -f "$TUMPUKAN" exec -T api python -c \
  "import json; from backend.main import aplikasi; print(json.dumps(aplikasi.openapi()))" > "$HASIL/openapi.json"

SANDI=$(sed -n 's/^HK_UJI_SANDI=//p' "$SEMENTARA/env")
TOKEN=$(MSYS_NO_PATHCONV=1 docker run --rm --network "$JARINGAN" curlimages/curl:latest -sk \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"kuswantoro.hendro01@gmail.com\",\"sandi\":\"$SANDI\"}" \
  https://www.hendrokuswantoro.com/api/v1/auth/login \
  | python -c "import json,sys; print(json.load(sys.stdin).get('akses',''))")
[ -n "$TOKEN" ] || { echo "masuk ke tiruan produksi gagal" >&2; exit 1; }
PENGGANTI="-config replacer.full_list(0).description=token -config replacer.full_list(0).enabled=true \
-config replacer.full_list(0).matchtype=REQ_HEADER -config replacer.full_list(0).matchstr=Authorization \
-config replacer.full_list(0).regex=false -config replacer.full_list(0).replacement=Bearer\ $TOKEN"

zap zap-baseline.py -t https://www.hendrokuswantoro.com/admin -m 2 -I -J dashboard-pasif.json -r dashboard-pasif.html
zap zap-api-scan.py -t /zap/wrk/openapi.json -f openapi -O https://www.hendrokuswantoro.com \
  -I -J api-aktif.json -r api-aktif.html -z "$PENGGANTI"
if [ "$MODE" = "penuh" ]; then
  zap zap-full-scan.py -t https://www.hendrokuswantoro.com/ -m 3 -I -J situs-aktif.json -r situs-aktif.html
fi

python - "$(jalur "$HASIL")" <<'PY'
import json, pathlib, sys
hasil = pathlib.Path(sys.argv[1])
tingkat = {"0": "Info", "1": "Low", "2": "Medium", "3": "High"}
berat = 0
for berkas in sorted(p for p in hasil.glob("*.json") if p.name != "openapi.json"):
    data = json.loads(berkas.read_text(encoding="utf-8"))
    print(f"== {berkas.stem}")
    temuan = [a for s in data.get("site", []) for a in s.get("alerts", [])]
    for a in sorted(temuan, key=lambda a: -int(a["riskcode"])):
        print(f"  {tingkat[a['riskcode']]:6} {a['alert']} ({a['count']})")
        berat += int(a["riskcode"]) >= 2
    if not temuan:
        print("  tidak ada temuan")
if berat:
    print(f"\n{berat} temuan Medium atau High")
    sys.exit(1)
print("\ntidak ada temuan Medium atau High")
PY
