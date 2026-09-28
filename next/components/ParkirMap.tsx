"use client";

import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import { PARKIR } from "@/content/parkir-jogja";
import { useLang } from "./LanguageProvider";
import { pustakaPeta } from "./peta/pustaka";
import type { ParkirHidup } from "./peta/parkir";
import type { DataParkir } from "./peta/parkir-hitung";

export function ParkirMap() {
  const { lang, say } = useLang();
  const section = useRef<HTMLElement | null>(null);
  const kanvas = useRef<HTMLDivElement>(null);
  const hidup = useRef<ParkirHidup | null>(null);

  useEffect(() => {
    hidup.current?.gantiBahasa();
  }, [lang]);

  useEffect(() => {
    let batal = false;

    async function mulai() {
      if (!kanvas.current || hidup.current) return;
      const [maplibregl, { bangunParkir }, data] = await Promise.all([
        pustakaPeta(),
        import("./peta/parkir"),
        import("@/content/parkir-data.json"),
      ]);
      if (batal || !kanvas.current) return;
      hidup.current = bangunParkir(maplibregl, kanvas.current, data.default as unknown as DataParkir);
    }

    function berhenti() {
      batal = true;
      hidup.current?.hapus();
      hidup.current = null;
    }

    const node = section.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      void mulai();
      return berhenti;
    }
    const io = new IntersectionObserver(
      (catatan) => {
        catatan.forEach((c) => {
          if (!c.isIntersecting) return;
          io.disconnect();
          void mulai();
        });
      },
      { rootMargin: "500px 0px" },
    );
    io.observe(node);
    return () => {
      io.disconnect();
      berhenti();
    };
  }, []);

  return (
    <section className="peta parkir" data-parkir ref={section} aria-label={say(PARKIR.coba.label)}>
      <div className="parkir__bungkus">
        <div className="peta__frame parkir__frame" data-gagal={say(PARKIR.coba.gagal)}>
          <div className="peta__kanvas" data-parkir-kanvas ref={kanvas} />
        </div>
      </div>
      <p className="peta__ket">{say(PARKIR.coba.ket)}</p>
    </section>
  );
}
