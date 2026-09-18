"use client";

import { useEffect, useState } from "react";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

const BUILD_YEAR = 2026;

export function Footer() {
  const { say } = useLang();
  const [year, setYear] = useState(BUILD_YEAR);

  /* Tahunnya dibetulkan di peramban, bukan dibekukan saat dibangun. Situs
     statis yang dibangun Desember akan menulis tahun lama sepanjang Januari,
     dan tidak ada satu pun yang mengadukannya. Nilai awalnya tetap tahun
     build supaya render server dan render pertama peramban sama. */
  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  return (
    <footer className="footer">
      <div className="wrap">
        <div className="footer__bottom">
          <p>
            &copy; {year} {say(COMMON.rights)}
          </p>
        </div>
      </div>
    </footer>
  );
}
