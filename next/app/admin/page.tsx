"use client";

import { useEffect, useState } from "react";
import gaya from "./admin.module.css";
import { DaftarTulisan } from "@/components/admin/DaftarTulisan";
import { MasukView } from "@/components/admin/MasukView";
import { PanelPasskey } from "@/components/admin/PanelPasskey";
import { PenyuntingTulisan } from "@/components/admin/PenyuntingTulisan";
import { keluar as keluarApi, sesiYangMasihHidup, type Sesi } from "@/lib/api";

/**
 * Permukaan menulis, versi Next.js.
 *
 * Seluruhnya klien. Tidak ada satu pun bagian yang dirender di server, dan itu
 * memang maunya: `next.config.ts` memakai output "export", sehingga yang
 * terbit adalah berkas statis tanpa runtime Node. Isinya datang dari API saat
 * halamannya dibuka, bukan saat ia dibangun, sebab draf yang ikut terbangun
 * ke dalam berkas statis berarti draf yang bisa dibaca siapa saja.
 *
 * Otorisasinya tetap sepenuhnya di server. Yang dikerjakan halaman ini hanya
 * menyembunyikan tombol yang tidak akan berhasil; setiap permintaan tetap
 * melewati `butuh_admin`. Menyembunyikan tombol bukan otorisasi.
 */
export default function Admin() {
  const [sesi, setSesi] = useState<Sesi | null>(null);
  const [memuat, setMemuat] = useState(true);
  const [sunting, setSunting] = useState<{ aktif: boolean; slug: string | null }>({
    aktif: false,
    slug: null,
  });
  const [segarkan, setSegarkan] = useState(0);

  /* Kalau cookie refresh masih hidup, langsung masuk tanpa menanyakan sandi. */
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
            <PanelPasskey />
          </>
        )}
      </div>
    </main>
  );
}
