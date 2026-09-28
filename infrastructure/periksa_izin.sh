#!/bin/sh

set -eu

AKAR=$(cd "$(dirname "$0")/.." && pwd)
CITRA=ubuntu:24.04

if command -v cygpath >/dev/null 2>&1; then
  AKAR=$(cygpath -m "$AKAR")
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker tidak ada, pemeriksaan dilewati" >&2
  exit 0
fi

echo "memeriksa izin VPS dengan $CITRA"

docker run --rm -i -v "$AKAR:/repo:ro" "$CITRA" sh -s <<'DALAM'
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null
apt-get install -y -qq sudo rsync python3 >/dev/null

printf '#!/bin/sh\necho "systemctl $*"\n' > /usr/bin/systemctl
chmod +x /usr/bin/systemctl

T=/srv/hendrokuswantoro
UNIT=/repo/infrastructure/systemd/hk-api.service

gagal() { echo "GAGAL: $1" >&2; exit 1; }
bisa() { d=$1; shift; "$@" >/dev/null 2>&1 || gagal "$d"; echo "ok   $d"; }
tidak() { d=$1; shift; if "$@" >/dev/null 2>&1; then gagal "BISA: $d"; fi; echo "ok   ditolak: $d"; }
sebagai() { u=$1; shift; runuser -u "$u" -- "$@"; }

sh /repo/infrastructure/izin.sh
sh /repo/infrastructure/izin.sh
echo "ok   izin.sh aman dijalankan dua kali"

printf 'DSN=rahasia\n' > /etc/hendrokuswantoro/env
chown root:hk /etc/hendrokuswantoro/env
chmod 0640 /etc/hendrokuswantoro/env

mkdir -p /tmp/kode/backend /tmp/situs
echo satu > /tmp/kode/backend/a.py
echo halaman > /tmp/situs/index.html
rsync -a /tmp/kode/ "$T/app/"
chown -R deploy:hk "$T/app"
echo gambar | sebagai hk tee "$T/unggahan/foto.webp" >/dev/null

echo dua > /tmp/kode/backend/a.py
echo baru > /tmp/kode/backend/b.py
bisa "deploy mengirim kode dengan rsync --delete" sebagai deploy rsync -a --delete --exclude /unggahan /tmp/kode/ "$T/app/"
grep -q dua "$T/app/backend/a.py" || gagal "isi kode tidak berganti"
bisa "deploy mengirim situs" sebagai deploy rsync -a --delete /tmp/situs/ "$T/situs/"
bisa "deploy memasang paket ke venv" sebagai deploy mkdir -p "$T/venv/lib/paket"
bisa "deploy membaca env untuk migrasi" sebagai deploy cat /etc/hendrokuswantoro/env
test -f "$T/unggahan/foto.webp" || gagal "unggahan hilang sesudah deploy"
echo "ok   unggahan selamat sesudah deploy"

tidak "deploy membuka folder cadangan" sebagai deploy ls "$T/cadangan"
tidak "hk mengubah kode yang ia jalankan" sebagai hk touch "$T/app/backend/c.py"
bisa "hk membaca kode" sebagai hk cat "$T/app/backend/a.py"
bisa "hk menulis unggahan" sebagai hk touch "$T/unggahan/video.mp4"
tidak "www-data membaca env" sebagai www-data cat /etc/hendrokuswantoro/env
bisa "www-data membaca situs" sebagai www-data cat "$T/situs/index.html"

MODE=$(sed -n 's/^RuntimeDirectoryMode=//p' "$UNIT")
install -d -o hk -g hk -m "$MODE" /run/hk-api
sebagai hk python3 -c '
import os, socket
s = socket.socket(socket.AF_UNIX)
s.bind("/run/hk-api/api.sock")
s.listen(8)
if os.fork():
    os._exit(0)
while True:
    c, _ = s.accept()
    c.sendall(b"ok")
    c.close()
'
PASCA=$(sed -n "s/^ExecStartPost=\/bin\/sh -c '\(.*\)'$/\1/p" "$UNIT")
test -n "$PASCA" || gagal "ExecStartPost tidak terbaca dari unit"
bisa "ExecStartPost jalan sebagai hk" sebagai hk sh -c "$PASCA"

SAMBUNG='import socket; s = socket.socket(socket.AF_UNIX); s.connect("/run/hk-api/api.sock"); assert s.recv(2) == b"ok"'
bisa "nginx (www-data) menyambung ke API" sebagai www-data python3 -c "$SAMBUNG"
bisa "deploy memeriksa API sesudah restart" sebagai deploy python3 -c "$SAMBUNG"
tidak "pengguna lain menyambung ke API" sebagai nobody python3 -c "$SAMBUNG"

bisa "deploy boleh menyalakan ulang hk-api" sebagai deploy sudo -n systemctl restart hk-api
tidak "deploy menghentikan hk-api" sebagai deploy sudo -n systemctl stop hk-api
tidak "deploy menjalankan shell sebagai root" sebagai deploy sudo -n /bin/sh -c id
tidak "deploy menyalakan ulang layanan lain" sebagai deploy sudo -n systemctl restart ssh

echo "izin VPS lolos"
DALAM
