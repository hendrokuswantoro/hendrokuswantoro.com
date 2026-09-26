from __future__ import annotations

import base64
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
    return [
        0.0, 0.0, 60.0, 60.0,
        mata_kanan_x, 80.0,
        mata_kiri_x, 80.0,
        hidung_x, 100.0,
        110.0, 120.0,
        130.0, 120.0,
        0.99,
    ]


def test_hidung_di_tengah_berarti_menghadap_lurus():
    assert wajah.arah_hadap(_penanda(120.0)) == "tengah"


def test_arah_menurut_orangnya_bukan_menurut_gambar():
    assert wajah.arah_hadap(_penanda(108.0)) == "kanan"
    assert wajah.arah_hadap(_penanda(132.0)) == "kiri"


def test_gambar_yang_dicerminkan_memberi_arah_yang_sama():
    cermin = dict(mata_kanan_x=140.0, mata_kiri_x=100.0)
    assert wajah.arah_hadap(_penanda(132.0, **cermin)) == "kanan"
    assert wajah.arah_hadap(_penanda(108.0, **cermin)) == "kiri"


def test_geseran_kecil_masih_dianggap_lurus():
    assert wajah.arah_hadap(_penanda(124.0)) == "tengah"


def test_wajah_terlalu_kecil_ditolak_bukan_dibagi_nol():
    with pytest.raises(wajah.Ditolak):
        wajah.arah_hadap(_penanda(100.0, mata_kanan_x=100.0, mata_kiri_x=100.0))


def test_gerakan_selalu_dimulai_lurus():
    for _ in range(30):
        g = wajah.gerakan_acak()
        assert g[0] == "tengah"
        assert sorted(g[1:]) == ["kanan", "kiri"]


def test_urutan_gerakan_benar_benar_berganti():
    assert len({tuple(wajah.gerakan_acak()) for _ in range(40)}) == 2


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
    monkeypatch.setattr(wajah, "BATAS_BITA", 1000)
    besar = base64.b64encode(b"x" * 1001).decode()
    with pytest.raises(wajah.Ditolak, match="KB"):
        wajah._baca(besar)


@butuh_model
def test_awalan_data_url_diterima():
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
    import cv2
    import numpy as np

    acak = np.random.default_rng(11).integers(0, 255, (240, 320, 3), dtype=np.uint8)
    ok, sandi = cv2.imencode(".jpg", acak)
    assert ok
    with pytest.raises(wajah.Ditolak, match="tidak ada wajah"):
        wajah._satu_wajah(wajah._baca(base64.b64encode(sandi.tobytes()).decode()))


@butuh_model
def test_dua_wajah_ditolak(monkeypatch):
    import numpy as np

    class DuaWajah:
        def setInputSize(self, ukuran):  # noqa: N802 
            pass

        def detect(self, gambar):
            return 0, np.vstack([_penanda(120.0), _penanda(120.0)])

    monkeypatch.setattr(wajah, "_mesin", lambda: (DuaWajah(), None))
    with pytest.raises(wajah.Ditolak, match="2 wajah"):
        wajah._satu_wajah(np.zeros((100, 100, 3), dtype=np.uint8))


@butuh_model
def test_ciri_bolak_balik_lewat_untai():
    import numpy as np

    asli = np.arange(128, dtype="float32").reshape(1, 128)
    kembali = wajah.dari_untai(wajah.ke_untai(asli))
    assert np.array_equal(asli, kembali)


@butuh_model
def test_mendaftar_butuh_lebih_dari_satu_bingkai():
    with pytest.raises(wajah.Ditolak, match="dua bingkai"):
        wajah.ciri_dari_bingkai(["apa pun"])


class _MesinPalsu:
    def __init__(self, arah: list[str], nilai: list[float]):
        self.arah = list(arah)
        self.nilai = list(nilai)


@pytest.fixture
def mesin_palsu(monkeypatch):
    def pasang(arah: list[str], nilai: list[float]):
        keadaan = _MesinPalsu(arah, nilai)
        geser = {"kanan": 100.0, "tengah": 120.0, "kiri": 140.0}

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
    mesin_palsu(["tengah", "tengah", "kanan"], [0.7, 0.7, 0.7])
    with pytest.raises(wajah.Ditolak, match="gerakan tidak sesuai"):
        wajah.periksa(["a", "b", "c"], ["tengah", "kiri", "kanan"], None)


def test_satu_bingkai_yang_tidak_cocok_menolak_semuanya(mesin_palsu):
    mesin_palsu(["tengah", "kiri", "kanan"], [0.9, 0.9, 0.1])
    with pytest.raises(wajah.Ditolak, match="tidak cocok"):
        wajah.periksa(["a", "b", "c"], ["tengah", "kiri", "kanan"], None)


def test_jumlah_bingkai_harus_sama_dengan_yang_diminta(mesin_palsu):
    mesin_palsu(["tengah"], [0.9])
    with pytest.raises(wajah.Ditolak, match="butuh 3 bingkai"):
        wajah.periksa(["a"], ["tengah", "kiri", "kanan"], None)


def test_ambangnya_angka_dari_penulis_modelnya():
    assert wajah.AMBANG == 0.363


def test_tidak_ada_satu_pun_foto_yang_disimpan():
    for nama in ("backend/layanan/wajah.py", "backend/repositori/keamanan.py"):
        isi = (AKAR / nama).read_text(encoding="utf-8")
        for baris in isi.splitlines():
            bersih = baris.strip()
            if bersih.startswith("#"):
                continue
            for terlarang in ("imwrite", "write_bytes", "open(", "NamedTemporaryFile"):
                assert terlarang not in bersih, f"{nama}: {baris}"


def test_kolom_wajah_disandikan_bukan_disimpan_apa_adanya():
    isi = (AKAR / "backend" / "layanan" / "keamanan.py").read_text(encoding="utf-8")
    assert "repo.simpan_wajah(pengguna[\"id\"], rahasia.sandikan(" in isi, (
        "ciri wajah masuk basis data tanpa disandikan"
    )


def test_migrasi_menyebut_batas_yang_sebenarnya():
    sql = (AKAR / "backend" / "db" / "migrations" / "0005_wajah.sql").read_text(
        encoding="utf-8"
    )
    assert "TIDAK" in sql
    assert "rekaman video" in sql.lower()
    assert "passkey" in sql.lower()
