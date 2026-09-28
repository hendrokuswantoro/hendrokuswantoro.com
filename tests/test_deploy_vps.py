from __future__ import annotations

import configparser
import re

from konftes import AKAR

INFRA = AKAR / "infrastructure"
IZIN = (INFRA / "izin.sh").read_text(encoding="utf-8")
PASANG = (INFRA / "pasang.sh").read_text(encoding="utf-8")
VPS = (AKAR / ".github" / "workflows" / "vps.yml").read_text(encoding="utf-8")
CI = (AKAR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def _unit() -> configparser.SectionProxy:
    p = configparser.ConfigParser(strict=False, allow_no_value=True, interpolation=None)
    p.optionxform = str
    p.read_string((INFRA / "systemd" / "hk-api.service").read_text(encoding="utf-8"))
    return p["Service"]


def test_sudo_deploy_hanya_menyalakan_ulang_api():
    aturan = re.findall(r"printf '([^']*)'", IZIN)
    assert aturan == ["%s ALL=(root) NOPASSWD: %s restart hk-api\\n"], aturan
    assert "visudo -cf" in IZIN, "aturan sudo dipasang tanpa diperiksa visudo"
    assert "NOPASSWD: ALL" not in IZIN + PASANG


def test_kode_milik_deploy_dan_hanya_terbaca_oleh_api():
    assert 'install -d -o "$PENGIRIM" -g "$PENGGUNA" -m 0755 "$TUJUAN/$folder"' in IZIN
    assert "for folder in app situs venv; do" in IZIN
    assert 'usermod -aG "$PENGGUNA,$SOKET" "$PENGIRIM"' in IZIN
    for jalur in ("app", "venv"):
        assert f'chown -R "$PENGIRIM:$PENGGUNA" "$TUJUAN/{jalur}"' in PASANG, jalur
    assert 'chown -R "$PENGGUNA:$PENGGUNA"' not in PASANG, "folder yang dikirim deploy kembali jadi milik hk"


def test_unggahan_di_luar_folder_yang_dihapus_deploy():
    assert 'install -d -o "$PENGGUNA" -g "$PENGGUNA" -m 0750 "$TUJUAN/unggahan"' in IZIN
    assert _unit()["ReadWritePaths"] == "/srv/hendrokuswantoro/unggahan"
    assert 's|^UNGGAHAN_DIR=.*|UNGGAHAN_DIR=$TUJUAN/unggahan|' in PASANG
    for teks, nama in ((PASANG, "pasang.sh"), (VPS, "vps.yml")):
        assert "--exclude '/unggahan'" in teks, f"rsync --delete di {nama} bisa menghapus unggahan"


def test_soket_api_terbuka_untuk_nginx_bukan_untuk_semua_orang():
    unit = _unit()
    assert unit["SupplementaryGroups"] == "hk-soket"
    assert unit["RuntimeDirectoryMode"] == "0751"
    assert "chgrp hk-soket /run/hk-api/api.sock; chmod 660 /run/hk-api/api.sock" in unit["ExecStartPost"]
    assert 'usermod -aG "$SOKET" www-data' in IZIN
    assert 'usermod -aG "$PENGGUNA" www-data' not in IZIN and "-aG hk www-data" not in IZIN, (
        "www-data di grup hk ikut bisa membaca /etc/hendrokuswantoro/env"
    )


def test_izin_diuji_sungguhan_di_ci():
    assert "sh infrastructure/periksa_izin.sh" in CI
    assert 'sh "$AKAR/infrastructure/izin.sh"' in PASANG


def test_situs_untuk_vps_dibangun_dengan_token_peta():
    langkah = VPS[VPS.index("- name: Build the static site"):VPS.index("sh tools/bangun_situs.sh")]
    assert "MAPBOX_TOKEN: ${{ secrets.MAPBOX_TOKEN }}" in langkah, (
        "tanpa token, situs di VPS memuat peta OpenFreeMap tanpa nama jalan dan tanpa gedung"
    )
    assert 'test -n "$MAPBOX_TOKEN"' in langkah
