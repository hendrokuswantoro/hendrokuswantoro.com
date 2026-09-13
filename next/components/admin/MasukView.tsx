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
  totp: "Buka aplikasi authenticator Anda dan ketikkan enam angka yang sedang tampil.",
  email: "Enam angka sudah dikirim ke alamat email Anda. Berlaku sepuluh menit.",
  pemulihan: "Salah satu dari delapan kode yang Anda simpan saat menyalakan authenticator. Sekali pakai.",
  wajah:
    "Kamera akan mengambil tiga bingkai mengikuti urutan gerakan yang baru diminta " +
    "server. Fotonya tidak disimpan di mana pun.",
};

export function MasukView({ sesudah }: { sesudah: (s: Sesi) => void }) {
  const [email, setEmail] = useState("");
  const [sandi, setSandi] = useState("");
  const [galat, setGalat] = useState("");
  const [kabar, setKabar] = useState("");
  const [sibuk, setSibuk] = useState(false);
  const [adaPasskey, setAdaPasskey] = useState(false);

  /* Tahap kedua. Null berarti belum sampai ke sana. */
  const [tiket, setTiket] = useState<{ nilai: string; cara: CaraFaktorKedua[] } | null>(null);
  const [caraDipakai, setCaraDipakai] = useState<CaraFaktorKedua>("totp");
  const [kode, setKode] = useState("");
  const [tantangan, setTantangan] = useState<TantanganWajah | null>(null);

  useEffect(() => {
    let batal = false;
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
        /* Sandinya dibuang dari memori begitu ia tidak dibutuhkan lagi. */
        setSandi("");
        return;
      }
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
          ? `${e.message}. Coba lagi dengan pencahayaan yang lebih baik.`
          : "gagal menghubungi server",
      );
    } finally {
      setSibuk(false);
    }
  }

  async function denganPasskey() {
    bersihkan();
    setSibuk(true);
    try {
      sesudah(await passkey.masuk());
    } catch (e) {
      if (!passkey.dibatalkan(e)) {
        setGalat(e instanceof Error ? e.message : "passkey gagal");
      }
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
          Kata sandi Anda benar. Karena akun ini memakai faktor kedua, satu kode lagi
          dibutuhkan sebelum sesinya dibuka. Tiketnya berlaku lima menit.
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
            {sibuk ? "Memeriksa..." : "Lanjutkan"}
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
            disabled={sibuk}
          >
            Masuk dengan sidik jari atau passkey
          </button>
          <p className={gaya.penjelasan} style={{ marginTop: 10 }}>
            Perangkat Anda yang meminta sidik jari, wajah, atau PIN. Tidak ada satu pun
            data biometrik yang dikirim ke server ini, dan karena itu tidak ada yang bisa
            bocor dari sini.
          </p>
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
          <input
            id="sandi"
            className={gaya.isian}
            type="password"
            autoComplete="current-password"
            required
            minLength={8}
            value={sandi}
            onChange={(e) => setSandi(e.target.value)}
          />
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
