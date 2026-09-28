from __future__ import annotations

import base64
import hashlib
import re

DASAR = (
    "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
    "img-src 'self' data: blob:; style-src 'self'; font-src 'self'; script-src 'self' blob:{hash}; "
    "worker-src 'self' blob:; child-src blob:; frame-src 'none'; connect-src 'self'; "
    "object-src 'none'; upgrade-insecure-requests"
)

SKRIP_SEBARIS = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)


def hash_sebaris(html: str) -> list[str]:
    hasil: list[str] = []
    for isi in SKRIP_SEBARIS.findall(html):
        sidik = base64.b64encode(hashlib.sha256(isi.encode("utf-8")).digest()).decode("ascii")
        nilai = f"'sha256-{sidik}'"
        if nilai not in hasil:
            hasil.append(nilai)
    return hasil


def kebijakan(html: str = "") -> str:
    return DASAR.format(hash="".join(" " + h for h in hash_sebaris(html)))
