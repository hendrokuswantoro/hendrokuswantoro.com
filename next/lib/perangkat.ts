import { useSyncExternalStore } from "react";

export type JedaKunci = 0 | 60 | 1800;

export type SetelanPerangkat = {
  kunci: boolean;
  jeda: JedaKunci;
  keluarOtomatis: boolean;
};

export const PILIHAN_JEDA: { nilai: JedaKunci; label: string }[] = [
  { nilai: 0, label: "Segera" },
  { nilai: 60, label: "Setelah 1 menit" },
  { nilai: 1800, label: "Setelah 30 menit" },
];

const KUNCI_SIMPAN = "hk-admin-perangkat";
const PERISTIWA = "hk-admin-perangkat";
const BAWAAN: SetelanPerangkat = { kunci: false, jeda: 0, keluarOtomatis: false };

let simpanan: SetelanPerangkat | null = null;

function rapikan(isi: Partial<SetelanPerangkat> | null): SetelanPerangkat {
  const jeda = PILIHAN_JEDA.some((p) => p.nilai === isi?.jeda) ? (isi?.jeda as JedaKunci) : 0;
  return {
    kunci: isi?.kunci === true,
    jeda,
    keluarOtomatis: isi?.keluarOtomatis === true,
  };
}

function baca(): SetelanPerangkat {
  if (simpanan) return simpanan;
  try {
    simpanan = rapikan(JSON.parse(window.localStorage.getItem(KUNCI_SIMPAN) ?? "null"));
  } catch {
    simpanan = BAWAAN;
  }
  return simpanan;
}

function dengar(ubah: () => void): () => void {
  const dariTabLain = (e: StorageEvent) => {
    if (e.key !== KUNCI_SIMPAN) return;
    simpanan = null;
    ubah();
  };
  window.addEventListener(PERISTIWA, ubah);
  window.addEventListener("storage", dariTabLain);
  return () => {
    window.removeEventListener(PERISTIWA, ubah);
    window.removeEventListener("storage", dariTabLain);
  };
}

export function ubahPerangkat(perubahan: Partial<SetelanPerangkat>): void {
  simpanan = rapikan({ ...baca(), ...perubahan });
  try {
    window.localStorage.setItem(KUNCI_SIMPAN, JSON.stringify(simpanan));
  } catch {}
  window.dispatchEvent(new Event(PERISTIWA));
}

export function labelJeda(jeda: JedaKunci): string {
  return PILIHAN_JEDA.find((p) => p.nilai === jeda)?.label ?? "Segera";
}

export function useSetelanPerangkat(): SetelanPerangkat {
  return useSyncExternalStore(dengar, baca, () => BAWAAN);
}
