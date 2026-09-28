"use client";

import { useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { Kabar, baik, buruk, type IsiKabar } from "@/components/admin/Kabar";
import { BarisSakelar, Halaman, Terkunci } from "@/components/admin/Setelan";
import type { Akses } from "@/components/admin/akses";
import { pesanDari, ubahSetelan, type KeadaanKeamanan, type Setelan } from "@/lib/api";

export function HalamanNotifikasi({
  keadaan,
  akses,
  muatKeadaan,
  kembali,
}: {
  keadaan: KeadaanKeamanan;
  akses: Akses;
  muatKeadaan: () => Promise<void>;
  kembali: () => void;
}) {
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);

  async function ubah(perubahan: Partial<Setelan>) {
    setKabar(null);
    setSibuk(true);
    try {
      await ubahSetelan(perubahan);
      await muatKeadaan();
      setKabar(
        baik(
          keadaan.surat_siap
            ? "Tersimpan. Kami juga kirim email soal perubahan ini."
            : "Tersimpan.",
        ),
      );
    } catch (e) {
      setKabar(buruk(pesanDari(e)));
    } finally {
      setSibuk(false);
    }
  }

  const mati = sibuk || !akses.penuh;

  return (
    <Halaman
      judul="Notifikasi keamanan"
      kembali={kembali}
      pahlawan="lonceng"
      pengantar={
        <>
          Kami kirim email ke <strong>{keadaan.email}</strong> kalau ada hal penting di akun kamu.
        </>
      }
    >
      <Kabar isi={kabar} />
      {!keadaan.surat_siap ? (
        <p className={`${gaya.kabar} ${gaya.salah}`}>
          Email belum bisa dikirim. Isi SMTP_HOST dan SURAT_DARI di <code>.env</code> dulu.
        </p>
      ) : null}
      {!akses.penuh ? <Terkunci /> : null}

      <ul className={gaya.setelan}>
        <BarisSakelar
          judul="Masuk dari perangkat baru"
          nyala={keadaan.kabar_masuk}
          mati={mati}
          ubah={(nilai) => void ubah({ kabar_masuk: nilai })}
        >
          Dapat email kalau akun kamu dibuka dari HP atau laptop yang belum pernah dipakai.
        </BarisSakelar>
        <BarisSakelar
          judul="Perubahan keamanan"
          nyala={keadaan.kabar_perubahan}
          mati={mati}
          ubah={(nilai) => void ubah({ kabar_perubahan: nilai })}
        >
          Dapat email kalau authenticator, sidik jari, atau wajah ditambah atau dihapus.
        </BarisSakelar>
      </ul>

      <p className={gaya.ket}>
        Mematikan notifikasi juga selalu dikabarkan lewat email. Jadi orang lain tidak bisa
        mematikannya diam diam.
      </p>
    </Halaman>
  );
}
