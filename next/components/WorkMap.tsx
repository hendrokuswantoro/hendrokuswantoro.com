"use client";

import { useEffect, useRef, useState } from "react";
import type { LngLatBoundsLike, Map as MapLibreMap, Marker, Popup, StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { PROJECTS, PROJECT_PAGE, type Category, type Project } from "@/content/projects";
import type { Copy, Lang } from "@/content/i18n";
import { useLang } from "./LanguageProvider";

const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

const MAPBOX_ATTRIBUTION =
  '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noopener">Mapbox</a> ' +
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';

const FALLBACK_STYLE = "https://tiles.openfreemap.org/styles/positron";

const DEM = TOKEN
  ? {
      type: "raster-dem" as const,
      tiles: [`https://api.mapbox.com/v4/mapbox.mapbox-terrain-dem-v1/{z}/{x}/{y}.pngraw?access_token=${TOKEN}`],
      encoding: "mapbox" as const,
      tileSize: 512,
      maxzoom: 14,
    }
  : {
      type: "raster-dem" as const,
      tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
      encoding: "terrarium" as const,
      tileSize: 256,
      maxzoom: 14,
      attribution: "Elevation: Mapzen, AWS Open Data",
    };

/**
 * One basemap, drawn here rather than pulled from a Mapbox style URL. Mapbox
 * styles address their sources with mapbox:// URLs that MapLibre cannot
 * resolve, and the raster version of the same style carries no building
 * heights, so the 3D buildings never appeared. Reading the vector tiles
 * directly fixes both.
 */
function mapboxStyle(): StyleSpecification {
  const source = `https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=${TOKEN}`;
  const font = ["DIN Pro Regular", "Arial Unicode MS Regular"];

  return {
    version: 8,
    glyphs: `https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=${TOKEN}`,
    sources: {
      jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
      dem: DEM,
    },
    layers: [
      { id: "latar", type: "background", paint: { "background-color": "#eef1f5" } },
      {
        id: "bayangan", type: "hillshade", source: "dem",
        paint: { "hillshade-exaggeration": 0.35, "hillshade-shadow-color": "#93a1ad", "hillshade-highlight-color": "#ffffff" },
      },
      {
        id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
        filter: ["in", ["get", "class"], ["literal", ["park", "grass", "wood", "scrub", "agriculture", "national_park", "pitch"]]],
        paint: { "fill-color": "#e0e9dd", "fill-opacity": 0.85 },
      },
      { id: "air", type: "fill", source: "jalan", "source-layer": "water", paint: { "fill-color": "#c7d9e8" } },
      {
        id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
        paint: { "line-color": "#c7d9e8", "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 16, 2.4] },
      },
      {
        id: "jalan-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 6,
        filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary", "secondary", "tertiary", "street", "street_limited"]]],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#d3dae1", "line-width": ["interpolate", ["exponential", 1.4], ["zoom"], 6, 1.2, 12, 4, 18, 22] },
      },
      {
        id: "jalan-isi", type: "line", source: "jalan", "source-layer": "road", minzoom: 6,
        filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary", "secondary", "tertiary", "street", "street_limited"]]],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["match", ["get", "class"], "motorway", "#ffffff", "trunk", "#ffffff", "#fbfcfd"],
          "line-width": ["interpolate", ["exponential", 1.4], ["zoom"], 6, 0.5, 12, 2.4, 18, 17],
        },
      },
      {
        id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
        filter: ["!=", ["get", "underground"], true],
        paint: { "fill-color": "#dfe4ea", "fill-outline-color": "#ccd3db" },
      },
      {
        id: "batas", type: "line", source: "jalan", "source-layer": "admin",
        filter: ["<=", ["get", "admin_level"], 2],
        paint: { "line-color": "#a7b1bc", "line-dasharray": [2.5, 1.5], "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 10, 1.4] },
      },
      {
        id: "nama-tempat", type: "symbol", source: "jalan", "source-layer": "place_label",
        filter: ["in", ["get", "class"], ["literal", ["country", "state", "settlement", "settlement_subdivision"]]],
        layout: {
          "text-field": ["get", "name_en"], "text-font": font,
          "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10, 8, 13, 14, 16], "text-max-width": 8,
        },
        paint: { "text-color": "#41505e", "text-halo-color": "#ffffff", "text-halo-width": 1.4 },
      },
      {
        id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 4,
        filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay"]]],
        layout: {
          "text-field": ["get", "name_en"], "text-font": font,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 10, 13], "text-max-width": 8,
        },
        paint: { "text-color": "#7d94a8", "text-halo-color": "#ffffff", "text-halo-width": 1 },
      },
    ],
  } as StyleSpecification;
}

const KINDS: { key: Category; label: Copy }[] = [
  { key: "app", label: { en: "Map app", id: "Aplikasi peta" } },
  { key: "analysis", label: { en: "Map analysis", id: "Analisis peta" } },
  { key: "satellite", label: { en: "Satellite data", id: "Data satelit" } },
  { key: "design", label: { en: "Map design", id: "Desain peta" } },
];

const TEXT = {
  panel: { en: "Map options", id: "Pilihan peta" } as Copy,
  view: { en: "View", id: "Tampilan" } as Copy,
  tour: { en: "Tour", id: "Jelajah" } as Copy,
  legend: { en: "Legend", id: "Legenda" } as Copy,
  reset: { en: "Reset view", id: "Kembalikan tampilan" } as Copy,
  home: { en: "Back to the starting view", id: "Kembali ke posisi semula" } as Copy,
  none: { en: "Nothing in view", id: "Tidak ada yang terlihat" } as Copy,
  of: { en: "of", id: "dari" } as Copy,
  inView: { en: "in view", id: "terlihat" } as Copy,
  more: { en: "and %n more", id: "dan %n lainnya" } as Copy,
};

function kindOf(categories: Category[]): Category {
  return (KINDS.find((entry) => categories.includes(entry.key))?.key ?? "analysis") as Category;
}

function popupHtml(project: Project, lang: Lang): string {
  const kind = kindOf(project.categories);
  return (
    `<span class="peta__kind peta__kind--${kind}">${project.badge[lang]}</span>` +
    `<strong>${project.title[lang]}</strong>` +
    `<a href="#karya-${project.id}">${PROJECT_PAGE.seeProject[lang]}</a>`
  );
}

type Entry = { project: Project; kind: Category; marker: Marker; popup: Popup };

export function WorkMap() {
  const { lang, say } = useLang();
  const section = useRef<HTMLElement | null>(null);
  const holder = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const entries = useRef<Entry[]>([]);
  const tour = useRef<number>(0);
  const tourAt = useRef<number>(0);

  const [ready, setReady] = useState(false);
  const [three, setThree] = useState(false);
  const [touring, setTouring] = useState(false);
  const [active, setActive] = useState<Category | null>(null);
  const [counts, setCounts] = useState<Record<Category, number>>({ app: 0, analysis: 0, satellite: 0, design: 0 });
  const [seen, setSeen] = useState<string[]>([]);
  const [folded, setFolded] = useState(false);

  function reduced(): boolean {
    return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function ms(value: number): number {
    return reduced() ? 0 : value;
  }

  /* the numbers answer one question only: what is on screen right now */
  function recount() {
    const instance = map.current;
    if (!instance) return;
    const view = instance.getBounds();
    const tally: Record<Category, number> = { app: 0, analysis: 0, satellite: 0, design: 0 };
    const names: string[] = [];
    entries.current.forEach((entry) => {
      if (entry.marker.getElement().classList.contains("is-off")) return;
      if (!view.contains([entry.project.point.lng, entry.project.point.lat])) return;
      tally[entry.kind] += 1;
      names.push(entry.project.title[lang]);
    });
    setCounts(tally);
    setSeen(names);
  }

  /* close enough to read the streets, tilted enough to see the buildings */
  function flyTo(entry: Entry, openPopup: boolean) {
    const instance = map.current;
    if (!instance) return;
    instance.flyTo({
      center: [entry.project.point.lng, entry.project.point.lat],
      zoom: 15.2,
      pitch: three ? 62 : 0,
      bearing: three ? -22 : 0,
      speed: 0.9,
      curve: 1.5,
      duration: ms(2600),
    });
    if (openPopup && !entry.popup.isOpen()) entry.marker.togglePopup();
  }

  function applyRelief(instance: MapLibreMap, on: boolean) {
    const run = () => {
      try {
        if (on) {
          instance.setTerrain({ source: "dem", exaggeration: 1.3 });
          if (instance.getSource("jalan") && !instance.getLayer("gedung3d")) {
            instance.addLayer({
              id: "gedung3d",
              type: "fill-extrusion",
              source: "jalan",
              "source-layer": "building",
              minzoom: 13.5,
              filter: ["all", ["==", ["get", "extrude"], "true"], ["!=", ["get", "underground"], "true"]],
              paint: {
                "fill-extrusion-color": ["interpolate", ["linear"], ["get", "height"], 0, "#e3e7ec", 20, "#d7dce3", 60, "#c9d0d9", 140, "#b9c2cd"],
                "fill-extrusion-height": ["coalesce", ["get", "height"], 6],
                "fill-extrusion-base": ["coalesce", ["get", "min_height"], 0],
                "fill-extrusion-opacity": 0.92,
                "fill-extrusion-vertical-gradient": true,
              },
            });
          }
          if (instance.getLayer("gedung")) instance.setLayoutProperty("gedung", "visibility", "none");
        } else {
          instance.setTerrain(null);
          if (instance.getLayer("gedung3d")) instance.removeLayer("gedung3d");
          if (instance.getLayer("gedung")) instance.setLayoutProperty("gedung", "visibility", "visible");
        }
        return true;
      } catch {
        return false;
      }
    };

    if (run()) return;
    instance.once("styledata", run);
    instance.once("idle", run);
  }

  function stopTour() {
    if (!tour.current) return;
    window.clearInterval(tour.current);
    tour.current = 0;
    setTouring(false);
  }

  function toggleTour() {
    if (tour.current) {
      stopTour();
      return;
    }
    tourAt.current = 0;
    const step = () => {
      const list = entries.current.filter((entry) => !entry.marker.getElement().classList.contains("is-off"));
      if (list.length === 0) return;
      flyTo(list[tourAt.current % list.length], true);
      tourAt.current += 1;
    };
    step();
    tour.current = window.setInterval(step, 7000);
    setTouring(true);
  }

  function home() {
    const instance = map.current;
    if (!instance) return;
    stopTour();
    setActive(null);
    entries.current.forEach((entry) => {
      entry.marker.getElement().classList.remove("is-off");
      if (entry.popup.isOpen()) entry.popup.remove();
    });
    instance.easeTo({ pitch: three ? 58 : 0, bearing: three ? -18 : 0, duration: ms(500) });
    import("maplibre-gl").then(({ default: maplibregl }) => {
      const bounds = new maplibregl.LngLatBounds();
      PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));
      instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: ms(750) });
    });
  }

  function filter(kind: Category) {
    const instance = map.current;
    if (!instance) return;
    stopTour();
    const next = active === kind ? null : kind;
    setActive(next);

    import("maplibre-gl").then(({ default: maplibregl }) => {
      const visible = new maplibregl.LngLatBounds();
      entries.current.forEach((entry) => {
        const show = !next || entry.kind === next;
        entry.marker.getElement().classList.toggle("is-off", !show);
        if (show) visible.extend([entry.project.point.lng, entry.project.point.lat]);
      });
      instance.fitBounds(visible, { padding: 56, maxZoom: next ? 7 : 6, duration: ms(700) });
      recount();
    });
  }

  function toggleThree(on: boolean) {
    const instance = map.current;
    if (!instance || on === three) return;
    setThree(on);
    applyRelief(instance, on);
    /* switching terrain on rebuilds the camera transform, which cancels any
       move started in the same tick, so the tilt waits one frame */
    window.requestAnimationFrame(() => {
      instance.easeTo({ pitch: on ? 58 : 0, bearing: on ? -18 : 0, duration: ms(900) });
    });
  }

  useEffect(() => {
    entries.current.forEach((entry) => entry.popup.setHTML(popupHtml(entry.project, lang)));
    recount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        style: TOKEN ? mapboxStyle() : FALLBACK_STYLE,
        bounds: bounds as LngLatBoundsLike,
        fitBoundsOptions: { padding: 56, maxZoom: 6 },
        minZoom: 2.5,
        maxZoom: 17,
        maxPitch: 75,
        attributionControl: false,
        cooperativeGestures: true,
      });

      instance.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
      instance.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");
      instance.addControl(new maplibregl.FullscreenControl(), "top-right");
      instance.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

      entries.current = PROJECTS.map((project) => {
        const kind = kindOf(project.categories);
        const pin = document.createElement("button");
        pin.type = "button";
        pin.className = "peta__pin";
        pin.setAttribute("data-work", project.id);
        pin.setAttribute("data-kind", kind);
        pin.title = project.title[lang];
        pin.setAttribute("aria-label", project.title[lang]);

        const popup = new maplibregl.Popup({ offset: 18, closeButton: false, className: "peta__popup" })
          .setHTML(popupHtml(project, lang));

        const marker = new maplibregl.Marker({ element: pin })
          .setLngLat([project.point.lng, project.point.lat])
          .setPopup(popup)
          .addTo(instance);

        const entry: Entry = { project, kind, marker, popup };
        pin.addEventListener("click", () => window.setTimeout(() => flyTo(entry, false), 0));
        return entry;
      });

      instance.on("load", () => {
        applyRelief(instance, three);
        instance.resize();
        instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
        instance.once("idle", recount);
        setReady(true);
      });
      instance.on("move", recount);
      instance.on("zoom", recount);
      /* the tour is a suggestion, not a ride: any hand on the map stops it */
      (["dragstart", "wheel", "touchstart"] as const).forEach((kind) => instance.on(kind, stopTour));

      map.current = instance;
    }

    const node = section.current;
    if (!node || typeof IntersectionObserver === "undefined") {
      void start();
    } else {
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
        cancelled = true;
        io.disconnect();
        stopTour();
        map.current?.remove();
        map.current = null;
      };
    }

    return () => {
      cancelled = true;
      stopTour();
      map.current?.remove();
      map.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const total = entries.current.filter((entry) => !entry.marker.getElement().classList.contains("is-off")).length || PROJECTS.length;
  const summary =
    seen.length === 0
      ? say(TEXT.none)
      : `${seen.length} ${say(TEXT.of)} ${total} ${say(TEXT.inView)}. ` +
        seen.slice(0, 2).join(", ") +
        (seen.length > 2 ? `, ${say(TEXT.more).replace("%n", String(seen.length - 2))}` : "") +
        ".";

  return (
    <section className="peta" ref={section}>
      <div className={ready ? "peta__frame is-ready" : "peta__frame"}>
        <div className="peta__kanvas" ref={holder} />
      </div>

      <div className={folded ? "peta__legenda is-collapsed" : "peta__legenda"}>
        <div className="peta__kepala">
          <span className="peta__kepala-judul">{say(TEXT.panel)}</span>
          <button
            type="button"
            className="peta__lipat"
            aria-expanded={!folded}
            aria-label={say(TEXT.panel)}
            onClick={() => {
              setFolded((was) => !was);
              window.setTimeout(() => map.current?.resize(), 220);
            }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="m6 9 6 6 6-6" />
            </svg>
          </button>
        </div>

        <div className="peta__grup">
          <p className="peta__legenda-judul">{say(TEXT.view)}</p>
          <div className="peta__chips">
            <button type="button" className="peta__chip" aria-pressed={!three} onClick={() => toggleThree(false)}>
              2D
            </button>
            <button type="button" className="peta__chip" aria-pressed={three} onClick={() => toggleThree(true)}>
              3D
            </button>
            <button type="button" className="peta__chip" aria-pressed={touring} onClick={toggleTour}>
              {say(TEXT.tour)}
            </button>
          </div>
        </div>

        <div className="peta__grup">
          <p className="peta__legenda-judul">{say(TEXT.legend)}</p>
          <p className="peta__ringkas">{summary}</p>
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
          <button type="button" className="peta__reset" onClick={home}>
            {say(TEXT.reset)}
          </button>
        </div>
      </div>

      <p className="peta__ket">{say(PROJECT_PAGE.mapNote)}</p>
    </section>
  );
}
