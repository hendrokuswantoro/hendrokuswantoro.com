"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import {
  daftarBerkas,
  hapusBerkas,
  unggahBerkas,
  type Berkas,
  type BerkasBaru,
} from "@/lib/api";

function ukuranTerbaca(bita: number): string {
  if (bita < 1024) return `${bita} B`;
  if (bita < 1024 * 1024) return `${Math.round(bita / 1024)} KB`;
  return `${(bita / (1024 * 1024)).toFixed(1)} MB`;
}

export function PanelBerkas({
  onSisip,
  onTutup,
}: {
  onSisip: (berkas: Berkas) => void;
  onTutup: () => void;
}) {
  const [isi, setIsi] = useState<Berkas[]>([]);
  const [memuat, setMemuat] = useState(true);
  const [kabar, setKabar] = useState<{ teks: string; baik: boolean } | null>(null);
  const [persen, setPersen] = useState<number | null>(null);
  const [seret, setSeret] = useState(false);
  const [buangMetadata, setBuangMetadata] = useState(false);
  const pilih = useRef<HTMLInputElement>(null);

  const muat = useCallback(async () => {
    try {
      const hasil = await daftarBerkas();
      setIsi(hasil.isi);
    } catch (e) {
      setKabar({ teks: e instanceof Error ? e.message : "gagal memuat", baik: false });
    } finally {
      setMemuat(false);
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat]);

  async function kirim(berkas: FileList | File[] | null) {
    if (!berkas || berkas.length === 0) return;
    setKabar(null);

    for (const satu of Array.from(berkas)) {
      setPersen(0);
      try {
        const hasil: BerkasBaru = await unggahBerkas(satu, setPersen, buangMetadata);
        setKabar({
          teks: hasil.sudah_ada
            ? `${hasil.nama_asal} sudah pernah diunggah. Yang lama yang dipakai.`
            : `${hasil.nama_asal} berhasil diunggah.`,
          baik: true,
        });
      } catch (e) {
        setKabar({
          teks: `${satu.name}: ${e instanceof Error ? e.message : "gagal mengunggah"}`,
          baik: false,
        });
      } finally {
        setPersen(null);
      }
    }
    await muat();
  }

  async function buang(berkas: Berkas) {
    if (!window.confirm(`Hapus ${berkas.nama_asal}? Ini tidak bisa dibatalkan.`)) return;
    try {
      await hapusBerkas(berkas.nama);
      setKabar({ teks: `${berkas.nama_asal} sudah dihapus.`, baik: true });
      await muat();
    } catch (e) {
      setKabar({ teks: e instanceof Error ? e.message : "gagal menghapus", baik: false });
    }
  }

  return (
    <section className={gaya.pustaka} aria-label="Foto dan video">
      <div className={gaya.tumpuk}>
        <h3 style={{ margin: 0 }}>Foto dan video</h3>
        <div className={gaya.kanan}>
          <button type="button" className={`${gaya.tombol} ${gaya.kecil}`} onClick={onTutup}>
            Tutup
          </button>
        </div>
      </div>

      <div
        className={`${gaya.jatuh} ${seret ? gaya.jatuhAktif : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setSeret(true);
        }}
        onDragLeave={() => setSeret(false)}
        onDrop={(e) => {
          e.preventDefault();
          setSeret(false);
          void kirim(e.dataTransfer.files);
        }}
      >
        <p style={{ margin: "0 0 10px" }}>
          Seret foto atau video ke sini, atau pilih dari komputer.
        </p>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.utama}`}
          onClick={() => pilih.current?.click()}
          disabled={persen !== null}
        >
          {persen === null ? "Pilih berkas" : `Mengunggah ${persen}%`}
        </button>
        <input
          ref={pilih}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif,image/avif,video/mp4,video/webm"
          multiple
          hidden
          onChange={(e) => {
            void kirim(e.target.files);
            e.target.value = "";
          }}
        />

        {persen !== null ? (
          <div
            className={gaya.laju}
            role="progressbar"
            aria-valuenow={persen}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <span style={{ width: `${persen}%` }} />
          </div>
        ) : null}

        <p className={gaya.ket}>
          Foto maksimal 10 MB, video maksimal 80 MB. Format: PNG, JPEG, WebP, GIF,
          AVIF, MP4, dan WebM.
        </p>

        <label className={gaya.centang} htmlFor="buang-metadata">
          <input
            id="buang-metadata"
            type="checkbox"
            checked={buangMetadata}
            onChange={(e) => setBuangMetadata(e.target.checked)}
          />
          <span>Buang lokasi dan keterangan kamera dari foto</span>
        </label>

        <p className={gaya.ket}>
          Foto dari HP bisa menyimpan lokasi tempat foto diambil. Kalau kotak ini tidak
          dicentang, lokasi itu ikut terbit.
        </p>
        <p className={gaya.ket}>
          Yang bisa dibersihkan cuma JPEG, PNG, dan WebP. GIF dan AVIF ditolak kalau
          kotaknya dicentang, supaya tidak ada foto yang setengah bersih.
        </p>
      </div>

      {kabar ? (
        <p
          className={`${gaya.kabar} ${kabar.baik ? gaya.baik : gaya.salah}`}
          role={kabar.baik ? "status" : "alert"}
        >
          {kabar.teks}
        </p>
      ) : null}

      {memuat ? <p className={gaya.ket}>Memuat...</p> : null}

      {!memuat && isi.length === 0 ? (
        <p className={gaya.ket}>Belum ada berkas yang diunggah.</p>
      ) : null}

      <ul className={gaya.petak}>
        {isi.map((b) => (
          <li key={b.id} className={gaya.petakSatu}>
            <button
              type="button"
              className={gaya.petakGambar}
              title={`Sisipkan ${b.nama_asal}`}
              onClick={() => onSisip(b)}
            >
              {b.jenis === "gambar" ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img src={b.alamat} alt="" loading="lazy" decoding="async" />
              ) : (
                <video src={b.alamat} preload="metadata" muted playsInline />
              )}
            </button>
            <p className={gaya.petakNama} title={b.nama_asal}>
              {b.nama_asal}
            </p>
            <p className={gaya.ket} style={{ margin: 0 }}>
              {b.jenis === "gambar" && b.lebar
                ? `${b.lebar}×${b.tinggi} · `
                : ""}
              {ukuranTerbaca(b.bita)}
            </p>
            <button
              type="button"
              className={`${gaya.tombol} ${gaya.bahaya}`}
              onClick={() => void buang(b)}
            >
              Hapus
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
