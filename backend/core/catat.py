"""Log terstruktur JSON. Bab 15.17.

Satu baris JSON per permintaan: waktu, metode, jalur, status, lama.

Yang tidak pernah ikut: kata sandi, token, kunci API, rahasia, dan data
pribadi. Karena itu yang dicatat hanya jalur tanpa query string. Query string
adalah tempat rahasia paling sering bocor ke log tanpa ada yang berniat.
"""

from __future__ import annotations

import json
import logging
import sys
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class Json(logging.Formatter):
    def format(self, rekaman: logging.LogRecord) -> str:
        badan = {
            "waktu": self.formatTime(rekaman, "%Y-%m-%dT%H:%M:%S%z"),
            "tingkat": rekaman.levelname.lower(),
            "pesan": rekaman.getMessage(),
        }
        badan.update(getattr(rekaman, "tambahan", {}) or {})
        return json.dumps(badan, ensure_ascii=False)


def pasang() -> logging.Logger:
    pencatat = logging.getLogger("hk")
    if pencatat.handlers:
        return pencatat
    saluran = logging.StreamHandler(sys.stdout)
    saluran.setFormatter(Json())
    pencatat.addHandler(saluran)
    pencatat.setLevel(logging.INFO)
    pencatat.propagate = False
    return pencatat


class CatatPermintaan(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.pencatat = pasang()

    async def dispatch(self, permintaan: Request, lanjut):
        mulai = time.perf_counter()
        jawaban = await lanjut(permintaan)
        lama_ms = round((time.perf_counter() - mulai) * 1000, 1)

        self.pencatat.info(
            "permintaan",
            extra={"tambahan": {
                "metode": permintaan.method,
                # tanpa query string, di situlah rahasia paling sering bocor
                "jalur": permintaan.url.path,
                "status": jawaban.status_code,
                "lama_ms": lama_ms,
            }},
        )
        jawaban.headers["X-Lama-Ms"] = str(lama_ms)
        return jawaban
