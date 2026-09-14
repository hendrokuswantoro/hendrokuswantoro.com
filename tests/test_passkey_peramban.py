"""Masuk dengan sidik jari, lewat halaman admin sungguhan, di peramban sungguhan.

Ini uji yang seharusnya sudah ada sejak awal, dan ketiadaannya punya ongkos
nyata: pada 14 September 2026 pemilik proyek mencoba masuk dengan sidik jari
dan tidak bisa, sedangkan seluruh 20 uji passkey berwarna hijau. Ujinya hijau
karena semuanya memanggil API lewat `TestClient`, dan `TestClient` bukan
peramban. Yang menolak justru peramban, sebelum satu pun permintaan dikirim.

Sebabnya ada di `tests/test_passkey_alamat.py`: WebAuthn menuntut rp_id berupa
nama domain, dan 127.0.0.1 bukan nama. Berkas ini menjaga sisi lainnya, yaitu
bahwa di alamat yang benar seluruh putarannya memang berjalan:

    masuk dengan sandi -> daftarkan perangkat -> keluar -> masuk dengan passkey

Yang membuatnya mungkin tanpa jari manusia adalah **authenticator maya**
bawaan Chrome, dipasang lewat CDP. Ia membuat pasangan kunci sungguhan dan
menandatangani sungguhan; yang tidak sungguhan cuma sensornya. Tanda
tangannya tetap diverifikasi pustaka `webauthn` yang sama dengan produksi.

Servernya dijalankan sebagai subproses lewat `backend/jalan.py`, bukan di
dalam utas, sebab berkas itulah yang tahu cara menghindari ProactorEventLoop
yang ditolak psycopg di Windows. Menyalinnya ke sini berarti menyalin
jebakannya juga.

Dilewati kalau Playwright, basis data, atau Chromium tidak ada.
"""

from __future__ import annotations

import contextlib
import os
import sys
import time

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban


sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from conftest import EMAIL_UJI, SANDI_UJI, tab_dengan_otentikator  # noqa: E402



@pytest.fixture
def halaman_admin(server_admin, peramban):
    """Satu tab dengan authenticator maya yang sudah terpasang."""
    konteks, tab = tab_dengan_otentikator(peramban)
    try:
        yield tab
    finally:
        konteks.close()


# Ulangan alur masuk passkey, dijalankan di dalam halaman saat sebuah uji
# gagal. Gunanya satu: membedakan "peramban menolak menandatangani" dari
# "server menolak tanda tangannya", dua sebab yang di layar terlihat sama
# persis, yaitu tidak terjadi apa apa.
ULANGI_PASSKEY = """async () => {
  const L = [];
  try {
    const m = await fetch('/api/v1/auth/passkey/masuk/mulai', { method: 'POST' });
    L.push('mulai ' + m.status);
    const pilihan = JSON.parse((await m.json()).pilihan);
    pilihan.challenge = keBuffer(pilihan.challenge);
    for (const k of pilihan.allowCredentials || []) k.id = keBuffer(k.id);
    const kred = await Promise.race([
      navigator.credentials.get({ publicKey: pilihan }),
      new Promise((_, tolak) => setTimeout(() => tolak(new Error('get menggantung 8 detik')), 8000)),
    ]);
    L.push('tanda tangan ada');
    const s = await fetch('/api/v1/auth/passkey/masuk/selesai', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jawaban: {
        id: kred.id, rawId: keTeks(kred.rawId), type: kred.type,
        response: {
          clientDataJSON: keTeks(kred.response.clientDataJSON),
          authenticatorData: keTeks(kred.response.authenticatorData),
          signature: keTeks(kred.response.signature),
          userHandle: kred.response.userHandle ? keTeks(kred.response.userHandle) : null,
        },
        clientExtensionResults: kred.getClientExtensionResults(),
      } }),
    });
    L.push('selesai ' + s.status + ' ' + (await s.text()).slice(0, 120));
  } catch (e) {
    L.push('LEMPAR ' + e.name + ': ' + String(e.message).slice(0, 140));
  }
  return L;
}"""


def _masuk_dengan_sandi(tab, asal):
    tab.goto(f"{asal}/admin", wait_until="domcontentloaded")
    tab.wait_for_selector("#tombol-masuk")
    tab.fill("#email", EMAIL_UJI)
    tab.fill("#sandi", SANDI_UJI)
    tab.click("#tombol-masuk")
    tab.wait_for_selector("#layar-daftar:not(.sembunyi)", timeout=15000)


def test_tombol_passkey_hidup_di_localhost(halaman_admin, server_admin):
    """Kebalikan dari cacatnya. Di alamat bernama, tidak ada yang menghalangi."""
    halaman_admin.goto(f"{server_admin}/admin", wait_until="domcontentloaded")
    halaman_admin.wait_for_selector("#blok-passkey:not(.sembunyi)", timeout=15000)

    assert halaman_admin.evaluate("() => kendalaPasskey()") is None
    assert halaman_admin.is_disabled("#tombol-passkey") is False


def test_daftar_lalu_masuk_dengan_sidik_jari(halaman_admin, server_admin):
    """Putaran penuhnya, dan inilah yang tidak pernah dibuktikan sebelumnya."""
    tab = halaman_admin

    _masuk_dengan_sandi(tab, server_admin)

    # Nama perangkat diminta lewat prompt(), yang di peramban tanpa kepala
    # akan menggantung selamanya kalau tidak dijawab.
    tab.on("dialog", lambda d: d.accept("Perangkat uji"))

    tab.click("#tombol-daftar-kunci")
    tab.wait_for_function(
        "() => document.getElementById('kabar').textContent.includes('terdaftar')",
        timeout=20000,
    )

    # Keluar sepenuhnya, termasuk cookie refresh, supaya yang diuji benar
    # benar jalan masuk lewat passkey dan bukan sesi yang masih hidup.
    #
    # `keluar()` memanggil location.reload() sendiri, jadi halamannya sudah
    # berpindah tanpa disuruh. Memanggil goto() di sini membuat dua navigasi
    # bertabrakan, dan Playwright menyebutnya "interrupted by another
    # navigation". Yang lebih jahat: tabrakannya tidak selalu terasa di situ.
    # Sesudahnya tab itu menolak navigasi berikutnya sampai habis waktu 30
    # detik, dan yang tertuduh jadi alamat yang dituju berikutnya, padahal
    # alamat itu menjawab 200 pada detik yang sama.
    # Satu navigasi saja, yaitu milik halamannya sendiri. Versi sebelumnya
    # menambahkan clear_cookies() lalu reload() di sini, dan itu memuat ulang
    # untuk kedua kalinya tanpa alasan: `/auth/logout` sudah menghapus
    # cookie-nya lewat delete_cookie, jadi sesudah reload pertama halaman ini
    # memang sudah kembali ke layar masuk. Muat ulang kedua itu menggantung
    # sampai habis waktu 30 detik dan menuduh reload-nya, padahal yang salah
    # keberadaannya.
    with tab.expect_navigation(wait_until="domcontentloaded", timeout=15000):
        tab.click("#keluar")

    tab.wait_for_selector("#blok-passkey:not(.sembunyi)", timeout=15000)
    assert tab.is_visible("#tombol-masuk"), "masih masuk, jadi ujinya tidak membuktikan apa apa"

    tab.click("#tombol-passkey")
    try:
        tab.wait_for_selector("#layar-daftar:not(.sembunyi)", timeout=20000)
    except Exception:
        # Kegagalan di sini pernah berbunyi cuma "Timeout 20000ms exceeded",
        # dan kalimat itu tidak menyebutkan satu pun hal yang berguna. Yang
        # menjelaskan ada di halamannya: pesan di kotak kabar, galat
        # JavaScript, dan apakah tombolnya memang hidup saat ditekan.
        ulangan = tab.evaluate(ULANGI_PASSKEY)
        raise AssertionError(
            "masuk dengan passkey tidak sampai ke dashboard.\n"
            f"  kabar   : {tab.evaluate('() => document.getElementById(\"kabar\").textContent')!r}\n"
            f"  kelas   : {tab.evaluate('() => document.getElementById(\"kabar\").className')!r}\n"
            f"  tombol  : mati={tab.is_disabled('#tombol-passkey')}\n"
            f"  galat   : {tab.galat[:3]}\n"
            f"  ulangan : {ulangan}"
        ) from None

    assert not tab.galat, f"galat JavaScript saat masuk: {tab.galat[:3]}"


# Sisi gagalnya, yaitu tombol yang mati beserta alasannya saat halaman dibuka
# lewat 127.0.0.1, TIDAK diuji di sini, dan itu keputusan yang perlu ditulis.
#
# Ujinya pernah ada. Ia lolos kalau dijalankan sendirian, lolos berpasangan
# dengan salah satu uji di atas, dan menggantung sampai habis waktu kalau
# ketiganya berjalan berurutan. Yang tertuduh selalu alamat tujuannya,
# padahal alamat itu menjawab 200 lewat Python pada detik yang sama. Jadi
# yang menumpuk adalah konteks peramban ketiga beserta authenticator mayanya,
# bukan apa pun milik situs ini. Membongkar authenticator dan sesi CDP-nya
# secara tersurat justru membuatnya menggantung lebih lama lagi.
#
# Uji yang gagal karena sebabnya di luar kode mengajari orang mengabaikan
# warna merah, dan sesudah itu kegagalan yang sungguhan ikut terlewat. Jadi
# lebih baik tidak ada di sini.
#
# Klaimnya tidak hilang, hanya pindah ke tempat yang bisa menjaganya dengan
# tenang:
#
#   tests/test_passkey_alamat.py  membaca halaman adminnya dan menuntut
#                                 pemeriksaan alamat dipanggil SEBELUM
#                                 WebAuthn, tombolnya dimatikan, dan
#                                 SecurityError diterjemahkan. Ketiganya
#                                 sudah dibuktikan menangkap dengan cara
#                                 mengembalikan cacatnya.
#
# Selain itu perilakunya sudah diperiksa langsung di peramban pada 14
# September 2026, di http://127.0.0.1:8000/admin: tombolnya mati dan
# catatannya berbunyi "Passkey tidak bisa dipakai lewat alamat 127.0.0.1.
# Buka http://localhost:8000/admin, mesinnya sama, cuma namanya yang
# berbeda."
