"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "./admin.module.css";
import { BrandMark } from "@/components/Icons";
import { DaftarTulisan } from "@/components/admin/DaftarTulisan";
import { MasukView } from "@/components/admin/MasukView";
import { PanelKeamanan } from "@/components/admin/PanelKeamanan";
import { PenyuntingTulisan } from "@/components/admin/PenyuntingTulisan";
import { aksesDari } from "@/components/admin/akses";
import {
  keadaanKeamanan,
  keluar as keluarApi,
  sesiYangMasihHidup,
  type KeadaanKeamanan,
  type Sesi,
} from "@/lib/api";

export default function Admin() {
  const [sesi, setSesi] = useState<Sesi | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [keadaan, setKeadaan] = useState<KeadaanKeamanan | null>(null);
  const [galatKeadaan, setGalatKeadaan] = useState("");
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

  const muatKeadaan = useCallback(async () => {
    try {
      setKeadaan(await keadaanKeamanan());
      setGalatKeadaan("");
    } catch (e) {
      setGalatKeadaan(e instanceof Error ? e.message : "gagal memuat keadaan keamanan");
    }
  }, []);

  useEffect(() => {
    if (sesi) void muatKeadaan();
    else setKeadaan(null);
  }, [sesi, muatKeadaan]);

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

  const akses = aksesDari(keadaan);

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
          <span className={gaya.namaSesi}>{sesi.nama}</span>
          <button type="button" className={gaya.tombol} onClick={keluar}>
            Keluar
          </button>
        </div>
      </header>

      <div className={gaya.isi}>
        {akses.terkunci ? (
          <div className={gaya.spanduk} role="status">
            <p>
              <strong>Akses kamu terbatas.</strong> Kamu belum masuk pakai authenticator
              atau sidik jari, jadi tulisan dan pengaturan keamanan dikunci.
            </p>
            <button type="button" className={`${gaya.tombol} ${gaya.utama}`} onClick={keluar}>
              Masuk ulang
            </button>
          </div>
        ) : akses.perluFaktor ? (
          <div className={gaya.spanduk} role="status">
            <p>
              <strong>Pasang authenticator dulu.</strong> Setelah terpasang, keluar lalu masuk
              lagi pakai kodenya. Tulisan bisa dibuka sesudah itu.
            </p>
            <a className={`${gaya.tombol} ${gaya.utama}`} href="#keamanan">
              Pasang sekarang
            </a>
          </div>
        ) : null}

        {sunting.aktif && akses.penuh ? (
          <PenyuntingTulisan
            slug={sunting.slug}
            onKembali={() => setSunting({ aktif: false, slug: null })}
            onBerubah={() => setSegarkan((n) => n + 1)}
          />
        ) : (
          <>
            <DaftarTulisan
              segarkan={segarkan}
              siap={keadaan !== null}
              terkunci={keadaan !== null && !akses.penuh}
              onBaru={() => setSunting({ aktif: true, slug: null })}
              onSunting={(slug) => setSunting({ aktif: true, slug })}
            />
            <PanelKeamanan
              keadaan={keadaan}
              galatKeadaan={galatKeadaan}
              akses={akses}
              muatKeadaan={muatKeadaan}
            />
          </>
        )}
      </div>
    </main>
  );
}
