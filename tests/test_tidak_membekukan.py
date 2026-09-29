from __future__ import annotations

import asyncio
import re
import sys
import time

import pytest

from konftes import AKAR

sys.path.insert(0, str(AKAR))

LAYANAN = AKAR / "backend" / "layanan"

BERAT = (
    "surat.kirim",
    "wajah_modul.periksa",
    "wajah_modul.ciri_dari_bingkai",
    "keamanan.sandi_cocok",
    "keamanan.hash_sandi",
)


@pytest.mark.parametrize("nama", BERAT)
def test_kerja_berat_tidak_dipanggil_langsung_dari_async(nama):
    for berkas in LAYANAN.glob("*.py"):
        isi = berkas.read_text(encoding="utf-8")
        for cocok in re.finditer(re.escape(nama) + r"\(", isi):
            baris = isi[:cocok.start()].count("\n") + 1
            raise AssertionError(
                f"{berkas.name}:{baris} memanggil {nama} langsung. Di dalam async ia membekukan "
                "seluruh server; pakai await asyncio.to_thread(" + nama + ", ...)"
            )


def test_server_tetap_menjawab_selama_surat_dikirim(monkeypatch):
    pytest.importorskip("psycopg")
    from backend.core import surat
    from backend.layanan import kabar

    def kirim_lambat(*_a, **_k):
        time.sleep(0.6)

    monkeypatch.setattr(surat, "kirim", kirim_lambat)

    async def jalankan():
        detak = 0

        async def jam():
            nonlocal detak
            while True:
                await asyncio.sleep(0.05)
                detak += 1

        tugas = asyncio.create_task(jam())
        await kabar.kabari_perubahan_keamanan({"id": "x", "email": "a@b.c"}, "uji", paksa=True)
        tugas.cancel()
        return detak

    detak = asyncio.run(jalankan())
    assert detak >= 6, f"hanya {detak} detak selama 0,6 detik: pengiriman surat membekukan loop"
