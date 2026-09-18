"""Dashboard admin, di peramban sungguhan.

Yang dijaga di sini bukan tata letaknya melainkan **kejujuran angkanya**, dan
itu aturan yang sudah berlaku di tempat lain di repositori ini: nol adalah
bacaan, ketiadaan data bukan, dan perbedaan itu wajib terlihat oleh yang
membacanya. Panel yang menjawab "0 perangkat masuk" padahal daftarnya gagal
dibaca justru menenangkan orang pada saat ia seharusnya waspada.

**Satu uji, satu kali masuk.** Ini keputusan yang dibayar untuk dipelajari.
Versi pertama memecahnya jadi sembilan uji, masing masing membuka konteks
peramban lalu masuk lagi. Sesudah dua atau tiga kali, servernya berhenti
menjawab sama sekali: `Page.goto` pun habis waktu tiga puluh detik ke alamat
yang sedetik sebelumnya melayani dengan baik. Masuk berkali kali dalam hitungan
detik bukan yang dikerjakan orang, dan bukan itu yang ingin dijaga berkas ini.

Sebagian sebabnya sudah ditemukan dan ditutup di `backend/jalan.py`: di
Windows `localhost` menunjuk `::1` lebih dulu, dan server yang hanya mengikat
IPv4 membuat TIAP permintaan menunggu dua detik. Terukur 2050 ms menjadi 13 ms
sesudah kedua loopback diikat. Sisanya belum saya temukan, dan uji yang
digabung ini adalah pengakuan atas batas itu, bukan penyembunyiannya.

Dilewati kalau Playwright, basis data, atau Chromium tidak ada.
"""

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
    """PNG sungguhan, bukan kepala berkas saja.

    Yang diuji di sini menempuh seluruh jalurnya: peramban mengunggah, server
    membaca kepalanya, berkasnya ditulis ke cakram, lalu peramban yang sama
    memintanya lagi dan menggambarnya. Kepala berkas tanpa isi akan lolos di
    server dan gagal digambar, yaitu bagian yang justru ingin diperiksa.
    """
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
        # --- sebelum masuk -------------------------------------------------
        tab.goto(f"{server_admin}/admin", wait_until="domcontentloaded")
        tab.wait_for_selector("#tombol-masuk")
        for panel in PANEL:
            assert tab.is_hidden(f"#{panel}"), (
                f"{panel} terlihat sebelum masuk, padahal isinya keterangan tentang akun"
            )

        # --- sesudah masuk -------------------------------------------------
        masuk_admin(tab, server_admin)

        # Penyegaran pertama sengaja ditunda supaya tidak berlomba dengan alur
        # masuk, jadi yang ditunggu isinya, bukan waktu. Menunggu dengan sleep
        # berarti ujinya pecah pada hari penundaannya diubah.
        tab.wait_for_function(
            "() => document.getElementById('ubin-terbit').textContent !== '?'",
            timeout=25000,
        )

        for panel in PANEL:
            assert tab.is_visible(f"#{panel}"), f"{panel} tidak muncul sesudah masuk"

        # --- angkanya benar benar terbaca ----------------------------------
        for ubin in UBIN:
            isi = tab.inner_text(f"#{ubin}").strip()
            assert isi.isdigit(), f"{ubin} berisi {isi!r}, bukan angka"

        # --- perangkat ini ditandai ----------------------------------------
        assert tab.locator("#daftar-sesi tr").count() >= 1
        assert tab.locator("#daftar-sesi .ini-perangkat").count() == 1, (
            "daftar perangkat tanpa penanda 'yang mana saya' tidak bisa dipakai "
            "memutuskan apa pun"
        )

        # --- jejak keamanan ada dan namanya diterjemahkan -------------------
        baris = tab.locator("#daftar-jejak tr")
        assert baris.count() >= 1, "jejak kosong, padahal baru saja ada yang masuk"
        nama_mentah = tab.evaluate(
            "() => Array.from(document.querySelectorAll('#daftar-jejak tr td:nth-child(2)'))"
            "  .map(t => t.textContent).filter(t => t.includes('_'))"
        )
        assert not nama_mentah, f"nama peristiwa tampil mentah: {nama_mentah[:3]}"

        # --- tombol segarkan memperbarui waktunya --------------------------
        sebelum = tab.inner_text("#waktu-segar")
        assert sebelum.startswith("diperbarui"), f"waktu segar tidak tertulis: {sebelum!r}"
        tab.wait_for_timeout(1100)   # jamnya berdetik
        tab.click("#tombol-segarkan")
        tab.wait_for_function(
            "(lama) => document.getElementById('waktu-segar').textContent !== lama",
            arg=sebelum, timeout=25000,
        )

        # --- penyegaran berhenti saat tab tidak terlihat --------------------
        # Diperiksa di dalam kodenya, sebab keadaan `hidden` tidak bisa
        # dipalsukan dari luar tanpa mengubah halamannya.
        assert "document.hidden" in tab.evaluate("() => mulaiSegarBerkala.toString()"), (
            "penyegaran berkala tidak memeriksa keadaan tab, jadi tab yang "
            "ditinggalkan terbuka akan terus mengetuk server"
        )

        # --- bilah format, unggahan, dan pratinjaunya ----------------------
        #
        # Ditaruh di dalam uji yang sama, bukan di uji sendiri, karena alasan
        # yang tertulis di kepala berkas ini: masuk berkali kali dalam
        # hitungan detik membuat servernya berhenti menjawab.
        tab.click("#tombol-baru")
        tab.wait_for_selector("#isi_en")

        # Tombol daftar butir menulis tanda yang memang dikenal pengurainya.
        tab.click("#isi_en")
        tab.fill("#isi_en", "satu")
        tab.click('.bilah button[data-baris^="- "]')
        assert tab.input_value("#isi_en") == "- satu", tab.input_value("#isi_en")

        # Menekan tombol yang sama dua kali mencabut tandanya lagi.
        tab.click('.bilah button[data-baris^="- "]')
        assert tab.input_value("#isi_en") == "satu"

        # Tebal membungkus yang sedang dipilih.
        tab.evaluate("() => { const k = document.getElementById('isi_en');"
                     " k.focus(); k.setSelectionRange(0, 4); }")
        tab.click('.bilah button[data-sisip^="**"]')
        assert tab.input_value("#isi_en") == "**satu**"

        # Unggah satu foto sungguhan, lalu sisipkan.
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
        except Exception as galat:  # pragma: no cover - hanya saat gagal
            # Tanpa baris ini yang terbaca cuma "selector tidak muncul", dan
            # sebab sebenarnya, yaitu kalimat penolakan dari server, hilang.
            raise AssertionError(
                "unggahan tidak muncul di pustaka. Kabar di layar: "
                + (tab.inner_text("#kabar-berkas") or "(kosong)")
            ) from galat

        nama_berkas = tab.evaluate(
            "() => document.querySelector('#petak-berkas button.sisip img').src"
        ).rsplit("/", 1)[-1]
        try:
            tab.click("#petak-berkas button.sisip")

            # Disisipkan ke KEDUA bahasa. Dua bahasa wajib sebangun blok demi
            # blok, jadi gambar yang hanya masuk ke satu bahasa langsung
            # membuat tulisannya ditolak.
            for kotak in ("isi_en", "isi_id"):
                assert nama_berkas in tab.input_value(f"#{kotak}"), (
                    f"{kotak} tidak ikut menerima gambarnya"
                )

            # Pratinjaunya dibangun server, dan ukurannya ikut ke dalam
            # atribut width dan height supaya tulisan di bawahnya tidak
            # melompat saat gambarnya tiba.
            tab.wait_for_function(
                "() => document.querySelector('#pratinjau img') !== null",
                timeout=25000,
            )
            gambar = tab.locator("#pratinjau img").first
            assert gambar.get_attribute("width") == "240"
            assert gambar.get_attribute("height") == "135"

            # Dan gambarnya benar benar bisa diambil lagi dari alamatnya.
            assert tab.evaluate(
                "() => { const g = document.querySelector('#pratinjau img');"
                " return g.complete && g.naturalWidth; }"
            ) == 240, "gambar di pratinjau tidak berhasil dimuat"

            # Markah yang ditolak disebut alasannya, sebagai teks, bukan
            # dirakit jadi HTML: alasannya memuat potongan baris yang baru
            # saja diketik orangnya.
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

        # --- yang gagal dibaca ditulis tanda tanya, bukan nol ---------------
        # Dijalankan paling akhir sebab ia sengaja mematahkan halamannya.
        tab.evaluate("() => { window.fetch = () => Promise.reject(new Error('putus')); }")
        tab.evaluate("() => muatRingkasan()")
        for ubin in UBIN:
            assert tab.inner_text(f"#{ubin}").strip() == "?", (
                f"{ubin} menulis angka padahal pembacaannya gagal. Nol adalah "
                f"bacaan; ketiadaan data bukan."
            )
    finally:
        konteks.close()
