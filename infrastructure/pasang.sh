#!/bin/sh
# Menyiapkan VPS Ubuntu 24.04 yang masih kosong. Bab 14.
#
# Dijalankan sekali, sebagai root, di VPS-nya:
#
#     git clone https://github.com/hendrokuswantoro/personal-web /tmp/hk
#     sh /tmp/hk/infrastructure/pasang.sh
#
# Idempoten dengan sengaja: menjalankannya dua kali tidak merusak apa apa dan
# tidak menggandakan apa pun. Skrip pemasangan yang hanya aman sekali adalah
# skrip yang tidak berani dijalankan lagi, dan itu artinya perbaikan kecil
# apa pun dikerjakan dengan tangan lalu tidak pernah tercatat di mana mana.
#
# Yang TIDAK dikerjakan skrip ini, dengan sengaja:
#
#   - tidak meminta sertifikat TLS. certbot butuh DNS sudah mengarah ke mesin
#     ini, dan itu bukan sesuatu yang bisa dipastikan skrip. Perintahnya
#     dicetak di akhir.
#   - tidak mengisi /etc/hendrokuswantoro/env. Rahasia diketik manusia, tidak
#     dibangkitkan skrip yang keluarannya masuk log.
#   - tidak membuka porta selain 22, 80, 443.
#   - tidak menjalankan `docker compose up`. Basis data dinyalakan sesudah
#     env-nya diisi.
#
# Baca docs/vps.md sebelum menjalankan ini.

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
TUJUAN=/srv/hendrokuswantoro
PENGGUNA=hk

if [ "$(id -u)" -ne 0 ]; then
  echo "jalankan sebagai root" >&2
  exit 1
fi

langkah() { printf '\n== %s\n' "$1"; }

# --- paket -------------------------------------------------------------------
langkah "paket"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  nginx python3 python3-venv python3-pip git curl ca-certificates \
  ufw fail2ban unattended-upgrades postgresql-client rsync

# Docker, untuk PostGIS dan Redis. Repositori resminya, bukan yang di apt
# Ubuntu, sebab yang di Ubuntu tertinggal beberapa versi.
if ! command -v docker >/dev/null 2>&1; then
  langkah "docker"
  curl -fsSL https://get.docker.com | sh
fi

if ! command -v rclone >/dev/null 2>&1; then
  langkah "rclone"
  curl -fsSL https://rclone.org/install.sh | bash
fi

# --- pengguna ----------------------------------------------------------------
# Aplikasi tidak pernah berjalan sebagai root. Akun ini tidak punya shell
# masuk dan tidak punya sandi: ia hanya ada untuk menjalankan satu layanan.
langkah "pengguna $PENGGUNA"
if ! id "$PENGGUNA" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$TUJUAN" --shell /usr/sbin/nologin "$PENGGUNA"
fi
usermod -aG docker "$PENGGUNA"

install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN/app"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN/situs"
# 0700: cadangan berisi salinan lengkap basis data.
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0700 "$TUJUAN/cadangan"
install -d -o root -g "$PENGGUNA" -m 0750 /etc/hendrokuswantoro
install -d -o root -g root -m 0755 /var/www/certbot

# --- kode --------------------------------------------------------------------
langkah "kode"
rsync -a --delete \
  --exclude '.git' --exclude 'node_modules' --exclude '__pycache__' \
  --exclude 'cadangan' --exclude '.env' \
  "$AKAR/" "$TUJUAN/app/"
chown -R "$PENGGUNA:$PENGGUNA" "$TUJUAN/app"
chmod +x "$TUJUAN/app/infrastructure/"*.sh

langkah "venv"
if [ ! -x "$TUJUAN/venv/bin/python" ]; then
  python3 -m venv "$TUJUAN/venv"
fi
"$TUJUAN/venv/bin/pip" install -q --upgrade pip
"$TUJUAN/venv/bin/pip" install -q -r "$TUJUAN/app/backend/requirements.txt"
chown -R "$PENGGUNA:$PENGGUNA" "$TUJUAN/venv"

# --- berkas rahasia ----------------------------------------------------------
# Dibuat kosong kalau belum ada, TIDAK PERNAH ditimpa kalau sudah ada.
langkah "env"
if [ ! -f /etc/hendrokuswantoro/env ]; then
  cp "$TUJUAN/app/.env.example" /etc/hendrokuswantoro/env
  echo "  /etc/hendrokuswantoro/env dibuat dari contoh. ISI DULU sebelum menyalakan."
else
  echo "  /etc/hendrokuswantoro/env sudah ada, tidak disentuh."
fi
chown root:"$PENGGUNA" /etc/hendrokuswantoro/env
chmod 0640 /etc/hendrokuswantoro/env

# --- systemd -----------------------------------------------------------------
langkah "systemd"
for unit in hk-api.service hk-cadangan.service hk-cadangan.timer hk-cadangan-gagal@.service; do
  install -m 0644 "$TUJUAN/app/infrastructure/systemd/$unit" "/etc/systemd/system/$unit"
  echo "  $unit"
done
systemctl daemon-reload
systemctl enable hk-api.service hk-cadangan.timer

# --- nginx -------------------------------------------------------------------
langkah "nginx"
install -m 0644 "$TUJUAN/app/infrastructure/nginx/hendrokuswantoro.conf" \
  /etc/nginx/sites-available/hendrokuswantoro.conf
ln -sf /etc/nginx/sites-available/hendrokuswantoro.conf \
  /etc/nginx/sites-enabled/hendrokuswantoro.conf
rm -f /etc/nginx/sites-enabled/default

# nginx menolak menyala tanpa sertifikat, dan sertifikatnya belum ada pada
# pemasangan pertama. Jadi konfigurasinya hanya diuji kalau sudah ada.
if [ -f /etc/letsencrypt/live/hendrokuswantoro.com/fullchain.pem ]; then
  nginx -t && systemctl reload nginx
else
  echo "  sertifikat belum ada, nginx belum dinyalakan ulang"
fi

# --- firewall ----------------------------------------------------------------
langkah "firewall"
ufw allow 22/tcp   >/dev/null
ufw allow 80/tcp   >/dev/null
ufw allow 443/tcp  >/dev/null
ufw --force enable >/dev/null
ufw status numbered | sed 's/^/  /'

# --- pembaruan keamanan otomatis ---------------------------------------------
langkah "pembaruan keamanan"
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true
systemctl enable --now fail2ban >/dev/null 2>&1 || true

# --- sisanya, yang harus dikerjakan manusia ----------------------------------
cat <<'SELESAI'

== Selesai sampai di sini. Sisanya menuntut keputusan, bukan skrip.

1. Isi rahasianya:
     sudo nano /etc/hendrokuswantoro/env
   Yang wajib: POSTGRES_PASSWORD, DSN, JWT_SECRET, CADANGAN_KUNCI,
   WEBAUTHN_RP_ID=hendrokuswantoro.com,
   WEBAUTHN_ASAL=["https://www.hendrokuswantoro.com"]

2. Nyalakan basis data dan cache:
     cd /srv/hendrokuswantoro/app/infrastructure
     sudo -u hk docker compose --env-file /etc/hendrokuswantoro/env up -d

3. Terapkan migrasi dan isi data awal:
     cd /srv/hendrokuswantoro/app
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/migrasi.py
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/muat_awal.py
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/buat_admin.py

4. Arahkan DNS A dan AAAA ke mesin ini, TUNGGU sampai menyebar, baru:
     sudo certbot --nginx -d hendrokuswantoro.com -d www.hendrokuswantoro.com

5. Nyalakan:
     sudo systemctl start hk-api
     sudo systemctl start hk-cadangan.timer
     sudo nginx -t && sudo systemctl reload nginx

6. Buktikan cadangannya benar benar bisa dipulihkan, sekarang, bukan nanti:
     sudo systemctl start hk-cadangan.service
     sudo journalctl -u hk-cadangan -n 40 --no-pager

SELESAI
