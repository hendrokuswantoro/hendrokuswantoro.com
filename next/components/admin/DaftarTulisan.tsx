"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil, pesanDari } from "@/lib/api";
import { Kabar, buruk } from "./Kabar";

type Ringkas = {
  slug: string;
  status: string;
  tanggal: string | null;
  terbit_pada: string | null;
  judul_en: string;
  judul_id: string;
};

export function DaftarTulisan({
  onSunting,
  onBaru,
  segarkan,
  siap,
  terkunci,
}: {
  onSunting: (slug: string) => void;
  onBaru: () => void;
  segarkan: number;
  siap: boolean;
  terkunci: boolean;
}) {
  const [isi, setIsi] = useState<Ringkas[] | null>(null);
  const [galat, setGalat] = useState("");

  const muat = useCallback(async () => {
    setGalat("");
    try {
      const jawaban = await ambil<{ isi: Ringkas[] }>("/api/v1/admin/blog");
      setIsi(jawaban.isi);
    } catch (e) {
      setGalat(pesanDari(e, "Tulisan gagal dimuat."));
      setIsi([]);
    }
  }, []);

  useEffect(() => {
    if (siap && !terkunci) void muat();
  }, [muat, segarkan, siap, terkunci]);

  const terbit = isi?.filter((t) => t.status === "terbit").length ?? 0;

  return (
    <section className={gaya.kartu} aria-labelledby="judul-tulisan">
      <div className={gaya.tumpuk}>
        <div className={gaya.judulKartu}>
          <h2 id="judul-tulisan">Tulisan</h2>
          {isi && isi.length && !terkunci ? (
            <small>
              {isi.length} tulisan, {terbit} terbit
            </small>
          ) : null}
        </div>
        <div className={gaya.kanan}>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
            onClick={onBaru}
            disabled={terkunci || !siap}
          >
            + Tulisan baru
          </button>
        </div>
      </div>

      {!siap ? (
        <p className={gaya.ket}>Memuat...</p>
      ) : terkunci ? (
        <p className={gaya.ket}>
          Daftar tulisan dikunci sampai kamu masuk pakai authenticator atau sidik jari.
        </p>
      ) : (
        <>
          <Kabar isi={galat ? buruk(galat) : null} />

          {isi === null ? (
            <p className={gaya.ket}>Memuat...</p>
          ) : isi.length === 0 && !galat ? (
            <p className={gaya.ket}>
              Belum ada tulisan. Tekan <strong>Tulisan baru</strong> untuk mulai, atau jalankan{" "}
              <code>python backend/db/muat_awal.py</code> untuk memuat tulisan dari{" "}
              <code>content/</code>.
            </p>
          ) : (
            <ul className={gaya.daftarRingkas}>
              {isi.map((t) => (
                <li key={t.slug}>
                  <span>
                    <strong>{t.judul_id || t.judul_en}</strong>
                    <small>
                      {t.terbit_pada ? `Terbit ${t.terbit_pada}` : "Belum terbit"}, /blog/
                      {t.slug}
                    </small>
                  </span>
                  <span className={gaya.ujungBaris}>
                    <span className={`${gaya.tanda} ${t.status === "terbit" ? gaya.terbit : ""}`}>
                      {t.status}
                    </span>
                    <button
                      type="button"
                      className={`${gaya.tombol} ${gaya.kecil}`}
                      onClick={() => onSunting(t.slug)}
                    >
                      Sunting
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
