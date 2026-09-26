import gaya from "@/app/admin/admin.module.css";

export type IsiKabar = { teks: string; baik: boolean } | null;

export const baik = (teks: string): IsiKabar => ({ teks, baik: true });
export const buruk = (teks: string): IsiKabar => ({ teks, baik: false });

function kalimat(teks: string): string {
  return teks.charAt(0).toUpperCase() + teks.slice(1);
}

export function Kabar({ isi }: { isi: IsiKabar }) {
  if (!isi?.teks) return null;
  return (
    <p
      className={`${gaya.kabar} ${isi.baik ? gaya.baik : gaya.salah}`}
      role={isi.baik ? "status" : "alert"}
    >
      {kalimat(isi.teks)}
    </p>
  );
}
