"use client";

import { useEffect, useRef, useState } from "react";
import type { LngLatBoundsLike, Map as MapLibreMap, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { PROJECTS, PROJECT_PAGE } from "@/content/projects";
import { useLang } from "./LanguageProvider";
import type { Lang } from "@/content/i18n";

/* OpenFreeMap serves OpenStreetMap data as vector tiles, free and without an
   API key. CARTO was tried first and now stamps API KEY REQUIRED across every
   tile, so it cannot be used without an account. */
const STYLE = "https://tiles.openfreemap.org/styles/positron";
const ATTRIBUTION =
  '&copy; <a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> ' +
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';

function popupHtml(id: string, lang: Lang): string {
  const project = PROJECTS.find((item) => item.id === id);
  if (!project) return "";
  return (
    `<span class="peta__kind">${project.badge[lang]}</span>` +
    `<strong>${project.title[lang]}</strong>` +
    `<a href="#karya-${project.id}">${PROJECT_PAGE.seeProject[lang]}</a>`
  );
}

/**
 * The library is a third of a megabyte, so it is imported only when the
 * visitor asks for the map. Everything before that click is plain markup.
 */
export function WorkMap() {
  const { lang, say } = useLang();
  const holder = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const popups = useRef<{ id: string; popup: Popup }[]>([]);
  const [live, setLive] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    popups.current.forEach((entry) => entry.popup.setHTML(popupHtml(entry.id, lang)));
  }, [lang]);

  useEffect(() => {
    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  async function start() {
    if (!holder.current || busy || live) return;
    setBusy(true);

    const maplibregl = (await import("maplibre-gl")).default;
    const bounds = new maplibregl.LngLatBounds();
    PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));

    const instance = new maplibregl.Map({
      container: holder.current,
      style: STYLE,
      bounds: bounds as LngLatBoundsLike,
      fitBoundsOptions: { padding: 44, maxZoom: 6 },
      minZoom: 2.5,
      maxZoom: 16,
      attributionControl: false,
      cooperativeGestures: true,
    });

    instance.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: ATTRIBUTION }),
      "bottom-right",
    );
    instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    PROJECTS.forEach((project) => {
      const pin = document.createElement("button");
      pin.type = "button";
      pin.className = "peta__pin";
      pin.setAttribute("data-work", project.id);

      const popup = new maplibregl.Popup({
        offset: 16,
        closeButton: false,
        className: "peta__popup",
      }).setHTML(popupHtml(project.id, lang));

      new maplibregl.Marker({ element: pin })
        .setLngLat([project.point.lng, project.point.lat])
        .setPopup(popup)
        .addTo(instance);

      popups.current.push({ id: project.id, popup });
    });

    instance.on("load", () => {
      instance.resize();
      instance.fitBounds(bounds, { padding: 44, maxZoom: 6, duration: 0 });
    });

    map.current = instance;
    setLive(true);
    setBusy(false);
  }

  return (
    <section className={live ? "peta is-live" : "peta"} aria-busy={busy}>
      <div className="peta__frame">
        <div className="peta__kanvas" ref={holder} />
        <div className="peta__ajakan">
          <h2>{say(PROJECT_PAGE.mapTitle)}</h2>
          <p>{say(PROJECT_PAGE.mapLede)}</p>
          <button className="btn btn--primary" type="button" onClick={start} disabled={busy}>
            {say(PROJECT_PAGE.mapButton)}
          </button>
        </div>
      </div>
      <p className="peta__ket">{say(PROJECT_PAGE.mapNote)}</p>
    </section>
  );
}
