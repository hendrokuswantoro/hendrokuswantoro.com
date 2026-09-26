import type { KeadaanKeamanan } from "@/lib/api";

export type Akses = {
  penuh: boolean;
  terkunci: boolean;
  perluFaktor: boolean;
  bolehMendaftar: boolean;
};

export function aksesDari(keadaan: KeadaanKeamanan | null): Akses {
  if (!keadaan) {
    return { penuh: false, terkunci: false, perluFaktor: false, bolehMendaftar: false };
  }
  const kuat = !keadaan.faktor_kedua_wajib || keadaan.sesi_kuat;
  const punyaFaktor = keadaan.totp_aktif || keadaan.passkey > 0 || keadaan.wajah_terdaftar;
  return {
    penuh: kuat,
    terkunci: !kuat && punyaFaktor,
    perluFaktor: !kuat && !punyaFaktor,
    bolehMendaftar: kuat || !punyaFaktor,
  };
}
