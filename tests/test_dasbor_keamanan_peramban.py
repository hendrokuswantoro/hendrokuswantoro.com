from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import threading

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban

from test_csp import _pasang_pengintai, _pelanggaran, _server, tajuk_nginx

KEADAAN = {
    "faktor_kedua_wajib": True, "sesi_kuat": True, "pencabutan_segera_siap": True,
    "email": "pemilik@contoh.id", "email_terverifikasi": True, "email_terverifikasi_pada": None,
    "totp_terpasang": False, "totp_aktif": False, "punya_sandi": True, "passkey": 1,
    "pemulihan_sisa": 0, "wajah_terdaftar": False, "surat_siap": True, "kunci_kolom_siap": True,
    "wajah_siap": False, "kabar_masuk": True, "kabar_perubahan": True, "mode_ketat": False,
}
QR = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 2"><rect width="1" height="1"/></svg>'


@pytest.fixture(scope="module")
def dasbor():
    sumber = AKAR / "backend" / "admin"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="uji-keamanan-"))
    (tmp / "admin").mkdir()
    for nama in ["index.html", "dasbor.css", *[p.name for p in sumber.glob("dasbor*.js")]]:
        shutil.copy(sumber / nama, tmp / "admin" / nama)
    srv = _server(tmp, tajuk_nginx("location ^~ /admin"), 8135)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:8135/admin/"
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


def _buka(peramban, alamat, perangkat=None):
    konteks = peramban.new_context(viewport={"width": 1280, "height": 900})
    tab = konteks.new_page()
    _pasang_pengintai(tab)
    tab.galat = []
    tab.on("pageerror", lambda e: tab.galat.append(str(e)))
    tab.kiriman = []
    if perangkat is not None:
        tab.add_init_script(f"localStorage.setItem('hk-admin-perangkat', {json.dumps(json.dumps(perangkat))})")

    jawaban = {
        ("POST", "/api/v1/auth/refresh"): {"akses": "uji", "nama": "Hendro"},
        ("GET", "/api/v1/keamanan"): KEADAAN,
        ("GET", "/api/v1/admin/blog"): {"isi": []},
        ("GET", "/api/v1/auth/passkey"): {"daftar": []},
        ("GET", "/api/v1/auth/sesi"): {"jumlah": 1, "sesi": []},
        ("GET", "/api/v1/keamanan/peristiwa"): {"peristiwa": []},
        ("GET", "/api/v1/auth/passkey/siap"): {"siap": False},
        ("PATCH", "/api/v1/keamanan/setelan"): KEADAAN,
        ("POST", "/api/v1/keamanan/totp/mulai"): {"rahasia": "RAHASIAUJI", "otpauth": "otpauth://uji", "qr": QR},
        ("POST", "/api/v1/auth/logout"): {},
        ("GET", "/health"): {"basis_data": True, "cache": True},
    }

    def tangani(rute):
        permintaan = rute.request
        jalur = "/" + permintaan.url.split("/", 3)[3].split("?")[0]
        tab.kiriman.append((permintaan.method, jalur, permintaan.post_data))
        isi = jawaban.get((permintaan.method, jalur))
        if isi is None:
            rute.fulfill(status=404, content_type="application/json", body='{"detail":"tidak ada"}')
        else:
            rute.fulfill(status=200, content_type="application/json", body=json.dumps(isi))

    tab.route("**/api/v1/**", tangani)
    tab.route("**/health", tangani)
    tab.goto(alamat, wait_until="load")
    tab.wait_for_selector("#isi-keamanan .baris-menu", state="attached", timeout=10000)
    return konteks, tab


def test_menu_keamanan_tampil_seperti_whatsapp(peramban, dasbor):
    konteks, tab = _buka(peramban, dasbor)
    try:
        judul = tab.locator("#isi-keamanan .baris-menu strong").all_inner_texts()
        assert judul == ["Verifikasi dua langkah", "Notifikasi keamanan", "Kunci aplikasi", "Lanjutan", "Aktivitas akun"]
        assert _pelanggaran(tab) == [], _pelanggaran(tab)
        assert not tab.galat, tab.galat
    finally:
        konteks.close()


def test_notifikasi_mengirim_setelan_yang_diubah(peramban, dasbor):
    konteks, tab = _buka(peramban, dasbor)
    try:
        tab.locator(".baris-menu", has_text="Notifikasi keamanan").click()
        sakelar = tab.locator("#isi-keamanan [role=switch]")
        assert sakelar.count() == 2
        assert sakelar.first.get_attribute("aria-checked") == "true"
        sakelar.first.click()
        tab.wait_for_timeout(500)
        dikirim = [k for k in tab.kiriman if k[0] == "PATCH"]
        assert dikirim and json.loads(dikirim[0][2]) == {"kabar_masuk": False}, tab.kiriman
        tab.locator("#isi-keamanan .kembali").click()
        assert tab.locator("#isi-keamanan .baris-menu").count() == 5
    finally:
        konteks.close()


def test_authenticator_menampilkan_qr_dari_server(peramban, dasbor):
    konteks, tab = _buka(peramban, dasbor)
    try:
        tab.locator(".baris-menu", has_text="Verifikasi dua langkah").click()
        tab.locator("summary", has_text="Aplikasi authenticator").click()
        tab.locator("button", has_text="Pasang authenticator").click()
        tab.wait_for_selector("#isi-keamanan .qr svg", timeout=5000)
        assert "RAHASIAUJI" in tab.locator("#isi-keamanan").inner_text()
        assert tab.locator("#kode-totp").is_visible()
        assert "rekaman video" in tab.locator("#isi-keamanan").text_content()
        assert _pelanggaran(tab) == [], _pelanggaran(tab)
    finally:
        konteks.close()


def test_keluar_otomatis_tersimpan_di_perangkat(peramban, dasbor):
    konteks, tab = _buka(peramban, dasbor)
    try:
        tab.locator(".baris-menu", has_text="Lanjutan").click()
        tab.locator("#isi-keamanan [role=switch]").nth(1).click()
        simpanan = json.loads(tab.evaluate("() => localStorage.getItem('hk-admin-perangkat')"))
        assert simpanan["keluarOtomatis"] is True
    finally:
        konteks.close()


def test_kunci_aplikasi_menutup_layar_sampai_dibuka(peramban, dasbor):
    konteks, tab = _buka(peramban, dasbor, {"kunci": True, "jeda": 0, "keluarOtomatis": False})
    try:
        assert tab.locator("#kunci-layar").is_visible()
        assert tab.evaluate("() => document.body.classList.contains('terkunci')")
        assert tab.evaluate("() => getComputedStyle(document.querySelector('.kerangka')).visibility") == "hidden"
        tab.locator("#tombol-keluar-kunci").click()
        tab.wait_for_timeout(500)
        assert ("POST", "/api/v1/auth/logout", None) in tab.kiriman or any(
            k[1] == "/api/v1/auth/logout" for k in tab.kiriman
        )
    finally:
        konteks.close()
