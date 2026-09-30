from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    sys.exit("pyyaml belum terpasang. Jalankan: pip install pyyaml")

AKAR = pathlib.Path(__file__).resolve().parent.parent
ALUR = AKAR / ".github" / "workflows"

BOLEH = ("printf", "echo", "sed", "awk", "tr", "python", "node", "join(")


def _bash() -> str | None:
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
