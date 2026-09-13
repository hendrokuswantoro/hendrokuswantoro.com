"""Memeriksa berkas alur kerja GitHub Actions sebelum ia dijalankan di sana.

    python tools/periksa_alur.py

Tiga hal, dan ketiganya pernah benar benar lolos sampai ke cabang main:

1. YAML-nya sah. Alur yang tidak bisa diparse tidak berjalan sama sekali, dan
   GitHub tidak memberi tahu apa pun selain bahwa tidak ada yang jalan.
2. Setiap blok `run` lolos `bash -n`. Satu bita carriage return pernah
   menyelundup ke dalam skrip dan membuat `sh -n` gagal di runner sementara
   lolos di mesin pengembangan.
3. Tidak ada "\\n" harfiah di luar printf, echo, atau sed.

Butir ketiga yang paling mahal. `kesehatan.yml` pernah memuat:

    for jalur in / /about \\n                   /blog/ ...

"\\n" di situ bukan baris baru, melainkan dua karakter yang dibaca shell
sebagai satu kata bernilai "n". Jadi pemeriksaan kesehatan meminta
`$situs/n`, dijawab 404, dan gagal tiap malam selama berhari hari sambil
membuka isu otomatis yang menyatakan situsnya mati. Situsnya sehat sepanjang
waktu itu. Pemeriksaan yang berbohong lebih buruk daripada tidak ada
pemeriksaan, dan `bash -n` tidak bisa menolongnya: sintaksnya sah sempurna.

Komentar di dalam blok run tidak diperiksa butir ketiga. Komentar memang
tempat menjelaskan kesalahan yang sudah lewat, dan aturan yang menghukum
penjelasan akan menghapus penjelasannya, bukan kesalahannya.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:  # pragma: no cover - hanya saat pyyaml belum terpasang
    sys.exit("pyyaml belum terpasang. Jalankan: pip install pyyaml")

AKAR = pathlib.Path(__file__).resolve().parent.parent
ALUR = AKAR / ".github" / "workflows"

# Di sini "\n" memang berarti baris baru, jadi tidak dilarang.
BOLEH = ("printf", "echo", "sed", "awk", "tr", "python", "node", "join(")


def _bash() -> str | None:
    """Bash yang bisa membaca jalur Windows.

    Di Windows, `bash` di PATH sering menunjuk WSL, yang tidak bisa membuka
    berkas sementara milik Windows dan gagal dengan pesan yang tidak
    menyinggung soal itu sama sekali.
    """
    for calon in (r"C:\Program Files\Git\usr\bin\bash.exe", "/bin/bash"):
        if pathlib.Path(calon).exists():
            return calon
    return shutil.which("bash")


def blok_run(berkas: pathlib.Path) -> list[tuple[str, str]]:
    isi = yaml.safe_load(berkas.read_text(encoding="utf-8"))
    hasil = []
    for nama_job, job in (isi.get("jobs") or {}).items():
        for langkah in job.get("steps", []):
            skrip = langkah.get("run")
            if skrip:
                hasil.append((f"{nama_job} / {langkah.get('name') or 'tanpa nama'}", skrip))
    return hasil


def periksa_sintaks(bash: str, nama: str, skrip: str) -> list[str]:
    # Ekspresi ${{ }} milik GitHub bukan sintaks shell; diganti satu kata.
    bersih = re.sub(r"\$\{\{[^}]*\}\}", "X", skrip)
    sementara = pathlib.Path(tempfile.mkdtemp()) / "langkah.sh"
    sementara.write_text(bersih, encoding="utf-8", newline="\n")
    hasil = subprocess.run([bash, "-n", str(sementara)], capture_output=True, text=True)
    if hasil.returncode:
        return [f"{nama}: bash menolak sintaksnya\n{hasil.stderr.strip()}"]
    return []


def periksa_garis_miring(nama: str, skrip: str) -> list[str]:
    salah = []
    for nomor, baris in enumerate(skrip.splitlines(), 1):
        bersih = baris.strip()
        if bersih.startswith("#") or "\\n" not in bersih:
            continue
        if any(kata in bersih for kata in BOLEH):
            continue
        salah.append(
            f'{nama}, baris {nomor}: "\\n" harfiah di luar printf.\n'
            f"    {bersih}\n"
            "    Shell membacanya sebagai kata bernilai n, bukan baris baru.\n"
            "    Tulis daftarnya dengan here-doc, satu baris satu nilai."
        )
    return salah


def main() -> int:
    bash = _bash()
    if bash is None:
        print("lewat: bash tidak ditemukan, pemeriksaan sintaks tidak dijalankan")

    salah: list[str] = []
    jumlah = 0
    for berkas in sorted(ALUR.glob("*.yml")):
        try:
            langkah = blok_run(berkas)
        except yaml.YAMLError as g:
            salah.append(f"{berkas.name}: YAML tidak sah\n{g}")
            continue

        for nama, skrip in langkah:
            jumlah += 1
            penuh = f"{berkas.name} / {nama}"
            if bash:
                salah += periksa_sintaks(bash, penuh, skrip)
            salah += periksa_garis_miring(penuh, skrip)

        print(f"ok  {berkas.name}: YAML sah, {len(langkah)} blok run")

    if salah:
        print()
        for s in salah:
            print(f"GAGAL {s}")
        return 1

    print(f"\n{jumlah} blok run diperiksa, semuanya lolos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
