ALTER TABLE sesi
    ADD COLUMN IF NOT EXISTS faktor_kedua BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN sesi.faktor_kedua IS
    'Apakah sesi ini lahir lewat faktor kedua, atau lewat passkey yang '
    'dihitung setara. Jalur tulis menuntutnya benar ketika '
    'FAKTOR_KEDUA_WAJIB menyala.';

CREATE INDEX IF NOT EXISTS sesi_dicabut ON sesi (dicabut_pada)
    WHERE dicabut_pada IS NOT NULL;
