-- Verifikasi wajah sebagai faktor kedua.
--
-- Sebelum apa pun yang lain, apa yang lapisan ini bisa dan tidak bisa
-- kerjakan, supaya tidak ada yang menganggapnya lebih kuat daripada yang
-- sebenarnya. Hal yang sama ditulis di layar tempat ia dinyalakan.
--
-- BISA  : menaikkan ongkos masuk bagi orang yang sudah tahu kata sandinya.
--         Ia harus hadir di depan kamera dengan wajah yang cocok, mengikuti
--         urutan gerakan yang baru diminta server saat itu juga.
-- TIDAK : menghentikan orang yang punya rekaman video wajah pemiliknya.
--         Pencocokan wajah bukan pembuktian kehadiran, dan urutan gerakan
--         hanya menyulitkan, bukan menutup.
-- TIDAK : menggantikan passkey. Passkey menandatangani dengan kunci yang
--         tidak pernah meninggalkan perangkat dan terikat pada alamat situs
--         ini; wajah tidak terikat pada apa pun.
--
-- Karena itu ia ditawarkan sebagai tambahan yang dinyalakan sendiri, bukan
-- sebagai bawaan, dan bukan sebagai pengganti apa pun yang sudah ada.
--
-- Yang disimpan dan yang tidak:
--
--   disimpan      : 128 angka hasil penyandian wajah, disandikan AES-256-GCM
--                   dengan kunci dari KUNCI_KOLOM, sama seperti rahasia TOTP
--   TIDAK disimpan: fotonya. Satu pun tidak, tidak saat mendaftar dan tidak
--                   saat masuk. Gambar yang tidak pernah tersimpan adalah
--                   gambar yang tidak bisa bocor.
--
-- UU 27/2022 menggolongkan data biometrik sebagai data pribadi yang bersifat
-- spesifik. Pemilik akun ini adalah subjek datanya sendiri, ia yang memilih
-- menyalakannya, dan ia bisa menghapusnya kapan saja lewat satu tombol yang
-- benar benar menghapus barisnya, bukan menandainya nonaktif.

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

-- ----------------------------------------------------------- tantangan ---

-- Urutan gerakan diputuskan server, bukan klien, dan hanya berlaku sekali.
--
-- Tanpa ini, "kirim tiga foto wajah Anda" bisa dijawab dengan tiga berkas yang
-- sudah disiapkan sejak lama. Dengan ini, tiga berkas itu harus kebetulan
-- memuat urutan gerakan yang baru saja diminta, dan urutannya berganti tiap
-- kali. Itu menyulitkan, dan perlu dikatakan terus terang bahwa menyulitkan
-- bukan menutup: rekaman video yang cukup panjang tetap memuat semuanya.
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
