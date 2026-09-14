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
 * Province names are missing from the Mapbox place_label layer for Indonesia:
 * its "state" class covers other countries but returns nothing here, checked
 * at zoom 4 through 9. The thirty eight names below are carried by the site
 * itself so the provinces can be read at island zoom. Each coordinate is a
 * spot to hang the label on, inside the province but not its centroid and
 * never a boundary. The boundary lines still come from the Mapbox admin layer.
 */
const PROVINSI_ID = {
  type: "FeatureCollection" as const,
  features: (
    [
      ["Aceh", "Aceh", 96.9, 4.7],
      ["Sumatera Utara", "North Sumatra", 99.0, 2.3],
      ["Sumatera Barat", "West Sumatra", 100.5, -0.8],
      ["Riau", "Riau", 101.6, 0.5],
      ["Kepulauan Riau", "Riau Islands", 104.6, 0.9],
      ["Jambi", "Jambi", 102.4, -1.7],
      ["Sumatera Selatan", "South Sumatra", 104.0, -3.3],
      ["Bengkulu", "Bengkulu", 102.3, -3.6],
      ["Lampung", "Lampung", 105.0, -4.9],
      ["Kepulauan Bangka Belitung", "Bangka Belitung Islands", 106.6, -2.7],
      ["Banten", "Banten", 106.1, -6.4],
      ["DKI Jakarta", "Jakarta", 106.83, -6.2],
      ["Jawa Barat", "West Java", 107.6, -7.0],
      ["Jawa Tengah", "Central Java", 110.0, -7.3],
      ["DI Yogyakarta", "Yogyakarta", 110.42, -7.92],
      ["Jawa Timur", "East Java", 112.5, -7.8],
      ["Bali", "Bali", 115.1, -8.4],
      ["Nusa Tenggara Barat", "West Nusa Tenggara", 117.4, -8.7],
      ["Nusa Tenggara Timur", "East Nusa Tenggara", 121.0, -8.9],
      ["Kalimantan Barat", "West Kalimantan", 110.0, 0.2],
      ["Kalimantan Tengah", "Central Kalimantan", 113.4, -1.8],
      ["Kalimantan Selatan", "South Kalimantan", 115.3, -2.9],
      ["Kalimantan Timur", "East Kalimantan", 116.5, 0.6],
      ["Kalimantan Utara", "North Kalimantan", 116.5, 3.2],
      ["Sulawesi Utara", "North Sulawesi", 124.5, 1.2],
      ["Gorontalo", "Gorontalo", 122.4, 0.7],
      ["Sulawesi Tengah", "Central Sulawesi", 120.6, -1.5],
      ["Sulawesi Barat", "West Sulawesi", 119.3, -2.6],
      ["Sulawesi Selatan", "South Sulawesi", 120.0, -4.2],
      ["Sulawesi Tenggara", "Southeast Sulawesi", 122.0, -4.3],
      ["Maluku", "Maluku", 129.3, -3.4],
      ["Maluku Utara", "North Maluku", 127.8, 0.9],
      ["Papua Barat", "West Papua", 132.6, -1.6],
      ["Papua Barat Daya", "Southwest Papua", 131.3, -1.0],
      ["Papua", "Papua", 139.5, -3.3],
      ["Papua Tengah", "Central Papua", 136.5, -3.9],
      ["Papua Pegunungan", "Highland Papua", 138.5, -4.3],
      ["Papua Selatan", "South Papua", 139.8, -7.3],
    ] as [string, string, number, number][]
  ).map((p) => ({
    type: "Feature" as const,
    properties: { name: p[0], name_en: p[1] },
    geometry: { type: "Point" as const, coordinates: [p[2], p[3]] },
  })),
};

/* Labels follow the language switch: Indonesian shows the local name, English
   falls back to the international one. */
function labelField(lang: Lang) {
  return lang === "id"
    ? ["coalesce", ["get", "name"], ["get", "name_en"]]
    : ["coalesce", ["get", "name_en"], ["get", "name"]];
}

/* every layer that carries a name, kept here so the language switch can
   retitle them without rebuilding the whole style */
const LAYER_NAMA = [
  "nama-jalan", "nama-kelurahan", "nama-kota", "nama-provinsi", "nama-provinsi-id",
  "nama-negara", "nama-alam", "nama-poi",
];

function retitleLabels(instance: MapLibreMap, lang: Lang) {
  const field = labelField(lang);
  LAYER_NAMA.forEach((id) => {
    try {
      if (instance.getLayer(id)) instance.setLayoutProperty(id, "text-field", field as never);
    } catch {
      /* style not ready, the next switch will catch it */
    }
  });
}

/* One colour per family of place. They stay muted on purpose: the map is a
   backdrop for the work markers, and a hospital dot must never compete with
   the point it sits behind. */
const KELOMPOK_POI = ["match", ["get", "class"],
  "park_like", "#6f9a63",
  "medical", "#b2626a",
  "education", "#6b7fa8",
  ["food_and_drink", "food_and_drink_stores", "store_like", "commercial_services"], "#a8815f",
  "religion", "#8c7aa6",
  "#8c99a6"];

/**
 * One basemap, drawn here rather than pulled from a Mapbox style URL. Mapbox
 * styles address their sources with mapbox:// URLs that MapLibre cannot
 * resolve, and the raster version of the same style carries no building
 * heights, so the 3D buildings never appeared. Reading the vector tiles
 * directly fixes both.
 */
function mapboxStyle(lang: Lang): StyleSpecification {
  const source = `https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=${TOKEN}`;
  const reguler = ["DIN Pro Regular", "Arial Unicode MS Regular"];
  const tebal = ["DIN Pro Medium", "Arial Unicode MS Regular"];
  const miring = ["DIN Pro Italic", "Arial Unicode MS Regular"];
  const nama = labelField(lang);

  /* road classes grouped the way a driver reads them: toll roads and trunks
     first, then the arteries, then the streets you actually turn into */
  const TOL = ["motorway", "motorway_link", "trunk", "trunk_link"];
  const ARTERI = ["primary", "primary_link", "secondary", "secondary_link"];
  const SEDANG = ["tertiary", "tertiary_link"];
  const JALAN = ["street", "street_limited", "residential", "service", "track"];

  const isClass = (list: string[]) => ["in", ["get", "class"], ["literal", list]];

  return {
    version: 8,
    glyphs: `https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=${TOKEN}`,
    sources: {
      jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
      dem: DEM,
      provinsi: { type: "geojson", data: PROVINSI_ID },
    },
    layers: [
      { id: "latar", type: "background", paint: { "background-color": "#e8ecf1" } },
      {
        id: "bayangan", type: "hillshade", source: "dem",
        paint: { "hillshade-exaggeration": 0.32, "hillshade-shadow-color": "#96a4b0", "hillshade-highlight-color": "#ffffff" },
      },
      {
        id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
        filter: ["in", ["get", "class"], ["literal", ["park", "grass", "wood", "scrub", "agriculture", "national_park", "pitch", "cemetery"]]],
        paint: { "fill-color": "#dfe9dc", "fill-opacity": 0.85 },
      },
      { id: "air", type: "fill", source: "jalan", "source-layer": "water", paint: { "fill-color": "#c3d7e8" } },
      {
        id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
        paint: { "line-color": "#c3d7e8", "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 16, 2.4] },
      },

      /* administrative boundaries, smallest unit first so the larger ones
         draw over it: kabupaten, then provinsi, then negara */
      {
        id: "batas-kabupaten", type: "line", source: "jalan", "source-layer": "admin", minzoom: 5,
        filter: ["all", ["==", ["get", "admin_level"], 2], ["!=", ["get", "maritime"], "true"]],
        paint: {
          "line-color": "#98a6b3", "line-dasharray": [1.4, 1.6], "line-opacity": 0.8,
          "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.5, 10, 1.2, 14, 1.8],
        },
      },
      {
        id: "batas-provinsi", type: "line", source: "jalan", "source-layer": "admin",
        filter: ["all", ["==", ["get", "admin_level"], 1], ["!=", ["get", "maritime"], "true"]],
        paint: {
          "line-color": "#6d7e8e", "line-dasharray": [3, 1.6],
          "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.8, 8, 1.7, 14, 2.8],
        },
      },
      {
        id: "batas-negara", type: "line", source: "jalan", "source-layer": "admin",
        filter: ["==", ["get", "admin_level"], 0],
        paint: {
          "line-color": "#54626f",
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.8, 8, 2, 14, 3.4],
        },
      },

      /* Four tiers, casings first and bodies on top, so the network reads as
         a route map: amber for the toll roads and trunks, a warm cream for
         the arteries, white for everything you turn into. */
      {
        id: "jalan-kecil-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 12,
        filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#c2ccd9", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 12, 1.5, 18, 14] },
      },
      {
        id: "jalan-sedang-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
        filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#b5c2d1", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 10, 1.6, 14, 5, 18, 17] },
      },
      {
        id: "arteri-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
        filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#d8bd7e", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 7, 1.8, 12, 5.5, 18, 21] },
      },
      {
        id: "tol-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
        filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#dd9a2b", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 4, 2, 10, 6.4, 18, 25] },
      },
      {
        id: "jalan-kecil", type: "line", source: "jalan", "source-layer": "road", minzoom: 12,
        filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 12, 0.6, 18, 11] },
      },
      {
        id: "jalan-sedang", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
        filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 10, 0.7, 14, 2.8, 18, 13] },
      },
      {
        id: "arteri", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
        filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#ffefcd", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 7, 0.8, 12, 3.4, 18, 17] },
      },
      {
        id: "tol", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
        filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#ffd27f", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 4, 1, 10, 4.4, 18, 20] },
      },
      /* runways, aprons and the railway, drawn the way an atlas draws them:
         a solid line with a white hatch laid over it */
      {
        id: "apron", type: "fill", source: "jalan", "source-layer": "aeroway", minzoom: 11,
        filter: ["in", ["get", "type"], ["literal", ["apron", "helipad"]]],
        paint: { "fill-color": "#dfe4eb" },
      },
      {
        id: "landasan", type: "line", source: "jalan", "source-layer": "aeroway", minzoom: 10,
        filter: ["in", ["get", "type"], ["literal", ["runway", "taxiway"]]],
        paint: {
          "line-color": "#d3dae3",
          "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
            10, ["match", ["get", "type"], "runway", 1.6, 0.6],
            16, ["match", ["get", "type"], "runway", 14, 5]],
        },
      },
      {
        id: "rel", type: "line", source: "jalan", "source-layer": "road", minzoom: 11,
        filter: ["==", ["get", "class"], "major_rail"],
        paint: { "line-color": "#a6b2bf", "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.9, 18, 3.2] },
      },
      {
        id: "rel-palang", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: ["==", ["get", "class"], "major_rail"],
        paint: {
          "line-color": "#ffffff", "line-dasharray": [2, 3],
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 18, 2],
        },
      },
      {
        id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
        filter: ["!=", ["get", "underground"], true],
        paint: { "fill-color": "#dde2e9", "fill-outline-color": "#c7cfd9" },
      },

      /* which way the traffic runs. The arrows ignore the collision grid, so
         they never take a slot a street name wanted. */
      {
        id: "panah-searah", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 15,
        filter: ["all", ["==", ["get", "oneway"], "true"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
        layout: {
          "symbol-placement": "line", "symbol-spacing": 110,
          "text-field": "\u25b8", "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 15, 9, 18, 13],
          "text-allow-overlap": true, "text-ignore-placement": true,
          "text-rotation-alignment": "map", "text-keep-upright": false, "text-padding": 0,
        },
        paint: { "text-color": "#9fadbb", "text-halo-color": "#ffffff", "text-halo-width": 1 },
      },

      /* the places a rider actually looks for, once the street is close
         enough to matter. Ranked by Mapbox's own filterrank, so a hospital
         arrives before a warung. */
      {
        id: "titik-poi", type: "circle", source: "jalan", "source-layer": "poi_label", minzoom: 15.5,
        filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 16, 2, 17, 3]],
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 15, 2.2, 18, 3.8],
          "circle-color": KELOMPOK_POI,
          "circle-stroke-width": 1, "circle-stroke-color": "#ffffff",
        },
      },
      {
        id: "nama-poi", type: "symbol", source: "jalan", "source-layer": "poi_label", minzoom: 15.5,
        filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 16, 2, 17, 3]],
        layout: {
          "text-field": nama, "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 15.5, 10, 18, 12],
          "text-anchor": "top", "text-offset": [0, 0.6], "text-max-width": 9,
          "symbol-sort-key": ["to-number", ["get", "sizerank"], 30],
        },
        paint: { "text-color": "#5d6a77", "text-halo-color": "#ffffff", "text-halo-width": 1.4 },
      },
      /* Labels, ordered small to large. MapLibre places symbols from the top
         of the stack downwards, so the last layer here wins a clash: a country
         name is never pushed off the map by a village. */
      {
        id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 3,
        filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay", "water", "landform"]]],
        layout: {
          "text-field": nama, "text-font": miring,
          "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10, 10, 13], "text-max-width": 8,
        },
        paint: { "text-color": "#7593aa", "text-halo-color": "#ffffff", "text-halo-width": 1 },
      },
      {
        id: "nama-kelurahan", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 12,
        filter: ["==", ["get", "class"], "settlement_subdivision"],
        layout: {
          "text-field": nama, "text-font": reguler, "text-size": 11, "text-max-width": 8,
          "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20],
        },
        paint: { "text-color": "#68757f", "text-halo-color": "#ffffff", "text-halo-width": 1.2 },
      },

      /* settlements thin out as you pull back: filterrank 1 is a capital, 5 is
         a hamlet, so low zoom keeps only the ranks that fit */
      {
        id: "nama-kota", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 3,
        filter: ["all",
          ["==", ["get", "class"], "settlement"],
          ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 2, 5, 3, 7, 4, 9, 5]]],
        layout: {
          "text-field": nama, "text-font": tebal,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 9, 13, 14, 17], "text-max-width": 8,
          "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20],
        },
        paint: { "text-color": "#2f3b46", "text-halo-color": "#ffffff", "text-halo-width": 1.5 },
      },

      /* road names ride along the line, the way a driver map shows them */
      {
        id: "nama-jalan", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: ["all", ["has", "name"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
        layout: {
          "symbol-placement": "line", "symbol-spacing": 250,
          "text-field": nama, "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 13, 11, 18, 13],
          "text-max-angle": 40, "text-padding": 2, "text-rotation-alignment": "map",
        },
        paint: { "text-color": "#46535f", "text-halo-color": "#ffffff", "text-halo-width": 1.6 },
      },
      {
        id: "nama-provinsi", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 5, maxzoom: 11,
        filter: ["==", ["get", "class"], "state"],
        layout: {
          "text-field": nama, "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 8, 12],
          "text-transform": "uppercase", "text-letter-spacing": 0.12, "text-max-width": 9,
        },
        paint: { "text-color": "#6d7e8e", "text-halo-color": "#ffffff", "text-halo-width": 1.3 },
      },
      {
        id: "nama-provinsi-id", type: "symbol", source: "provinsi", minzoom: 5, maxzoom: 10.5,
        layout: {
          "text-field": nama, "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 8, 12.5],
          "text-transform": "uppercase", "text-letter-spacing": 0.12, "text-max-width": 9,
        },
        paint: { "text-color": "#67788a", "text-halo-color": "#ffffff", "text-halo-width": 1.6 },
      },
      {
        id: "nama-negara", type: "symbol", source: "jalan", "source-layer": "place_label", maxzoom: 5,
        filter: ["==", ["get", "class"], "country"],
        layout: {
          "text-field": nama, "text-font": tebal,
          "text-size": ["interpolate", ["linear"], ["zoom"], 2, 11, 6, 15],
          "text-transform": "uppercase", "text-letter-spacing": 0.1, "text-max-width": 8,
        },
        paint: { "text-color": "#33404c", "text-halo-color": "#ffffff", "text-halo-width": 1.6 },
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

/* Satu tampilan peta bisa dibagikan. Sama persis dengan assets/js/peta.js:
   alamat #peta-<id> membuka petanya tepat di karya itu, dan tiap terbang
   menuliskannya kembali dengan replaceState, bukan dengan location.hash,
   supaya menggeser peta tidak menumpuk riwayat. */
const AWALAN_HASH = "#peta-";

function idDariHash(): string | null {
  if (typeof window === "undefined") return null;
  const hash = window.location.hash || "";
  if (!hash.startsWith(AWALAN_HASH)) return null;
  const id = hash.slice(AWALAN_HASH.length);
  return PROJECTS.some((project) => project.id === id) ? id : null;
}

function tulisHash(id: string | null) {
  if (typeof window === "undefined" || !window.history?.replaceState) return;
  if (id && window.location.hash === AWALAN_HASH + id) return;
  if (!id && !window.location.hash) return;
  const alamat = id ? AWALAN_HASH + id : window.location.pathname + window.location.search;
  try {
    window.history.replaceState(null, "", alamat);
  } catch {
    /* alamat file://, tidak ada riwayat untuk ditulisi */
  }
}

/* Layar sentuh tanpa kursor. Dipakai memutuskan siapa yang butuh
   cooperativeGestures, bukan untuk menebak lebar layar. */
function sentuh(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(hover: none) and (pointer: coarse)").matches;
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
  const dipusatkan = useRef(false);

  const [ready, setReady] = useState(false);
  const [three, setThree] = useState(false);
  const [touring, setTouring] = useState(false);
  const [active, setActive] = useState<Category | null>(null);
  const [counts, setCounts] = useState<Record<Category, number>>({ app: 0, analysis: 0, satellite: 0, design: 0 });
  const [seen, setSeen] = useState<string[]>([]);
  const [folded, setFolded] = useState(false);
  /* Angka di legenda berubah di layar tanpa bunyi apa pun. Wilayah aria-live
     ini yang mengucapkannya, dan ia duduk di luar panel yang bisa dilipat:
     .peta__legenda.is-collapsed menyembunyikan .peta__grup dengan
     display:none, dan aria-live di dalam elemen tersembunyi tidak dibacakan. */
  const [kabar, setKabar] = useState("");

  function umumkan(teks: string) {
    /* dikosongkan lebih dulu supaya pesan yang sama persis tetap terbaca
       sebagai perubahan */
    setKabar("");
    window.setTimeout(() => setKabar(teks), 60);
  }

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
    tulisHash(entry.project.id);
  }

  /* Dipanggil dari luar: tautan "Lihat di peta" di tiap kartu, dan alamat
     #peta-<id> yang dibuka langsung atau dibagikan. */
  function buka(id: string): boolean {
    const entry = entries.current.find((item) => item.project.id === id);
    if (!entry) return false;
    /* Sesudah ini kamera punya tujuan sendiri, dan siap() tidak boleh
       menariknya kembali ke tampilan awal. */
    dipusatkan.current = true;
    stopTour();
    /* karya yang sedang tersaring keluar harus dikembalikan dulu, kalau tidak
       petanya terbang ke penanda yang tidak tergambar */
    if (active && entry.kind !== active) filter(active);
    flyTo(entry, true);
    umumkan(say(PROJECT_PAGE.mapFocus).replace("%w", entry.project.title[lang]));
    return true;
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
    import("maplibre-gl").then((maplibregl) => {
      const bounds = new maplibregl.LngLatBounds();
      PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));
      instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: ms(750) });
    });
    tulisHash(null);
  }

  function filter(kind: Category) {
    const instance = map.current;
    if (!instance) return;
    stopTour();
    const next = active === kind ? null : kind;
    setActive(next);

    import("maplibre-gl").then((maplibregl) => {
      const visible = new maplibregl.LngLatBounds();
      entries.current.forEach((entry) => {
        const show = !next || entry.kind === next;
        entry.marker.getElement().classList.toggle("is-off", !show);
        if (show) visible.extend([entry.project.point.lng, entry.project.point.lat]);
      });
      instance.fitBounds(visible, { padding: 56, maxZoom: next ? 7 : 6, duration: ms(700) });
      recount();
      const tampil = entries.current.filter(
        (entry) => !entry.marker.getElement().classList.contains("is-off"),
      ).length;
      umumkan(
        next
          ? say(PROJECT_PAGE.filterOn)
              .replace("%k", say(KINDS.find((item) => item.key === next)!.label))
              .replace("%n", String(tampil))
              .replace("%t", String(entries.current.length))
          : say(PROJECT_PAGE.filterOff).replace("%t", String(entries.current.length)),
      );
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
    if (TOKEN && map.current) retitleLabels(map.current, lang);
    recount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      if (!holder.current || map.current) return;
      const maplibregl = await import("maplibre-gl");
      if (cancelled || !holder.current) return;

      const bounds = new maplibregl.LngLatBounds();
      PROJECTS.forEach((project) => bounds.extend([project.point.lng, project.point.lat]));

      const instance = new maplibregl.Map({
        container: holder.current,
        style: TOKEN ? mapboxStyle(lang) : FALLBACK_STYLE,
        bounds: bounds as LngLatBoundsLike,
        fitBoundsOptions: { padding: 56, maxZoom: 6 },
        minZoom: 2.5,
        maxZoom: 17,
        maxPitch: 75,
        attributionControl: false,
        /* Kenapa tulisan "Use Ctrl + scroll to zoom the map" tidak ada lagi.

           Tulisan itu datang dari cooperativeGestures, dan ia muncul tiap kali
           pembaca menggulir halaman sambil kursornya kebetulan lewat di atas
           peta. Tetapi tulisan itu ada sebabnya: tanpa dia, roda tetikus di
           atas peta memperbesar peta, bukan menggulir halaman, dan pembaca
           terjebak di tengah halaman. Jadi yang dihapus bukan tulisannya,
           melainkan sebabnya. Di tetikus, roda menggulir halaman, dan peta
           diperbesar lewat tombol + dan -, klik dua kali, atau papan ketik.

           Di layar sentuh keduanya tetap hidup: tanpa cooperativeGestures,
           satu jari di atas peta menggeser peta dan halamannya berhenti bisa
           digulir sama sekali. */
        cooperativeGestures: sentuh(),
        scrollZoom: sentuh(),
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

      /* Penataan sesudah peta berdiri, dan ia TIDAK menumpang pada "load"
         saja. Diukur di port statis, yang kodenya sama: dengan ubin Mapbox
         yang dijawab 403, "load" dan "idle" tidak menyala satu kali pun dalam
         tujuh detik, padahal petanya tergambar dan loaded() menjawab true.
         Akibatnya relief tidak terpasang, ringkasan legenda tinggal kosong,
         dan alamat yang dibagikan tidak pernah dibuka. Sebab yang sama
         mengenai pembaca dengan sambungan lambat.
         Jadi yang dipakai yang pertama tiba di antara ketiga peristiwa itu,
         ditambah satu jaring pengaman berwaktu. Isinya dijalankan sekali, dan
         tidak ada di dalamnya yang menuntut satu ubin pun. */
      let sudahSiap = false;
      const siap = () => {
        if (sudahSiap || cancelled) return;
        sudahSiap = true;
        applyRelief(instance, three);
        instance.resize();
        if (!dipusatkan.current) {
          instance.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
        }
        setReady(true);
        /* fitBounds di atas berdurasi nol, jadi tidak ada gerakan yang bisa
           dibatalkan oleh terbang yang menyusul satu bingkai kemudian */
        window.requestAnimationFrame(() => {
          recount();
          const id = idDariHash();
          if (id) buka(id);
        });
      };

      instance.on("load", siap);
      instance.on("styledata", siap);
      instance.on("idle", siap);
      window.setTimeout(siap, 4000);
      instance.on("move", recount);
      instance.on("zoom", recount);
      /* the tour is a suggestion, not a ride: any hand on the map stops it */
      (["dragstart", "wheel", "touchstart"] as const).forEach((kind) => instance.on(kind, stopTour));

      /* alamat yang berganti tanpa memuat ulang halaman: tautan "Lihat di
         peta" di kartu, dan tombol maju mundur peramban */
      window.addEventListener("hashchange", dengarAlamat);

      map.current = instance;
      /* dipakai tautan di kartu ketika alamatnya sudah benar, jadi hashchange
         tidak akan menyala lagi. Sama dengan port statis. */
      (window as unknown as { HK_PETA_STATE?: { buka: (id: string) => boolean } }).HK_PETA_STATE = { buka };
    }

    function dengarAlamat() {
      const id = idDariHash();
      if (id) buka(id);
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
        window.removeEventListener("hashchange", dengarAlamat);
        stopTour();
        map.current?.remove();
        map.current = null;
      };
    }

    return () => {
      cancelled = true;
      window.removeEventListener("hashchange", dengarAlamat);
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

      <p className="peta__kabar visually-hidden" aria-live="polite">
        {kabar}
      </p>

      <p className="peta__ket">{say(PROJECT_PAGE.mapNote)}</p>
    </section>
  );
}
