from __future__ import annotations

import sys

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from conftest import masuk_admin, tab_dengan_otentikator  # noqa: E402

def png_kecil(lebar: int, tinggi: int, warna: tuple[int, int, int]) -> bytes:
    import struct
    import zlib

    baris = b"".join(b"\x00" + bytes(warna) * lebar for _ in range(tinggi))

    def kotak(nama: bytes, isi: bytes) -> bytes:
        return (struct.pack(">I", len(isi)) + nama + isi
                + struct.pack(">I", zlib.crc32(nama + isi) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + kotak(b"IHDR", struct.pack(">IIBBBBB", lebar, tinggi, 8, 2, 0, 0, 0))
            + kotak(b"IDAT", zlib.compress(baris))
            + kotak(b"IEND", b""))


PANEL = ("layar-ringkasan", "layar-perangkat", "layar-jejak")
UBIN = ("ubin-terbit", "ubin-draf", "ubin-passkey", "ubin-sesi")


def test_dashboard_hidup_dan_jujur(server_admin, peramban):
    konteks, tab = tab_dengan_otentikator(peramban)
    try:
        tab.goto(f"{server_admin}/admin", wait_until="domcontentloaded")
        tab.wait_for_selector("#tombol-masuk")
        for panel in PANEL:
            assert tab.is_hidden(f"#{panel}"), (
                f"{panel} terlihat sebelum masuk, padahal isinya keterangan tentang akun"
            )

        masuk_admin(tab, server_admin)

        tab.wait_for_function(
            "() => document.getElementById('ubin-terbit').textContent !== '?'",
            timeout=25000,
        )

        for panel in PANEL:
            assert tab.is_visible(f"#{panel}"), f"{panel} tidak muncul sesudah masuk"

        for ubin in UBIN:
            isi = tab.inner_text(f"#{ubin}").strip()
            assert isi.isdigit(), f"{ubin} berisi {isi!r}, bukan angka"

        assert tab.locator("#daftar-sesi tr").count() >= 1
        assert tab.locator("#daftar-sesi .ini-perangkat").count() == 1, (
            "daftar perangkat tanpa penanda 'yang mana saya' tidak bisa dipakai "
            "memutuskan apa pun"
        )

        baris = tab.locator("#daftar-jejak tr")
        assert baris.count() >= 1, "jejak kosong, padahal baru saja ada yang masuk"
        nama_mentah = tab.evaluate(
            "() => Array.from(document.querySelectorAll('#daftar-jejak tr td:nth-child(2)'))"
            "  .map(t => t.textContent).filter(t => t.includes('_'))"
        )
        assert not nama_mentah, f"nama peristiwa tampil mentah: {nama_mentah[:3]}"

        sebelum = tab.inner_text("#waktu-segar")
        assert sebelum.startswith("diperbarui"), f"waktu segar tidak tertulis: {sebelum!r}"
        tab.wait_for_timeout(1100)
        tab.click("#tombol-segarkan")
        tab.wait_for_function(
            "(lama) => document.getElementById('waktu-segar').textContent !== lama",
            arg=sebelum, timeout=25000,
        )

        assert "document.hidden" in tab.evaluate("() => mulaiSegarBerkala.toString()"), (
            "penyegaran berkala tidak memeriksa keadaan tab, jadi tab yang "
            "ditinggalkan terbuka akan terus mengetuk server"
        )

        tab.click("#tombol-baru")
        tab.wait_for_selector("#isi_en")

        tab.click("#isi_en")
        tab.fill("#isi_en", "satu")
        tab.click('.bilah button[data-baris^="- "]')
        assert tab.input_value("#isi_en") == "- satu", tab.input_value("#isi_en")

        tab.click('.bilah button[data-baris^="- "]')
        assert tab.input_value("#isi_en") == "satu"

        tab.evaluate("() => { const k = document.getElementById('isi_en');"
                     " k.focus(); k.setSelectionRange(0, 4); }")
        tab.click('.bilah button[data-sisip^="**"]')
        assert tab.input_value("#isi_en") == "**satu**"

        tab.fill("#isi_en", "A paragraph.")
        tab.fill("#isi_id", "Satu paragraf.")
        tab.click("#buka-berkas")
        tab.set_input_files("#berkas-masuk", files=[{
            "name": "uji-dasbor.png",
            "mimeType": "image/png",
            "buffer": png_kecil(240, 135, (58, 92, 140)),
        }])
        try:
            tab.wait_for_selector("#petak-berkas button.sisip", timeout=25000)
        except Exception as galat:  # pragma: no cover
            raise AssertionError(
                "unggahan tidak muncul di pustaka. Kabar di layar: "
                + (tab.inner_text("#kabar-berkas") or "(kosong)")
            ) from galat

        nama_berkas = tab.evaluate(
            "() => document.querySelector('#petak-berkas button.sisip img').src"
        ).rsplit("/", 1)[-1]
        try:
            tab.click("#petak-berkas button.sisip")

            for kotak in ("isi_en", "isi_id"):
                assert nama_berkas in tab.input_value(f"#{kotak}"), (
                    f"{kotak} tidak ikut menerima gambarnya"
                )

            tab.wait_for_function(
                "() => document.querySelector('#pratinjau img') !== null",
                timeout=25000,
            )
            gambar = tab.locator("#pratinjau img").first
            assert gambar.get_attribute("width") == "240"
            assert gambar.get_attribute("height") == "135"

            assert tab.evaluate(
                "() => { const g = document.querySelector('#pratinjau img');"
                " return g.complete && g.naturalWidth; }"
            ) == 240, "gambar di pratinjau tidak berhasil dimuat"

            tab.fill("#isi_en", "![peta](https://contoh.example/a.png)")
            tab.fill("#isi_id", "![peta](https://contoh.example/a.png)")
            tab.dispatch_event("#isi_id", "input")
            tab.wait_for_function(
                "() => (document.getElementById('pratinjau').textContent || '')"
                "  .includes('diunggah ke situs ini')",
                timeout=25000,
            )
            assert tab.locator("#pratinjau img").count() == 0
        finally:
            tab.evaluate(
                "async (nama) => { await panggil('/api/v1/admin/berkas/' + nama,"
                " { method: 'DELETE' }); }",
                arg=nama_berkas,
            )

        tab.click("#tombol-kembali") if tab.locator("#tombol-kembali").count() else None

        tab.evaluate("() => { window.fetch = () => Promise.reject(new Error('putus')); }")
        tab.evaluate("() => muatRingkasan()")
        for ubin in UBIN:
            assert tab.inner_text(f"#{ubin}").strip() == "?", (
                f"{ubin} menulis angka padahal pembacaannya gagal. Nol adalah "
                f"bacaan; ketiadaan data bukan."
            )
    finally:
        konteks.close()
