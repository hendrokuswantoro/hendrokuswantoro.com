-- Setelan keamanan yang dipilih pemilik akun sendiri.
--
-- kabar_masuk dan kabar_perubahan menentukan surat pemberitahuan mana yang
-- dikirim. Mematikan salah satunya selalu dikabarkan lewat surat, apa pun
-- setelannya, supaya orang yang mengambil alih akun tidak bisa membungkam
-- pemiliknya dengan diam diam.
--
-- mode_ketat menutup cara masuk yang lemah: wajah tidak lagi diterima
-- sebagai faktor kedua selama akun punya authenticator atau passkey.

ALTER TABLE users ADD COLUMN IF NOT EXISTS kabar_masuk BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabar_perubahan BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mode_ketat BOOLEAN NOT NULL DEFAULT false;

-- Tantangan WebAuthn untuk membuka kunci layar dashboard. Selalu atas nama
-- orang yang sedang masuk, jadi pengguna_id wajib ada.
ALTER TABLE tantangan DROP CONSTRAINT IF EXISTS tujuan_dikenal;
ALTER TABLE tantangan ADD CONSTRAINT tujuan_dikenal
    CHECK (tujuan IN ('daftar', 'masuk', 'buka'));
ALTER TABLE tantangan ADD CONSTRAINT buka_punya_pengguna
    CHECK (tujuan <> 'buka' OR pengguna_id IS NOT NULL);
