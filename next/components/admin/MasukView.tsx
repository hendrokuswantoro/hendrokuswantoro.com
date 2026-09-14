"use client";

import { useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { BrandMark } from "@/components/Icons";
import { KameraWajah } from "@/components/admin/KameraWajah";
import {
  GagalApi,
  kirimUlangKode,
  masukSandi,
  selesaikanFaktorKedua,
  tantanganWajah,
  type CaraFaktorKedua,
  type Sesi,
  type TantanganWajah,
} from "@/lib/api";
import * as passkey from "@/lib/passkey";

/**
 * Tiga jalan masuk, dan urutannya disengaja.
 *
 * Passkey lebih dulu karena ia yang tahan halaman palsu: kunci privatnya tidak
 * pernah meninggalkan perangkat, dan tanda tangannya terikat pada alamat situs
 * ini. Sandi tetap ada di bawahnya sebagai jalan pulang; perangkat bisa
 * hilang, dan akun yang satu satunya kunci ikut hilang bersama ponselnya
 * adalah akun yang terkunci selamanya.
 *
 * Jalur sandi bisa berhenti di tengah. Kalau ada faktor kedua yang berlaku,
 * yang kembali dari server bukan sesi melainkan tiket berumur lima menit, dan
 * layar ini berganti jadi kotak kode. Passkey tidak lewat situ, dan itu benar:
 * passkey sudah dua faktor pada dirinya sendiri, yaitu perangkatnya dan sidik
 * jari atau PIN yang membukanya.
 */

const NAMA_CARA: Record<CaraFaktorKedua, string> = {
  totp: "Aplikasi authenticator",
  email: "Kode yang dikirim ke email",
  pemulihan: "Kode pemulihan",
  wajah: "Verifikasi wajah",
};

const PETUNJUK: Record<CaraFaktorKedua, string> = {
  totp: "Buka aplikasi authenticator, lalu ketik enam angka yang tampil.",
  email: "Enam angka sudah dikirim ke email Anda. Berlaku sepuluh menit.",
  pemulihan: "Pakai salah satu kode yang Anda simpan dulu. Sekali pakai.",
  wajah: "Kamera minta tiga foto. Ikuti gerakan yang diminta. Fotonya tidak disimpan.",
};

export function MasukView({ sesudah }: { sesudah: (s: Sesi) => void }) {
  const [email, setEmail] = useState("");
  const [sandi, setSandi] = useState("");
  const [galat, setGalat] = useState("");
  const [kabar, setKabar] = useState("");
  const [sibuk, setSibuk] = useState(false);
  const [adaPasskey, setAdaPasskey] = useState(false);
  /* Sandi terlihat atau tidak. Bawaannya tidak, dan ia dikembalikan ke tidak
     begitu sesinya terbuka: sandi yang tadi ditampilkan tidak boleh tinggal
     terbaca di layar yang mungkin ditinggalkan pemiliknya. */
  const [sandiTerlihat, setSandiTerlihat] = useState(false);
  /* Kenapa sidik jari tidak bisa dipakai di alamat ini, kalau memang tidak
     bisa. Diisi di useEffect, bukan saat render, sebab ia membaca
     window.location dan server tidak punya itu. */
  const [halangan, setHalangan] = useState<passkey.Kendala | null>(null);

  /* Tahap kedua. Null berarti belum sampai ke sana. */
  const [tiket, setTiket] = useState<{ nilai: string; cara: CaraFaktorKedua[] } | null>(null);
  const [caraDipakai, setCaraDipakai] = useState<CaraFaktorKedua>("totp");
  const [kode, setKode] = useState("");
  const [tantangan, setTantangan] = useState<TantanganWajah | null>(null);

  useEffect(() => {
    let batal = false;
    setHalangan(passkey.kendala());
    passkey.siap().then((ya) => {
      if (!batal) setAdaPasskey(ya);
    });
    return () => {
      batal = true;
    };
  }, []);

  function bersihkan() {
    setGalat("");
    setKabar("");
  }

  async function denganSandi(event: React.FormEvent) {
    event.preventDefault();
    bersihkan();
    setSibuk(true);
    try {
      const hasil = await masukSandi(email.trim(), sandi);
      if (hasil.tahap === "faktor2") {
        setTiket({ nilai: hasil.tiket, cara: hasil.cara });
        setCaraDipakai(hasil.cara[0]);
        /* Sandinya dibuang dari memori begitu ia tidak dibutuhkan lagi, dan
           saklarnya dikembalikan ke tersembunyi bersamanya. */
        setSandi("");
        setSandiTerlihat(false);
        return;
      }
      setSandi("");
      setSandiTerlihat(false);
      sesudah(hasil);
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  async function denganKode(event: React.FormEvent) {
    event.preventDefault();
    if (!tiket) return;
    bersihkan();
    setSibuk(true);
    try {
      sesudah(await selesaikanFaktorKedua(tiket.nilai, caraDipakai, kode.trim()));
    } catch (e) {
      setKode("");
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  async function kirimUlang() {
    if (!tiket) return;
    bersihkan();
    setSibuk(true);
    try {
      const hasil = await kirimUlangKode(tiket.nilai);
      /* Kalau SMTP belum dikonfigurasi, server mengatakannya terus terang dan
         layar ini ikut mengatakannya. Membalas "kode sudah dikirim" untuk
         surat yang tidak pernah berangkat adalah cara mengunci orang di luar
         pintunya sendiri sambil meyakinkannya bahwa semuanya baik baik saja. */
      setKabar(hasil.terkirim ? "Kode baru sudah dikirim." : hasil.catatan);
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  async function mulaiWajah() {
    if (!tiket) return;
    bersihkan();
    setSibuk(true);
    try {
      setTantangan(await tantanganWajah(tiket.nilai));
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  async function kirimWajah(bingkai: string[]) {
    if (!tiket || !tantangan) return;
    bersihkan();
    setSibuk(true);
    try {
      sesudah(
        await selesaikanFaktorKedua(tiket.nilai, "wajah", "", {
          tantangan: tantangan.tantangan,
          bingkai,
        }),
      );
    } catch (e) {
      /* Tantangannya sekali pakai, jadi gagal berarti harus minta yang baru.
         Dikosongkan di sini supaya layarnya tidak menawarkan tombol yang
         sudah pasti ditolak. */
      setTantangan(null);
      setGalat(
        e instanceof GagalApi
          ? `${e.message}. Coba lagi di tempat yang lebih terang.`
          : "gagal menghubungi server",
      );
    } finally {
      setSibuk(false);
    }
  }

  async function denganPasskey() {
    bersihkan();

    /* Diperiksa lagi di sini, bukan hanya saat tombolnya digambar. Alamat
       halaman bisa berganti tanpa komponennya dipasang ulang. */
    const h = passkey.kendala();
    if (h) {
      setHalangan(h);
      setGalat(h.saran ? `${h.pesan} Buka ${h.saran}` : h.pesan);
      return;
    }

    setSibuk(true);
    try {
      sesudah(await passkey.masuk());
    } catch (e) {
      if (passkey.dibatalkan(e)) return;
      /* SecurityError datang dari peramban, bukan dari server, dan bunyinya
         "This is an invalid domain." Kalimat itu benar tetapi tidak memberi
         tahu siapa pun apa yang harus dikerjakan. */
      if ((e as { name?: string })?.name === "SecurityError") {
        const lagi = passkey.kendala();
        setGalat(
          lagi?.saran
            ? `${lagi.pesan} Buka ${lagi.saran}`
            : "Alamat halaman ini tidak bisa dipakai untuk sidik jari.",
        );
        return;
      }
      setGalat(e instanceof Error ? e.message : "passkey gagal");
    } finally {
      setSibuk(false);
    }
  }

  const kepala = (
    <div className={gaya.masukKepala}>
      <BrandMark size={40} />
      <div>
        <h1 className={gaya.judul} style={{ fontSize: "1.2rem" }}>
          {tiket ? "Satu langkah lagi" : "Masuk"}
        </h1>
        <p className={gaya.ket} style={{ margin: 0 }}>
          hendrokuswantoro.com
        </p>
      </div>
    </div>
  );

  const pesan = (
    <>
      {galat ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
          {galat}
        </p>
      ) : null}
      {kabar ? (
        <p className={`${gaya.kabar} ${gaya.baik}`} role="status">
          {kabar}
        </p>
      ) : null}
    </>
  );

  /* ------------------------------------------------------- tahap kedua */

  if (tiket) {
    return (
      <section className={`${gaya.kartu} ${gaya.masuk}`}>
        {kepala}
        {pesan}

        <p className={gaya.penjelasan}>
          Sandi Anda benar. Tinggal satu langkah lagi, dan waktunya lima menit.
        </p>

        {tiket.cara.length > 1 ? (
          <div className={gaya.baris}>
            <label htmlFor="cara">Cara</label>
            <select
              id="cara"
              className={gaya.isian}
              value={caraDipakai}
              onChange={(e) => {
                setCaraDipakai(e.target.value as CaraFaktorKedua);
                setKode("");
                setTantangan(null);
                bersihkan();
              }}
            >
              {tiket.cara.map((c) => (
                <option key={c} value={c}>
                  {NAMA_CARA[c]}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <p className={gaya.penjelasan}>{PETUNJUK[caraDipakai]}</p>

        {caraDipakai === "wajah" ? (
          <>
            {tantangan ? (
              <KameraWajah
                gerakan={tantangan.gerakan}
                sibuk={sibuk}
                batal={() => setTantangan(null)}
                selesai={(bingkai) => void kirimWajah(bingkai)}
              />
            ) : (
              <div className={gaya.aksi}>
                <button
                  type="button"
                  className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
                  onClick={() => void mulaiWajah()}
                  disabled={sibuk}
                >
                  {sibuk ? "Sebentar..." : "Nyalakan kamera"}
                </button>
              </div>
            )}
            <div className={gaya.aksi} style={{ marginTop: 14 }}>
              <button
                type="button"
                className={gaya.tombol}
                onClick={() => {
                  setTiket(null);
                  setTantangan(null);
                  bersihkan();
                }}
              >
                Kembali
              </button>
            </div>
          </>
        ) : (
        <>
        <form onSubmit={denganKode}>
          <div className={gaya.baris}>
            <label htmlFor="kode">
              {caraDipakai === "pemulihan" ? "Kode pemulihan" : "Kode enam angka"}
            </label>
            <input
              id="kode"
              className={`${gaya.isian} ${gaya.kodeIsian}`}
              /* inputMode numeric, bukan type number: type number membawa
                 tombol naik turun dan membuang angka nol di depan. */
              inputMode={caraDipakai === "pemulihan" ? "text" : "numeric"}
              autoComplete={caraDipakai === "pemulihan" ? "off" : "one-time-code"}
              autoFocus
              required
              value={kode}
              onChange={(e) => setKode(e.target.value)}
              placeholder={caraDipakai === "pemulihan" ? "XXXXX-XXXXX" : "000000"}
            />
          </div>

          <button
            type="submit"
            className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
            disabled={sibuk || kode.trim().length < 4}
          >
            {sibuk ? "Sebentar..." : "Lanjutkan"}
          </button>
        </form>

        <div className={gaya.aksi} style={{ marginTop: 14 }}>
          {caraDipakai === "email" ? (
            <button type="button" className={gaya.tombol} onClick={kirimUlang} disabled={sibuk}>
              Kirim ulang kode
            </button>
          ) : null}
          <button
            type="button"
            className={gaya.tombol}
            onClick={() => {
              setTiket(null);
              setKode("");
              bersihkan();
            }}
          >
            Kembali
          </button>
        </div>
        </>
        )}
      </section>
    );
  }

  /* ------------------------------------------------------ tahap pertama */

  return (
    <section className={`${gaya.kartu} ${gaya.masuk}`}>
      {kepala}
      {pesan}

      {adaPasskey ? (
        <>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
            onClick={denganPasskey}
            disabled={sibuk || halangan !== null}
          >
            Masuk pakai sidik jari
          </button>
          {halangan ? (
            <p className={gaya.penjelasan} style={{ marginTop: 10 }}>
              {halangan.pesan}{" "}
              {halangan.saran ? (
                <>
                  Buka <a href={halangan.saran}>{halangan.saran}</a>. Mesinnya sama, cuma
                  namanya yang berbeda.
                </>
              ) : null}
            </p>
          ) : (
            <p className={gaya.penjelasan} style={{ marginTop: 10 }}>
              Perangkat Anda yang meminta sidik jari, wajah, atau PIN. Sidik jari Anda tidak
              dikirim ke mana pun.
            </p>
          )}
          <div className={gaya.pisah}>atau dengan sandi</div>
        </>
      ) : null}

      <form onSubmit={denganSandi}>
        <div className={gaya.baris}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            className={gaya.isian}
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className={gaya.baris}>
          <label htmlFor="sandi">Sandi</label>
          {/* Tombolnya di DALAM bidang isian, dan isiannya diberi ruang kanan
              supaya sandi yang panjang tidak pernah tersembunyi di baliknya. */}
          <div className={gaya.sandiBidang}>
            <input
              id="sandi"
              className={gaya.isian}
              type={sandiTerlihat ? "text" : "password"}
              autoComplete="current-password"
              required
              minLength={8}
              value={sandi}
              onChange={(e) => setSandi(e.target.value)}
            />
            <button
              type="button"
              className={gaya.lihat}
              aria-controls="sandi"
              aria-pressed={sandiTerlihat}
              aria-label={sandiTerlihat ? "Sembunyikan sandi" : "Tampilkan sandi"}
              title={sandiTerlihat ? "Sembunyikan sandi" : "Tampilkan sandi"}
              onClick={() => setSandiTerlihat((t) => !t)}
            >
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="M1.8 12S5.4 5.5 12 5.5 22.2 12 22.2 12 18.6 18.5 12 18.5 1.8 12 1.8 12z" />
                <circle cx="12" cy="12" r="3.2" />
                <path className={gaya.coret} d="M4 20 20 4" />
              </svg>
            </button>
          </div>
        </div>

        <button
          type="submit"
          className={`${gaya.tombol} ${adaPasskey ? "" : gaya.utama} ${gaya.lebar}`}
          disabled={sibuk}
        >
          {sibuk ? "Sebentar..." : "Masuk"}
        </button>
      </form>
    </section>
  );
}
