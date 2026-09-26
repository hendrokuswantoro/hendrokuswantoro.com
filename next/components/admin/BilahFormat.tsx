"use client";

import { useCallback, useEffect } from "react";
import gaya from "@/app/admin/admin.module.css";


export type Sisip = {
  depan: string;
  belakang?: string;
  baris?: boolean;
  contoh?: string;
};

const TOMBOL: {
  nama: string;
  judul: string;
  pintasan?: string;
  sisip: Sisip;
}[] = [
  { nama: "B", judul: "Tebal", pintasan: "Ctrl B", sisip: { depan: "**", belakang: "**", contoh: "tebal" } },
  { nama: "I", judul: "Miring", pintasan: "Ctrl I", sisip: { depan: "*", belakang: "*", contoh: "miring" } },
  { nama: "H2", judul: "Judul bagian", sisip: { depan: "## ", baris: true, contoh: "Judul bagian" } },
  { nama: "“”", judul: "Kutipan", sisip: { depan: "> ", baris: true, contoh: "Kutipan" } },
  { nama: "•", judul: "Daftar butir", sisip: { depan: "- ", baris: true, contoh: "butir" } },
  { nama: "1.", judul: "Daftar bernomor", sisip: { depan: "1. ", baris: true, contoh: "langkah" } },
  { nama: "⌨", judul: "Kode", sisip: { depan: "`", belakang: "`", contoh: "kode" } },
  { nama: "\u{1F517}", judul: "Tautan", pintasan: "Ctrl K", sisip: { depan: "[", belakang: "](/blog/)", contoh: "teks" } },
];

function sisipkan(kotak: HTMLTextAreaElement, teks: string, sesudah: () => void) {
  kotak.focus();
  let berhasil = false;
  try {
    berhasil = document.execCommand("insertText", false, teks);
  } catch {
    berhasil = false;
  }
  if (!berhasil) {
    const { selectionStart: a, selectionEnd: b, value } = kotak;
    kotak.value = value.slice(0, a) + teks + value.slice(b);
    kotak.selectionStart = kotak.selectionEnd = a + teks.length;
  }
  sesudah();
}

function awalBaris(nilai: string, posisi: number): number {
  const sebelum = nilai.lastIndexOf("\n", Math.max(0, posisi - 1));
  return sebelum === -1 ? 0 : sebelum + 1;
}

export function terapkan(kotak: HTMLTextAreaElement, sisip: Sisip, sesudah: () => void) {
  const { value } = kotak;
  let mulai = kotak.selectionStart;
  let akhir = kotak.selectionEnd;

  if (sisip.baris) {
    mulai = awalBaris(value, mulai);
    const habis = value.indexOf("\n", akhir);
    akhir = habis === -1 ? value.length : habis;
    const baris = value.slice(mulai, akhir);

    kotak.selectionStart = mulai;
    kotak.selectionEnd = akhir;

    if (baris.startsWith(sisip.depan)) {
      sisipkan(kotak, baris.slice(sisip.depan.length), sesudah);
      return;
    }
    const isi = baris || (sisip.contoh ?? "");
    sisipkan(kotak, sisip.depan + isi, sesudah);
    return;
  }

  const dipilih = value.slice(mulai, akhir) || (sisip.contoh ?? "");
  sisipkan(kotak, sisip.depan + dipilih + (sisip.belakang ?? ""), sesudah);

  if (kotak.selectionStart === kotak.selectionEnd && dipilih) {
    const ujung = kotak.selectionEnd - (sisip.belakang ?? "").length;
    kotak.selectionStart = ujung - dipilih.length;
    kotak.selectionEnd = ujung;
  }
}

export function BilahFormat({
  kotak,
  onUbah,
  onGambar,
  kata,
}: {
  kotak: () => HTMLTextAreaElement | null;
  onUbah: () => void;
  onGambar: () => void;
  kata: number;
}) {
  const tekan = useCallback(
    (sisip: Sisip) => {
      const el = kotak();
      if (el) terapkan(el, sisip, onUbah);
    },
    [kotak, onUbah],
  );

  useEffect(() => {
    const el = kotak();
    if (!el) return;

    function pada(peristiwa: KeyboardEvent) {
      if (!(peristiwa.ctrlKey || peristiwa.metaKey) || peristiwa.altKey) return;
      const huruf = peristiwa.key.toLowerCase();
      const pilihan: Record<string, Sisip> = {
        b: { depan: "**", belakang: "**", contoh: "tebal" },
        i: { depan: "*", belakang: "*", contoh: "miring" },
        k: { depan: "[", belakang: "](/blog/)", contoh: "teks" },
      };
      const sisip = pilihan[huruf];
      if (!sisip) return;
      peristiwa.preventDefault();
      terapkan(peristiwa.currentTarget as HTMLTextAreaElement, sisip, onUbah);
    }

    el.addEventListener("keydown", pada);
    return () => el.removeEventListener("keydown", pada);
  }, [kotak, onUbah]);

  return (
    <div className={gaya.bilah} role="toolbar" aria-label="Format tulisan">
      {TOMBOL.map((t) => (
        <button
          key={t.judul}
          type="button"
          className={gaya.bilahTombol}
          title={t.pintasan ? `${t.judul} (${t.pintasan})` : t.judul}
          aria-label={t.judul}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => tekan(t.sisip)}
        >
          {t.nama}
        </button>
      ))}

      <span className={gaya.bilahPisah} aria-hidden="true" />

      <button
        type="button"
        className={gaya.bilahTombol}
        title="Sisipkan foto atau video yang sudah diunggah"
        onMouseDown={(e) => e.preventDefault()}
        onClick={onGambar}
      >
        Foto / video
      </button>

      {}
      <span className={gaya.bilahKata}>{kata} kata</span>
    </div>
  );
}
