-- Skema awal.
--
-- Dua keputusan yang tidak ada di spesifikasi mana pun dan dirancang di sini,
-- alasannya di docs/rancangan-platform.md bagian 6:
--
--   1. Situs ini dwibahasa. Tiap kolom teks berpasangan dan NOT NULL,
--      bukan tabel terjemahan. Dua bahasa, keduanya selalu wajib, tidak akan
--      bertambah. Dengan begini "tulisan tanpa terjemahan" mustahil, bukan
--      sekadar tidak dianjurkan.
--
--   2. Keadaan yang mustahil dibuat mustahil oleh basis datanya, bukan
--      diingat oleh kodenya. Tulisan berstatus terbit tanpa tanggal terbit
--      akan merusak urutan umpan RSS tanpa galat apa pun.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- --------------------------------------------------------------- pengguna --

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    nama            VARCHAR(100) NOT NULL,
    peran           VARCHAR(20) NOT NULL DEFAULT 'admin',
    sandi_hash      VARCHAR(255),
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT peran_dikenal CHECK (peran IN ('admin', 'visitor')),
    CONSTRAINT email_masuk_akal CHECK (position('@' IN email) > 1)
);

COMMENT ON COLUMN users.sandi_hash IS
    'Argon2id. Boleh NULL: passkey adalah jalur masuk utama, kata sandi cadangan.';

-- ------------------------------------------------------------------ blog --

CREATE TYPE status_terbit AS ENUM ('draf', 'terbit', 'arsip');

CREATE TABLE blog_posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(150) UNIQUE NOT NULL,

    judul_en        VARCHAR(200) NOT NULL,
    judul_id        VARCHAR(200) NOT NULL,
    ringkas_en      VARCHAR(300) NOT NULL,
    ringkas_id      VARCHAR(300) NOT NULL,
    keterangan_en   VARCHAR(300) NOT NULL,
    keterangan_id   VARCHAR(300) NOT NULL,
    lede_en         TEXT NOT NULL,
    lede_id         TEXT NOT NULL,
    isi_en          TEXT NOT NULL,
    isi_id          TEXT NOT NULL,

    tag_en          VARCHAR(50) NOT NULL,
    tag_id          VARCHAR(50) NOT NULL,
    baca_en         VARCHAR(30) NOT NULL,
    baca_id         VARCHAR(30) NOT NULL,

    status          status_terbit NOT NULL DEFAULT 'draf',
    terbit_pada     DATE,
    penulis_id      UUID REFERENCES users(id) ON DELETE RESTRICT,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    diubah_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT terbit_punya_tanggal
        CHECK (status <> 'terbit' OR terbit_pada IS NOT NULL),
    CONSTRAINT slug_bentuknya_benar
        CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$')
);

CREATE INDEX idx_blog_terbit  ON blog_posts (status, terbit_pada DESC);
CREATE INDEX idx_blog_cari_en ON blog_posts USING GIN (judul_en gin_trgm_ops);
CREATE INDEX idx_blog_cari_id ON blog_posts USING GIN (judul_id gin_trgm_ops);

-- ---------------------------------------------------------------- proyek --

CREATE TYPE kategori_proyek AS ENUM ('app', 'analysis', 'satellite', 'design');

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(150) UNIQUE NOT NULL,
    urut            SMALLINT NOT NULL,

    judul_en        VARCHAR(200) NOT NULL,
    judul_id        VARCHAR(200) NOT NULL,
    ringkas_en      TEXT NOT NULL,
    ringkas_id      TEXT NOT NULL,
    peran_en        VARCHAR(200) NOT NULL,
    peran_id        VARCHAR(200) NOT NULL,
    badge_en        VARCHAR(50) NOT NULL,
    badge_id        VARCHAR(50) NOT NULL,

    kategori        kategori_proyek[] NOT NULL,
    jenis_peta      kategori_proyek NOT NULL,
    teknologi       TEXT[] NOT NULL,

    gambar          VARCHAR(255) NOT NULL,
    gambar_alt_en   VARCHAR(300) NOT NULL,
    gambar_alt_id   VARCHAR(300) NOT NULL,

    geom            GEOMETRY(Point, 4326) NOT NULL,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT kategori_tidak_kosong CHECK (cardinality(kategori) > 0),
    CONSTRAINT teknologi_tidak_kosong CHECK (cardinality(teknologi) > 0),
    CONSTRAINT slug_bentuknya_benar CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    -- salinan uji yang sudah ada di tests/test_peta.py, ditaruh di tempat
    -- yang tidak bisa dilewati
    CONSTRAINT titik_di_indonesia CHECK (
        ST_X(geom) BETWEEN 94 AND 142 AND ST_Y(geom) BETWEEN -12 AND 7
    )
);

CREATE INDEX idx_projects_geom ON projects USING GIST (geom);
CREATE INDEX idx_projects_kategori ON projects USING GIN (kategori);
CREATE UNIQUE INDEX idx_projects_urut ON projects (urut);

COMMENT ON COLUMN projects.geom IS
    'Titik untuk menggantungkan penanda di peta. BUKAN koordinat survei dan '
    'BUKAN batas wilayah kajian. Keterangan yang sama tercetak di bawah peta.';

-- -------------------------------------------------------- lapisan spasial --

CREATE TABLE spatial_layers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nama            VARCHAR(100) NOT NULL,
    jenis           VARCHAR(30) NOT NULL,
    geom            GEOMETRY(Geometry, 4326) NOT NULL,
    sifat           JSONB NOT NULL DEFAULT '{}'::jsonb,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_spatial_layers_geom ON spatial_layers USING GIST (geom);

-- -------------------------------------------------------------- pengaturan --

CREATE TABLE settings (
    kunci           VARCHAR(60) PRIMARY KEY,
    nilai           TEXT NOT NULL,
    diubah_pada     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------- pemicu ----

CREATE OR REPLACE FUNCTION sentuh_diubah_pada() RETURNS TRIGGER AS $$
BEGIN
    NEW.diubah_pada = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER blog_diubah
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION sentuh_diubah_pada();
