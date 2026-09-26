from __future__ import annotations

from backend.core.basis_data import koneksi

_PERINTAH = {
    "sesi": (
        "DELETE FROM sesi "
        "WHERE kadaluarsa < now() - make_interval(hours => %(jam)s) "
        "   OR dicabut_pada < now() - make_interval(hours => %(jam)s)"
    ),
    "tantangan": "DELETE FROM tantangan WHERE kadaluarsa < now() - make_interval(hours => %(jam)s)",
    "tantangan_wajah": (
        "DELETE FROM tantangan_wajah WHERE kadaluarsa < now() - make_interval(hours => %(jam)s)"
    ),
    "kode_sekali": "DELETE FROM kode_sekali WHERE kadaluarsa < now() - make_interval(hours => %(jam)s)",
    "gagal_masuk": "DELETE FROM gagal_masuk WHERE pada < now() - make_interval(mins => %(menit)s)",
}


async def hapus_yang_mati(jam: int, menit_gagal: int) -> dict[str, int]:
    hasil: dict[str, int] = {}
    async with koneksi() as s, s.cursor() as k:
        for tabel, perintah in _PERINTAH.items():
            await k.execute(perintah, {"jam": jam, "menit": menit_gagal})
            hasil[tabel] = k.rowcount
    return hasil
