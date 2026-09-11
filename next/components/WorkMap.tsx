"use client";

import { useEffect, useRef, useState } from "react";
import type { LngLatBoundsLike, Map as MapLibreMap, Marker, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { PROJECTS, PROJECT_PAGE, type Category } from "@/content/projects";
import type { Copy, Lang } from "@/content/i18n";
import { useLang } from "./LanguageProvider";

/* OpenFreeMap serves OpenStreetMap data as vector tiles, free and without an
   API key. CARTO was tried first and now stamps API KEY REQUIRED across every
   tile, so it cannot be used without an account. */
const STYLE = "https://tiles.openfreemap.org/styles/positron";
const KINDS: { key: Category; label: Copy }[] = [
  { key: "app", label: { en: "Map app", id: "Aplikasi peta" } },
  { key: "analysis", label: { en: "Map analysis", id: "Analisis peta" } },
  { key: "satellite", label: { en: "Satellite data", id: "Data satelit" } },
  { key: "design", label: { en: "Map design", id: "Desain peta" } },
];

const TEXT = {
  legend: { en: "Legend", id: "Legenda" } as Copy,
  reset: { en: "Reset view", id: "Kembalikan tampilan" } as Copy,
};

/* the kind a marker takes its colour from, the first one it belongs to */
function kindOf(categories: Category[]): Category {
  return (KINDS.find((entry) => categories.includes(entry.key))?.key ?? "analysis") as Category;
}

function popupHtml(id: string, lang: Lang): string {
  const project = PROJECTS.find((item) => item.id === id);
  if (!project) return "";
  const kind = kindOf(project.categories);
  return (
    `<span class="peta__kind peta__kind--${kind}">${project.badge[lang]}</span>` +
    `<strong>${project.title[lang]}</strong>` +
    `<a href="#karya-${project.id}">${PROJECT_PAGE.seeProject[lang]}</a>`
  );
}

/* Positron is already quiet, these nudges pull it towards the site palette.
   Every change is guarded: a missing layer must never break the map. */
function tuneBasemap(map: MapLibreMap) {
  const tweaks: [string, string, string][] = [
    ["water", "fill-color", "#dbe3ea"],
    ["water_shadow", "fill-color", "#dbe3ea"],
    ["landcover_wood", "fill-color", "#eceee9"],
    ["landcover_grass", "fill-color", "#eef0ec"],
    ["landuse_residential", "fill-color", "#f2f2f2"],
    ["building", "fill-color", "#e9e9e9"],
    ["background", "background-color", "#f7f7f7"],
  ];
  tweaks.forEach(([layer, property, value]) => {
    try {
      if (map.getLayer(layer)) map.setPaintProperty(layer, property, value);
    } catch {
      /* style changed upstream, leave that layer alone */
    }
  });
}

export function WorkMap() {
  const { lang, say } = useLang();
  const holder = useRef<HTMLDivElement>(null);
  const section = useRef<HTMLElement | null>(null);
  const map = useRef<MapLibreMap | null>(null);
  const markers = useRef<{ id: string; kind: Category; lngLat: [number, number]; marker: Marker; popup: Popup }[]>([]);
  const [ready, setReady] = useState(false);
  const [active, setActive] = useState<Category | null>(null);
  const [counts, setCounts] = useState<Record<Category, number>>({ app: 0, analysis: 0, satellite: 0, design: 0 });

  /* the numbers answer one question only: what is on screen right now */
  function recount() {
    const instance = map.current;
    if (!instance) return;
    const view = instance.getBounds();
    const seen: Record<Category, number> = { app: 0, analysis: 0, satellite: 0, design: 0 };
    markers.current.forEach((entry) => {
      if (entry.marker.getElement().classList.contains("is-off")) return;
      if (view.contains(entry.lngLat)) seen[entry.kind] += 1;
    });
    setCounts(seen);
  }

  useEffect(() => {
    markers.current.forEach((entry) => entry.popup.setHTML(popupHtml(entry.id, lang)));
  }, [lang]);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      if (!holder.current || map.current) return;
      const maplibregl = (await import("maplibre-gl")).default;
      if (cancelled || !holder.current) return;

      const bounds = new maplibregl.LngLatBounds();
      PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));

      const instance = new maplibregl.Map({
        container: holder.current,
        style: STYLE,
        bounds: bounds as LngLatBoundsLike,
        fitBoundsOptions: { padding: 56, maxZoom: 6 },
        minZoom: 2.5,
        maxZoom: 16,
        attributionControl: false,
        cooperativeGestures: true,
      });

      instance.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
      instance.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");
      instance.addControl(new maplibregl.FullscreenControl(), "top-right");
      /* the style ships its own credit line, adding ours would repeat it */
      instance.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

      markers.current = PROJECTS.map((project) => {
        const kind = kindOf(project.categories);
        const pin = document.createElement("button");
        pin.type = "button";
        pin.className = "peta__pin";
        pin.setAttribute("data-work", project.id);
        pin.setAttribute("data-kind", kind);
        pin.title = project.title[lang];
        pin.setAttribute("aria-label", project.title[lang]);

        const popup = new maplibregl.Popup({
          offset: 18,
          closeButton: false,
          className: "peta__popup",
        }).setHTML(popupHtml(project.id, lang));

        const marker = new maplibregl.Marker({ element: pin })
          .setLngLat([project.point.lng, project.point.lat])
          .setPopup(popup)
          .addTo(instance);

        return { id: project.id, kind, lngLat: [project.point.lng, project.point.lat] as [number, number], marker, popup };
      });

      instance.on("load", () => {
        tuneBasemap(instance);
        instance.resize();
        instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
        instance.once("idle", recount);
        setReady(true);
      });
      instance.on("moveend", recount);
      instance.on("zoomend", recount);

      map.current = instance;
    }

    /* the library is heavier than the rest of the site, so it waits until the
       section is about to be looked at, then loads without being asked */
    const node = section.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      void start();
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            io.disconnect();
            void start();
          });
        },
        { rootMargin: "500px 0px" },
      );
      io.observe(node);
      return () => {
        cancelled = true;
        io.disconnect();
        map.current?.remove();
        map.current = null;
      };
    }

    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function filter(kind: Category) {
    const instance = map.current;
    if (!instance) return;
    const next = active === kind ? null : kind;
    setActive(next);

    import("maplibre-gl").then(({ default: maplibregl }) => {
      const visible = new maplibregl.LngLatBounds();
      markers.current.forEach((entry) => {
        const show = !next || entry.kind === next;
        entry.marker.getElement().classList.toggle("is-off", !show);
        if (show) visible.extend(entry.lngLat);
      });
      instance.fitBounds(visible, { padding: 56, maxZoom: next ? 7 : 6, duration: 700 });
    });
  }

  function reset() {
    if (active) {
      filter(active);
      return;
    }
    import("maplibre-gl").then(({ default: maplibregl }) => {
      const instance = map.current;
      if (!instance) return;
      const bounds = new maplibregl.LngLatBounds();
      PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));
      instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 700 });
    });
  }

  return (
    <section className="peta" ref={section}>
      <div className={ready ? "peta__frame is-ready" : "peta__frame"}>
        <div className="peta__kanvas" ref={holder} />
      </div>

      <div className={active ? "peta__legenda is-filtered" : "peta__legenda"}>
        <p className="peta__legenda-judul">{say(TEXT.legend)}</p>
        {KINDS.map((entry) => (
          <button
            key={entry.key}
            type="button"
            className={counts[entry.key] === 0 ? "peta__baris is-empty" : "peta__baris"}
            data-kind={entry.key}
            aria-pressed={active === entry.key}
            onClick={() => filter(entry.key)}
          >
            <i />
            <span className="peta__nama">{say(entry.label)}</span>
            <span className="peta__angka">{counts[entry.key]}</span>
          </button>
        ))}
        <button type="button" className="peta__reset" onClick={reset}>
          {say(TEXT.reset)}
        </button>
      </div>

      <p className="peta__ket">{say(PROJECT_PAGE.mapNote)}</p>
    </section>
  );
}
