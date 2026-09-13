"use client";

import { useCallback, useEffect, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil } from "@/lib/api";

export type Ringkas = {
  slug: string;
  status: string;
  tanggal: string | null;
  terbit_pada: string | null;
  judul_en: string;
  judul_id: string;
};

/**
 * Daftar tulisan, termasuk draf.
 *
 * Keadaan kosongnya disebut, bukan dibiarkan jadi tabel tanpa baris. Tabel
 * kosong tidak bisa dibedakan dari tabel yang gagal dimuat, dan pembacanya
 * akan menunggu sesuatu yang tidak akan datang.
 */
export function DaftarTulisan({
  onSunting,
  onBaru,
  segarkan,
}: {
  onSunting: (slug: string) => void;
  onBaru: () => void;
  segarkan: number;
}) {
  const [isi, setIsi] = useState<Ringkas[] | null>(null);
  const [galat, setGalat] = useState("");

  const muat = useCallback(async () => {
    setGalat("");
    try {
      const jawaban = await ambil<{ isi: Ringkas[] }>("/api/v1/admin/blog");
      setIsi(jawaban.isi);
    } catch (e) {
      setGalat(e instanceof Error ? e.message : "gagal memuat");
      setIsi([]);
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat, segarkan]);

  return (
    <section className={gaya.kartu}>
      <div className={gaya.tumpuk}>
        <h2>Tulisan</h2>
        <div className={gaya.kanan}>
          <button type="button" className={`${gaya.tombol} ${gaya.utama}`} onClick={onBaru}>
            Tulisan baru
          </button>
        </div>
      </div>

      {galat ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
          {galat}
        </p>
      ) : null}

      {isi === null ? (
        <p className={gaya.ket}>Memuat...</p>
      ) : isi.length === 0 && !galat ? (
        <p className={gaya.ket}>
          Belum ada satu tulisan pun di basis data. Tekan <strong>Tulisan baru</strong> untuk
          memulai, atau jalankan <code>python backend/db/muat_awal.py</code> untuk memuat
          tulisan yang sudah ada di <code>content/</code>.
        </p>
      ) : (
        <div className={gaya.tabelBungkus}>
          <table>
            <thead>
              <tr>
                <th>Judul</th>
                <th>Status</th>
                <th>Tanggal</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {isi.map((t) => (
                <tr key={t.slug}>
                  <td>{t.judul_id || t.judul_en}</td>
                  <td>
                    <span
                      className={`${gaya.tanda} ${t.status === "terbit" ? gaya.terbit : ""}`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td>{t.terbit_pada ?? "belum"}</td>
                  <td>
                    <button
                      type="button"
                      className={gaya.tombol}
                      onClick={() => onSunting(t.slug)}
                    >
                      Sunting
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
