from __future__ import annotations

import sys

import pytest

from konftes import AKAR

pytest.importorskip("playwright", reason="playwright belum terpasang")

pytestmark = pytest.mark.peramban


sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from conftest import EMAIL_UJI, SANDI_UJI, tab_dengan_otentikator  # noqa: E402


@pytest.fixture
def halaman_admin(server_admin, peramban):
    konteks, tab = tab_dengan_otentikator(peramban)
    try:
        yield tab
    finally:
        konteks.close()


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
    halaman_admin.goto(f"{server_admin}/admin", wait_until="domcontentloaded")
    halaman_admin.wait_for_selector("#blok-passkey:not(.sembunyi)", timeout=15000)

    assert halaman_admin.evaluate("() => kendalaPasskey()") is None
    assert halaman_admin.is_disabled("#tombol-passkey") is False


def test_daftar_lalu_masuk_dengan_sidik_jari(halaman_admin, server_admin):
    tab = halaman_admin

    _masuk_dengan_sandi(tab, server_admin)

    tab.on("dialog", lambda d: d.accept("Perangkat uji"))

    tab.click("#tombol-daftar-kunci")
    tab.wait_for_function(
        "() => document.getElementById('kabar').textContent.includes('terdaftar')",
        timeout=20000,
    )

    with tab.expect_navigation(wait_until="domcontentloaded", timeout=15000):
        tab.click("#keluar")

    tab.wait_for_selector("#blok-passkey:not(.sembunyi)", timeout=15000)
    assert tab.is_visible("#tombol-masuk"), "masih masuk, jadi ujinya tidak membuktikan apa apa"

    tab.click("#tombol-passkey")
    try:
        tab.wait_for_selector("#layar-daftar:not(.sembunyi)", timeout=20000)
    except Exception:
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


