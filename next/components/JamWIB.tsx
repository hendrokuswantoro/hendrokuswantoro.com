"use client";

import { useEffect, useState } from "react";
import { useLang } from "./LanguageProvider";

const WIB = "Asia/Jakarta";

/* Tanggal dan jam di kepala halaman. Pasangan port Next dari initJam() di
 * assets/js/app.js, dan aturannya sama persis. Itu disengaja: dua port yang
 * menampilkan jam berbeda adalah cacat yang tidak pernah ketahuan sampai ada
 * yang membuka keduanya berdampingan.
 *
 * Angkanya dihitung dari zona waktu Yogyakarta lewat Intl, bukan dari jam
 * perangkat pembaca yang bisa di mana saja. Yang tertulis di layar tidak
 * menyebut "Yogyakarta"; yang menyebut tempatnya "WIB" di sebelahnya dan
 * aria-label pada jamnya.
 *
 * Tanggalnya pendek, "Sat, 19 Sept 2026". Kepala halaman punya satu baris
 * untuk semuanya, dan nama hari penuh beserta nama bulan penuh menghabiskan
 * dua ratus piksel yang tidak ada.
 *
 * Tidak dirender sama sekali sampai ada angka yang benar. Itu juga yang
 * menjaga render server dan render peramban tetap sama: di server tidak ada
 * jam pembaca, jadi yang dikirim memang kosong.
 */
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
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  };
  let tanggalnya = bentuk(opsi, pilihan);
  if (tanggalnya && !tanggalnya.resolvedOptions().locale.startsWith(pilihan.slice(0, 2))) {
    tanggalnya = bentuk(opsi, "en-GB");
  }
  if (tanggalnya === null) return null;

  return { jam: jamnya.format(kini), tanggal: tanggalnya.format(kini) };
}

export function JamWIB() {
  const { lang } = useLang();
  const kini = useKini(lang);
  if (kini === null) return null;

  const [depan, belakang] = kini.jam.split(":");

  return (
    <p className="kini">
      <span className="kini__tanggal">{kini.tanggal}</span>
      <span
        className="jam"
        aria-label={lang === "id" ? "Waktu setempat di Yogyakarta" : "Local time in Yogyakarta"}
      >
        {depan}
        <span className="jam__titik">:</span>
        {belakang}
      </span>
      <span className="kini__zona">WIB</span>
    </p>
  );
}
