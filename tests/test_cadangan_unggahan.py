from __future__ import annotations

import base64
import datetime as dt
import os
import random
import subprocess

import pytest

from konftes import AKAR

pytest.importorskip("cryptography")

from backend.db import enkripsi, unggahan_cadangan as uc  # noqa: E402

HARI = dt.date(2026, 9, 29)
FOTO = b"\xff\xd8\xff" + os.urandom(4000)
VIDEO = b"\x00\x00\x00\x18ftypmp42" + os.urandom(9000)


@pytest.fixture
def kunci() -> bytes:
    return base64.b64decode(enkripsi.buat_kunci())


@pytest.fixture
def folder(tmp_path):
    sumber = tmp_path / "unggahan"
    sumber.mkdir()
    (sumber / "9f3c1a7b2d4e5f60-1600x900.jpg").write_bytes(FOTO)
    (sumber / "0a1b2c3d4e5f6071.mp4").write_bytes(VIDEO)
    (sumber / ".0a1b.sebagian").write_bytes(b"setengah")
    return sumber, tmp_path / "cadangan" / "unggahan"


def test_tiap_unggahan_dikunci_dan_bisa_dibuka_lagi(folder, kunci):
    sumber, tujuan = folder
    laporan = uc.salin(sumber, tujuan, kunci, HARI)
    assert sorted(laporan.baru) == ["0a1b2c3d4e5f6071.mp4", "9f3c1a7b2d4e5f60-1600x900.jpg"]
    foto = tujuan / "9f3c1a7b2d4e5f60-1600x900.jpg.enc"
    assert enkripsi.terenkripsi(foto.read_bytes())
    assert FOTO[100:132] not in foto.read_bytes()
    assert uc.isi(foto, kunci) == FOTO
    assert not any(p.name.startswith(".") for p in tujuan.iterdir()), "berkas setengah jadi ikut dicadangkan"


def test_berkas_yang_sudah_dicadangkan_tidak_dikunci_ulang(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    sebelum = (tujuan / "0a1b2c3d4e5f6071.mp4.enc").read_bytes()
    assert uc.salin(sumber, tujuan, kunci, HARI).baru == []
    assert (tujuan / "0a1b2c3d4e5f6071.mp4.enc").read_bytes() == sebelum


def test_unggahan_yang_dihapus_disimpan_tiga_puluh_hari(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    (sumber / "0a1b2c3d4e5f6071.mp4").unlink()

    laporan = uc.salin(sumber, tujuan, kunci, HARI)
    assert laporan.dipindah == ["0a1b2c3d4e5f6071.mp4"]
    gudang = tujuan / uc.TERHAPUS / HARI.isoformat() / "0a1b2c3d4e5f6071.mp4.enc"
    assert gudang.exists()

    uc.salin(sumber, tujuan, kunci, HARI + dt.timedelta(days=uc.SIMPAN_TERHAPUS_HARI))
    assert gudang.exists(), "dibuang sebelum retensinya habis"
    laporan = uc.salin(sumber, tujuan, kunci, HARI + dt.timedelta(days=uc.SIMPAN_TERHAPUS_HARI + 1))
    assert laporan.dibuang == [HARI.isoformat()]
    assert not gudang.exists()


def test_folder_unggahan_yang_kosong_tidak_menyapu_cadangannya(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    for berkas in sumber.iterdir():
        berkas.unlink()
    with pytest.raises(uc.Salah, match="UNGGAHAN_DIR"):
        uc.salin(sumber, tujuan, kunci, HARI)
    assert len(list(tujuan.glob("*.enc"))) == 2


def test_folder_unggahan_yang_tidak_ada_ditolak(tmp_path, kunci):
    with pytest.raises(uc.Salah, match="tidak ada"):
        uc.salin(tmp_path / "salah-ketik", tmp_path / "cadangan", kunci, HARI)


def test_pemulihan_hanya_mengembalikan_yang_hilang(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    (sumber / "0a1b2c3d4e5f6071.mp4").unlink()
    (sumber / "9f3c1a7b2d4e5f60-1600x900.jpg").write_bytes(b"versi yang sekarang")

    assert uc.pulihkan(tujuan, sumber, kunci) == ["0a1b2c3d4e5f6071.mp4"]
    assert (sumber / "0a1b2c3d4e5f6071.mp4").read_bytes() == VIDEO
    assert (sumber / "9f3c1a7b2d4e5f60-1600x900.jpg").read_bytes() == b"versi yang sekarang"


def test_unggahan_yang_terhapus_bisa_dikembalikan_dengan_namanya(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    (sumber / "0a1b2c3d4e5f6071.mp4").unlink()
    uc.salin(sumber, tujuan, kunci, HARI)

    assert uc.pulihkan(tujuan, sumber, kunci) == []
    assert uc.pulihkan(tujuan, sumber, kunci, "0a1b2c3d4e5f6071.mp4") == ["0a1b2c3d4e5f6071.mp4"]
    assert (sumber / "0a1b2c3d4e5f6071.mp4").read_bytes() == VIDEO


@pytest.mark.parametrize("nama", ["../env", "a/b.jpg", "..\\x", ".tersembunyi", ""])
def test_nama_yang_keluar_dari_folder_ditolak(folder, kunci, nama):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    with pytest.raises(uc.Salah):
        uc.pulihkan(tujuan, sumber, kunci, nama)


def test_pemeriksaan_menangkap_yang_hilang_dan_yang_rusak(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    assert uc.periksa(sumber, tujuan, kunci) == []

    (sumber / "baru-belum-dicadangkan.webp").write_bytes(b"RIFF....WEBP")
    rusak = tujuan / "0a1b2c3d4e5f6071.mp4.enc"
    data = bytearray(rusak.read_bytes())
    data[-5] ^= 1
    rusak.write_bytes(bytes(data))

    masalah = uc.periksa(sumber, tujuan, kunci, contoh=10, acak=random.Random(1))
    assert "tanpa cadangan: baru-belum-dicadangkan.webp" in masalah
    assert any("0a1b2c3d4e5f6071.mp4.enc" in m for m in masalah), masalah


def test_kunci_yang_salah_ketahuan_saat_diperiksa(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, kunci, HARI)
    lain = base64.b64decode(enkripsi.buat_kunci())
    masalah = uc.periksa(sumber, tujuan, lain, contoh=10)
    assert len(masalah) == 2 and all("tidak bisa dibuka" in m for m in masalah)


def test_tanpa_kunci_disalin_polos_lalu_dikunci_begitu_kuncinya_ada(folder, kunci):
    sumber, tujuan = folder
    uc.salin(sumber, tujuan, None, HARI)
    assert (tujuan / "0a1b2c3d4e5f6071.mp4").read_bytes() == VIDEO

    laporan = uc.salin(sumber, tujuan, kunci, HARI)
    assert len(laporan.baru) == 2 and laporan.dipindah == []
    assert not (tujuan / "0a1b2c3d4e5f6071.mp4").exists(), "salinan polos tertinggal sesudah dikunci"
    assert uc.isi(tujuan / "0a1b2c3d4e5f6071.mp4.enc", kunci) == VIDEO


def _kirim(folder, *arg):
    return subprocess.run(
        ["sh", str(AKAR / "infrastructure" / "kirim.sh"), "--coba", *arg],
        capture_output=True, text=True,
        env={**os.environ, "CADANGAN_FOLDER": str(folder), "CADANGAN_TUJUAN": "palsu:bucket"},
    )


def test_pengirim_ikut_mengirim_unggahan_yang_terkunci(tmp_path, kunci):
    sumber = tmp_path / "unggahan"
    sumber.mkdir()
    (sumber / "a.jpg").write_bytes(FOTO)
    uc.salin(sumber, tmp_path / "cadangan" / "unggahan", kunci, HARI)
    (tmp_path / "cadangan" / "hk-2026-09-29-0240.sql.gz.enc").write_bytes(b"HKCAD1\n" + b"x" * 64)

    hasil = _kirim(tmp_path / "cadangan")
    assert hasil.returncode == 0, hasil.stderr
    assert "akan dikirim: 1 berkas unggahan" in hasil.stdout


def test_pengirim_menolak_unggahan_yang_tidak_terkunci(tmp_path):
    cadangan = tmp_path / "cadangan"
    (cadangan / "unggahan").mkdir(parents=True)
    (cadangan / "unggahan" / "a.jpg").write_bytes(FOTO)
    (cadangan / "unggahan" / "b.jpg.enc").write_bytes(b"bukan HKCAD1")
    (cadangan / "hk-2026-09-29-0240.sql.gz.enc").write_bytes(b"HKCAD1\n" + b"x" * 64)

    hasil = _kirim(cadangan)
    assert hasil.returncode != 0
    assert "TOLAK unggahan/a.jpg" in hasil.stderr and "TOLAK unggahan/b.jpg.enc" in hasil.stderr


def test_retensi_penyedia_tidak_menyentuh_unggahan():
    isi = (AKAR / "infrastructure" / "kirim.sh").read_text(encoding="utf-8")
    hapus = [b for b in isi.splitlines() if "rclone delete" in b]
    assert hapus and all("--max-depth 1" in b for b in hapus), (
        "retensi 30 hari akan menghapus cadangan unggahan yang masih dipakai"
    )
    assert "rclone sync" not in isi, "sync dari mesin yang kosong menyapu cadangan di penyedia"


def test_cadangan_ditulis_ke_folder_yang_boleh_ditulis_unitnya():
    unit = (AKAR / "infrastructure" / "systemd" / "hk-cadangan.service").read_text(encoding="utf-8")
    pasang = (AKAR / "infrastructure" / "pasang.sh").read_text(encoding="utf-8")
    assert "ReadWritePaths=/srv/hendrokuswantoro/cadangan" in unit
    assert 's|^CADANGAN_FOLDER=.*|CADANGAN_FOLDER=$TUJUAN/cadangan|' in pasang
    assert "CADANGAN_FOLDER=cadangan" in (AKAR / ".env.example").read_text(encoding="utf-8")
    kode = (AKAR / "backend" / "db" / "cadangan.py").read_text(encoding="utf-8")
    assert '_folder("CADANGAN_FOLDER", "cadangan")' in kode


def test_perintah_cadangan_mengurus_unggahan_dari_awal_sampai_pulih(folder, kunci, monkeypatch, capsys):
    import sys

    sys.path.insert(0, str(AKAR))
    from backend.db import cadangan

    sumber, tujuan = folder
    monkeypatch.setattr(cadangan, "UNGGAHAN", sumber)
    monkeypatch.setattr(cadangan, "CADANGAN_UNGGAHAN", tujuan)
    monkeypatch.setenv(enkripsi.NAMA_ENV, base64.b64encode(kunci).decode())

    assert cadangan.cadangkan_unggahan() == 0
    assert cadangan.uji_unggahan() == 0
    (sumber / "0a1b2c3d4e5f6071.mp4").unlink()
    assert cadangan.pulihkan_unggahan(None) == 0
    assert (sumber / "0a1b2c3d4e5f6071.mp4").read_bytes() == VIDEO
    keluar = capsys.readouterr().out
    assert "2 baru dicadangkan" in keluar and "BERHASIL" in keluar and "dikembalikan: 0a1b2c3d4e5f6071.mp4" in keluar
