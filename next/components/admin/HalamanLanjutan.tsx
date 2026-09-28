"use client";

import { useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { BarisSakelar, Halaman, Terkunci } from "@/components/admin/Setelan";
import type { Akses } from "@/components/admin/akses";
import { pesanDari, ubahSetelan, type KeadaanKeamanan } from "@/lib/api";
import { ubahPerangkat, useSetelanPerangkat } from "@/lib/perangkat";

export function HalamanLanjutan({
  keadaan,
  akses,
  muatKeadaan,
  kembali,
}: {
  keadaan: KeadaanKeamanan;
  akses: Akses;
  muatKeadaan: () => Promise<void>;
  kembali: () => void;
}) {
  const perangkat = useSetelanPerangkat();
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  const punyaFaktorKuat = keadaan.totp_aktif || keadaan.passkey > 0;

  async function ketat(nilai: boolean) {
    setKabar(null);
    setSibuk(true);
    try {
      await ubahSetelan({ mode_ketat: nilai });
      await muatKeadaan();
      setKabar(baik(nilai ? "Mode ketat nyala." : "Mode ketat dimatikan."));
    } catch (e) {
      setKabar(buruk(pesanDari(e)));
    } finally {
      setSibuk(false);
    }
  }

  return (
    <Halaman judul="Lanjutan" kembali={kembali}>
      <Kabar isi={kabar} />
      {!akses.penuh ? <Terkunci /> : null}

      <ul className={gaya.setelan}>
        <BarisSakelar
          judul="Mode ketat"
          nyala={keadaan.mode_ketat}
          mati={sibuk || !akses.penuh || (!keadaan.mode_ketat && !punyaFaktorKuat)}
          ubah={(nilai) => void ketat(nilai)}
        >
          Masuk cuma bisa pakai authenticator atau sidik jari. Wajah tidak bisa lagi dipakai untuk
          masuk.
        </BarisSakelar>
        <BarisSakelar
          judul="Keluar otomatis"
          nyala={perangkat.keluarOtomatis}
          ubah={(nilai) => ubahPerangkat({ keluarOtomatis: nilai })}
        >
          Keluar sendiri kalau dashboard tidak dipakai 30 menit. Berlaku di perangkat ini.
        </BarisSakelar>
      </ul>

      {!punyaFaktorKuat ? (
        <p className={gaya.ket}>
          Mode ketat butuh authenticator atau sidik jari. Pasang salah satunya dulu.
        </p>
      ) : null}
    </Halaman>
  );
}
