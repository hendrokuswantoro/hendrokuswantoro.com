from __future__ import annotations

import base64
import binascii
import functools
import pathlib
import secrets

RUMAH = pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "model"
PENDETEKSI = RUMAH / "face_detection_yunet_2023mar.onnx"
PENGENAL = RUMAH / "face_recognition_sface_2021dec.onnx"

AMBANG = 0.363

BATAS_BITA = 2 * 1024 * 1024
SISI_MAKS = 1600

GERAKAN = ("tengah", "kiri", "kanan")
JUMLAH_BINGKAI = 3

AMBANG_TOLEH = 0.16


class Ditolak(Exception):
    pass


class BelumSiap(Exception):
    pass


def siap() -> bool:
    try:
        import cv2  # noqa: F401
    except ImportError:
        return False
    return PENDETEKSI.exists() and PENGENAL.exists()


def _alasan_belum_siap() -> str:
    try:
        import cv2  # noqa: F401
    except ImportError:
        return (
            "opencv-python-headless belum terpasang. "
            "Jalankan: pip install -r backend/requirements.txt"
        )
    return (
        "model pengenalan wajah belum diunduh, 37 MB. "
        "Jalankan: python tools/ambil_model.py"
    )


@functools.lru_cache(maxsize=1)
def _mesin():
    if not siap():
        raise BelumSiap(_alasan_belum_siap())
    import cv2

    pendeteksi = cv2.FaceDetectorYN_create(
        str(PENDETEKSI), "", (320, 320),
        score_threshold=0.8,
        nms_threshold=0.3,
        top_k=50,
    )
    pengenal = cv2.FaceRecognizerSF_create(str(PENGENAL), "")
    return pendeteksi, pengenal


def _baca(bingkai: str):
    import cv2
    import numpy as np

    isi = bingkai.split(",", 1)[-1] if bingkai.startswith("data:") else bingkai
    try:
        mentah = base64.b64decode(isi, validate=True)
    except (binascii.Error, ValueError) as galat:
        raise Ditolak("bingkai bukan base64 yang sah") from galat

    if not mentah:
        raise Ditolak("bingkai kosong")
    if len(mentah) > BATAS_BITA:
        raise Ditolak(f"bingkai lebih dari {BATAS_BITA // 1024} KB")

    gambar = cv2.imdecode(np.frombuffer(mentah, np.uint8), cv2.IMREAD_COLOR)
    if gambar is None:
        raise Ditolak("bingkai bukan gambar yang bisa dibaca")

    tinggi, lebar = gambar.shape[:2]
    if max(tinggi, lebar) > SISI_MAKS:
        skala = SISI_MAKS / max(tinggi, lebar)
        gambar = cv2.resize(gambar, (int(lebar * skala), int(tinggi * skala)))
    return gambar


def _satu_wajah(gambar):
    pendeteksi, _ = _mesin()
    tinggi, lebar = gambar.shape[:2]
    pendeteksi.setInputSize((lebar, tinggi))
    _, hasil = pendeteksi.detect(gambar)

    if hasil is None or len(hasil) == 0:
        raise Ditolak("tidak ada wajah di dalam bingkai")
    if len(hasil) > 1:
        raise Ditolak(f"ada {len(hasil)} wajah di dalam bingkai, harus satu")
    return hasil[0]


def _ciri(gambar, wajah):
    import cv2

    _, pengenal = _mesin()
    lurus = pengenal.alignCrop(gambar, wajah)
    return pengenal.feature(lurus)


def arah_hadap(wajah) -> str:
    mata_kanan = (wajah[4], wajah[5])
    mata_kiri = (wajah[6], wajah[7])
    hidung_x = wajah[8]

    tengah = (mata_kanan[0] + mata_kiri[0]) / 2
    jarak = mata_kiri[0] - mata_kanan[0]
    if abs(jarak) < 1:
        raise Ditolak("wajahnya terlalu kecil di dalam bingkai")

    geser = (hidung_x - tengah) / jarak
    if geser > AMBANG_TOLEH:
        return "kiri"
    if geser < -AMBANG_TOLEH:
        return "kanan"
    return "tengah"


def ciri_dari_bingkai(bingkai: list[str]):
    import numpy as np

    if len(bingkai) < 2:
        raise Ditolak("butuh setidaknya dua bingkai")

    semua = []
    for satu in bingkai:
        gambar = _baca(satu)
        semua.append(_ciri(gambar, _satu_wajah(gambar)))

    rata = np.mean(np.vstack(semua), axis=0, keepdims=True).astype("float32")
    norma = float(np.linalg.norm(rata))
    if norma == 0:
        raise Ditolak("ciri wajahnya kosong")
    return rata / norma


def ke_untai(ciri) -> str:
    return base64.b64encode(ciri.astype("float32").tobytes()).decode("ascii")


def dari_untai(untai: str):
    import numpy as np

    mentah = base64.b64decode(untai)
    return np.frombuffer(mentah, dtype="float32").reshape(1, -1)


def kemiripan(a, b) -> float:
    import cv2

    _, pengenal = _mesin()
    return float(pengenal.match(a, b, cv2.FaceRecognizerSF_FR_COSINE))


def gerakan_acak() -> list[str]:
    sisa = ["kiri", "kanan"]
    if secrets.randbelow(2):
        sisa.reverse()
    return ["tengah", *sisa]


def periksa(bingkai: list[str], diminta: list[str], tersimpan) -> dict:
    if len(bingkai) != len(diminta):
        raise Ditolak(f"butuh {len(diminta)} bingkai, diterima {len(bingkai)}")

    nilai: list[float] = []
    arah: list[str] = []

    for satu, harus in zip(bingkai, diminta):
        gambar = _baca(satu)
        wajah = _satu_wajah(gambar)
        arah_nya = arah_hadap(wajah)
        arah.append(arah_nya)
        if arah_nya != harus:
            raise Ditolak(
                f"gerakan tidak sesuai: diminta menghadap {harus}, "
                f"yang terbaca menghadap {arah_nya}"
            )
        nilai.append(kemiripan(_ciri(gambar, wajah), tersimpan))

    terendah = min(nilai)
    if terendah < AMBANG:
        raise Ditolak("wajahnya tidak cocok dengan yang terdaftar")

    return {
        "terendah": round(terendah, 4),
        "tertinggi": round(max(nilai), 4),
        "arah": arah,
    }
