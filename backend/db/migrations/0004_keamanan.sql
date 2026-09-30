ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email_terverifikasi_pada TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS totp_rahasia             TEXT,
    ADD COLUMN IF NOT EXISTS totp_aktif_pada          TIMESTAMPTZ;

COMMENT ON COLUMN users.email_terverifikasi_pada IS
    'NULL berarti alamatnya belum pernah dibuktikan dikuasai pemiliknya.';

COMMENT ON COLUMN users.totp_rahasia IS
    'Rahasia TOTP, disandikan AES-256-GCM dengan kunci dari KUNCI_KOLOM, lalu '
    'base64. Rahasia TOTP yang tersimpan apa adanya adalah faktor kedua yang '
    'ikut bocor bersama basis datanya, dan faktor kedua yang bocor bersama '
    'yang pertama bukan faktor kedua.';

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS totp_aktif_punya_rahasia;
ALTER TABLE users
    ADD CONSTRAINT totp_aktif_punya_rahasia
    CHECK (totp_aktif_pada IS NULL OR totp_rahasia IS NOT NULL);

CREATE TABLE IF NOT EXISTS kode_sekali (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    tujuan          VARCHAR(20) NOT NULL,

    kode_hash       CHAR(64) NOT NULL,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    kadaluarsa      TIMESTAMPTZ NOT NULL,
    dipakai_pada    TIMESTAMPTZ,

    percobaan       SMALLINT NOT NULL DEFAULT 0,

    alamat_ringkas  VARCHAR(64),

    CONSTRAINT tujuan_dikenal CHECK (tujuan IN ('email', 'masuk')),
    CONSTRAINT kadaluarsa_sesudah_dibuat CHECK (kadaluarsa > dibuat_pada),
    CONSTRAINT percobaan_tidak_negatif CHECK (percobaan >= 0)
);

CREATE INDEX IF NOT EXISTS kode_sekali_milik
    ON kode_sekali (pengguna_id, tujuan, dipakai_pada);

CREATE TABLE IF NOT EXISTS kode_pemulihan (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kode_hash       CHAR(64) NOT NULL,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    dipakai_pada    TIMESTAMPTZ,

    CONSTRAINT kode_pemulihan_unik UNIQUE (pengguna_id, kode_hash)
);

CREATE INDEX IF NOT EXISTS kode_pemulihan_sisa
    ON kode_pemulihan (pengguna_id) WHERE dipakai_pada IS NULL;

CREATE TABLE IF NOT EXISTS peristiwa_keamanan (
    id              BIGSERIAL PRIMARY KEY,
    pengguna_id     UUID REFERENCES users(id) ON DELETE CASCADE,

    jenis           VARCHAR(40) NOT NULL,
    berhasil        BOOLEAN NOT NULL,
    keterangan      VARCHAR(200),
    alamat_ringkas  VARCHAR(64),
    peramban        VARCHAR(200),

    pada            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS peristiwa_terbaru
    ON peristiwa_keamanan (pengguna_id, pada DESC);
