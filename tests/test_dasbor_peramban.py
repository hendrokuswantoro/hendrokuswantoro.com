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
