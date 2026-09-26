-- Pengguna basis data untuk aplikasi, dengan hak sekecil yang masih cukup.
--
--     psql "$DSN_PEMILIK" -f infrastructure/postgres/hak_terkecil.sql
--
-- Kenapa berkas ini ada.
--
-- Sampai 19 September 2026 aplikasi terhubung sebagai pemilik skemanya
-- sendiri. Pemilik skema boleh DROP TABLE. Artinya satu injeksi SQL yang
-- lolos, atau satu kekeliruan di lapisan repositori, bisa menghapus seluruh
-- basis data alih alih merusak satu baris.
--
-- Injeksi SQL sendiri sudah dijaga: seluruh kueri berparameter, dan
-- tests/test_api.py menolak SQL di luar lapisan repositori. Berkas ini bukan
-- pengganti penjagaan itu. Ia lapis kedua, dan gunanya justru pada hari lapis
-- pertama ternyata bocor. Yang membedakan gangguan dari bencana biasanya
-- bukan apakah ada yang masuk, melainkan seberapa jauh ia bisa melangkah.
--
-- Yang TIDAK dipunyai hk_app:
--
--   CREATE, DROP, ALTER   migrasi dijalankan pengguna lain, yaitu pemiliknya
--   TRUNCATE              menghapus seluruh tabel dalam satu perintah
--   hak atas tabel baru   kecuali diberikan lagi, sengaja, lihat catatan bawah
--
-- Yang dipunyainya: SELECT, INSERT, UPDATE, DELETE pada tabel yang sudah ada,
-- dan USAGE pada urutan BIGSERIAL. Itu seluruh yang dibutuhkan aplikasinya.

\set ON_ERROR_STOP on

-- Sandinya TIDAK ditulis di sini. Ia datang dari luar, dan berkas ini masuk
-- git. Jalankan dengan:
--
--     PGPASSWORD_APP='...' psql -v sandi_app="'$PGPASSWORD_APP'" -f ...
--
-- Tanda kutip tunggal di dalam -v memang perlu: psql menyisipkan nilainya apa
-- adanya, jadi tanpa kutip ia jadi pengenal, bukan teks.
\if :{?sandi_app}
\else
\echo 'Jalankan dengan -v sandi_app="''...''". Sandi tidak pernah ditulis di berkas ini.'
\quit 1
\endif

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hk_app') THEN
        CREATE ROLE hk_app LOGIN;
    END IF;
END
$$;

ALTER ROLE hk_app WITH PASSWORD :sandi_app;

-- Tidak boleh membuat apa pun di dalam skema, termasuk tabel sementara yang
-- dipakai sebagian teknik injeksi untuk menampung hasil curiannya.
REVOKE ALL ON SCHEMA public FROM hk_app;
GRANT USAGE ON SCHEMA public TO hk_app;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM hk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hk_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hk_app;

-- Tabel yang dibuat migrasi BERIKUTNYA tidak otomatis ikut.
--
-- Ini disengaja, dan arah gagalnya dipilih: migrasi baru yang lupa memberi
-- hak akan membuat aplikasinya menjawab galat izin dengan jelas, sekali,
-- saat pertama kali menyentuh tabel itu. Kebalikannya, memberi hak otomatis
-- ke segala yang akan dibuat, berarti satu tabel yang seharusnya tertutup
-- ikut terbuka tanpa ada yang menyadarinya.
--
-- Jadi sesudah tiap migrasi yang membuat tabel, jalankan ulang berkas ini.
-- tools/verifikasi.sh tidak bisa memeriksanya; yang memeriksa adalah galat
-- izin yang muncul pada percobaan pertama.

-- Migrasi tetap dijalankan pemiliknya, bukan hk_app:
--
--     DSN=postgresql://hendro:...@host/db  python backend/db/migrasi.py
--
-- dan aplikasinya jalan sebagai hk_app:
--
--     DSN=postgresql://hk_app:...@host/db  python backend/jalan.py
--
-- Dua DSN yang berbeda untuk dua pekerjaan yang berbeda. Satu DSN untuk
-- keduanya berarti hak paling besar dipakai sepanjang waktu demi pekerjaan
-- yang berlangsung beberapa detik sebulan sekali.
