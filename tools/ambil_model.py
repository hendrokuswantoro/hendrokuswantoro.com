"""Mengunduh dua model pengenalan wajah, dan mencatat sidiknya.

    python tools/ambil_model.py            # unduh
    python tools/ambil_model.py --periksa  # periksa luring, untuk CI

Dua berkas, keduanya dari opencv_zoo, keduanya Apache-2.0:

- **YuNet**, 232 KB, pendeteksi wajah. Menjawab di mana wajahnya berada dan
  lima titik penanda: dua mata, hidung, dua sudut mulut.
- **SFace**, 38,7 MB, pengenal wajah. Mengubah wajah yang sudah diluruskan
  jadi 128 angka, dan dua wajah orang yang sama menghasilkan angka yang
  berdekatan.

Kenapa diunduh, bukan disimpan di repositori: 39 MB adalah 39 MB, dan ia tidak
pernah berubah. Pola yang sama dipakai Playwright untuk peramban ujinya dan
`tools/ambil_font.py` untuk Poppins. `assets/model/` ada di .gitignore.

Kenapa dua model ini dan bukan yang lain: keduanya punya API khusus di dalam
OpenCV, yaitu `cv2.FaceDetectorYN` dan `cv2.FaceRecognizerSF`. Artinya
pemotongan, pelurusan, dan penyandiannya dikerjakan pustaka yang memang
dibuat untuk itu, bukan oleh saya yang menuliskan ulang pembacaan anchor dan
transformasi kesamaan dari makalahnya. Kode kriptografi bukan satu satunya
jenis kode yang tidak boleh dikarang sendiri.

Sidik sha256 keduanya dicatat di `assets/model/sumber.json`, dan `--periksa`
membandingkannya tanpa menyentuh jaringan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import urllib.request

AKAR = pathlib.Path(__file__).resolve().parent.parent
RUMAH = AKAR / "assets" / "model"
CATATAN = RUMAH / "sumber.json"

DASAR = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models"

MODEL = {
    "face_detection_yunet_2023mar.onnx": (
        f"{DASAR}/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    ),
    "face_recognition_sface_2021dec.onnx": (
        f"{DASAR}/face_recognition_sface/face_recognition_sface_2021dec.onnx"
    ),
}

# Berkas ONNX selalu dimulai dengan bita ini, bagian dari Protocol Buffers-nya.
# Tanpa pemeriksaan ini, halaman galat HTML dari GitHub akan tersimpan dengan
# nama .onnx dan baru ketahuan saat OpenCV menolaknya dengan pesan yang tidak
# menyinggung soal itu sama sekali.
AWALAN_ONNX = b"\x08"


def sidik(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unduh() -> list[dict]:
    RUMAH.mkdir(parents=True, exist_ok=True)
    hasil = []
    for nama, alamat in MODEL.items():
        print(f"  mengunduh {nama} ...", flush=True)
        with urllib.request.urlopen(alamat, timeout=180) as jawab:
            data = jawab.read()
        if data[:1] != AWALAN_ONNX or len(data) < 100_000:
            sys.exit(
                f"{nama} bukan berkas ONNX, {len(data)} bita. "
                "Kemungkinan yang terunduh penunjuk Git LFS atau halaman galat."
            )
        (RUMAH / nama).write_bytes(data)
        hasil.append({
            "nama": nama, "asal": alamat,
            "bita": len(data), "sha256": sidik(data),
        })
        print(f"  {nama:<38} {len(data) / 1024 / 1024:5.1f} MB")
    return hasil


def periksa() -> int:
    if not CATATAN.exists():
        print(f"GAGAL: {CATATAN.relative_to(AKAR)} tidak ada.")
        print("Jalankan: python tools/ambil_model.py")
        return 1

    catatan = json.loads(CATATAN.read_text(encoding="utf-8"))["berkas"]
    salah = []
    for e in catatan:
        jalur = RUMAH / e["nama"]
        if not jalur.exists():
            salah.append(f"hilang: {e['nama']}")
            continue
        data = jalur.read_bytes()
        if len(data) != e["bita"]:
            salah.append(f"ukuran beda: {e['nama']}")
        elif sidik(data) != e["sha256"]:
            salah.append(f"sha256 beda: {e['nama']}")

    if salah:
        for s in salah:
            print(f"GAGAL: {s}")
        print("Jalankan: python tools/ambil_model.py")
        return 1

    total = sum(e["bita"] for e in catatan)
    print(f"cocok: {len(catatan)} model, {total / 1024 / 1024:.1f} MB")
    return 0


def main() -> int:
    alasan = argparse.ArgumentParser(description=__doc__)
    alasan.add_argument("--periksa", action="store_true")
    if alasan.parse_args().periksa:
        return periksa()

    berkas = unduh()
    CATATAN.write_text(
        json.dumps(
            {
                "lisensi": "Apache-2.0, dari github.com/opencv/opencv_zoo",
                "perintah": "python tools/ambil_model.py",
                "berkas": berkas,
            },
            indent=2, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"ditulis: {len(berkas)} model dan catatannya")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
