CREATE TABLE IF NOT EXISTS berkas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    nama            VARCHAR(200) NOT NULL UNIQUE,

    nama_asal       VARCHAR(255) NOT NULL,

    jenis           VARCHAR(10) NOT NULL,
    tipe_mime       VARCHAR(100) NOT NULL,
    bita            BIGINT NOT NULL,

    lebar           INTEGER,
    tinggi          INTEGER,

    sidik           CHAR(64) NOT NULL UNIQUE,

    pengunggah_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT berkas_jenis_dikenal CHECK (jenis IN ('gambar', 'video')),
    CONSTRAINT berkas_tidak_kosong CHECK (bita > 0),
    CONSTRAINT berkas_ukuran_gambar CHECK (
        (jenis = 'gambar' AND lebar > 0 AND tinggi > 0)
        OR (jenis = 'video' AND lebar IS NULL AND tinggi IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS berkas_terbaru ON berkas (dibuat_pada DESC);

COMMENT ON TABLE berkas IS
    'Catatan foto dan video yang diunggah lewat dashboard. Berkasnya sendiri '
    'ada di cakram, di folder yang disebut UNGGAHAN_DIR, dan dilayani sebagai '
    'berkas statis di /unggahan/.';

COMMENT ON COLUMN berkas.nama_asal IS
    'Nama yang dikirim pengunggah. Hanya untuk dilihat orang, tidak pernah '
    'dipakai membentuk jalur berkas.';
