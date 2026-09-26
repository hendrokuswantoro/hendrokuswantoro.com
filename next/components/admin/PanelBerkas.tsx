"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { daftarBerkas, hapusBerkas, pesanDari, unggahBerkas, type Berkas } from "@/lib/api";
import { Kabar, baik, buruk, type IsiKabar } from "./Kabar";

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
  const [isi, setIsi] = useState<Berkas[] | null>(null);
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [persen, setPersen] = useState<number | null>(null);
  const [seret, setSeret] = useState(false);
  const [buangMetadata, setBuangMetadata] = useState(false);
  const pilih = useRef<HTMLInputElement>(null);

  const muat = useCallback(async () => {
    try {
      setIsi((await daftarBerkas()).isi);
    } catch (e) {
      setIsi([]);
      setKabar(buruk(pesanDari(e, "Daftar berkas gagal dimuat.")));
    }
  }, []);

  useEffect(() => {
    void muat();
  }, [muat]);

  async function kirim(berkas: FileList | null) {
    if (!berkas?.length) return;
    setKabar(null);
    for (const satu of Array.from(berkas)) {
      setPersen(0);
      try {
        const hasil = await unggahBerkas(satu, setPersen, buangMetadata);
        setKabar(
          baik(
            hasil.sudah_ada
              ? `${hasil.nama_asal} sudah pernah diunggah. Yang lama yang dipakai.`
              : `${hasil.nama_asal} berhasil diunggah.`,
          ),
        );
      } catch (e) {
        setKabar(buruk(`${satu.name}: ${pesanDari(e, "gagal mengunggah")}`));
      } finally {
        setPersen(null);
      }
    }
    await muat();
  }

  async function buang(berkas: Berkas) {
    if (!window.confirm(`Hapus ${berkas.nama_asal}? Berkas yang dihapus tidak bisa dikembalikan.`)) return;
    try {
      await hapusBerkas(berkas.nama);
      setKabar(baik(`${berkas.nama_asal} sudah dihapus.`));
      await muat();
    } catch (e) {
      setKabar(buruk(pesanDari(e, "Berkas gagal dihapus.")));
    }
  }

  const mengunggah = persen !== null;

  return (
    <section className={gaya.pustaka} aria-labelledby="judul-pustaka">
      <div className={gaya.tumpuk}>
        <h3 id="judul-pustaka" className={gaya.subJudul}>
          Foto dan video
        </h3>
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
        <p className={gaya.jatuhJudul}>Seret foto atau video ke sini</p>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.kecil} ${gaya.utama}`}
          onClick={() => pilih.current?.click()}
          disabled={mengunggah}
        >
          {mengunggah ? `Mengunggah ${persen}%` : "Pilih dari komputer"}
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
        {mengunggah ? (
          <progress className={gaya.laju} value={persen} max={100} aria-label="Kemajuan unggahan" />
        ) : null}
        <p className={gaya.jatuhKet}>Foto maksimal 10 MB, video 80 MB. PNG, JPEG, WebP, GIF, AVIF, MP4, WebM.</p>
      </div>

      <label className={gaya.centang} htmlFor="buang-metadata">
        <input
          id="buang-metadata"
          type="checkbox"
          checked={buangMetadata}
          onChange={(e) => setBuangMetadata(e.target.checked)}
        />
        <span>
          <strong>Buang lokasi dan data kamera dari foto</strong>
          <small>
            Foto dari HP bisa menyimpan koordinat tempat foto diambil. Tanpa centang, metadata
            tidak dibuang dan koordinat itu ikut terbit. Cuma JPEG, PNG, dan WebP yang bisa
            dibersihkan, jadi GIF dan AVIF ditolak selama kotak ini dicentang.
          </small>
        </span>
      </label>

      <Kabar isi={kabar} />

      {isi === null ? (
        <p className={gaya.ket}>Memuat...</p>
      ) : isi.length === 0 ? (
        <p className={gaya.ket}>Belum ada berkas yang diunggah.</p>
      ) : (
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
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={b.alamat} alt="" loading="lazy" decoding="async" />
                ) : (
                  <video src={b.alamat} preload="metadata" muted playsInline />
                )}
                <span className={gaya.petakSisip}>Sisipkan</span>
              </button>
              <div className={gaya.petakBawah}>
                <span className={gaya.petakTeks}>
                  <strong title={b.nama_asal}>{b.nama_asal}</strong>
                  <small>
                    {b.jenis === "gambar" && b.lebar ? `${b.lebar}×${b.tinggi}, ` : ""}
                    {ukuranTerbaca(b.bita)}
                  </small>
                </span>
                <button
                  type="button"
                  className={gaya.petakHapus}
                  aria-label={`Hapus ${b.nama_asal}`}
                  title="Hapus"
                  onClick={() => void buang(b)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
                  </svg>
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
