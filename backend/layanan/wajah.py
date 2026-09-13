"""Pengenalan wajah: mendeteksi, meluruskan, menyandikan, membandingkan.

Yang jujur disebut lebih dulu, sebab sisa berkas ini hanya masuk akal kalau
batasnya sudah jelas.

**Apa yang lapisan ini kerjakan.** Ia mengambil beberapa bingkai gambar,
memastikan tiap bingkai memuat tepat satu wajah, mengubah wajah itu jadi 128
angka, lalu membandingkannya dengan 128 angka yang tersimpan saat mendaftar.
Ia juga memperkirakan arah hadap kepala dari lima titik penanda, dan menuntut
urutan arah yang baru saja diminta server.

**Apa yang ia TIDAK kerjakan, dan tidak bisa.** Ia tidak membuktikan bahwa
yang di depan kamera adalah orang hidup. Rekaman video wajah pemiliknya akan
lolos, termasuk urutan gerakannya kalau rekamannya cukup panjang. Deteksi
kehidupan yang sungguhan menuntut model tersendiri, dan yang dipakai penyedia
identitas komersial pun masih bisa ditipu. Jadi lapisan ini menaikkan ongkos,
bukan menutup pintu, dan itu dikatakan di layar tempat ia dinyalakan.

Karena itu ia **tambahan yang dinyalakan sendiri**, bukan bawaan, dan bukan
pengganti passkey. Passkey menandatangani dengan kunci yang tidak pernah
meninggalkan perangkat dan terikat pada alamat situs ini. Wajah tidak terikat
pada apa pun: ia bisa difoto dari jauh, dan tidak bisa diganti kalau bocor.

**Yang tidak dikarang sendiri.** Deteksi, pelurusan, dan penyandiannya
seluruhnya dikerjakan `cv2.FaceDetectorYN` dan `cv2.FaceRecognizerSF`, dua API
OpenCV yang memang dibuat untuk dua model ini. Ambang 0,363 untuk kemiripan
kosinus adalah angka yang disebut penulis SFace sendiri, bukan angka yang saya
pilih. Ketepatan modelnya klaim penulisnya; yang diuji di repositori ini
sambungan di sekelilingnya, dan itu disebut apa adanya di berkas ujinya.

**Yang tidak pernah disimpan.** Fotonya. Satu pun tidak. Yang tersimpan cuma
128 angka, disandikan dengan kunci yang terpisah dari basis datanya.
"""

from __future__ import annotations

import base64
import binascii
import functools
import pathlib
import secrets

RUMAH = pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "model"
PENDETEKSI = RUMAH / "face_detection_yunet_2023mar.onnx"
PENGENAL = RUMAH / "face_recognition_sface_2021dec.onnx"

# Ambang kemiripan kosinus untuk SFace, dari penulis modelnya.
AMBANG = 0.363

# Batas gambar. Bingkai kamera 640x480 berformat JPEG mutu 0,8 sekitar 60 KB;
# dua megabita memberi ruang untuk kamera beresolusi tinggi tanpa membuka
# jalan bagi seseorang mengirimi server ini berkas 200 MB.
BATAS_BITA = 2 * 1024 * 1024
SISI_MAKS = 1600

GERAKAN = ("tengah", "kiri", "kanan")
JUMLAH_BINGKAI = 3

# Ambang arah hadap, dihitung dari posisi hidung terhadap titik tengah kedua
# mata, dibagi jarak antarmata. Nol berarti menghadap lurus. Angkanya diukur
# kasar dengan sengaja: yang dibedakan cuma "lurus", "menoleh ke satu sisi",
# dan "menoleh ke sisi lain".
AMBANG_TOLEH = 0.16


class Ditolak(Exception):
    """Bingkainya tidak memenuhi syarat, atau wajahnya tidak cocok."""


class BelumSiap(Exception):
    """Model atau pustakanya belum ada. Disebut, bukan disiasati."""


def siap() -> bool:
    """Apakah verifikasi wajah bisa dipakai sama sekali di mesin ini."""
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
    """Kedua model dimuat sekali seumur proses.

    Memuat 37 MB tiap permintaan akan membuat tiap masuk terasa seperti
    kesalahan jaringan.
    """
    if not siap():
        raise BelumSiap(_alasan_belum_siap())
    import cv2

    pendeteksi = cv2.FaceDetectorYN_create(
        str(PENDETEKSI), "", (320, 320),
        score_threshold=0.8,   # di bawah ini terlalu sering menemukan wajah di tembok
        nms_threshold=0.3,
        top_k=50,
    )
    pengenal = cv2.FaceRecognizerSF_create(str(PENGENAL), "")
    return pendeteksi, pengenal


# --------------------------------------------------------------- gambar ---


def _baca(bingkai: str):
    """base64 data URL jadi larik BGR. Menolak apa pun yang bukan gambar."""
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
    """Tepat satu wajah, bukan minimal satu.

    Dua wajah di dalam bingkai berarti tidak ada cara memastikan yang mana
    yang sedang diperiksa, dan itu cukup alasan untuk menolak alih alih
    menebak.
    """
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
    """Memperkirakan arah hadap dari lima titik penanda YuNet.

    Baris hasil YuNet: x, y, lebar, tinggi, lalu mata kanan, mata kiri,
    hidung, sudut mulut kanan, sudut mulut kiri, lalu skornya.

    Perkiraannya kasar dengan sengaja. Yang dibutuhkan cuma membedakan lurus
    dari menoleh, dan ukuran yang lebih halus akan menolak orang yang duduk
    sedikit miring.
    """
    mata_kanan = (wajah[4], wajah[5])
    mata_kiri = (wajah[6], wajah[7])
    hidung_x = wajah[8]

    tengah = (mata_kanan[0] + mata_kiri[0]) / 2
    jarak = abs(mata_kiri[0] - mata_kanan[0])
    if jarak < 1:
        raise Ditolak("wajahnya terlalu kecil di dalam bingkai")

    geser = (hidung_x - tengah) / jarak
    if geser > AMBANG_TOLEH:
        return "kanan"
    if geser < -AMBANG_TOLEH:
        return "kiri"
    return "tengah"


# ------------------------------------------------------------- mendaftar ---


def ciri_dari_bingkai(bingkai: list[str]):
    """Rata rata ciri dari beberapa bingkai.

    Dirata ratakan, bukan diambil satu, sebab satu bingkai bisa kebetulan
    berbayang, buram, atau terpotong, dan ciri dari bingkai seperti itu akan
    menolak pemiliknya sendiri di kemudian hari.
    """
    import numpy as np

    if len(bingkai) < 2:
        raise Ditolak("butuh setidaknya dua bingkai")

    semua = []
    for satu in bingkai:
        gambar = _baca(satu)
        semua.append(_ciri(gambar, _satu_wajah(gambar)))

    rata = np.mean(np.vstack(semua), axis=0, keepdims=True).astype("float32")
    # Dinormalkan supaya kemiripan kosinusnya tidak bergantung pada panjangnya.
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


# ---------------------------------------------------------- memverifikasi ---


def kemiripan(a, b) -> float:
    import cv2

    _, pengenal = _mesin()
    return float(pengenal.match(a, b, cv2.FaceRecognizerSF_FR_COSINE))


def gerakan_acak() -> list[str]:
    """Urutan yang selalu dimulai lurus, lalu dua arah dalam urutan acak.

    Dimulai lurus supaya bingkai pertama yang dipakai membandingkan wajah
    adalah bingkai yang paling mudah dikenali; menoleh mengurangi ketepatan
    pencocokan, dan menolak pemiliknya sendiri lebih sering daripada menolak
    orang lain adalah kegagalan yang paling cepat membuat fitur ini dimatikan.
    """
    sisa = ["kiri", "kanan"]
    if secrets.randbelow(2):
        sisa.reverse()
    return ["tengah", *sisa]


def periksa(bingkai: list[str], diminta: list[str], tersimpan) -> dict:
    """Memeriksa bingkai terhadap urutan gerakan dan ciri yang terdaftar.

    Mengembalikan rincian yang cukup untuk dicatat di jejak keamanan, dan
    melempar Ditolak dengan alasan yang bisa dibaca kalau ada yang tidak
    memenuhi syarat.
    """
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

    # Dinilai dari bingkai yang menghadap lurus, dan hanya kalau semuanya
    # lolos ambang. Rata rata akan membiarkan satu bingkai yang jelas bukan
    # pemiliknya tertutup oleh dua bingkai lain yang cocok.
    terendah = min(nilai)
    if terendah < AMBANG:
        raise Ditolak("wajahnya tidak cocok dengan yang terdaftar")

    return {
        "terendah": round(terendah, 4),
        "tertinggi": round(max(nilai), 4),
        "arah": arah,
    }
