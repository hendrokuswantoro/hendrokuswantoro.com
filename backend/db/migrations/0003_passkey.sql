CREATE TABLE kredensial (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pengguna_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    kredensial_id   BYTEA UNIQUE NOT NULL,
    kunci_publik    BYTEA NOT NULL,

    penghitung      BIGINT NOT NULL DEFAULT 0,

    jenis_perangkat VARCHAR(20) NOT NULL,
    tercadang       BOOLEAN NOT NULL DEFAULT false,
    transportasi    TEXT[] NOT NULL DEFAULT '{}',

    nama            VARCHAR(80) NOT NULL,

    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),
    dipakai_pada    TIMESTAMPTZ,

    CONSTRAINT penghitung_tidak_mundur CHECK (penghitung >= 0),
    CONSTRAINT kredensial_id_masuk_akal
        CHECK (octet_length(kredensial_id) BETWEEN 16 AND 1023),
    CONSTRAINT jenis_perangkat_dikenal
        CHECK (jenis_perangkat IN ('single_device', 'multi_device')),
    CONSTRAINT nama_tidak_kosong CHECK (btrim(nama) <> '')
);

CREATE INDEX idx_kredensial_pengguna ON kredensial (pengguna_id);

COMMENT ON TABLE kredensial IS
    'Passkey. Hanya kunci publik; tidak ada rahasia apa pun di tabel ini.';
COMMENT ON COLUMN kredensial.penghitung IS
    'Sign count dari authenticator. Nilai yang tidak naik menandakan salinan.';

CREATE TABLE tantangan (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tujuan          VARCHAR(10) NOT NULL,
    pengguna_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    nilai           BYTEA UNIQUE NOT NULL,
    kadaluarsa      TIMESTAMPTZ NOT NULL,
    dipakai_pada    TIMESTAMPTZ,
    dibuat_pada     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT tujuan_dikenal CHECK (tujuan IN ('daftar', 'masuk')),
    CONSTRAINT daftar_punya_pengguna
        CHECK (tujuan <> 'daftar' OR pengguna_id IS NOT NULL),
    CONSTRAINT tantangan_cukup_panjang CHECK (octet_length(nilai) >= 16),
    CONSTRAINT kadaluarsa_sesudah_dibuat CHECK (kadaluarsa > dibuat_pada)
);

CREATE INDEX idx_tantangan_kadaluarsa ON tantangan (kadaluarsa);

COMMENT ON COLUMN tantangan.dipakai_pada IS
    'Sekali pakai. Baris yang sudah terisi tidak pernah diterima lagi.';
