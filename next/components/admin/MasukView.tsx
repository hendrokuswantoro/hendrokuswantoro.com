"use client";

import { useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { GagalApi, masukSandi, type Sesi } from "@/lib/api";
import * as passkey from "@/lib/passkey";

/**
 * Dua jalan masuk, dan urutannya disengaja.
 *
 * Passkey lebih dulu karena ia yang tahan halaman palsu: kunci privatnya tidak
 * pernah meninggalkan perangkat, dan tanda tangannya terikat pada alamat situs
 * ini. Sandi tetap ada di bawahnya sebagai jalan pulang; perangkat bisa
 * hilang, dan akun yang satu satunya kunci ikut hilang bersama ponselnya
 * adalah akun yang terkunci selamanya.
 *
 * Tombol passkey hanya muncul kalau peramban mendukungnya DAN server sudah
 * dikonfigurasi. Tombol yang selalu ada lalu selalu gagal lebih buruk
 * daripada tombol yang tidak ada.
 */
export function MasukView({ sesudah }: { sesudah: (s: Sesi) => void }) {
  const [email, setEmail] = useState("");
  const [sandi, setSandi] = useState("");
  const [galat, setGalat] = useState("");
  const [sibuk, setSibuk] = useState(false);
  const [adaPasskey, setAdaPasskey] = useState(false);

  useEffect(() => {
    let batal = false;
    passkey.siap().then((ya) => {
      if (!batal) setAdaPasskey(ya);
    });
    return () => {
      batal = true;
    };
  }, []);

  async function denganSandi(event: React.FormEvent) {
    event.preventDefault();
    setGalat("");
    setSibuk(true);
    try {
      sesudah(await masukSandi(email.trim(), sandi));
    } catch (e) {
      setGalat(e instanceof GagalApi ? e.message : "gagal menghubungi server");
    } finally {
      setSibuk(false);
    }
  }

  async function denganPasskey() {
    setGalat("");
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

  return (
    <section className={`${gaya.kartu} ${gaya.masuk}`}>
      <h1 className={gaya.judul} style={{ marginBottom: 18, fontSize: "1.2rem" }}>
        Masuk
      </h1>

      {galat ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
          {galat}
        </p>
      ) : null}

      {adaPasskey ? (
        <>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
            onClick={denganPasskey}
            disabled={sibuk}
          >
            Masuk dengan passkey
          </button>
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
