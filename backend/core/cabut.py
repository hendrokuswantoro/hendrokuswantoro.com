"""Daftar sesi yang dicabut, supaya access token ikut mati saat itu juga.

Kenapa berkas ini ada.

Access token adalah JWT: ia diperiksa dengan tanda tangannya sendiri dan
tidak pernah ditanyakan ke basis data. Itu yang membuatnya murah, dan itu
juga yang membuatnya **tidak bisa dicabut**. Mencabut sesi hanya mematikan
refresh token-nya; token akses yang sudah terlanjur terbit tetap sah sampai
lima belas menit berikutnya.

Lima belas menit terdengar pendek sampai diingat kapan tombolnya ditekan.
"Keluarkan perangkat lain" ditekan justru ketika pemiliknya curiga ada orang
lain di dalam akunnya, dan pada saat itu lima belas menit adalah waktu yang
sangat panjang.

Yang dikerjakan di sini: tiap sesi yang dicabut dicatat di Redis selama
sisa umur token akses, dan tiap permintaan memeriksa `sid` miliknya terhadap
daftar itu. Satu pembacaan Redis per permintaan, di jalur yang sudah memanggil
Redis untuk pembatas laju.

**Kalau Redis tidak ada, pencabutan segera tidak bekerja.** Itu disebut
terus terang, bukan didiamkan: `siap()` menjawab false, halaman keamanan
menampilkannya, dan tombolnya tetap mencabut refresh token seperti biasa.
Berpura pura sesi sudah mati saat ia masih hidup adalah kebohongan yang
justru membuat orang berhenti waspada.
"""

from __future__ import annotations

from backend.core.konfigurasi import pengaturan

_redis = None
_gagal = False


async def _klien():
    """Klien Redis, atau None kalau memang tidak dikonfigurasi.

    Dipakai bersama pembatas laju, tetapi dibuat sendiri di sini supaya
    kegagalan salah satunya tidak mematikan yang lain.
    """
    global _redis, _gagal
    if _gagal:
        return None
    if _redis is None:
        atur = pengaturan()
        if not atur.redis_url:
            return None
        import redis.asyncio as redis_async

        _redis = redis_async.from_url(atur.redis_url, socket_connect_timeout=2)
    return _redis


def siap() -> bool:
    """Apakah pencabutan segera bisa bekerja sama sekali."""
    return bool(pengaturan().redis_url)


def _kunci(sesi_id: str) -> str:
    return f"cabut:{sesi_id}"


def _umur_detik() -> int:
    """Selama sisa umur token akses, ditambah satu menit kelonggaran.

    Lebih lama dari itu tidak ada gunanya: token yang lebih tua dari umurnya
    sudah ditolak pemeriksa tanda tangannya sendiri.
    """
    return pengaturan().akses_umur_menit * 60 + 60


async def catat(sesi_id: list[str]) -> None:
    """Menandai sesi sesi ini dicabut.

    Kegagalan Redis tidak dilempar ke atas. Yang memanggilnya adalah jalur
    keluar dan jalur cabut, dan menggagalkan permintaan "keluar" karena cache
    sedang mati berarti menahan orang di dalam akun yang justru ingin ia
    tinggalkan. Refresh token-nya sudah mati di Postgres, dan itu bagian yang
    tidak bergantung pada Redis.
    """
    if not sesi_id:
        return
    r = await _klien()
    if r is None:
        return
    try:
        pipa = r.pipeline()
        for satu in sesi_id:
            pipa.set(_kunci(str(satu)), "1", ex=_umur_detik())
        await pipa.execute()
    except Exception:
        return


async def sudah_dicabut(sesi_id: str | None) -> bool:
    """Apakah sesi ini ada di daftar cabut.

    Menjawab False kalau Redis tidak ada atau sedang mati, dan itu arah gagal
    yang dipilih dengan sengaja. Arah sebaliknya, menolak setiap permintaan
    saat cache mati, berarti satu Redis yang tumbang mengunci pemiliknya di
    luar situsnya sendiri. Yang hilang di arah ini cuma pemendekan jendela
    lima belas menit, dan halaman keamanan menyebutkan kalau ia sedang hilang.
    """
    if not sesi_id:
        return False
    r = await _klien()
    if r is None:
        return False
    try:
        return await r.exists(_kunci(str(sesi_id))) == 1
    except Exception:
        return False
