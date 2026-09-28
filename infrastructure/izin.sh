#!/bin/sh

set -eu

TUJUAN=${TUJUAN:-/srv/hendrokuswantoro}
PENGGUNA=hk
PENGIRIM=deploy
SOKET=hk-soket

if [ "$(id -u)" -ne 0 ]; then
  echo "jalankan sebagai root" >&2
  exit 1
fi

getent group "$SOKET" >/dev/null || groupadd --system "$SOKET"

if ! id "$PENGGUNA" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$TUJUAN" --shell /usr/sbin/nologin "$PENGGUNA"
fi
if ! id "$PENGIRIM" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$PENGIRIM"
fi

usermod -aG "$SOKET" "$PENGGUNA"
usermod -aG "$PENGGUNA,$SOKET" "$PENGIRIM"
if id www-data >/dev/null 2>&1; then
  usermod -aG "$SOKET" www-data
fi

install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0755 "$TUJUAN"
for folder in app situs venv; do
  install -d -o "$PENGIRIM" -g "$PENGGUNA" -m 0755 "$TUJUAN/$folder"
  chown -R "$PENGIRIM:$PENGGUNA" "$TUJUAN/$folder"
done
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0750 "$TUJUAN/unggahan"
install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0700 "$TUJUAN/cadangan"
install -d -o root -g "$PENGGUNA" -m 0750 /etc/hendrokuswantoro
install -d -o root -g root -m 0700 /etc/ssl/hendrokuswantoro

RUMAH=$(getent passwd "$PENGIRIM" | cut -d: -f6)
install -d -o "$PENGIRIM" -g "$PENGIRIM" -m 0700 "$RUMAH/.ssh"
if [ ! -f "$RUMAH/.ssh/authorized_keys" ]; then
  install -o "$PENGIRIM" -g "$PENGIRIM" -m 0600 /dev/null "$RUMAH/.ssh/authorized_keys"
fi

SYSTEMCTL=$(command -v systemctl || echo /usr/bin/systemctl)
ATURAN=/etc/sudoers.d/hk-deploy
printf '%s ALL=(root) NOPASSWD: %s restart hk-api\n' "$PENGIRIM" "$SYSTEMCTL" > "$ATURAN.baru"
chmod 0440 "$ATURAN.baru"
if visudo -cf "$ATURAN.baru" >/dev/null; then
  mv "$ATURAN.baru" "$ATURAN"
else
  rm -f "$ATURAN.baru"
  echo "aturan sudo untuk $PENGIRIM ditolak visudo" >&2
  exit 1
fi
