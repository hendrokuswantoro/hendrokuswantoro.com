"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import {
  ambil,
  panggil,
  pesanGalat,
  pratinjauTulisan,
  type Berkas,
  type Pratinjau,
} from "@/lib/api";
import { BilahFormat, terapkan } from "./BilahFormat";
import { PanelBerkas } from "./PanelBerkas";

/** Persis kolom yang diterima TulisanMasuk di backend/skema/tulis.py. Kalau
 *  daftar ini dan daftar di sana berbeda, yang ketahuan lebih dulu adalah 422
 *  yang menyebut kolom mana, bukan halaman yang diam. */
const KOLOM = [
  "slug", "tanggal",
  "judul_en", "judul_id",
  "ringkas_en", "ringkas_id",
  "keterangan_en", "keterangan_id",
  "lede_en", "lede_id",
  "tag_en", "tag_id",
  "baca_en", "baca_id",
  "isi_en", "isi_id",
] as const;

type Kolom = (typeof KOLOM)[number];
type Isi = Record<Kolom, string>;

const KOSONG: Isi = KOLOM.reduce((k, nama) => ({ ...k, [nama]: "" }), {} as Isi);

/** Hitungan blok, sekadar untuk memberi tahu lebih awal.
 *
 *  Aturan sebenarnya ditegakkan server lewat tools/markah.py, dan itu memang
 *  tempatnya: aturan yang hanya ada di peramban adalah aturan yang hilang
 *  begitu seseorang memanggil API-nya langsung. Yang di sini hanya supaya
 *  penulisnya tidak menunggu sampai menekan Simpan untuk tahu jumlah
 *  paragrafnya tidak sama. */
function blok(teks: string): number {
  return teks
    .split(/\n{2,}/)
    .map((b) => b.trim())
    .filter(Boolean).length;
}

export function PenyuntingTulisan({
  slug,
  onKembali,
  onBerubah,
}: {
  slug: string | null;
  onKembali: () => void;
  onBerubah: () => void;
}) {
  const [isi, setIsi] = useState<Isi>(KOSONG);
  const [status, setStatus] = useState<string>("belum disimpan");
  const [kabar, setKabar] = useState<{ teks: string; baik: boolean } | null>(null);
  const [sibuk, setSibuk] = useState(false);
  const [pustaka, setPustaka] = useState(false);
  const [lihat, setLihat] = useState(true);
  const [pratinjau, setPratinjau] = useState<Pratinjau | null>(null);
  const [galatMarkah, setGalatMarkah] = useState<string | null>(null);
  const baru = slug === null;

  const kotakEn = useRef<HTMLTextAreaElement>(null);
  const kotakId = useRef<HTMLTextAreaElement>(null);
  /* Kotak yang terakhir disentuh. Tombol bilah format bekerja pada yang ini,
     supaya satu bilah bisa melayani dua bahasa tanpa menggandakannya. */
  const terakhir = useRef<"en" | "id">("en");

  const muat = useCallback(async () => {
    if (slug === null) {
      setIsi(KOSONG);
      setStatus("belum disimpan");
      return;
    }
    try {
      const t = await ambil<Record<string, string | null>>(`/api/v1/admin/blog/${slug}`);
      const ke: Isi = { ...KOSONG };
      for (const nama of KOLOM) ke[nama] = (t[nama] as string) ?? "";
      setIsi(ke);
      setStatus((t.status as string) ?? "draf");
    } catch (e) {
      setKabar({ teks: e instanceof Error ? e.message : "gagal memuat", baik: false });
    }
  }, [slug]);

  useEffect(() => {
    void muat();
  }, [muat]);

  const timpang = useMemo(
    () => blok(isi.isi_en) !== blok(isi.isi_id),
    [isi.isi_en, isi.isi_id],
  );

  /* Pratinjau dibangun server, oleh pembangkit yang sama dengan yang
     membangun halaman blog yang sudah terbit. Jadi yang terlihat di sini
     memang yang akan terbit, dan markah yang ditolak di sini adalah markah
     yang akan ditolak Simpan, dengan kalimat yang sama.

     Ditunda 500 ms sesudah ketikan terakhir. Tanpa penundaan, tiap huruf
     mengirim satu permintaan, dan yang sampai duluan belum tentu yang
     terakhir diketik. */
  useEffect(() => {
    if (!lihat) return;
    if (!isi.isi_en && !isi.isi_id) {
      setPratinjau(null);
      setGalatMarkah(null);
      return;
    }
    let batal = false;
    const tunda = window.setTimeout(() => {
      pratinjauTulisan(isi.isi_en, isi.isi_id)
        .then((hasil) => {
          if (batal) return;
          setPratinjau(hasil);
          setGalatMarkah(null);
        })
        .catch((e) => {
          if (batal) return;
          setGalatMarkah(e instanceof Error ? e.message : "markahnya belum bisa dibaca");
        });
    }, 500);
    return () => {
      batal = true;
      window.clearTimeout(tunda);
    };
  }, [isi.isi_en, isi.isi_id, lihat]);

  function ubah(nama: Kolom, nilai: string) {
    setIsi((s) => ({ ...s, [nama]: nilai }));
  }

  /** Membaca kembali nilai kotak sesudah bilah format menulis ke dalamnya.
   *
   *  Bilah itu menyisipkan lewat execCommand supaya tumpukan urung peramban
   *  tetap utuh, dan execCommand tidak lewat React. Jadi nilainya disalin
   *  balik ke state di sini, sesudahnya. */
  const serap = useCallback(() => {
    if (kotakEn.current) ubah("isi_en", kotakEn.current.value);
    if (kotakId.current) ubah("isi_id", kotakId.current.value);
  }, []);

  /** Menyisipkan gambar atau video ke KEDUA bahasa sekaligus.
   *
   *  Bukan kenyamanan: dua bahasa wajib sebangun blok demi blok, jadi gambar
   *  yang hanya masuk ke satu bahasa langsung membuat tulisannya ditolak.
   *  Keterangannya dikosongkan supaya penulisnya mengisinya sendiri di tiap
   *  bahasa, dan gambar tanpa keterangan tetap sah: ia terbit dengan alt
   *  kosong, yaitu pernyataan "ini hiasan". */
  function sisipBerkas(berkas: Berkas) {
    const tanda = berkas.jenis === "video" ? "!video[](" : "![](";
    const baris = `${tanda}${berkas.alamat})`;
    for (const kotak of [kotakEn.current, kotakId.current]) {
      if (!kotak) continue;
      const perlu = kotak.value && !kotak.value.endsWith("\n\n");
      terapkan(
        kotak,
        { depan: (perlu ? "\n\n" : "") + baris + "\n\n", contoh: "" },
        () => undefined,
      );
    }
    serap();
    setPustaka(false);
    setKabar({
      teks: `${berkas.nama_asal} disisipkan ke kedua bahasa. Isi keterangannya di dalam kurung siku.`,
      baik: true,
    });
  }

  async function simpan() {
    setKabar(null);
    setSibuk(true);
    try {
      const jawaban = baru
        ? await panggil("/api/v1/admin/blog", {
            method: "POST",
            body: JSON.stringify(isi),
          })
        : await panggil(`/api/v1/admin/blog/${slug}`, {
            method: "PATCH",
            body: JSON.stringify(
              Object.fromEntries(KOLOM.filter((k) => k !== "slug").map((k) => [k, isi[k]])),
            ),
          });

      const hasil = await jawaban.json().catch(() => null);
      if (!jawaban.ok) {
        setKabar({ teks: pesanGalat(hasil), baik: false });
        return;
      }
      setKabar({ teks: baru ? "tersimpan sebagai draf" : "tersimpan", baik: true });
      onBerubah();
      if (baru) onKembali();
    } finally {
      setSibuk(false);
    }
  }

  async function ubahStatus(ke: string) {
    const jawaban = await panggil(`/api/v1/admin/blog/${slug}/status`, {
      method: "POST",
      body: JSON.stringify({ status: ke }),
    });
    const hasil = await jawaban.json().catch(() => null);
    if (!jawaban.ok) {
      setKabar({ teks: pesanGalat(hasil), baik: false });
      return;
    }
    setStatus(ke);
    setKabar({ teks: `status jadi ${ke}`, baik: true });
    onBerubah();
  }

  async function hapus() {
    if (!window.confirm(`Hapus "${slug}"? Ini tidak bisa dibatalkan.`)) return;
    const jawaban = await panggil(`/api/v1/admin/blog/${slug}`, { method: "DELETE" });
    if (!jawaban.ok) {
      setKabar({ teks: pesanGalat(await jawaban.json().catch(() => null)), baik: false });
      return;
    }
    onBerubah();
    onKembali();
  }

  const isian = (nama: Kolom, label: string, jenis = "text") => (
    <div className={gaya.baris} key={nama}>
      <label htmlFor={nama}>{label}</label>
      <input
        id={nama}
        className={gaya.isian}
        type={jenis}
        value={isi[nama]}
        disabled={nama === "slug" && !baru}
        onChange={(e) => ubah(nama, e.target.value)}
      />
    </div>
  );

  return (
    <section className={gaya.kartu}>
      <div className={gaya.tumpuk}>
        <h2>{baru ? "Tulisan baru" : "Sunting"}</h2>
        <span className={`${gaya.tanda} ${status === "terbit" ? gaya.terbit : ""}`}>
          {status}
        </span>
        <div className={gaya.kanan}>
          <button type="button" className={gaya.tombol} onClick={onKembali}>
            Kembali
          </button>
        </div>
      </div>

      {kabar ? (
        <p
          className={`${gaya.kabar} ${kabar.baik ? gaya.baik : gaya.salah}`}
          role={kabar.baik ? "status" : "alert"}
        >
          {kabar.teks}
        </p>
      ) : null}

      <div className={gaya.dua}>
        {isian("slug", "Slug, sekaligus alamatnya")}
        {isian("tanggal", "Tanggal", "date")}
      </div>

      <div className={gaya.dua}>
        {isian("judul_en", "Judul, Inggris")}
        {isian("judul_id", "Judul, Indonesia")}
        {isian("ringkas_en", "Ringkas, Inggris")}
        {isian("ringkas_id", "Ringkas, Indonesia")}
        {isian("keterangan_en", "Keterangan meta, Inggris")}
        {isian("keterangan_id", "Keterangan meta, Indonesia")}
        {isian("lede_en", "Lede, Inggris")}
        {isian("lede_id", "Lede, Indonesia")}
        {isian("tag_en", "Tag, Inggris")}
        {isian("tag_id", "Tag, Indonesia")}
        {isian("baca_en", "Lama baca, Inggris")}
        {isian("baca_id", "Lama baca, Indonesia")}
      </div>

      {timpang ? (
        <p className={`${gaya.kabar} ${gaya.salah}`} role="status">
          Jumlah blok tidak sama: Inggris {blok(isi.isi_en)}, Indonesia {blok(isi.isi_id)}.
          Server akan menolaknya. Satu bahasa yang kehilangan satu paragraf adalah
          kegagalan yang diam: halamannya tetap terbit, hanya isinya berbeda tergantung
          bahasa yang sedang dipilih pembaca.
        </p>
      ) : null}

      <BilahFormat
        kotak={() => (terakhir.current === "id" ? kotakId.current : kotakEn.current)}
        onUbah={serap}
        onGambar={() => setPustaka((b) => !b)}
        kata={
          pratinjau
            ? terakhir.current === "id"
              ? pratinjau.kata_id
              : pratinjau.kata_en
            : 0
        }
      />

      {pustaka ? (
        <PanelBerkas onSisip={sisipBerkas} onTutup={() => setPustaka(false)} />
      ) : null}

      <div className={gaya.dua}>
        <div className={gaya.baris}>
          <label htmlFor="isi_en">Isi, Inggris &middot; {blok(isi.isi_en)} blok</label>
          <textarea
            id="isi_en"
            ref={kotakEn}
            className={gaya.luas}
            value={isi.isi_en}
            onFocus={() => {
              terakhir.current = "en";
            }}
            onChange={(e) => ubah("isi_en", e.target.value)}
          />
        </div>
        <div className={gaya.baris}>
          <label htmlFor="isi_id">Isi, Indonesia &middot; {blok(isi.isi_id)} blok</label>
          <textarea
            id="isi_id"
            ref={kotakId}
            className={gaya.luas}
            value={isi.isi_id}
            onFocus={() => {
              terakhir.current = "id";
            }}
            onChange={(e) => ubah("isi_id", e.target.value)}
          />
        </div>
      </div>

      <div className={gaya.tumpuk}>
        <h3 style={{ margin: 0 }}>Pratinjau</h3>
        <div className={gaya.kanan}>
          <button
            type="button"
            className={gaya.tombol}
            aria-pressed={lihat}
            onClick={() => setLihat((b) => !b)}
          >
            {lihat ? "Sembunyikan" : "Tampilkan"}
          </button>
        </div>
      </div>

      {lihat ? (
        galatMarkah ? (
          <p className={`${gaya.kabar} ${gaya.salah}`} role="alert">
            {galatMarkah}
          </p>
        ) : (
          /* dangerouslySetInnerHTML dengan sengaja, dan aman justru karena
             sumbernya.

             HTML ini tidak datang dari orang dan tidak datang dari peramban.
             Ia dibangun tools/markah.py di server, yaitu pengurai yang
             meng-escape seluruh teks, menolak HTML mentah dengan galat, dan
             menolak skema tautan selain http, https, dan mailto. Tidak ada
             satu jalur pun yang membuat markah berubah jadi tag yang tidak
             ada di daftar itu. Membersihkannya lagi di sini berarti dua
             aturan untuk satu hal, dan dua aturan akan berpisah. */
          <div
            className={`${gaya.pratinjau} article`}
            dangerouslySetInnerHTML={{ __html: pratinjau?.html ?? "" }}
          />
        )
      ) : null}

      <div className={gaya.aksi}>
        <button
          type="button"
          className={`${gaya.tombol} ${gaya.utama}`}
          onClick={simpan}
          disabled={sibuk}
        >
          {sibuk ? "Menyimpan..." : "Simpan"}
        </button>

        {!baru ? (
          <>
            <button
              type="button"
              className={gaya.tombol}
              onClick={() => ubahStatus(status === "terbit" ? "draf" : "terbit")}
            >
              {status === "terbit" ? "Jadikan draf" : "Terbitkan"}
            </button>
            <button type="button" className={`${gaya.tombol} ${gaya.bahaya}`} onClick={hapus}>
              Hapus
            </button>
          </>
        ) : null}
      </div>
    </section>
  );
}
