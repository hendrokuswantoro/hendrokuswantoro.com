ALTER TABLE sesi ADD COLUMN IF NOT EXISTS awal TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE sesi ADD COLUMN IF NOT EXISTS dicabut_karena VARCHAR(10);
ALTER TABLE sesi ADD CONSTRAINT dicabut_karena_dikenal
    CHECK (dicabut_karena IS NULL OR dicabut_karena IN ('putar', 'keluar', 'cabut', 'curi', 'lewat'));
