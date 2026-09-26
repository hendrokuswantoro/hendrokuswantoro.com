from __future__ import annotations

import asyncio

from backend.core.catat import pasang
from backend.core.konfigurasi import pengaturan
from backend.repositori import pembersihan as repo

JEDA_DETIK = 60 * 60
TUNDA_AWAL_DETIK = 60
SIMPAN_JAM = 24


async def bersihkan() -> dict[str, int]:
    jendela = pengaturan().masuk_jendela_menit
    return await repo.hapus_yang_mati(SIMPAN_JAM, max(SIMPAN_JAM * 60, jendela * 2))


async def ulangi(jeda: float = JEDA_DETIK, tunda: float = TUNDA_AWAL_DETIK) -> None:
    await asyncio.sleep(tunda)
    while True:
        try:
            hasil = await bersihkan()
            if any(hasil.values()):
                pasang().info("pembersihan", extra={"tambahan": hasil})
        except asyncio.CancelledError:
            raise
        except Exception as galat:
            pasang().warning(
                "pembersihan gagal",
                extra={"tambahan": {"jenis": type(galat).__name__}},
            )
        await asyncio.sleep(jeda)
