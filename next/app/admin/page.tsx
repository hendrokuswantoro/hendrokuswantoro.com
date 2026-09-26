"use client";

import { useEffect, useState } from "react";
import gaya from "./admin.module.css";
import { BrandMark } from "@/components/Icons";
import { DaftarTulisan } from "@/components/admin/DaftarTulisan";
import { MasukView } from "@/components/admin/MasukView";
import { PanelKeamanan } from "@/components/admin/PanelKeamanan";
import { PenyuntingTulisan } from "@/components/admin/PenyuntingTulisan";
import { keluar as keluarApi, sesiYangMasihHidup, type Sesi } from "@/lib/api";

export default function Admin() {
  const [sesi, setSesi] = useState<Sesi | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [sunting, setSunting] = useState<{ aktif: boolean; slug: string | null }>({
    aktif: false,
    slug: null,
  });
  const [segarkan, setSegarkan] = useState(0);

  useEffect(() => {
    let batal = false;
    sesiYangMasihHidup()
      .then((s) => {
        if (!batal) setSesi(s);
      })
      .finally(() => {
        if (!batal) setMemuat(false);
      });
    return () => {
      batal = true;
    };
  }, []);

  async function keluar() {
    await keluarApi();
    setSesi(null);
    setSunting({ aktif: false, slug: null });
  }

  if (memuat) {
    return (
      <main className={gaya.bingkai}>
        <div className={gaya.isi}>
          <p className={gaya.ket}>Memeriksa sesi...</p>
        </div>
      </main>
    );
  }

  if (!sesi) {
    return (
      <main className={gaya.bingkai}>
        <MasukView sesudah={setSesi} />
      </main>
    );
  }

  return (
    <main className={gaya.bingkai}>
      <header className={gaya.kepala}>
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a className={gaya.lambang} href="/" aria-label="Kembali ke situs">
          <BrandMark size={30} />
        </a>
        <h1 className={gaya.judul}>hendrokuswantoro.com</h1>
        <span className={gaya.lencana}>admin</span>
        <div className={gaya.kanan}>
          <span className={gaya.ket} style={{ margin: 0 }}>
            {sesi.nama}
          </span>
          <button type="button" className={gaya.tombol} onClick={keluar}>
            Keluar
          </button>
        </div>
      </header>

      <div className={gaya.isi}>
        {sunting.aktif ? (
          <PenyuntingTulisan
            slug={sunting.slug}
            onKembali={() => setSunting({ aktif: false, slug: null })}
            onBerubah={() => setSegarkan((n) => n + 1)}
          />
        ) : (
          <>
            <DaftarTulisan
              segarkan={segarkan}
              onBaru={() => setSunting({ aktif: true, slug: null })}
              onSunting={(slug) => setSunting({ aktif: true, slug })}
            />
            <PanelKeamanan />
          </>
        )}
      </div>
    </main>
  );
}
