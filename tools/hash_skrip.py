from __future__ import annotations

import base64
import hashlib
import pathlib
import re
import sys

AKAR = pathlib.Path(__file__).resolve().parent.parent
HALAMAN = AKAR / "index.html"
KEPALA = AKAR / "_headers"

SEBARIS = re.compile(r"<script>(?!</script>)(.*?)</script>", re.DOTALL)


def skrip_sebaris(berkas: pathlib.Path) -> list[str]:
    return SEBARIS.findall(berkas.read_text(encoding="utf-8"))


def hash_csp(isi: str) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(isi.encode("utf-8")).digest()).decode()


def hash_terpasang() -> set[str]:
    return set(re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", KEPALA.read_text(encoding="utf-8")))


def periksa() -> int:
    diharapkan = {hash_csp(s) for s in skrip_sebaris(HALAMAN)}
    terpasang = hash_terpasang()

    for isi in skrip_sebaris(HALAMAN):
        print(f"  {hash_csp(isi)}  {isi[:60]}...")

    kurang = diharapkan - terpasang
    lebih = terpasang - diharapkan

    if kurang:
        print("\nHash berikut ada di halaman tetapi tidak di _headers:")
        for h in sorted(kurang):
            print(f"  '{h}'")
    if lebih:
        print("\nHash berikut ada di _headers tetapi tidak dipakai halaman mana pun:")
        for h in sorted(lebih):
            print(f"  '{h}'")

    if kurang or lebih:
        return 1
    print(f"\ncocok: {len(diharapkan)} skrip sebaris, {len(terpasang)} hash di _headers")
    return 0


if __name__ == "__main__":
    sys.exit(periksa())
