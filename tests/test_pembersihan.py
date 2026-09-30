from __future__ import annotations

import asyncio
import os
import secrets
import sys

import pytest

from konftes import AKAR, EMAIL_UJI, ada_basis_data, loop_untuk_psycopg

sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / "tools"))

from muat_env import muat

muat()

pytest.importorskip("pydantic_settings")
pembersihan = pytest.importorskip("backend.layanan.pembersihan")

DSN = os.environ.get("DSN", "")


def test_pengulang_tidak_mati_karena_satu_putaran_gagal(monkeypatch):
    panggilan = []

    async def palsu():
        panggilan.append(1)
        if len(panggilan) == 1:
            raise RuntimeError("basis data sedang tidur")
        if len(panggilan) >= 3:
            raise asyncio.CancelledError
        return {"sesi": 0}

    monkeypatch.setattr(pembersihan, "bersihkan", palsu)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(pembersihan.ulangi(jeda=0, tunda=0))
    assert len(panggilan) == 3


def test_aplikasi_menjalankan_pembersihan_selama_hidup():
    sumber = (AKAR / "backend" / "main.py").read_text(encoding="utf-8")
    assert "pembersihan.ulangi()" in sumber
    assert "tugas.cancel()" in sumber


@pytest.mark.skipif(not ada_basis_data(DSN), reason="tidak ada basis data")
def test_yang_mati_dihapus_dan_yang_hidup_tetap():
    psycopg = pytest.importorskip("psycopg")
    from backend.core import basis_data

    tanda = secrets.token_hex(8)
    with psycopg.connect(DSN) as s, s.cursor() as k:
        k.execute("SELECT id FROM users WHERE lower(email) = lower(%s)", (EMAIL_UJI,))
        pengguna = k.fetchone()[0]

        def sesi(dibuat: str, kadaluarsa: str, dicabut: str | None) -> str:
            k.execute(
                "INSERT INTO sesi (pengguna_id, token_hash, dibuat_pada, kadaluarsa, dicabut_pada) "
                f"VALUES (%s, %s, now() - interval '{dibuat}', now() - interval '{kadaluarsa}', "
                + ("NULL" if dicabut is None else f"now() - interval '{dicabut}'")
                + ") RETURNING id",
                (pengguna, secrets.token_hex(32)),
            )
            return str(k.fetchone()[0])

        sesi_basi = sesi("40 days", "26 days", None)
        sesi_dicabut_lama = sesi("3 days", "-11 days", "2 days")
        sesi_hidup = sesi("1 hour", "-14 days", None)
        sesi_baru_dicabut = sesi("1 hour", "-14 days", "5 minutes")

        def tantangan(kadaluarsa: str) -> str:
            k.execute(
                "INSERT INTO tantangan (tujuan, nilai, dibuat_pada, kadaluarsa) "
                f"VALUES ('masuk', %s, now() - interval '{kadaluarsa}' - interval '5 minutes', "
                f"now() - interval '{kadaluarsa}') RETURNING id",
                (secrets.token_bytes(32),),
            )
            return str(k.fetchone()[0])

        tantangan_basi = tantangan("2 days")
        tantangan_segar = tantangan("1 minute")

        k.execute(
            "INSERT INTO tantangan_wajah (pengguna_id, gerakan, dibuat_pada, kadaluarsa) "
            "VALUES (%s, ARRAY['kiri','kanan'], now() - interval '3 days', "
            "now() - interval '3 days' + interval '2 minutes') RETURNING id",
            (pengguna,),
        )
        wajah_basi = str(k.fetchone()[0])

        k.execute(
            "INSERT INTO kode_sekali (pengguna_id, tujuan, kode_hash, dibuat_pada, kadaluarsa) "
            "VALUES (%s, 'email', %s, now() - interval '3 days', now() - interval '2 days') "
            "RETURNING id",
            (pengguna, secrets.token_hex(32)),
        )
        kode_basi = str(k.fetchone()[0])

        k.execute(
            "INSERT INTO gagal_masuk (email, alamat_hash, pada) VALUES "
            "(%s, %s, now() - interval '3 days'), (%s, %s, now())",
            (f"basi-{tanda}@contoh.test", "0" * 64, f"segar-{tanda}@contoh.test", "0" * 64),
        )
        s.commit()

    async def jalan():
        await basis_data.buka()
        try:
            return await pembersihan.bersihkan()
        finally:
            await basis_data.tutup()

    loop_untuk_psycopg()
    hasil = asyncio.run(jalan())
    assert hasil["sesi"] >= 2 and hasil["tantangan"] >= 1

    with psycopg.connect(DSN) as s, s.cursor() as k:
        def ada(tabel: str, nomor: str) -> bool:
            k.execute(f"SELECT 1 FROM {tabel} WHERE id = %s", (nomor,))
            return k.fetchone() is not None

        assert not ada("sesi", sesi_basi)
        assert not ada("sesi", sesi_dicabut_lama)
        assert ada("sesi", sesi_hidup)
        assert ada("sesi", sesi_baru_dicabut)
        assert not ada("tantangan", tantangan_basi)
        assert ada("tantangan", tantangan_segar)
        assert not ada("tantangan_wajah", wajah_basi)
        assert not ada("kode_sekali", kode_basi)

        k.execute("SELECT email FROM gagal_masuk WHERE email LIKE %s", (f"%{tanda}%",))
        tersisa = {b[0] for b in k.fetchall()}
        assert tersisa == {f"segar-{tanda}@contoh.test"}

        k.execute("DELETE FROM sesi WHERE id IN (%s, %s)", (sesi_hidup, sesi_baru_dicabut))
        k.execute("DELETE FROM tantangan WHERE id = %s", (tantangan_segar,))
        k.execute("DELETE FROM gagal_masuk WHERE email LIKE %s", (f"%{tanda}%",))
        s.commit()
