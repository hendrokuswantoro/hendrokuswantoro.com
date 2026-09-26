"use client";

import { useEffect, useRef } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import { PROJECT_PAGE } from "@/content/projects";
import { useLang } from "./LanguageProvider";
import type { PetaHidup } from "./peta/bangun";

type JendelaPeta = Window & {
  HK_PETA_MAP?: PetaHidup["map"];
  HK_PETA_STATE?: PetaHidup["state"];
};

export function WorkMap() {
  const { lang, say } = useLang();
  const section = useRef<HTMLElement | null>(null);
  const holder = useRef<HTMLDivElement>(null);
  const hidup = useRef<PetaHidup | null>(null);

  useEffect(() => {
    hidup.current?.gantiBahasa();
  }, [lang]);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      if (!holder.current || hidup.current) return;
      const [maplibregl, { bangun }] = await Promise.all([import("maplibre-gl"), import("./peta/bangun")]);
      if (cancelled || !holder.current) return;
      hidup.current = bangun(maplibregl, holder.current);
      const jendela = window as JendelaPeta;
      jendela.HK_PETA_MAP = hidup.current.map;
      jendela.HK_PETA_STATE = hidup.current.state;
    }

    function berhenti() {
      cancelled = true;
      hidup.current?.hapus();
      hidup.current = null;
    }

    const node = section.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      void start();
      return berhenti;
    }
    const io = new IntersectionObserver(
      (records) => {
        records.forEach((record) => {
          if (!record.isIntersecting) return;
          io.disconnect();
          void start();
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
    <section className="peta" data-peta ref={section}>
      <div className="peta__frame">
        <div className="peta__kanvas" data-peta-kanvas ref={holder} />
      </div>
      <p className="peta__ket">{say(PROJECT_PAGE.mapNote)}</p>
    </section>
  );
}
