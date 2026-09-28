"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { daftarSesi, keluarkanPerangkatLain, pesanDari, type SesiPerangkat } from "@/lib/api";

function tanggal(nilai: string): string {
  try {
    return new Intl.DateTimeFormat("id-ID", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Asia/Jakarta",
    }).format(new Date(nilai));
  } catch {
    return nilai;
  }
}

export function PerangkatTepercaya() {
  const [sesi, setSesi] = useState<SesiPerangkat[] | null>(null);
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  const muat = useCallback(async () => {
    try {
      setSesi((await daftarSesi()).sesi);
    } catch (e) {
      setKabar(buruk(pesanDari(e, "Daftar perangkat gagal dimuat.")));
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat]);

  async function keluarkan() {
    setKabar(null);
    setSibuk(true);
    try {
      const { sesi_dicabut } = await keluarkanPerangkatLain();
      setKabar(
        baik(
          sesi_dicabut
            ? `${sesi_dicabut} perangkat lain sudah dikeluarkan.`
            : "Tidak ada perangkat lain.",
        ),
      );
      await muat();
    } catch (e) {
      setKabar(buruk(pesanDari(e)));
    } finally {
      setSibuk(false);
    }
  }

  const lain = (sesi ?? []).filter((s) => !s.perangkat_ini).length;

  return (
    <>
      <p className={gaya.penjelasan}>
        Perangkat yang sedang masuk ke akun kamu. Kalau ada yang tidak kamu kenal, keluarkan
        sekarang.
      </p>
      <Kabar isi={kabar} />
      {sesi === null ? (
        <p className={gaya.ket}>Sebentar...</p>
      ) : (
        <ul className={gaya.daftarRingkas}>
          {sesi.map((s) => (
            <li key={s.id}>
              <span>
                <strong>{s.perangkat_ini ? "Perangkat ini" : "Perangkat lain"}</strong>
                <small>Masuk {tanggal(s.dibuat_pada)}</small>
              </span>
              {s.perangkat_ini ? (
                <span className={`${gaya.tanda} ${gaya.terbit}`}>sekarang</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      <div className={gaya.aksi}>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.kecil} ${gaya.bahaya}`}
          disabled={sibuk || lain === 0}
          onClick={() => void keluarkan()}
        >
          Keluarkan perangkat lain
        </button>
      </div>
    </>
  );
}
