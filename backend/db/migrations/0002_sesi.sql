CREATE TABLE sesi (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      CHAR(64) UNIQUE NOT NULL,
    kadaluarsa      TIMESTAMPTZ NOT NULL,
    dicabut_pada    TIMESTAMPTZ,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT kadaluarsa_di_masa_depan CHECK (kadaluarsa > dibuat_pada)
);

CREATE INDEX idx_sesi_pengguna ON sesi (pengguna_id) WHERE dicabut_pada IS NULL;
CREATE INDEX idx_sesi_kadaluarsa ON sesi (kadaluarsa);

COMMENT ON COLUMN sesi.token_hash IS
    'SHA-256 dari refresh token. Tokennya sendiri tidak pernah disimpan.';

CREATE TABLE gagal_masuk (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    alamat_hash     CHAR(64) NOT NULL,
    pada            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_gagal_masuk_waktu ON gagal_masuk (email, pada DESC);
