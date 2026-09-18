"use client";

import { useEffect, useState } from "react";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

const BUILD_YEAR = 2026;
const WIB = "Asia/Jakarta";

/* Pasangan port Next dari initJam() di assets/js/app.js. Aturannya sama
 * persis, dan itu disengaja: dua port yang menampilkan jam berbeda adalah
 * cacat yang tidak pernah ketahuan sampai ada yang membuka keduanya
 * berdampingan.
 *
 * Angkanya dihitung dari zona waktu Yogyakarta lewat Intl, bukan dari jam
 * perangkat pembaca yang bisa di mana saja. Yang tertulis di layar tidak
 * menyebut "Yogyakarta"; yang menyebut tempatnya "WIB" dan aria-label pada
 * jamnya.
 *
 * Barisnya tidak dirender sama sekali sampai ada angka yang benar. Itu juga
 * yang menjaga render server dan render peramban tetap sama: di server tidak
 * ada jam pembaca, jadi yang dikirim memang kosong. */
function bentuk(opsi: Intl.DateTimeFormatOptions, locale: string) {
  try {
    return new Intl.DateTimeFormat(locale, { timeZone: WIB, ...opsi });
  } catch {
    return null;
  }
}

function useKini(lang: string) {
  const [kini, setKini] = useState<Date | null>(null);

  useEffect(() => {
    setKini(new Date());
    const denyut = window.setInterval(() => setKini(new Date()), 1000);
    return () => window.clearInterval(denyut);
  }, []);

  if (kini === null) return null;

  const jamnya = bentuk({ hour: "2-digit", minute: "2-digit", hour12: false }, "en-GB");
  if (jamnya === null) return null;

  /* Intl tidak mengadu kalau locale yang diminta tidak ada, ia diam diam
     menjawab dengan locale bawaan. Kalau id-ID tidak terpasang, yang keluar
     nama hari Inggris di halaman berbahasa Indonesia. */
  const pilihan = lang === "id" ? "id-ID" : "en-GB";
  const opsi: Intl.DateTimeFormatOptions = {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  };
  let tanggalnya = bentuk(opsi, pilihan);
  if (tanggalnya && !tanggalnya.resolvedOptions().locale.startsWith(pilihan.slice(0, 2))) {
    tanggalnya = bentuk(opsi, "en-GB");
  }
  if (tanggalnya === null) return null;

  return { jam: jamnya.format(kini), tanggal: tanggalnya.format(kini) };
}

export function Footer() {
  const { lang, say } = useLang();
  const [year, setYear] = useState(BUILD_YEAR);
  const kini = useKini(lang);

  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  const [jamDepan, jamBelakang] = kini ? kini.jam.split(":") : ["", ""];

  return (
    <footer className="footer">
      <div className="wrap">
        {kini ? (
          <p className="footer__kini">
            <span className="footer__tanggal">{kini.tanggal}</span>
            <span
              className="jam"
              aria-label={lang === "id" ? "Waktu setempat di Yogyakarta" : "Local time in Yogyakarta"}
            >
              {jamDepan}
              <span className="jam__titik">:</span>
              {jamBelakang}
            </span>
            <span className="footer__zona">WIB</span>
          </p>
        ) : null}

        <div className="footer__bottom">
          <p>
            &copy; {year} {say(COMMON.rights)}
          </p>
        </div>
      </div>
    </footer>
  );
}
