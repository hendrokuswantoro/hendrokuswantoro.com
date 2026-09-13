-- Verifikasi email, kode sekali pakai, TOTP, kode pemulihan, dan jejak
-- keamanan. Bab 15.8 dan 15.10.
--
-- Sampai migrasi ini, jalan masuk ke dashboard ada dua: sandi Argon2id dan
-- passkey. Keduanya kuat, dan keduanya punya lubang yang sama bentuknya:
-- tidak ada satu pun jejak tentang apa yang terjadi pada akun itu, dan tidak
-- ada cara memastikan bahwa alamat email pemiliknya memang alamat yang ia
-- kuasai. Akun yang emailnya tidak pernah dibuktikan adalah akun yang jalur
-- pemulihannya menuju entah ke mana.
--
-- Empat hal ditambahkan di sini, dan satu aturan berlaku untuk semuanya:
-- yang disimpan hanya sidiknya, tidak pernah nilainya. Kode OTP yang tersimpan
-- apa adanya sama saja dengan sandi yang tersimpan apa adanya, hanya umurnya
-- lebih pendek. Basis data yang bocor seluruhnya tidak boleh memberi siapa pun
-- satu pun kode yang masih bisa dipakai.

-- --------------------------------------------------------------- pengguna --

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

-- Rahasia yang ada tetapi belum pernah diaktifkan adalah rahasia yang sedang
-- dipasang dan belum dibuktikan bisa dibaca perangkatnya. Yang mustahil:
-- aktif tanpa rahasia.
ALTER TABLE users
    DROP CONSTRAINT IF EXISTS totp_aktif_punya_rahasia;
ALTER TABLE users
    ADD CONSTRAINT totp_aktif_punya_rahasia
    CHECK (totp_aktif_pada IS NULL OR totp_rahasia IS NOT NULL);

-- ------------------------------------------------------- kode sekali pakai --

-- Dipakai dua hal yang bentuknya sama: tautan verifikasi email, dan kode enam
-- angka yang dikirim ke email saat masuk. Keduanya lahir, dipakai sekali, lalu
-- mati. Dijadikan satu tabel karena aturannya memang satu.
CREATE TABLE IF NOT EXISTS kode_sekali (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    tujuan          VARCHAR(20) NOT NULL,

    -- sha256 heksa. Bukan kodenya. Lihat komentar di kepala berkas ini.
    kode_hash       CHAR(64) NOT NULL,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    kadaluarsa      TIMESTAMPTZ NOT NULL,
    dipakai_pada    TIMESTAMPTZ,

    -- Tebakan yang gagal dihitung di baris kodenya sendiri, bukan per alamat
    -- IP. Penebak yang berpindah pindah IP tetap membakar jatah kode yang
    -- sama, dan kode itu mati sebelum ruang tebakannya habis.
    percobaan       SMALLINT NOT NULL DEFAULT 0,

    alamat_ringkas  VARCHAR(64),

    CONSTRAINT tujuan_dikenal CHECK (tujuan IN ('email', 'masuk')),
    CONSTRAINT kadaluarsa_sesudah_dibuat CHECK (kadaluarsa > dibuat_pada),
    CONSTRAINT percobaan_tidak_negatif CHECK (percobaan >= 0)
);

CREATE INDEX IF NOT EXISTS kode_sekali_milik
    ON kode_sekali (pengguna_id, tujuan, dipakai_pada);

-- ---------------------------------------------------------- kode pemulihan --

-- Delapan kode sekali pakai yang dicetak saat TOTP dinyalakan, dan tidak
-- pernah bisa dilihat lagi sesudah itu.
--
-- Tanpa ini, ponsel yang hilang berarti akun yang terkunci selamanya, dan akun
-- yang terkunci selamanya membuat orang mematikan faktor keduanya. Faktor
-- kedua yang dimatikan tidak menjaga apa pun.
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

-- -------------------------------------------------------- jejak keamanan ---

-- Yang membuat halaman "aktivitas terakhir" milik Google dan Meta berguna
-- bukan daftarnya, melainkan bahwa yang GAGAL pun tercatat. Masuk yang
-- berhasil hanya memberi tahu pemiliknya apa yang sudah ia lakukan; masuk yang
-- gagal memberi tahu bahwa ada orang lain sedang mencoba.
--
-- Yang TIDAK disimpan: alamat IP apa adanya. Hanya ringkasannya, digaram per
-- proses, sama seperti pembatas laju. Jejak keamanan yang berubah jadi catatan
-- lokasi pembacanya adalah jejak yang menciptakan risiko baru sambil
-- menutup yang lama.
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
