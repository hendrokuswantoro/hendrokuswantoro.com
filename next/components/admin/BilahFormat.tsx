"use client";

import type { KeyboardEvent, ReactNode } from "react";
import gaya from "@/app/admin/admin.module.css";

export type Sisip = {
  depan: string;
  belakang?: string;
  baris?: boolean;
  contoh?: string;
};

type Alat = {
  judul: string;
  tanda: ReactNode;
  tombol?: string;
  sisip: Sisip;
};

const garis = (isi: ReactNode) => (
  <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
    {isi}
  </svg>
);

const ALAT: Alat[] = [
  { judul: "Tebal", tanda: <b>B</b>, tombol: "b", sisip: { depan: "**", belakang: "**", contoh: "tebal" } },
  { judul: "Miring", tanda: <i>I</i>, tombol: "i", sisip: { depan: "*", belakang: "*", contoh: "miring" } },
  { judul: "Judul bagian", tanda: <span>H2</span>, sisip: { depan: "## ", baris: true, contoh: "Judul bagian" } },
  {
    judul: "Kutipan",
    tanda: garis(<path d="M7 7h4v4c0 3-1.5 5-4 6M14 7h4v4c0 3-1.5 5-4 6" />),
    sisip: { depan: "> ", baris: true, contoh: "Kutipan" },
  },
  {
    judul: "Daftar butir",
    tanda: garis(<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01" />),
    sisip: { depan: "- ", baris: true, contoh: "butir" },
  },
  {
    judul: "Daftar bernomor",
    tanda: garis(<path d="M10 6h10M10 12h10M10 18h10M4 5l1.5-1v5M3.5 14.5c.4-.6 1-.9 1.6-.8.8.1 1.2.8.9 1.5L3.5 18.5H6.5" />),
    sisip: { depan: "1. ", baris: true, contoh: "langkah" },
  },
  {
    judul: "Kode",
    tanda: garis(<path d="m8 8-4 4 4 4M16 8l4 4-4 4" />),
    sisip: { depan: "`", belakang: "`", contoh: "kode" },
  },
  {
    judul: "Tautan",
    tanda: garis(
      <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />,
    ),
    tombol: "k",
    sisip: { depan: "[", belakang: "](/blog/)", contoh: "teks" },
  },
];

const PINTASAN = new Map(ALAT.filter((a) => a.tombol).map((a) => [a.tombol as string, a.sisip]));

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
    sisipkan(kotak, sisip.depan + (baris || (sisip.contoh ?? "")), sesudah);
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

export function pintasanFormat(peristiwa: KeyboardEvent<HTMLTextAreaElement>, sesudah: () => void) {
  if (!(peristiwa.ctrlKey || peristiwa.metaKey) || peristiwa.altKey) return;
  const sisip = PINTASAN.get(peristiwa.key.toLowerCase());
  if (!sisip) return;
  peristiwa.preventDefault();
  terapkan(peristiwa.currentTarget, sisip, sesudah);
}

export function BilahFormat({
  kotak,
  onUbah,
  onGambar,
  gambarTerbuka,
  kata,
}: {
  kotak: () => HTMLTextAreaElement | null;
  onUbah: () => void;
  onGambar: () => void;
  gambarTerbuka: boolean;
  kata: number;
}) {
  function tekan(sisip: Sisip) {
    const el = kotak();
    if (el) terapkan(el, sisip, onUbah);
  }

  return (
    <div className={gaya.bilah} role="toolbar" aria-label="Format tulisan">
      {ALAT.map((alat) => (
        <button
          key={alat.judul}
          type="button"
          className={gaya.bilahTombol}
          title={alat.tombol ? `${alat.judul} (Ctrl ${alat.tombol.toUpperCase()})` : alat.judul}
          aria-label={alat.judul}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => tekan(alat.sisip)}
        >
          {alat.tanda}
        </button>
      ))}

      <span className={gaya.bilahPisah} aria-hidden="true" />

      <button
        type="button"
        className={`${gaya.bilahTombol} ${gaya.bilahTeks}`}
        aria-pressed={gambarTerbuka}
        onMouseDown={(e) => e.preventDefault()}
        onClick={onGambar}
      >
        {garis(
          <>
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="m3 16 5-5 4 4 3-3 6 6" />
            <circle cx="15.5" cy="9" r="1.4" />
          </>,
        )}
        Foto / video
      </button>

      <span className={gaya.bilahKata}>{kata} kata</span>
    </div>
  );
}
