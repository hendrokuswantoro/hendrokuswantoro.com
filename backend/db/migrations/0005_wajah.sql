ALTER TABLE users
    ADD COLUMN IF NOT EXISTS wajah_ciri          TEXT,
    ADD COLUMN IF NOT EXISTS wajah_didaftar_pada TIMESTAMPTZ;

COMMENT ON COLUMN users.wajah_ciri IS
    '128 angka float32, dirata ratakan dari beberapa bingkai, disandikan '
    'AES-256-GCM lalu base64. Bukan foto, dan tidak bisa dikembalikan jadi '
    'foto. Tetap data biometrik, dan tetap disandikan.';

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS wajah_punya_waktu;
ALTER TABLE users
    ADD CONSTRAINT wajah_punya_waktu
    CHECK ((wajah_ciri IS NULL) = (wajah_didaftar_pada IS NULL));

CREATE TABLE IF NOT EXISTS tantangan_wajah (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    gerakan         TEXT[] NOT NULL,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    kadaluarsa      TIMESTAMPTZ NOT NULL,
    dipakai_pada    TIMESTAMPTZ,

    CONSTRAINT gerakan_tidak_kosong CHECK (array_length(gerakan, 1) BETWEEN 2 AND 5),
    CONSTRAINT tantangan_wajah_kadaluarsa CHECK (kadaluarsa > dibuat_pada)
);

CREATE INDEX IF NOT EXISTS tantangan_wajah_milik
    ON tantangan_wajah (pengguna_id, dipakai_pada);
