#!/bin/sh

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
TUJUAN=/srv/hendrokuswantoro
PENGGUNA=hk

if [ "$(id -u)" -ne 0 ]; then
  echo "jalankan sebagai root" >&2
  exit 1
fi

langkah() { printf '\n== %s\n' "$1"; }

langkah "paket"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  nginx python3 python3-venv python3-pip git curl ca-certificates \
  ufw fail2ban unattended-upgrades postgresql-client rsync

if ! command -v docker >/dev/null 2>&1; then
  langkah "docker"
  curl -fsSL https://get.docker.com | sh
fi

if ! command -v rclone >/dev/null 2>&1; then
  langkah "rclone"
  curl -fsSL https://rclone.org/install.sh | bash
fi

langkah "pengguna $PENGGUNA"
if ! id "$PENGGUNA" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$TUJUAN" --shell /usr/sbin/nologin "$PENGGUNA"
fi
usermod -aG docker "$PENGGUNA"

install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN/app"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN/situs"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0700 "$TUJUAN/cadangan"
install -d -o root -g "$PENGGUNA" -m 0750 /etc/hendrokuswantoro
install -d -o root -g root -m 0700 /etc/ssl/hendrokuswantoro

langkah "kode"
rsync -a --delete \
  --exclude '.git' --exclude 'node_modules' --exclude '__pycache__' \
  --exclude 'cadangan' --exclude '.env' --exclude 'next/out' --exclude 'next/.next' \
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

langkah "env"
if [ ! -f /etc/hendrokuswantoro/env ]; then
  cp "$TUJUAN/app/.env.example" /etc/hendrokuswantoro/env
  echo "  /etc/hendrokuswantoro/env dibuat dari contoh. ISI DULU sebelum menyalakan."
else
  echo "  /etc/hendrokuswantoro/env sudah ada, tidak disentuh."
fi
chown root:"$PENGGUNA" /etc/hendrokuswantoro/env
chmod 0640 /etc/hendrokuswantoro/env

langkah "systemd"
for unit in hk-api.service hk-cadangan.service hk-cadangan.timer hk-cadangan-gagal@.service; do
  install -m 0644 "$TUJUAN/app/infrastructure/systemd/$unit" "/etc/systemd/system/$unit"
  echo "  $unit"
done
systemctl daemon-reload
systemctl enable hk-api.service hk-cadangan.timer

langkah "nginx"
install -m 0644 "$TUJUAN/app/infrastructure/nginx/hendrokuswantoro.conf" \
  /etc/nginx/sites-available/hendrokuswantoro.conf
ln -sf /etc/nginx/sites-available/hendrokuswantoro.conf \
  /etc/nginx/sites-enabled/hendrokuswantoro.conf
rm -f /etc/nginx/sites-enabled/default

if [ -f /etc/ssl/hendrokuswantoro/origin.pem ]; then
  nginx -t && systemctl reload nginx
else
  echo "  sertifikat origin belum ada, nginx belum dinyalakan ulang"
fi

langkah "firewall"
ufw default deny incoming  >/dev/null
ufw default allow outgoing >/dev/null
ufw allow 22/tcp >/dev/null
ufw delete allow 80/tcp  >/dev/null 2>&1 || true
ufw delete allow 443/tcp >/dev/null 2>&1 || true
while IFS= read -r jaringan; do
  [ -n "$jaringan" ] || continue
  ufw allow proto tcp from "$jaringan" to any port 443 >/dev/null
done < "$TUJUAN/app/infrastructure/cloudflare-ip.txt"
ufw --force enable >/dev/null
ufw status numbered | sed 's/^/  /'

langkah "pembaruan keamanan"
dpkg-reconfigure -f noninteractive unattended-upgrades >/dev/null 2>&1 || true
systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true
systemctl enable --now fail2ban >/dev/null 2>&1 || true

cat <<'SELESAI'

== Selesai sampai di sini. Sisanya menuntut keputusan, bukan skrip.

1. Isi rahasianya:
     sudo nano /etc/hendrokuswantoro/env
   Yang wajib: POSTGRES_PASSWORD, DSN, JWT_SECRET, CADANGAN_KUNCI,
   WEBAUTHN_RP_ID=admin.hendrokuswantoro.com,
   WEBAUTHN_ASAL=["https://admin.hendrokuswantoro.com"],
   KUNCI_KOLOM (salinan dari laptop kalau basis datanya dipindah),
   SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, SURAT_DARI, SURAT_WAJIB=1

2. Nyalakan basis data dan cache:
     cd /srv/hendrokuswantoro/app/infrastructure
     sudo -u hk docker compose --env-file /etc/hendrokuswantoro/env up -d

3. Terapkan migrasi dan isi data awal:
     cd /srv/hendrokuswantoro/app
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/migrasi.py
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/muat_awal.py
     sudo -u hk /srv/hendrokuswantoro/venv/bin/python backend/db/buat_admin.py

4. Di dasbor Cloudflare, bukan di mesin ini:
   a. DNS: record A (dan AAAA) bernama admin ke alamat mesin ini, Proxied
      (awan oranye). Tanpa awan oranye firewall di atas menolak semuanya.
   b. SSL/TLS, Overview: Full (strict).
   c. SSL/TLS, Origin Server, Create Certificate untuk
      hendrokuswantoro.com dan *.hendrokuswantoro.com. Tempel hasilnya ke:
        sudo nano /etc/ssl/hendrokuswantoro/origin.pem
        sudo nano /etc/ssl/hendrokuswantoro/origin.key
        sudo chmod 0600 /etc/ssl/hendrokuswantoro/origin.key
   Kuncinya hanya ditampilkan sekali. Kalau hilang, buat sertifikat baru.

5. Dashboard admin yang terbit adalah versi Next (ADMIN_NEXT=1 di env).
   Berkasnya, next/out, dibangun GitHub Actions dan dikirim oleh alur Deploy VPS,
   bukan dibangun di mesin ini. Selama next/out belum pernah terkirim, /admin
   menyajikan dashboard HTML dengan sendirinya.

6. Nyalakan:
     sudo systemctl start hk-api
     sudo systemctl start hk-cadangan.timer
     sudo nginx -t && sudo systemctl reload nginx

7. SEGERA buka https://admin.hendrokuswantoro.com/admin, masuk, lalu pasang
   authenticator dan passkey di menu Keamanan. Sampai itu selesai, siapa pun
   yang tahu sandinya bisa memasang faktor pertamanya sendiri.

8. Buktikan cadangannya benar benar bisa dipulihkan, sekarang, bukan nanti:
     sudo systemctl start hk-cadangan.service
     sudo journalctl -u hk-cadangan -n 40 --no-pager

SELESAI
