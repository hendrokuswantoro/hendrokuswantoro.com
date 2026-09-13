"""Verifikasi wajah: yang diuji, dan yang sengaja TIDAK diuji.

**Yang tidak diuji di sini, dan alasannya.** Ketepatan pengenalan wajahnya.
Untuk mengujinya saya butuh foto wajah orang sungguhan, dan foto wajah orang
sungguhan tidak akan saya masukkan ke repositori ini. Ketepatan YuNet dan
SFace adalah klaim terukur penulisnya, di atas kumpulan data yang memang
dibuat untuk itu; SFace menyebut sekitar 99,6 persen pada LFW dengan ambang
0,363, dan ambang itulah yang dipakai di sini apa adanya.

Jadi tidak ada satu pun uji di berkas ini yang boleh dibaca sebagai "wajah
orang lain ditolak". Yang dibuktikan di sini sambungan di sekelilingnya, dan
justru di situlah kesalahan biasanya duduk:

- bingkai yang bukan gambar, kosong, atau kelewat besar ditolak sebelum
  menyentuh model
- tidak ada wajah berarti ditolak, bukan diloloskan
- arah hadap dihitung benar dari lima titik penanda
- urutan gerakan diputuskan server, sekali pakai, dan tidak bisa diulang
- ciri wajahnya tersandi di basis data, dan fotonya tidak pernah tersimpan
- satu bingkai yang tidak cocok cukup untuk menolak semuanya

Uji yang menuntut model dilewati kalau modelnya belum diunduh, dengan alasan
yang menyebut perintahnya.
"""

from __future__ import annotations

import asyncio
import base64
import os
import sys

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat  # noqa: E402

muat()

from backend.layanan import wajah  # noqa: E402

butuh_model = pytest.mark.skipif(
    not wajah.siap(),
    reason=(
        "model pengenalan wajah belum ada.\n"
        "    Jalankan: pip install -r backend/requirements.txt\n"
        "    lalu    : python tools/ambil_model.py\n"
        "    Selama belum, uji wajah tidak menjaga apa apa."
    ),
)


def _penanda(hidung_x: float, mata_kanan_x: float = 100.0, mata_kiri_x: float = 140.0):
    """Satu baris hasil YuNet, isinya yang dipakai saja.

    Urutannya: x, y, lebar, tinggi, mata kanan, mata kiri, hidung, mulut
    kanan, mulut kiri, skor.
    """
    return [
        0.0, 0.0, 60.0, 60.0,
        mata_kanan_x, 80.0,
        mata_kiri_x, 80.0,
        hidung_x, 100.0,
        110.0, 120.0,
        130.0, 120.0,
        0.99,
    ]


# --------------------------------------------------------- arah hadap ---


def test_hidung_di_tengah_berarti_menghadap_lurus():
    assert wajah.arah_hadap(_penanda(120.0)) == "tengah"


def test_hidung_bergeser_berarti_menoleh():
    # Jarak antarmata 40 piksel, ambangnya 0,16, jadi geser lebih dari 6,4
    # piksel sudah terbaca menoleh.
    assert wajah.arah_hadap(_penanda(132.0)) == "kanan"
    assert wajah.arah_hadap(_penanda(108.0)) == "kiri"


def test_geseran_kecil_masih_dianggap_lurus():
    """Orang yang duduk sedikit miring tidak boleh ditolak."""
    assert wajah.arah_hadap(_penanda(124.0)) == "tengah"


def test_wajah_terlalu_kecil_ditolak_bukan_dibagi_nol():
    """Jarak antarmata nol akan membuat pembaginya nol. Ditolak dengan alasan,
    bukan dilempar ZeroDivisionError ke pemanggilnya."""
    with pytest.raises(wajah.Ditolak):
        wajah.arah_hadap(_penanda(100.0, mata_kanan_x=100.0, mata_kiri_x=100.0))


# ------------------------------------------------------------- gerakan ---


def test_gerakan_selalu_dimulai_lurus():
    """Bingkai yang dipakai membandingkan wajah harus yang paling mudah
    dikenali. Menoleh mengurangi ketepatan, dan menolak pemiliknya sendiri
    lebih sering daripada menolak orang lain adalah kegagalan yang paling
    cepat membuat fitur ini dimatikan."""
    for _ in range(30):
        g = wajah.gerakan_acak()
        assert g[0] == "tengah"
        assert sorted(g[1:]) == ["kanan", "kiri"]


def test_urutan_gerakan_benar_benar_berganti():
    """Urutan yang selalu sama sama saja dengan tidak ada tantangan."""
    assert len({tuple(wajah.gerakan_acak()) for _ in range(40)}) == 2


# ------------------------------------------------------- bingkai masuk ---


@pytest.mark.parametrize("buruk", [
    "",
    "bukan base64 sama sekali!!",
    base64.b64encode(b"ini bukan gambar").decode(),
])
@butuh_model
def test_bingkai_yang_bukan_gambar_ditolak(buruk):
    with pytest.raises(wajah.Ditolak):
        wajah._baca(buruk)


@butuh_model
def test_bingkai_kelewat_besar_ditolak_sebelum_didekode(monkeypatch):
    """Batasnya ditegakkan, bukan ditemukan saat memorinya habis."""
    monkeypatch.setattr(wajah, "BATAS_BITA", 1000)
    besar = base64.b64encode(b"x" * 1001).decode()
    with pytest.raises(wajah.Ditolak, match="KB"):
        wajah._baca(besar)


@butuh_model
def test_awalan_data_url_diterima():
    """Kamera peramban mengirim data:image/jpeg;base64,... apa adanya."""
    import cv2
    import numpy as np

    kosong = np.zeros((40, 40, 3), dtype=np.uint8)
    ok, sandi = cv2.imencode(".jpg", kosong)
    assert ok
    url = "data:image/jpeg;base64," + base64.b64encode(sandi.tobytes()).decode()
    gambar = wajah._baca(url)
    assert gambar.shape[0] == 40


@butuh_model
def test_gambar_tanpa_wajah_ditolak():
    """Yang penting bukan bahwa ia tidak menemukan wajah, melainkan bahwa
    ketiadaan wajah berarti DITOLAK, bukan diloloskan."""
    import cv2
    import numpy as np

    acak = np.random.default_rng(11).integers(0, 255, (240, 320, 3), dtype=np.uint8)
    ok, sandi = cv2.imencode(".jpg", acak)
    assert ok
    with pytest.raises(wajah.Ditolak, match="tidak ada wajah"):
        wajah._satu_wajah(wajah._baca(base64.b64encode(sandi.tobytes()).decode()))


@butuh_model
def test_dua_wajah_ditolak(monkeypatch):
    """Dua wajah berarti tidak ada cara memastikan yang mana yang diperiksa,
    dan itu cukup alasan untuk menolak alih alih menebak.

    Detektornya dipalsukan di sini, bukan modelnya diuji: yang diuji cabang
    milik berkas ini, dan menyiapkan foto berisi dua orang sungguhan bukan
    sesuatu yang pantas masuk repositori."""
    import numpy as np

    class DuaWajah:
        def setInputSize(self, ukuran):  # noqa: N802 - meniru API OpenCV
            pass

        def detect(self, gambar):
            return 0, np.vstack([_penanda(120.0), _penanda(120.0)])

    monkeypatch.setattr(wajah, "_mesin", lambda: (DuaWajah(), None))
    with pytest.raises(wajah.Ditolak, match="2 wajah"):
        wajah._satu_wajah(np.zeros((100, 100, 3), dtype=np.uint8))


# ------------------------------------------------------------ ciri wajah ---


@butuh_model
def test_ciri_bolak_balik_lewat_untai():
    import numpy as np

    asli = np.arange(128, dtype="float32").reshape(1, 128)
    kembali = wajah.dari_untai(wajah.ke_untai(asli))
    assert np.array_equal(asli, kembali)


@butuh_model
def test_mendaftar_butuh_lebih_dari_satu_bingkai():
    """Satu bingkai bisa kebetulan berbayang atau buram, dan ciri dari bingkai
    seperti itu akan menolak pemiliknya sendiri di kemudian hari."""
    with pytest.raises(wajah.Ditolak, match="dua bingkai"):
        wajah.ciri_dari_bingkai(["apa pun"])


# -------------------------------------------------------------- periksa ---


class _MesinPalsu:
    """Mesin tiruan yang mengembalikan wajah dan kemiripan yang ditentukan uji.

    Dipakai untuk menguji aturan di dalam `periksa`, bukan untuk menguji
    modelnya. Yang diuji: gerakan yang tidak sesuai ditolak, dan satu bingkai
    yang tidak cocok cukup untuk menolak semuanya.
    """

    def __init__(self, arah: list[str], nilai: list[float]):
        self.arah = list(arah)
        self.nilai = list(nilai)


@pytest.fixture
def mesin_palsu(monkeypatch):
    def pasang(arah: list[str], nilai: list[float]):
        keadaan = _MesinPalsu(arah, nilai)
        geser = {"kiri": 100.0, "tengah": 120.0, "kanan": 140.0}

        monkeypatch.setattr(wajah, "_baca", lambda b: b)
        monkeypatch.setattr(
            wajah, "_satu_wajah",
            lambda g: _penanda(geser[keadaan.arah.pop(0)]),
        )
        monkeypatch.setattr(wajah, "_ciri", lambda g, w: None)
        monkeypatch.setattr(wajah, "kemiripan", lambda a, b: keadaan.nilai.pop(0))

    return pasang


def test_semua_cocok_dan_gerakannya_benar(mesin_palsu):
    mesin_palsu(["tengah", "kiri", "kanan"], [0.7, 0.6, 0.55])
    hasil = wajah.periksa(["a", "b", "c"], ["tengah", "kiri", "kanan"], None)
    assert hasil["terendah"] == 0.55
    assert hasil["arah"] == ["tengah", "kiri", "kanan"]


def test_gerakan_yang_tidak_sesuai_ditolak(mesin_palsu):
    """Ini yang membuat tantangannya berarti. Tanpa pemeriksaan ini, tiga
    berkas yang sudah disiapkan sejak lama akan lolos."""
    mesin_palsu(["tengah", "tengah", "kanan"], [0.7, 0.7, 0.7])
    with pytest.raises(wajah.Ditolak, match="gerakan tidak sesuai"):
        wajah.periksa(["a", "b", "c"], ["tengah", "kiri", "kanan"], None)


def test_satu_bingkai_yang_tidak_cocok_menolak_semuanya(mesin_palsu):
    """Rata rata akan membiarkan satu bingkai yang jelas bukan pemiliknya
    tertutup oleh dua bingkai lain yang cocok."""
    mesin_palsu(["tengah", "kiri", "kanan"], [0.9, 0.9, 0.1])
    with pytest.raises(wajah.Ditolak, match="tidak cocok"):
        wajah.periksa(["a", "b", "c"], ["tengah", "kiri", "kanan"], None)


def test_jumlah_bingkai_harus_sama_dengan_yang_diminta(mesin_palsu):
    mesin_palsu(["tengah"], [0.9])
    with pytest.raises(wajah.Ditolak, match="butuh 3 bingkai"):
        wajah.periksa(["a"], ["tengah", "kiri", "kanan"], None)


def test_ambangnya_angka_dari_penulis_modelnya():
    """0,363 disebut penulis SFace, bukan dipilih di sini. Uji ini ada supaya
    angkanya tidak digeser diam diam ketika ada yang merasa fiturnya terlalu
    galak."""
    assert wajah.AMBANG == 0.363


# ------------------------------------------------------ tidak ada foto ---


def test_tidak_ada_satu_pun_foto_yang_disimpan():
    """Gambar yang tidak pernah tersimpan adalah gambar yang tidak bisa bocor.

    Diperiksa dari kodenya: tidak ada satu pun penulisan berkas di lapisan
    wajah maupun di repositori yang menyentuhnya.
    """
    for nama in ("backend/layanan/wajah.py", "backend/repositori/keamanan.py"):
        isi = (AKAR / nama).read_text(encoding="utf-8")
        for baris in isi.splitlines():
            bersih = baris.strip()
            if bersih.startswith("#"):
                continue
            for terlarang in ("imwrite", "write_bytes", "open(", "NamedTemporaryFile"):
                assert terlarang not in bersih, f"{nama}: {baris}"


def test_kolom_wajah_disandikan_bukan_disimpan_apa_adanya():
    """Dibaca dari kodenya: yang masuk repositori selalu hasil
    rahasia.sandikan, tidak pernah cirinya langsung."""
    isi = (AKAR / "backend" / "layanan" / "keamanan.py").read_text(encoding="utf-8")
    assert "repo.simpan_wajah(pengguna[\"id\"], rahasia.sandikan(" in isi, (
        "ciri wajah masuk basis data tanpa disandikan"
    )


def test_migrasi_menyebut_batas_yang_sebenarnya():
    """Berkas migrasinya wajib menyebut apa yang lapisan ini TIDAK bisa
    kerjakan. Fitur keamanan yang batasnya tidak tertulis akan dipercaya
    melebihi yang sebenarnya, dan itu justru menurunkan keamanan."""
    sql = (AKAR / "backend" / "db" / "migrations" / "0005_wajah.sql").read_text(
        encoding="utf-8"
    )
    assert "TIDAK" in sql
    assert "rekaman video" in sql.lower()
    assert "passkey" in sql.lower()
