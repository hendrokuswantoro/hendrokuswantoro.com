"use client";

import { useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { BarisSakelar, Halaman, LabelBagian } from "@/components/admin/Setelan";
import type { KeadaanKeamanan } from "@/lib/api";
import * as passkey from "@/lib/passkey";
import { PILIHAN_JEDA, ubahPerangkat, useSetelanPerangkat } from "@/lib/perangkat";

export function HalamanKunci({
  keadaan,
  kembali,
}: {
  keadaan: KeadaanKeamanan;
  kembali: () => void;
}) {
  const perangkat = useSetelanPerangkat();
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  const halangan = passkey.didukung() ? passkey.kendala() : null;
  const bisa = keadaan.passkey > 0 && passkey.didukung() && !halangan;

  async function nyalakan(nilai: boolean) {
    setKabar(null);
    if (!nilai) {
      ubahPerangkat({ kunci: false });
      setKabar(baik("Kunci aplikasi dimatikan di perangkat ini."));
      return;
    }
    setSibuk(true);
    try {
      await passkey.bukaKunci();
      ubahPerangkat({ kunci: true });
      setKabar(baik("Kunci aplikasi nyala. Buka pakai sidik jari tiap kali terkunci."));
    } catch (e) {
      if (!passkey.dibatalkan(e)) {
        setKabar(buruk(e instanceof Error ? e.message : "Sidik jari tidak terbaca."));
      }
    } finally {
      setSibuk(false);
    }
  }

  return (
    <Halaman judul="Kunci aplikasi" kembali={kembali}>
      <Kabar isi={kabar} />

      <ul className={gaya.setelan}>
        <BarisSakelar
          judul="Buka kunci pakai sidik jari"
          nyala={perangkat.kunci}
          mati={sibuk || (!perangkat.kunci && !bisa)}
          ubah={(nilai) => void nyalakan(nilai)}
        >
          Kalau nyala, dashboard harus dibuka pakai sidik jari, wajah di HP, atau PIN perangkat.
        </BarisSakelar>
      </ul>

      {keadaan.passkey === 0 ? (
        <p className={gaya.ket}>Daftarkan sidik jari dulu di Verifikasi dua langkah.</p>
      ) : halangan ? (
        <p className={gaya.ket}>{halangan.pesan}</p>
      ) : !passkey.didukung() ? (
        <p className={gaya.ket}>Browser ini belum bisa membaca sidik jari.</p>
      ) : null}

      <LabelBagian>Kunci secara otomatis</LabelBagian>
      <fieldset className={gaya.pilihanJeda} disabled={!perangkat.kunci}>
        <legend className={gaya.tersembunyi}>Kunci secara otomatis</legend>
        {PILIHAN_JEDA.map((p) => (
          <label key={p.nilai} className={gaya.radio}>
            <input
              type="radio"
              name="jeda-kunci"
              checked={perangkat.jeda === p.nilai}
              onChange={() => ubahPerangkat({ jeda: p.nilai })}
            />
            <span>{p.label}</span>
          </label>
        ))}
      </fieldset>

      <p className={gaya.ket}>
        Waktunya dihitung sejak kamu pindah ke tab atau aplikasi lain. Setelan ini cuma berlaku di
        perangkat ini.
      </p>
    </Halaman>
  );
}
