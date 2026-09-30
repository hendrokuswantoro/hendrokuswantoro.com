ALTER TABLE users ADD COLUMN IF NOT EXISTS kabar_masuk BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabar_perubahan BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mode_ketat BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE tantangan DROP CONSTRAINT IF EXISTS tujuan_dikenal;
ALTER TABLE tantangan ADD CONSTRAINT tujuan_dikenal
    CHECK (tujuan IN ('daftar', 'masuk', 'buka'));
ALTER TABLE tantangan ADD CONSTRAINT buka_punya_pengguna
    CHECK (tujuan <> 'buka' OR pengguna_id IS NOT NULL);
