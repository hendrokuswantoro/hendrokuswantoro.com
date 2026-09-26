-- Nomor jendela TOTP terakhir yang berhasil dipakai.
--
-- Sampai 26 September 2026 keterangan di backend/layanan/totp.py sudah
-- berjanji bahwa kode yang sudah dipakai ditolak sampai jendelanya lewat,
-- tetapi nomor jendelanya dibuang begitu saja dan tidak pernah disimpan.
-- Kode yang terlihat orang lain tetap berlaku sampai sekitar sembilan puluh
-- detik. Kolom ini yang membuat janji itu benar.

ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_langkah_terakhir BIGINT;
