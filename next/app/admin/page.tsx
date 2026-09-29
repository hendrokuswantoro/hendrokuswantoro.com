"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "./admin.module.css";
import { BrandMark } from "@/components/Icons";
import { DaftarTulisan } from "@/components/admin/DaftarTulisan";
import { KunciLayar } from "@/components/admin/KunciLayar";
import { MasukView } from "@/components/admin/MasukView";
import { PanelKeamanan } from "@/components/admin/PanelKeamanan";
import { PenyuntingTulisan } from "@/components/admin/PenyuntingTulisan";
import { aksesDari } from "@/components/admin/akses";
import { useKeluarOtomatis, useKunciLayar } from "@/components/admin/kunci";
import {
  keadaanKeamanan,
  keluar as keluarApi,
  sesiYangMasihHidup,
  type KeadaanKeamanan,
  type Sesi,
} from "@/lib/api";
import { useSetelanPerangkat } from "@/lib/perangkat";

export default function Admin() {
  const [sesi, setSesi] = useState<Sesi | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [ulangKuat, setUlangKuat] = useState(false);
  const [keadaan, setKeadaan] = useState<KeadaanKeamanan | null>(null);
  const [galatKeadaan, setGalatKeadaan] = useState("");
  const [sunting, setSunting] = useState<{ aktif: boolean; slug: string | null }>({
    aktif: false,
    slug: null,
  });
  const [segarkan, setSegarkan] = useState(0);
  const perangkat = useSetelanPerangkat();

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

  const keluar = useCallback(async () => {
    await keluarApi();
    setSesi(null);
    setSunting({ aktif: false, slug: null });
  }, []);

  const bisaDikunci = sesi !== null && perangkat.kunci && (keadaan?.passkey ?? 0) > 0;
  const kunci = useKunciLayar(keadaan !== null, bisaDikunci, perangkat.jeda);
  const tertutup = kunci.terkunci || (sesi !== null && perangkat.kunci && keadaan === null);
  useKeluarOtomatis(sesi !== null && perangkat.keluarOtomatis, keluar);

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
        <MasukView
          hanyaKuat={ulangKuat}
          sesudah={(baru) => {
            setUlangKuat(false);
            setSesi(baru);
          }}
        />
      </main>
    );
  }

  const akses = aksesDari(keadaan);

  return (
    <main className={gaya.bingkai}>
      {kunci.terkunci ? <KunciLayar terbuka={kunci.buka} keluar={keluar} /> : null}
      <div className={gaya.dasbor} inert={tertutup} aria-hidden={tertutup}>
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
                <strong>Akses kamu terbatas.</strong> Kamu belum masuk pakai authenticator atau
                sidik jari, jadi tulisan dan pengaturan keamanan dikunci.
              </p>
              <button
                type="button"
                className={`${gaya.tombol} ${gaya.utama}`}
                onClick={() => {
                  setUlangKuat(true);
                  void keluar();
                }}
              >
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
      </div>
    </main>
  );
}
