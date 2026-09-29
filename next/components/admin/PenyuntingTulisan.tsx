"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import gaya from "@/app/admin/admin.module.css";
import { ambil, panggil, pesanDari, pesanGalat, pratinjauTulisan, type Berkas, type Pratinjau } from "@/lib/api";
import { BilahFormat, pintasanFormat, terapkan } from "./BilahFormat";
import { Kabar, baik, buruk, type IsiKabar } from "./Kabar";
import { PanelBerkas } from "./PanelBerkas";

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
type Bahasa = "en" | "id";

const KOSONG: Isi = KOLOM.reduce((k, nama) => ({ ...k, [nama]: "" }), {} as Isi);

const UTAMA: [string, Kolom, Kolom][] = [
  ["Judul", "judul_en", "judul_id"],
  ["Ringkas", "ringkas_en", "ringkas_id"],
];

const TAMBAHAN: [string, Kolom, Kolom][] = [
  ["Deskripsi untuk Google", "keterangan_en", "keterangan_id"],
  ["Kalimat pembuka", "lede_en", "lede_id"],
  ["Tag", "tag_en", "tag_id"],
  ["Lama baca", "baca_en", "baca_id"],
];

function paragraf(teks: string): number {
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
  const baru = slug === null;
  const [isi, setIsi] = useState<Isi>(KOSONG);
  const [awal, setAwal] = useState<Isi>(KOSONG);
  const [status, setStatus] = useState(baru ? "belum disimpan" : "draf");
  const [kabar, setKabar] = useState<IsiKabar>(null);
  const [sibuk, setSibuk] = useState(false);
  const [pustaka, setPustaka] = useState(false);
  const [lihat, setLihat] = useState(true);
  const [pratinjau, setPratinjau] = useState<Pratinjau | null>(null);
  const [galatMarkah, setGalatMarkah] = useState<string | null>(null);

  const kotakEn = useRef<HTMLTextAreaElement>(null);
  const kotakId = useRef<HTMLTextAreaElement>(null);
  const terakhir = useRef<Bahasa>("en");

  const berubah = useMemo(() => KOLOM.some((k) => isi[k] !== awal[k]), [isi, awal]);
  const timpang = paragraf(isi.isi_en) !== paragraf(isi.isi_id);
  const adaTambahan = TAMBAHAN.some(([, en, id]) => awal[en] || awal[id]);

  useEffect(() => {
    if (slug === null) return;
    let batal = false;
    ambil<Record<string, string | null>>(`/api/v1/admin/blog/${slug}`)
      .then((t) => {
        if (batal) return;
        const dimuat = { ...KOSONG };
        for (const nama of KOLOM) dimuat[nama] = t[nama] ?? "";
        setIsi(dimuat);
        setAwal(dimuat);
        setStatus(t.status ?? "draf");
      })
      .catch((e) => {
        if (!batal) setKabar(buruk(pesanDari(e, "Tulisan gagal dimuat.")));
      });
    return () => {
      batal = true;
    };
  }, [slug]);

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
          if (!batal) setGalatMarkah(pesanDari(e, "Markahnya belum bisa dibaca."));
        });
    }, 500);
    return () => {
      batal = true;
      window.clearTimeout(tunda);
    };
  }, [isi.isi_en, isi.isi_id, lihat]);

  useEffect(() => {
    if (!berubah) return;
    const tahan = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", tahan);
    return () => window.removeEventListener("beforeunload", tahan);
  }, [berubah]);

  function ubah(nama: Kolom, nilai: string) {
    setIsi((s) => ({ ...s, [nama]: nilai }));
  }

  const serap = useCallback(() => {
    const en = kotakEn.current?.value;
    const id = kotakId.current?.value;
    setIsi((s) => ({ ...s, isi_en: en ?? s.isi_en, isi_id: id ?? s.isi_id }));
  }, []);

  async function kerjakan(kerja: () => Promise<void>) {
    setKabar(null);
    setSibuk(true);
    try {
      await kerja();
    } catch (e) {
      setKabar(buruk(pesanDari(e)));
    } finally {
      setSibuk(false);
    }
  }

  async function kirim(jalur: string, metode: string, badan?: unknown) {
    const jawaban = await panggil(jalur, {
      method: metode,
      body: badan === undefined ? undefined : JSON.stringify(badan),
    });
    if (!jawaban.ok) throw new Error(pesanGalat(await jawaban.json().catch(() => null)));
  }

  const simpan = () =>
    kerjakan(async () => {
      if (baru) {
        await kirim("/api/v1/admin/blog", "POST", isi);
      } else {
        const tanpaSlug = Object.fromEntries(KOLOM.filter((k) => k !== "slug").map((k) => [k, isi[k]]));
        await kirim(`/api/v1/admin/blog/${slug}`, "PATCH", tanpaSlug);
      }
      setAwal(isi);
      onBerubah();
      if (baru) {
        onKembali();
        return;
      }
      setKabar(baik("Tersimpan."));
    });

  const ubahStatus = (ke: "terbit" | "draf") =>
    kerjakan(async () => {
      await kirim(`/api/v1/admin/blog/${slug}/status`, "POST", { status: ke });
      setStatus(ke);
      setKabar(
        baik(
          ke === "terbit"
            ? "Tulisan ditandai terbit. Supaya tampil di situs, klik dua kali tools/terbitkan.cmd di laptop."
            : "Tulisan jadi draf lagi.",
        ),
      );
      onBerubah();
    });

  function hapus() {
    if (!window.confirm(`Hapus "${slug}"? Tulisan yang dihapus tidak bisa dikembalikan.`)) return;
    void kerjakan(async () => {
      await kirim(`/api/v1/admin/blog/${slug}`, "DELETE");
      onBerubah();
      onKembali();
    });
  }

  function kembali() {
    if (berubah && !window.confirm("Ada perubahan yang belum disimpan. Tetap keluar?")) return;
    onKembali();
  }

  const bolehSimpan = !sibuk && (baru || berubah);
  const simpanTerbaru = useRef(simpan);

  useEffect(() => {
    simpanTerbaru.current = simpan;
  });

  useEffect(() => {
    function tekan(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        if (bolehSimpan) void simpanTerbaru.current();
      }
    }
    window.addEventListener("keydown", tekan);
    return () => window.removeEventListener("keydown", tekan);
  }, [bolehSimpan]);

  function sisipBerkas(berkas: Berkas) {
    const baris = `${berkas.jenis === "video" ? "!video[](" : "![]("}${berkas.alamat})`;
    for (const el of [kotakEn.current, kotakId.current]) {
      if (!el) continue;
      const jeda = el.value && !el.value.endsWith("\n\n") ? "\n\n" : "";
      terapkan(el, { depan: `${jeda}${baris}\n\n`, contoh: "" }, () => undefined);
    }
    serap();
    setPustaka(false);
    setKabar(baik(`${berkas.nama_asal} disisipkan ke kedua bahasa. Isi keterangannya di dalam kurung siku.`));
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

  const pasangan = ([label, en, id]: [string, Kolom, Kolom]) => (
    <div className={gaya.dua} key={label}>
      {isian(en, `${label}, Inggris`)}
      {isian(id, `${label}, Indonesia`)}
    </div>
  );

  const kotakIsi = (bahasa: Bahasa, label: string) => {
    const nama: Kolom = bahasa === "en" ? "isi_en" : "isi_id";
    return (
      <div className={gaya.baris}>
        <label htmlFor={nama}>
          {label} <span className={gaya.hitung}>&middot; {paragraf(isi[nama])} paragraf</span>
        </label>
        <textarea
          id={nama}
          ref={bahasa === "en" ? kotakEn : kotakId}
          className={gaya.luas}
          value={isi[nama]}
          onFocus={() => {
            terakhir.current = bahasa;
          }}
          onKeyDown={(e) => pintasanFormat(e, serap)}
          onChange={(e) => ubah(nama, e.target.value)}
        />
      </div>
    );
  };

  return (
    <section className={`${gaya.kartu} ${gaya.penyunting}`} aria-labelledby="judul-penyunting">
      <div className={gaya.tumpuk}>
        <button type="button" className={`${gaya.tombol} ${gaya.kecil} ${gaya.hantu}`} onClick={kembali}>
          &larr; Tulisan
        </button>
        <h2 id="judul-penyunting" className={gaya.judulSunting}>
          {baru ? "Tulisan baru" : isi.judul_id || isi.judul_en || "Sunting"}
        </h2>
        <span className={`${gaya.tanda} ${status === "terbit" ? gaya.terbit : ""}`}>{status}</span>
      </div>

      <Kabar isi={kabar} />

      <fieldset className={gaya.kelompok}>
        <legend>Dasar</legend>
        <div className={gaya.dua}>
          {isian("slug", "Alamat tulisan (slug)")}
          {isian("tanggal", "Tanggal", "date")}
        </div>
      </fieldset>

      <fieldset className={gaya.kelompok}>
        <legend>Judul dan ringkasan</legend>
        {UTAMA.map(pasangan)}
      </fieldset>

      <details className={gaya.kelompokLipat} open={adaTambahan || undefined}>
        <summary>Detail tambahan</summary>
        <p className={gaya.ket}>Deskripsi untuk Google, kalimat pembuka, tag, dan lama baca. Boleh dikosongkan.</p>
        {TAMBAHAN.map(pasangan)}
      </details>

      <fieldset className={gaya.kelompok}>
        <legend>Isi tulisan</legend>

        {timpang ? (
          <p className={`${gaya.kabar} ${gaya.salah}`} role="status">
            Jumlah paragraf belum sama: Inggris {paragraf(isi.isi_en)}, Indonesia {paragraf(isi.isi_id)}.
            Samakan dulu, karena server akan menolaknya.
          </p>
        ) : null}

        <BilahFormat
          kotak={() => (terakhir.current === "id" ? kotakId.current : kotakEn.current)}
          onUbah={serap}
          onGambar={() => setPustaka((b) => !b)}
          gambarTerbuka={pustaka}
          kata={pratinjau ? (terakhir.current === "id" ? pratinjau.kata_id : pratinjau.kata_en) : 0}
        />

        {pustaka ? <PanelBerkas onSisip={sisipBerkas} onTutup={() => setPustaka(false)} /> : null}

        <div className={gaya.dua}>
          {kotakIsi("en", "Isi, Inggris")}
          {kotakIsi("id", "Isi, Indonesia")}
        </div>
      </fieldset>

      <div className={gaya.tumpuk}>
        <h3 className={gaya.subJudul}>Pratinjau</h3>
        <div className={gaya.kanan}>
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.kecil}`}
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
        ) : pratinjau ? (
          <div className={`${gaya.pratinjau} article`} dangerouslySetInnerHTML={{ __html: pratinjau.html }} />
        ) : (
          <p className={gaya.ket}>Pratinjau muncul di sini begitu isi tulisan diketik.</p>
        )
      ) : null}

      <div className={gaya.bilahSimpan}>
        <span className={`${gaya.keadaanSimpan} ${berubah ? gaya.belumTersimpan : ""}`}>
          {berubah ? "Ada perubahan yang belum disimpan" : baru ? "Belum disimpan" : "Semua perubahan tersimpan"}
        </span>
        <div className={gaya.aksi}>
          {!baru ? (
            <>
              <button type="button" className={`${gaya.tombol} ${gaya.bahaya}`} onClick={hapus} disabled={sibuk}>
                Hapus
              </button>
              <button
                type="button"
                className={gaya.tombol}
                onClick={() => void ubahStatus(status === "terbit" ? "draf" : "terbit")}
                disabled={sibuk || berubah}
                title={berubah ? "Simpan dulu perubahannya" : undefined}
              >
                {status === "terbit" ? "Jadikan draf" : "Terbitkan"}
              </button>
            </>
          ) : null}
          <button
            type="button"
            className={`${gaya.tombol} ${gaya.utama}`}
            onClick={() => void simpan()}
            disabled={!bolehSimpan}
            title="Ctrl S"
          >
            {sibuk ? "Menyimpan..." : baru ? "Simpan sebagai draf" : "Simpan"}
          </button>
        </div>
      </div>
    </section>
  );
}
