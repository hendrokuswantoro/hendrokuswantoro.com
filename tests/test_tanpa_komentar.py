from __future__ import annotations

import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR / "tools"))

import cari_komentar  # noqa: E402


def _cetak(hasil) -> str:
    return "\n".join(
        f"{p.relative_to(AKAR).as_posix()}:{n}: {t}" for p, isi in sorted(hasil.items()) for n, t in isi
    )


def test_kode_sumber_tidak_berkomentar_python_css_html_dan_konfigurasi():
    hasil = cari_komentar.semua(dengan_skrip=False)
    assert not hasil, "komentar dilarang sejak 26 September 2026:\n" + _cetak(hasil)


def test_javascript_dan_typescript_tidak_berkomentar():
    if not cari_komentar.ts_ada():
        pytest.skip("next/node_modules belum terpasang; CI memeriksanya di job Type Check")
    hasil = {p: t for p, t in cari_komentar.semua().items() if p.suffix in (".js", ".mjs", ".cjs", ".ts", ".tsx")}
    assert not hasil, "komentar dilarang sejak 26 September 2026:\n" + _cetak(hasil)


def test_pemindai_menangkap_komentar_tetapi_tidak_regex_atau_alamat(tmp_path, monkeypatch):
    if not cari_komentar.ts_ada():
        pytest.skip("next/node_modules belum terpasang")
    contoh = tmp_path / "contoh.ts"
    contoh.write_text(
        'const r = /\\//g;\nconst u = `https://${"x"}`;\nconst a = 1; // sungguhan\n/* blok */\n',
        encoding="utf-8",
    )
    hasil = cari_komentar.skrip([contoh])[contoh]
    assert [n for n, _ in hasil] == [3, 4], hasil


def test_berkas_konfigurasi_ikut_diperiksa(tmp_path):
    for nama in (".gitignore", ".gitattributes", "_headers", "_redirects", "Dockerfile", "requirements.txt",
                 "requirements-dev.txt", "pasang.ps1"):
        p = tmp_path / nama
        assert cari_komentar._cocok(p, (".ps1",), cari_komentar.NAMA_PAGAR + ("requirements",)), nama
        p.write_text("# alasan\nisi\n", encoding="utf-8")
        assert cari_komentar.pagar(p) == [(1, "# alasan")], nama
    assert not cari_komentar._cocok(tmp_path / ".env.example", (".ps1",), cari_komentar.NAMA_PAGAR + ("requirements",))

    batch = tmp_path / "nyala.cmd"
    batch.write_bytes(b"@echo off\r\nREM alasan\r\n:: alasan\r\necho ok\r\n")
    assert [n for n, _ in cari_komentar.batch(batch)] == [2, 3]
