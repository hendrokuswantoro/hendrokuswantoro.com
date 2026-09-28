-- Umur mutlak sesi dan alasan pencabutannya.
--
-- `awal` adalah saat orangnya masuk, dan ikut diwariskan setiap kali refresh
-- token diputar. Sebelum kolom ini ada, tiap putaran memberi umur baru, jadi
-- sesi yang terus dipakai tidak pernah berakhir.
--
-- `dicabut_karena` membedakan token yang dicabut karena diputar dari yang
-- dicabut karena keluar atau dikeluarkan. Hanya token yang sudah DIPUTAR lalu
-- dipakai lagi yang menandakan pencurian: pemilik sahnya sudah memegang token
-- penggantinya, jadi yang memakai token lama adalah salinan. Perangkat yang
-- dikeluarkan lalu mencoba memperpanjang bukan pencuri, dan tidak boleh
-- memicu pencabutan seluruh sesi.

ALTER TABLE sesi ADD COLUMN IF NOT EXISTS awal TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE sesi ADD COLUMN IF NOT EXISTS dicabut_karena VARCHAR(10);
ALTER TABLE sesi ADD CONSTRAINT dicabut_karena_dikenal
    CHECK (dicabut_karena IS NULL OR dicabut_karena IN ('putar', 'keluar', 'cabut', 'curi', 'lewat'));
