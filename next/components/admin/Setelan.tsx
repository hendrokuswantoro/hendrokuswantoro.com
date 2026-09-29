import { useEffect, useId, useRef, type ReactNode } from "react";
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
  perisai: (
    <>
      <path d="M12 3 5 6v5.5c0 4.3 3 7.9 7 9.5 4-1.6 7-5.2 7-9.5V6z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  lonceng: (
    <>
      <path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z" />
      <path d="M10 20.5a2.2 2.2 0 0 0 4 0" />
    </>
  ),
  gembok: (
    <>
      <rect x="5" y="10.5" width="14" height="10" rx="2" />
      <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5M12 14.5v2" />
    </>
  ),
  geser: (
    <>
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" />
      <circle cx="16" cy="7" r="2" />
      <circle cx="10" cy="17" r="2" />
    </>
  ),
  sandi: (
    <>
      <path d="M4 18h16" />
      <path d="M6 9v5M4 10.5l4 2M4 12.5l4-2M12 9v5M10 10.5l4 2M10 12.5l4-2M18 9v5M16 10.5l4 2M16 12.5l4-2" />
    </>
  ),
  perangkat: (
    <>
      <rect x="4" y="5" width="16" height="11" rx="1.5" />
      <path d="M2.5 19h19" />
    </>
  ),
};

function Ikon({ nama }: { nama: keyof typeof GARIS | string }) {
  return (
    <span className={gaya.ikon} aria-hidden="true">
      <svg viewBox="0 0 24 24">{GARIS[nama]}</svg>
    </span>
  );
}

function Sakelar({
  nyala,
  ubah,
  labelOleh,
  mati = false,
}: {
  nyala: boolean;
  ubah: (nilai: boolean) => void;
  labelOleh: string;
  mati?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={nyala}
      aria-labelledby={labelOleh}
      className={gaya.sakelar}
      disabled={mati}
      onClick={() => ubah(!nyala)}
    >
      <span className={gaya.sakelarBulat} aria-hidden="true">
        <svg viewBox="0 0 24 24">
          {nyala ? <path d="m6.5 12.5 3.5 3.5 7.5-8" /> : <path d="M7 12h10" />}
        </svg>
      </span>
    </button>
  );
}

export function BarisSakelar({
  judul,
  nyala,
  ubah,
  mati = false,
  children,
}: {
  judul: string;
  nyala: boolean;
  ubah: (nilai: boolean) => void;
  mati?: boolean;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <li className={gaya.barisSakelar}>
      <div className={gaya.setelanTeks}>
        <strong id={id}>{judul}</strong>
        <span className={gaya.keterangan}>{children}</span>
      </div>
      <Sakelar nyala={nyala} ubah={ubah} labelOleh={id} mati={mati} />
    </li>
  );
}

export function BarisMenu({
  ikon,
  judul,
  sub,
  buka,
}: {
  ikon: string;
  judul: string;
  sub: ReactNode;
  buka: () => void;
}) {
  return (
    <li>
      <button type="button" className={gaya.barisMenu} onClick={buka}>
        <Ikon nama={ikon} />
        <span className={gaya.setelanTeks}>
          <strong>{judul}</strong>
          <small>{sub}</small>
        </span>
        <svg className={gaya.panah} viewBox="0 0 24 24" aria-hidden="true">
          <path d="m9 6 6 6-6 6" />
        </svg>
      </button>
    </li>
  );
}

export function Halaman({
  judul,
  kembali,
  pahlawan,
  pengantar,
  children,
}: {
  judul: string;
  kembali: () => void;
  pahlawan?: string;
  pengantar?: ReactNode;
  children: ReactNode;
}) {
  const kepala = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const judul = kepala.current;
    if (!judul) return;
    judul.focus({ preventScroll: true });
    if (judul.getBoundingClientRect().top < 80) judul.scrollIntoView({ block: "start" });
  }, []);

  return (
    <div className={gaya.halaman}>
      <div className={gaya.halamanKepala}>
        <button type="button" className={gaya.kembali} onClick={kembali} aria-label="Kembali">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M19 12H5M11 6l-6 6 6 6" />
          </svg>
        </button>
        <h2 ref={kepala} tabIndex={-1}>
          {judul}
        </h2>
      </div>
      {pahlawan ? (
        <div className={gaya.pahlawan}>
          <span className={gaya.pahlawanIkon} aria-hidden="true">
            <svg viewBox="0 0 24 24">{GARIS[pahlawan]}</svg>
          </span>
          {pengantar ? <p className={gaya.penjelasan}>{pengantar}</p> : null}
        </div>
      ) : null}
      {children}
    </div>
  );
}

export function LabelBagian({ children }: { children: ReactNode }) {
  return <p className={gaya.labelBagian}>{children}</p>;
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
