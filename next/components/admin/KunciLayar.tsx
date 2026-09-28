"use client";

import { useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { Kabar, buruk, type IsiKabar } from "@/components/admin/Kabar";
import * as passkey from "@/lib/passkey";

export function KunciLayar({ terbuka, keluar }: { terbuka: () => void; keluar: () => void }) {
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  async function buka() {
    setKabar(null);
    setSibuk(true);
    try {
      await passkey.bukaKunci();
      terbuka();
    } catch (e) {
      if (!passkey.dibatalkan(e)) {
        setKabar(buruk(e instanceof Error ? e.message : "Sidik jari tidak terbaca."));
      }
    } finally {
      setSibuk(false);
    }
  }

  return (
    <div className={gaya.kunciLayar} role="dialog" aria-modal="true" aria-labelledby="judul-kunci">
      <div className={gaya.kunciKartu}>
        <span className={gaya.pahlawanIkon} aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <rect x="5" y="10.5" width="14" height="10" rx="2" />
            <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5M12 14.5v2" />
          </svg>
        </span>
        <h2 id="judul-kunci">Dashboard terkunci</h2>
        <p className={gaya.penjelasan}>Buka pakai sidik jari, wajah di HP, atau PIN perangkat.</p>
        <Kabar isi={kabar} />
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.utama} ${gaya.lebar}`}
          disabled={sibuk}
          onClick={() => void buka()}
          autoFocus
        >
          {sibuk ? "Sebentar..." : "Buka kunci"}
        </button>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.hantu} ${gaya.lebar}`}
          onClick={keluar}
        >
          Keluar
        </button>
      </div>
    </div>
  );
}
