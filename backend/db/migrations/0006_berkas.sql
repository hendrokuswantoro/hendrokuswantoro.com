-- Foto dan video yang diunggah lewat dashboard admin.
--
-- Berkasnya sendiri TIDAK disimpan di sini. Yang di sini catatannya: nama
-- berkas di cakram, jenisnya, ukurannya, dan siapa yang mengunggahnya.
-- PostgreSQL bisa menyimpan bita, dan tetap tidak dipakai begitu: satu video
-- dua puluh megabita di dalam baris membuat setiap cadangan basis data ikut
-- membawanya, setiap replikasi mengirimnya lagi, dan setiap pembacaan
-- halaman melewati kolam koneksi untuk sesuatu yang bisa dilayani berkas
-- statis tanpa satu pun kueri.
--
-- Nama berkasnya tidak pernah datang dari pengunggahnya. Yang dipakai nama
-- acak enam belas heksa, ditambah ukuran gambarnya, ditambah akhiran yang
-- ditentukan dari bita pertama berkasnya, bukan dari nama yang dikirim.
-- Nama kiriman bisa berbunyi "../../etc/passwd" atau "laporan.pdf.exe", dan
-- keduanya pernah jadi kerentanan di tempat lain. Nama aslinya tetap dicatat
-- di kolom terpisah supaya pengunggahnya bisa mengenali berkasnya lagi, dan
-- ia tidak pernah dipakai untuk membentuk jalur.
--
-- Ukuran gambar ikut ke dalam nama berkasnya, misalnya
-- "9f3c1a7b2d4e5f60-1600x900.webp". Itu membuat pembangkit halaman tahu
-- lebar dan tingginya tanpa membuka berkasnya dan tanpa bertanya ke basis
-- data, sehingga tulisan di bawah gambar tidak melompat saat gambarnya tiba.

CREATE TABLE IF NOT EXISTS berkas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Nama di cakram, sekaligus bagian terakhir alamatnya di /unggahan/.
    nama            VARCHAR(200) NOT NULL UNIQUE,

    -- Nama yang dikirim pengunggahnya, hanya untuk dilihat orang.
    nama_asal       VARCHAR(255) NOT NULL,

    -- 'gambar' atau 'video'. Ditentukan dari bita pertama berkasnya.
    jenis           VARCHAR(10) NOT NULL,
    tipe_mime       VARCHAR(100) NOT NULL,
    bita            BIGINT NOT NULL,

    -- Hanya terisi untuk gambar. Video tidak diukur: mengukurnya menuntut
    -- ffmpeg, dan menebaknya berarti menuliskan angka yang tidak diukur.
    lebar           INTEGER,
    tinggi          INTEGER,

    -- sha256 isi berkasnya. Dipakai mengenali unggahan yang sama dua kali,
    -- supaya satu foto yang dipakai di tiga tulisan tetap satu berkas.
    sidik           CHAR(64) NOT NULL UNIQUE,

    pengunggah_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT berkas_jenis_dikenal CHECK (jenis IN ('gambar', 'video')),
    CONSTRAINT berkas_tidak_kosong CHECK (bita > 0),
    -- Gambar punya ukuran, video tidak. Dijaga di sini supaya tidak ada
    -- baris gambar yang lolos tanpa ukuran dan berakhir sebagai halaman
    -- yang melompat.
    CONSTRAINT berkas_ukuran_gambar CHECK (
        (jenis = 'gambar' AND lebar > 0 AND tinggi > 0)
        OR (jenis = 'video' AND lebar IS NULL AND tinggi IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS berkas_terbaru ON berkas (dibuat_pada DESC);

COMMENT ON TABLE berkas IS
    'Catatan foto dan video yang diunggah lewat dashboard. Berkasnya sendiri '
    'ada di cakram, di folder yang disebut UNGGAHAN_DIR, dan dilayani sebagai '
    'berkas statis di /unggahan/.';

COMMENT ON COLUMN berkas.nama_asal IS
    'Nama yang dikirim pengunggah. Hanya untuk dilihat orang, tidak pernah '
    'dipakai membentuk jalur berkas.';
