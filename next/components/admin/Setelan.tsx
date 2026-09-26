import type { ReactNode } from "react";
import gaya from "@/app/admin/admin.module.css";

const GARIS: Record<string, ReactNode> = {
  surat: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" />
    </>
  ),
  ponsel: (
    <>
      <rect x="7" y="2.5" width="10" height="19" rx="2" />
      <path d="M11 18h2" />
    </>
  ),
  sidik: (
    <>
      <path d="M7.5 18.5c.8-1.5 1.2-3.3 1.2-5.2a3.3 3.3 0 0 1 6.6 0c0 1.2-.1 2.4-.3 3.5" />
      <path d="M5 15.5c.4-1 .6-2.1.6-3.2a6.4 6.4 0 0 1 12.8 0c0 2-.3 4-.9 5.8" />
      <path d="M12 13.3c0 2.6-.6 5-1.8 7.2" />
      <path d="M7 5.5A8.4 8.4 0 0 1 17 5.5" />
    </>
  ),
  wajah: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M9 10v.5M15 10v.5M9 15c1.7 1.4 4.3 1.4 6 0" />
    </>
  ),
  jam: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </>
  ),
};

export function Ikon({ nama }: { nama: keyof typeof GARIS | string }) {
  return (
    <span className={gaya.ikon} aria-hidden="true">
      <svg viewBox="0 0 24 24">{GARIS[nama]}</svg>
    </span>
  );
}

export function Terkunci() {
  return (
    <p className={gaya.terkunci}>
      Dikunci. Masuk ulang pakai authenticator atau sidik jari untuk membukanya.
    </p>
  );
}

export function BarisSetelan({
  ikon,
  judul,
  sub,
  tanda,
  baik = false,
  children,
}: {
  ikon: string;
  judul: string;
  sub: ReactNode;
  tanda?: string;
  baik?: boolean;
  children: ReactNode;
}) {
  return (
    <li>
      <details className={gaya.setelanBaris}>
        <summary>
          <Ikon nama={ikon} />
          <span className={gaya.setelanTeks}>
            <strong>{judul}</strong>
            <small>{sub}</small>
          </span>
          {tanda ? (
            <span className={`${gaya.tanda} ${baik ? gaya.terbit : ""}`}>{tanda}</span>
          ) : null}
          <svg className={gaya.panah} viewBox="0 0 24 24" aria-hidden="true">
            <path d="m9 6 6 6-6 6" />
          </svg>
        </summary>
        <div className={gaya.setelanIsi}>{children}</div>
      </details>
    </li>
  );
}
