"use client";

import { useEffect, useState } from "react";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

/**
 * Satu tombol, bukan dua seperti saklar bahasa: tema hanya punya dua keadaan
 * dan yang kedua selalu "yang satunya", jadi aria-pressed sudah menyatakannya
 * dan labelnya bisa tetap.
 *
 * Bawaannya terang. Dulu palet gelap menempel pada prefers-color-scheme,
 * yang berarti pembaca dengan laptop gelap tidak pernah melihat palet terang
 * dan tidak punya cara memintanya.
 *
 * Yang mencegah kedipan bukan komponen ini melainkan skrip sebaris di
 * app/layout.tsx: React baru menyala setelah hidrasi, jadi kalau atribut
 * data-theme baru dipasang di sini, pembaca yang memilih gelap melihat satu
 * bingkai putih lebih dulu.
 */
export function ThemeSwitch() {
  const { say } = useLang();
  const [gelap, setGelap] = useState(false);

  useEffect(() => {
    setGelap(document.documentElement.getAttribute("data-theme") === "dark");
  }, []);

  function ganti() {
    const berikut = !gelap;
    setGelap(berikut);
    document.documentElement.setAttribute("data-theme", berikut ? "dark" : "light");
    try {
      window.localStorage.setItem("hk-tema", berikut ? "dark" : "light");
    } catch {
      /* mode penyamaran */
    }
  }

  return (
    <button
      className="tema"
      type="button"
      aria-pressed={gelap}
      aria-label={say(COMMON.darkTheme)}
      onClick={ganti}
    >
      <svg className="tema__bulan" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" />
      </svg>
      <svg className="tema__matahari" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
      </svg>
    </button>
  );
}
