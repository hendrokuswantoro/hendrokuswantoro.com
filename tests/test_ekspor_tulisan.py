from __future__ import annotations

import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

import bangun_tulisan  # noqa: E402
import unggahan_publik  # noqa: E402
from isi import IsiSalah, SumberBerkas, Teks, Tulisan, tulis_tulisan  # noqa: E402

FOTO = "9f3c1a7b2d4e5f60-1600x900.webp"
VIDEO = "0a1b2c3d4e5f6071.mp4"
ISI_FOTO = b"RIFF\x00\x00\x00\x00WEBPVP8 " + os.urandom(3000)
ISI_VIDEO = b"\x00\x00\x00\x18ftypmp42" + os.urandom(5000)

TULISAN_BARU = {
    "slug": "catatan-lapangan",
    "tanggal": "2026-09-29",
    "judul": {"en": "Field notes", "id": "Catatan lapangan"},
    "tag": {"en": "Field", "id": "Lapangan"},
    "baca": {"en": "2 min read", "id": "2 menit baca"},
    "ringkas": {"en": "What I saw.", "id": "Yang saya lihat."},
    "keterangan": {"en": "Notes from the field.", "id": "Catatan dari lapangan."},
    "lede": {"en": "A short walk.", "id": "Jalan singkat."},
    "isi_en": f"## Street\n\nA paragraph.\n\n![The corner](/unggahan/{FOTO})\n\n!video[The walk](/unggahan/{VIDEO})",
    "isi_id": f"## Jalan\n\nSatu paragraf.\n\n![Sudutnya](/unggahan/{FOTO})\n\n!video[Jalannya](/unggahan/{VIDEO})",
}


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


@pytest.fixture
def api():
    berkas = {FOTO: ISI_FOTO, VIDEO: ISI_VIDEO}
    diminta = []

    class Tangan(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            jalur = self.path.split("?")[0]
            diminta.append(jalur)
            if jalur == "/api/v1/blog":
                badan, jenis = json.dumps({"isi": [{"slug": TULISAN_BARU["slug"]}]}).encode(), "application/json"
            elif jalur == f"/api/v1/blog/{TULISAN_BARU['slug']}":
                badan, jenis = json.dumps(TULISAN_BARU).encode(), "application/json"
            elif jalur.startswith("/unggahan/") and jalur[10:] in berkas:
                badan, jenis = berkas[jalur[10:]], "application/octet-stream"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", jenis)
            self.send_header("Content-Length", str(len(badan)))
            self.end_headers()
            self.wfile.write(badan)

        def log_message(self, *a):
            pass

    srv = _Server(("127.0.0.1", 0), Tangan)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}", diminta
    finally:
        srv.shutdown()


@pytest.fixture
def situs(tmp_path, monkeypatch):
    for nama in ("index.html", "sitemap.xml"):
        shutil.copy(AKAR / nama, tmp_path / nama)
    shutil.copytree(AKAR / "blog", tmp_path / "blog")
    shutil.copytree(AKAR / "content" / "blog", tmp_path / "content" / "blog")
    monkeypatch.setattr(bangun_tulisan, "AKAR", tmp_path)
    monkeypatch.setattr(bangun_tulisan, "ISI", tmp_path / "content")
    return tmp_path


def _jalankan(monkeypatch, *arg) -> int:
    monkeypatch.setattr(sys, "argv", ["bangun_tulisan.py", *arg])
    try:
        return bangun_tulisan.main()
    except SystemExit as keluar:
        return keluar.code if isinstance(keluar.code, int) else 1


def test_tulisan_yang_ada_ditulis_ulang_persis_sama():
    for t in SumberBerkas(AKAR / "content").tulisan():
        asli = (AKAR / "content" / "blog" / f"{t.slug}.md").read_bytes().decode("utf-8")
        assert tulis_tulisan(t) == asli, f"{t.slug}.md berubah saat ditulis ulang"


def test_nilai_dengan_baris_baru_ditolak():
    t = SumberBerkas(AKAR / "content").tulisan()[0]
    rusak = Tulisan(**{**t.__dict__, "judul": Teks(en="Satu\nDua", id="Satu")})
    with pytest.raises(IsiSalah, match="baris baru"):
        tulis_tulisan(rusak)


def test_tulisan_dari_dashboard_terbit_lewat_berkas_bersama_fotonya(api, situs, monkeypatch, capsys):
    pangkal, diminta = api
    assert _jalankan(monkeypatch, "--sumber", "api", "--api", pangkal) == 0

    md = situs / "content" / "blog" / "catatan-lapangan.md"
    assert md.exists(), "tulisan dashboard tidak jadi berkas di content/blog"
    assert (situs / "content" / "unggahan" / FOTO).read_bytes() == ISI_FOTO
    assert (situs / "content" / "unggahan" / VIDEO).read_bytes() == ISI_VIDEO

    halaman = (situs / "blog" / "catatan-lapangan.html").read_text(encoding="utf-8")
    assert f'src="/unggahan/{FOTO}"' in halaman and f'src="/unggahan/{VIDEO}"' in halaman
    assert "catatan-lapangan" in (situs / "blog" / "index.html").read_text(encoding="utf-8")

    for lama in ("kapan-peta-diam", "sumber-di-pojok-peta", "titik-panas-bukan-kebakaran"):
        assert (situs / "content" / "blog" / f"{lama}.md").exists(), "tulisan lama ikut hilang"
    assert "tidak disentuh" in capsys.readouterr().out

    assert _jalankan(monkeypatch, "--periksa") == 0, "CI akan menolak hasil ekspor"

    jumlah = len(diminta)
    assert _jalankan(monkeypatch, "--sumber", "api", "--api", pangkal) == 0
    assert not [j for j in diminta[jumlah:] if j.startswith("/unggahan/")], "foto diunduh ulang"


def test_foto_yang_hilang_atau_yatim_ketahuan(api, situs, monkeypatch, capsys):
    pangkal, _ = api
    assert _jalankan(monkeypatch, "--sumber", "api", "--api", pangkal) == 0
    folder = situs / "content" / "unggahan"

    (folder / VIDEO).unlink()
    assert _jalankan(monkeypatch, "--periksa") == 1
    assert f"HILANG content/unggahan/{VIDEO}" in capsys.readouterr().out
    assert _jalankan(monkeypatch) == 1, "bangun dari berkas meloloskan tulisan yang videonya hilang"

    (folder / VIDEO).write_bytes(ISI_VIDEO)
    (folder / "sisa-lama.webp").write_bytes(b"x")
    assert _jalankan(monkeypatch, "--periksa") == 1
    assert "YATIM content/unggahan/sisa-lama.webp" in capsys.readouterr().out
    assert _jalankan(monkeypatch) == 0
    assert not (folder / "sisa-lama.webp").exists(), "foto yang tidak lagi dipakai tidak dibuang"
    assert (folder / FOTO).exists() and (folder / VIDEO).exists()


def test_berkas_di_atas_batas_cloudflare_ditolak(api, tmp_path):
    pangkal, _ = api
    dipakai = {VIDEO: ["catatan-lapangan"]}
    with pytest.raises(IsiSalah, match="lebih dari"):
        unggahan_publik.salin(dipakai, tmp_path, pangkal, batas=1024)
    assert not list(tmp_path.iterdir()), "berkas setengah jadi tertinggal"
    assert unggahan_publik.BATAS_BITA == 25 * 1024 * 1024


@pytest.mark.parametrize("alamat", ["/unggahan/../env.webp", "/unggahan/a/b.webp", "/unggahan/.x.webp"])
def test_nama_unggahan_yang_keluar_folder_ditolak(alamat):
    t = SumberBerkas(AKAR / "content").tulisan()[0]
    isi = f"![x]({alamat})"
    rusak = Tulisan(**{**t.__dict__, "isi_en": isi, "isi_id": isi})
    with pytest.raises(IsiSalah, match=t.slug):
        unggahan_publik.rujukan([rusak])


def test_foto_terbit_ikut_git_dan_ikut_situs():
    hasil = subprocess.run(
        ["git", "check-ignore", "-q", "content/unggahan/contoh.webp"], cwd=AKAR, capture_output=True
    )
    assert hasil.returncode == 1, "content/unggahan diabaikan git, jadi fotonya tidak pernah sampai ke Cloudflare"
    bangun = (AKAR / "tools" / "bangun_situs.sh").read_text(encoding="utf-8")
    assert "content/unggahan" in bangun and "dist/unggahan" in bangun
    kepala = (AKAR / "_headers").read_text(encoding="utf-8")
    assert "/unggahan/*\n  Cache-Control: public, max-age=31536000, immutable" in kepala
    assert "content" in (AKAR / "tools" / "build_dist.py").read_text(encoding="utf-8")
