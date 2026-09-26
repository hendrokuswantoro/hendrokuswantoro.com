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

/**
 * Pustaka foto dan video, sekaligus tempat mengunggahnya.
 *
 * Yang perlu diketahui sebelum membaca kodenya:
 *
 * - Jenis berkas ditentukan server dari bita pertamanya, bukan dari nama atau
 *   dari `file.type`. Penyaringan di sini hanya supaya penolakannya terasa
 *   lebih cepat, dan ia tidak menjaga apa apa sendirian.
 * - Metadata EXIF dibuang hanya kalau diminta. Foto dari ponsel bisa membawa
 *   koordinat tempat pemotretannya, dan itu akan ikut terbit. Kotak
 *   centangnya mati secara bawaan, sebab yang tahu apakah tempatnya boleh
 *   diketahui umum adalah pemiliknya, bukan layar ini. Kalimatnya tertulis di
 *   layar, bukan hanya di dokumentasi: yang mengunggah foto anaknya di rumah
 *   tidak akan membuka dokumentasi lebih dulu.
 * - Berkas dengan isi yang sama persis tidak digandakan. Server mengembalikan
 *   yang lama, dan layar ini mengatakannya.
 */

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

    // Satu per satu, bukan sekaligus. Enam video delapan puluh megabita yang
    // berangkat bersamaan akan saling berebut sambungan yang sama dan tidak
    // ada satu pun yang selesai lebih cepat karenanya.
    for (const satu of Array.from(berkas)) {
      setPersen(0);
      try {
        const hasil: BerkasBaru = await unggahBerkas(satu, setPersen, buangMetadata);
        setKabar({
          teks: hasil.sudah_ada
            ? `${hasil.nama_asal} sudah pernah diunggah, yang dipakai yang lama`
            : `${hasil.nama_asal} masuk`,
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
      setKabar({ teks: `${berkas.nama_asal} dihapus`, baik: true });
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
          <button type="button" className={gaya.tombol} onClick={onTutup}>
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
          Seret berkasnya ke sini, atau pilih dari komputer.
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
          Foto sampai 10 MB, video sampai 80 MB. Yang diterima PNG, JPEG, WebP,
          GIF, AVIF, MP4, dan WebM.
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
          Kalau kotak itu tidak dicentang, metadata foto tidak dibuang. Foto
          dari ponsel bisa membawa koordinat tempat pemotretannya, dan
          koordinat itu ikut terbit.
        </p>
        <p className={gaya.ket}>
          Yang bisa dibuang JPEG, PNG, dan WebP. GIF dan AVIF ditolak kalau
          kotaknya dicentang, sebab membuang setengah lalu mengaku sudah
          bersih lebih berbahaya daripada tidak membuang sama sekali.
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
