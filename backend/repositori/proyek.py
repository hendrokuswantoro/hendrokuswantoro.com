"""SQL untuk proyek, termasuk yang spasial.

ST_AsGeoJSON dikerjakan di basis data, bukan di Python. Itu bukan soal
kerapian: PostGIS menulis GeoJSON yang benar menurut RFC 7946 termasuk
urutan sumbu, sedangkan merakitnya sendiri di Python adalah cara klasik
menukar bujur dengan lintang tanpa ada yang sadar sampai peta menggambar
Indonesia di Somalia.
"""

from __future__ import annotations

from typing import Any

from backend.core.basis_data import koneksi

KOLOM = """
    slug, urut,
    judul_en, judul_id, ringkas_en, ringkas_id,
    peran_en, peran_id, badge_en, badge_id,
    -- ENUM buatan tidak dikenal psycopg, jadi kembali sebagai string mentah
    -- '{app}' dan Pydantic mengurainya huruf per huruf. Dicor ke text di sini,
    -- di satu satunya lapisan yang memang tahu SQL.
    kategori::text[] AS kategori,
    jenis_peta::text AS jenis_peta,
    teknologi,
    gambar, gambar_alt_en, gambar_alt_id,
    ST_X(geom) AS lng, ST_Y(geom) AS lat
"""


async def jumlah(kategori: str | None = None) -> int:
    async with koneksi() as s, s.cursor() as k:
        if kategori:
            await k.execute(
                "SELECT count(*) AS n FROM projects WHERE %s = ANY(kategori)",
                (kategori,),
            )
        else:
            await k.execute("SELECT count(*) AS n FROM projects")
        return (await k.fetchone())["n"]


async def daftar(batas: int, lewati: int, kategori: str | None = None) -> list[dict[str, Any]]:
    async with koneksi() as s, s.cursor() as k:
        if kategori:
            await k.execute(
                f"SELECT {KOLOM} FROM projects WHERE %s = ANY(kategori) "
                "ORDER BY urut LIMIT %s OFFSET %s",
                (kategori, batas, lewati),
            )
        else:
            await k.execute(
                f"SELECT {KOLOM} FROM projects ORDER BY urut LIMIT %s OFFSET %s",
                (batas, lewati),
            )
        return await k.fetchall()


async def satu(slug: str) -> dict[str, Any] | None:
    async with koneksi() as s, s.cursor() as k:
        await k.execute(f"SELECT {KOLOM} FROM projects WHERE slug = %s", (slug,))
        return await k.fetchone()


async def geojson() -> dict[str, Any]:
    """FeatureCollection dirakit PostGIS, bukan Python."""
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', coalesce(json_agg(f ORDER BY f->'properties'->>'slug'), '[]'::json)
            ) AS geo
            FROM (
                SELECT json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geom)::json,
                    'properties', json_build_object(
                        'slug', slug,
                        'judul', json_build_object('en', judul_en, 'id', judul_id),
                        'kategori', kategori,
                        'jenis_peta', jenis_peta,
                        'teknologi', teknologi
                    )
                ) AS f
                FROM projects
                ORDER BY urut
            ) t
            """
        )
        return (await k.fetchone())["geo"]


async def dekat(lng: float, lat: float, meter: int, batas: int) -> list[dict[str, Any]]:
    """Jarak dihitung di geography, jadi satuannya meter dan bukan derajat.

    Derajat bukan satuan jarak: satu derajat bujur di Sabang dan di Merauke
    panjangnya berbeda, dan menghitung radius dengan derajat menghasilkan
    lingkaran yang bentuknya berubah ubah menurut lintang.
    """
    async with koneksi() as s, s.cursor() as k:
        await k.execute(
            f"""
            SELECT {KOLOM},
                   round(ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                   ))::int AS jarak_m
            FROM projects
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s)
            ORDER BY jarak_m
            LIMIT %s
            """,
            (lng, lat, lng, lat, meter, batas),
        )
        return await k.fetchall()
