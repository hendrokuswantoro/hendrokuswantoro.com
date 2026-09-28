import { useCallback, useEffect, useRef, useState } from "react";

const DIAM_SEBELUM_KELUAR_MS = 30 * 60 * 1000;
const JEDA_PERIKSA_MS = 30 * 1000;
const GERAKAN = ["pointerdown", "pointermove", "keydown", "scroll", "wheel"] as const;
const TENANG_SESUDAH_DIBUKA_MS = 1500;

export function useKunciLayar(siap: boolean, aktif: boolean, jedaDetik: number) {
  const [terkunci, setTerkunci] = useState(false);
  const dinilai = useRef(false);
  const sejak = useRef<number | null>(null);
  const dibukaPada = useRef(0);

  useEffect(() => {
    if (!siap || dinilai.current) return;
    dinilai.current = true;
    if (aktif) setTerkunci(true);
  }, [siap, aktif]);

  useEffect(() => {
    if (!aktif) {
      setTerkunci(false);
      return;
    }
    const ubah = () => {
      if (document.visibilityState === "hidden") {
        sejak.current = Date.now();
        return;
      }
      const baruDibuka = Date.now() - dibukaPada.current < TENANG_SESUDAH_DIBUKA_MS;
      if (!baruDibuka && sejak.current !== null && Date.now() - sejak.current >= jedaDetik * 1000) {
        setTerkunci(true);
      }
      sejak.current = null;
    };
    document.addEventListener("visibilitychange", ubah);
    return () => document.removeEventListener("visibilitychange", ubah);
  }, [aktif, jedaDetik]);

  const buka = useCallback(() => {
    dibukaPada.current = Date.now();
    sejak.current = null;
    setTerkunci(false);
  }, []);
  return { terkunci, buka };
}

export function useKeluarOtomatis(aktif: boolean, keluar: () => void) {
  useEffect(() => {
    if (!aktif) return;
    let terakhir = Date.now();
    const gerak = () => {
      terakhir = Date.now();
    };
    const periksa = () => {
      if (Date.now() - terakhir >= DIAM_SEBELUM_KELUAR_MS) keluar();
    };
    for (const jenis of GERAKAN) window.addEventListener(jenis, gerak, { passive: true });
    document.addEventListener("visibilitychange", periksa);
    const jam = window.setInterval(periksa, JEDA_PERIKSA_MS);
    return () => {
      for (const jenis of GERAKAN) window.removeEventListener(jenis, gerak);
      document.removeEventListener("visibilitychange", periksa);
      window.clearInterval(jam);
    };
  }, [aktif, keluar]);
}
