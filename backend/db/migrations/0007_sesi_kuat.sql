-- Dua hal yang dicatat per sesi, dan keduanya soal jalan masuk.
--
-- 1. Apakah sesi ini lahir lewat faktor kedua.
--
-- Sampai 19 September 2026 faktor kedua sepenuhnya pilihan. Kalau pemiliknya
-- belum menyalakan TOTP, sandi saja membuka dashboard yang bisa menerbitkan
-- tulisan dan mengunggah berkas. Itu keadaan yang boleh, dan halaman
-- keamanannya memang menyebutnya terus terang, tetapi ia bukan keadaan yang
-- pantas jadi bawaan untuk permukaan tulis.
--
-- Sekarang jalur tulis menuntut sesi yang lahir lewat faktor kedua, dan
-- kolom inilah yang mencatatnya. Dicatat di sesi, bukan disimpulkan ulang
-- tiap permintaan, sebab yang benar adalah keadaan saat ia masuk: menyalakan
-- TOTP sesudah masuk tidak boleh diam diam menguatkan sesi yang sudah
-- terbit, dan mematikannya tidak boleh melemahkan sesi yang sedang berjalan.
--
-- Passkey dihitung faktor kedua dengan sendirinya. Ia menandatangani dengan
-- kunci yang tidak pernah meninggalkan perangkat dan terikat pada alamat
-- situs ini; tidak ada yang bisa ditipu untuk menyerahkannya lewat halaman
-- palsu. Menuntut TOTP di atasnya berarti menuntut faktor yang lebih lemah
-- untuk menjaga faktor yang lebih kuat.
--
-- Nilai bawaannya false, dan itu disengaja: sesi yang sudah terbit sebelum
-- migrasi ini tidak pernah membuktikan faktor kedua, jadi menandainya true
-- berarti mengarang bukti. Pemiliknya cukup masuk sekali lagi.

ALTER TABLE sesi
    ADD COLUMN IF NOT EXISTS faktor_kedua BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN sesi.faktor_kedua IS
    'Apakah sesi ini lahir lewat faktor kedua, atau lewat passkey yang '
    'dihitung setara. Jalur tulis menuntutnya benar ketika '
    'FAKTOR_KEDUA_WAJIB menyala.';

-- 2. Kapan sesi ini dicabut, dan siapa yang mencabutnya, sudah ada di
--    kolom dicabut_pada. Yang belum ada: cara mematikan access token yang
--    sudah terlanjur terbit dari sesi itu.
--
-- Access token adalah JWT dan tidak pernah ditanyakan ke basis data, jadi
-- mencabut sesi hanya mematikan refresh token-nya. Token aksesnya tetap sah
-- sampai lima belas menit berikutnya. Itu jendela yang pendek dan tetap
-- nyata: tombol "keluarkan perangkat lain" ditekan justru ketika orangnya
-- curiga, dan lima belas menit adalah waktu yang panjang untuk dicurigai.
--
-- Yang menutupnya bukan kolom baru melainkan daftar cabut di Redis, dan
-- token membawa `sid` berisi id sesi ini. Lihat backend/core/cabut.py.
-- Indeks di bawah dipakai membersihkan daftar itu, dan tidak lebih.
CREATE INDEX IF NOT EXISTS sesi_dicabut ON sesi (dicabut_pada)
    WHERE dicabut_pada IS NOT NULL;
