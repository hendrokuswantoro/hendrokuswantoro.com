import type { Map as MapLibreMap, StyleSpecification } from "maplibre-gl";
import type { Lang } from "@/content/i18n";

export const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

export const FALLBACK_STYLE = "https://tiles.openfreemap.org/styles/positron";

export const DEM = TOKEN
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

export type OpsiGaya = { gelap: boolean; satelit: boolean; medan: boolean; tiga: boolean; lang: Lang };

type Lapis = { id: string; layout?: Record<string, unknown> } & Record<string, unknown>;
type GayaMentah = { layers: Lapis[]; terrain?: unknown } & Record<string, unknown>;

const MAPBOX_ATTRIBUTION =
  '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noopener">Mapbox</a> ' +
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';

const CITRA_ATTRIBUTION =
  '&copy; <a href="https://www.maxar.com/" target="_blank" rel="noopener">Maxar</a>';

function labelField(lang: Lang) {
  return lang === "id"
    ? ["coalesce", ["get", "name"], ["get", "name_en"]]
    : ["coalesce", ["get", "name_en"], ["get", "name"]];
}

const PROVINSI_ID = {
  type: "FeatureCollection" as const,
  features: ([
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
    ["Papua Selatan", "South Papua", 139.8, -7.3]
  ] as [string, string, number, number][]).map(function (p) {
    return {
      type: "Feature" as const,
      properties: { name: p[0], name_en: p[1] },
      geometry: { type: "Point" as const, coordinates: [p[2], p[3]] }
    };
  })
};

export const PALET = {
  terang: {
    latar: "#f1f3f4", latarMedan: "#eeede6",
    pemukiman: "#e8eaed", niaga: "#f1ece4", industri: "#e9e6ee", rumahSakit: "#fbe3e3",
    sekolah: "#ece8f4", bandara: "#e4e7ec", parkir: "#e6e8eb",
    taman: "#c9e9cf", hutan: "#bfe2c6", rumput: "#d4eed9", tani: "#e5efdc", makam: "#d3e6d4",
    pasir: "#f6eed2", es: "#ffffff",
    air: "#9fcbf5", sungai: "#9fcbf5",
    bayanganGelap: "#9aa3ad", bayanganTerang: "#ffffff",
    kontur: "#c7b89f", konturTeks: "#8f7d62",
    batasNegara: "#8d949b", batasProvinsi: "#aab0b6", batasKab: "#c3c7cc",
    tepiKecil: "#dcdfe3", tepiSedang: "#d3d6db", tepiSekunder: "#d0d4d9", tepiPrimer: "#e3c16a", tepiTol: "#dd9d2c",
    isiKecil: "#ffffff", isiSedang: "#ffffff", isiSekunder: "#ffffff", isiPrimer: "#fde7a4", isiTol: "#fbc95a",
    apron: "#e3e6ea", landasan: "#d5d9df", rel: "#b9bec5", relPalang: "#ffffff",
    gedung: "#e7e8ec", gedungTepi: "#d6d8dd",
    gedung3d: ["#eceef1", "#e1e4e8", "#d6d9df", "#c9cdd4", "#b9bec7"],
    panah: "#a4aab1",
    teksKota: "#3c4043", teksKelurahan: "#7d8287", teksJalan: "#5f6368", teksProvinsi: "#80868b",
    teksNegara: "#3c4043", teksAlam: "#3f7fc1", teksGunung: "#6f6252", halo: "#ffffff",
    langit: "#bcd8f5", cakrawala: "#eaf2fb", kabut: "#f1f3f4"
  },
  gelap: {
    latar: "#1f2023", latarMedan: "#22221f",
    pemukiman: "#26282c", niaga: "#2b2925", industri: "#28272d", rumahSakit: "#3a2728",
    sekolah: "#2a2833", bandara: "#2a2d32", parkir: "#292b2f",
    taman: "#1f3526", hutan: "#1c3122", rumput: "#223829", tani: "#262f23", makam: "#233226",
    pasir: "#35311f", es: "#3a3d42",
    air: "#17314c", sungai: "#1d3a58",
    bayanganGelap: "#000000", bayanganTerang: "#4a4d52",
    kontur: "#5a5244", konturTeks: "#a89a82",
    batasNegara: "#80868b", batasProvinsi: "#5f6368", batasKab: "#4a4d52",
    tepiKecil: "#2b2d31", tepiSedang: "#2d2f33", tepiSekunder: "#2f3135", tepiPrimer: "#4d4432", tepiTol: "#5c4a24",
    isiKecil: "#3c3f44", isiSedang: "#45484d", isiSekunder: "#4b4e54", isiPrimer: "#6b5f40", isiTol: "#8a6c30",
    apron: "#2c2f34", landasan: "#3a3d43", rel: "#5f6368", relPalang: "#26282c",
    gedung: "#2d2f33", gedungTepi: "#373a3f",
    gedung3d: ["#34373c", "#3a3d43", "#41444a", "#484c53", "#51555d"],
    panah: "#6f747a",
    teksKota: "#e8eaed", teksKelurahan: "#9aa0a6", teksJalan: "#bdc1c6", teksProvinsi: "#9aa0a6",
    teksNegara: "#e8eaed", teksAlam: "#8ab4f8", teksGunung: "#c6b89e", halo: "#1f2023",
    langit: "#0e1a2b", cakrawala: "#2a3547", kabut: "#1f2023"
  }
};

type Palet = typeof PALET.terang;

const PALET_CITRA: Partial<Palet> = {
  latar: "#0b0f14",
  batasNegara: "rgba(255, 255, 255, .85)", batasProvinsi: "rgba(255, 255, 255, .6)",
  batasKab: "rgba(255, 255, 255, .4)",
  isiKecil: "rgba(255, 255, 255, .32)", isiSedang: "rgba(255, 255, 255, .4)",
  isiSekunder: "rgba(255, 255, 255, .5)", isiPrimer: "rgba(255, 236, 170, .75)", isiTol: "rgba(251, 201, 90, .85)",
  rel: "rgba(255, 255, 255, .35)", relPalang: "rgba(0, 0, 0, 0)", panah: "rgba(255, 255, 255, .75)",
  teksKota: "#ffffff", teksKelurahan: "#e8eaed", teksJalan: "#ffffff", teksProvinsi: "#e8eaed",
  teksNegara: "#ffffff", teksAlam: "#cfe3ff", teksGunung: "#f1e7d3", halo: "rgba(0, 0, 0, .78)"
};

type Poi = { kelas: string[]; warna: string; teks: string; teksGelap: string; jalur: string };

const POI: Record<string, Poi> = {
  makan: { kelas: ["food_and_drink", "food_and_drink_stores"], warna: "#f29900", teks: "#b06000", teksGelap: "#fdc56b",
    jalur: "M7 3v6a2 2 0 0 0 1.4 1.9V21h2.2V10.9A2 2 0 0 0 12 9V3h-1.3v5.2h-.9V3H8.2v5.2h-.9V3zM14.2 3c2.4 1 3.8 3.6 3.8 7v3h-1.6v8h-2.2z" },
  belanja: { kelas: ["store_like", "commercial_services"], warna: "#4285f4", teks: "#1a5fb4", teksGelap: "#8ab4f8",
    jalur: "M5.5 8h13l-1 13h-11zM8.8 8V6.8a3.2 3.2 0 0 1 6.4 0V8h-1.8V6.8a1.4 1.4 0 0 0-2.8 0V8z" },
  kesehatan: { kelas: ["medical"], warna: "#ea4335", teks: "#c5221f", teksGelap: "#f6aea9",
    jalur: "M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" },
  pendidikan: { kelas: ["education"], warna: "#8e6fd8", teks: "#5e45a8", teksGelap: "#c5b3f6",
    jalur: "M12 4 1.5 9.3 12 14.6l8.4-4.2V16H22V9.3zM6 12.6V16c0 1.6 2.8 3.4 6 3.4s6-1.8 6-3.4v-3.4l-6 3z" },
  taman: { kelas: ["park_like", "sport_and_leisure"], warna: "#34a853", teks: "#188038", teksGelap: "#81c995",
    jalur: "M12 2 5.8 11h3.1L4.8 17H11v5h2v-5h6.2l-4.1-6h3.1z" },
  ibadah: { kelas: ["religion"], warna: "#7c848c", teks: "#5f6368", teksGelap: "#bdc1c6",
    jalur: "M12 3l2.6 3.4V9H17l3 3.4V21h-5.4v-4.4a2.6 2.6 0 0 0-5.2 0V21H4v-8.6L7 9h2.4V6.4z" },
  wisata: { kelas: ["arts_and_entertainment", "historic", "landmark", "visitor_amenities"], warna: "#12b5cb", teks: "#0b7f8c", teksGelap: "#78d9ec",
    jalur: "M12 3l2.6 5.6 6.1.7-4.6 4.1 1.3 6L12 16.3l-5.4 3.1 1.3-6-4.6-4.1 6.1-.7z" },
  inap: { kelas: ["lodging"], warna: "#e8457c", teks: "#c2185b", teksGelap: "#f4a3c0",
    jalur: "M3 6h2v7h16v7h-2v-2H5v2H3zM6.5 10a2 2 0 1 0 4 0 2 2 0 0 0-4 0zM11.5 8H17a3 3 0 0 1 3 3v1h-8.5z" },
  transit: { kelas: [], warna: "#1a73e8", teks: "#1967d2", teksGelap: "#8ab4f8",
    jalur: "M7 3h10a2 2 0 0 1 2 2v10a3 3 0 0 1-2.1 2.9L18.1 20h-2.3l-1-2H9.2l-1 2H5.9l1.2-2.1A3 3 0 0 1 5 15V5a2 2 0 0 1 2-2zm0 3v4.2h10V6zm1.6 7a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6zm6.8 0a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6z" },
  bandara: { kelas: [], warna: "#1a73e8", teks: "#1967d2", teksGelap: "#8ab4f8",
    jalur: "M11 2.5a1 1 0 0 1 2 0V9l8 5v2l-8-2.5V19l2 1.5V22l-3-.9-3 .9v-1.5l2-1.5v-5.5L3 16v-2l8-5z" },
  umum: { kelas: [], warna: "#8a9199", teks: "#5f6368", teksGelap: "#bdc1c6",
    jalur: "M12 8.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z" }
};

const URUTAN_POI = ["makan", "belanja", "kesehatan", "pendidikan", "taman", "ibadah", "wisata", "inap"];

function kelompokPoi(): unknown[] {
  const ungkapan: unknown[] = ["match", ["get", "class"]];
  URUTAN_POI.forEach(function (kunci) {
    ungkapan.push(POI[kunci].kelas, kunci);
  });
  ungkapan.push("umum");
  return ungkapan;
}

function warnaTeksPoi(gelap: boolean, satelit: boolean): unknown {
  if (satelit) return "#ffffff";
  const ungkapan: unknown[] = ["match", kelompokPoi()];
  URUTAN_POI.forEach(function (kunci) {
    ungkapan.push(kunci, gelap ? POI[kunci].teksGelap : POI[kunci].teks);
  });
  ungkapan.push(gelap ? POI.umum.teksGelap : POI.umum.teks);
  return ungkapan;
}

export function tambahIkon(map: MapLibreMap, id: string) {
  const kunci = id.replace("hk-poi-", "");
  const def = POI[kunci];
  if (!def || map.hasImage(id)) return;
  const ukuran = 44;
  const kanvas = document.createElement("canvas");
  kanvas.width = ukuran;
  kanvas.height = ukuran;
  const c = kanvas.getContext("2d");
  if (!c || typeof Path2D === "undefined") return;
  c.beginPath();
  c.arc(22, 22, 19, 0, Math.PI * 2);
  c.fillStyle = def.warna;
  c.fill();
  c.lineWidth = 3;
  c.strokeStyle = "#ffffff";
  c.stroke();
  c.save();
  c.translate(10, 10);
  c.scale(1, 1);
  c.fillStyle = "#ffffff";
  c.fill(new Path2D(def.jalur), "evenodd");
  c.restore();
  map.addImage(id, c.getImageData(0, 0, ukuran, ukuran), { pixelRatio: 2 });
}

export const LAYER_NAMA = [
  "nama-poi", "nama-transit", "nama-bandara", "nama-gunung", "nama-alam", "nama-kelurahan",
  "nama-kota", "nama-jalan", "nama-provinsi", "nama-provinsi-id", "nama-negara"
];

function teksNama(id: string, lang: Lang): unknown {
  const nama = labelField(lang);
  if (id === "nama-gunung") {
    return ["concat", "▲ ", nama,
      ["case", ["has", "elevation_m"],
        ["concat", "\n", ["to-string", ["round", ["to-number", ["get", "elevation_m"]]]], " m"], ""]];
  }
  return nama;
}

function lengkapiGaya(o: OpsiGaya, gaya: GayaMentah): StyleSpecification {
  gaya.layers.forEach(function (lapis) {
    if (LAYER_NAMA.indexOf(lapis.id) !== -1) {
      lapis.layout = { ...(lapis.layout || {}), "text-field": teksNama(lapis.id, o.lang) };
    }
  });
  if (o.tiga) gaya.terrain = { source: "dem", exaggeration: 1.3 };
  return gaya as unknown as StyleSpecification;
}

export function mapboxStyle(o: OpsiGaya): StyleSpecification {
  const dasar: Palet = PALET[o.gelap ? "gelap" : "terang"];
  const P: Palet = { ...dasar, ...(o.satelit ? PALET_CITRA : {}) };
  if (o.medan && !o.satelit) P.latar = dasar.latarMedan;

  const source = "https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN;
  const reguler = ["Roboto Regular", "Arial Unicode MS Regular"];
  const sedang = ["Roboto Medium", "Arial Unicode MS Regular"];
  const miring = ["Roboto Italic", "Arial Unicode MS Regular"];

  const TOL = ["motorway", "motorway_link", "trunk", "trunk_link"];
  const PRIMER = ["primary", "primary_link"];
  const ARTERI = ["primary", "primary_link", "secondary", "secondary_link"];
  const SEDANG = ["tertiary", "tertiary_link"];
  const JALAN = ["street", "street_limited", "residential", "service", "track"];

  function isClass(list: string[]) {
    return ["in", ["get", "class"], ["literal", list]];
  }

  function tampak(ya: boolean) {
    return ya ? "visible" : "none";
  }

  const terowongan: unknown[] = ["match", ["get", "structure"], "tunnel", 0.45, 1];
  const alam = !o.satelit;

  function lebar(stops: number[]) {
    return ["interpolate", ["exponential", 1.5], ["zoom"]].concat(stops);
  }

  return lengkapiGaya(o, {
    version: 8,
    glyphs: "https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=" + TOKEN,
    sources: {
      jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
      citra: {
        type: "raster", tileSize: 512, maxzoom: 19, attribution: CITRA_ATTRIBUTION,
        tiles: ["https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.webp?access_token=" + TOKEN]
      },
      kontur: {
        type: "vector", maxzoom: 15,
        tiles: ["https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN]
      },
      dem: DEM,
      provinsi: { type: "geojson", data: PROVINSI_ID }
    },
    sky: {
      "sky-color": o.satelit ? "#8fb7e3" : P.langit,
      "horizon-color": o.satelit ? "#dbe8f5" : P.cakrawala,
      "fog-color": o.satelit ? "#c9d6e3" : P.kabut,
      "sky-horizon-blend": 0.6,
      "horizon-fog-blend": 0.7,
      "fog-ground-blend": 0.9,
      "atmosphere-blend": 0
    },
    layers: [
      { id: "latar", type: "background", paint: { "background-color": P.latar } },
      { id: "citra", type: "raster", source: "citra", layout: { visibility: tampak(o.satelit) },
        paint: { "raster-fade-duration": 180, "raster-saturation": o.gelap ? -0.15 : 0, "raster-brightness-max": o.gelap ? 0.82 : 1 } },
      { id: "bayangan", type: "hillshade", source: "dem", layout: { visibility: tampak(alam) },
        paint: {
          "hillshade-exaggeration": o.medan ? 0.48 : 0.24,
          "hillshade-shadow-color": P.bayanganGelap,
          "hillshade-highlight-color": P.bayanganTerang,
          "hillshade-accent-color": P.bayanganGelap
        } },
      { id: "kawasan", type: "fill", source: "jalan", "source-layer": "landuse", minzoom: 8,
        layout: { visibility: tampak(alam) },
        filter: isClass(["residential", "commercial_area", "industrial", "hospital", "school", "airport", "parking", "facility"]),
        paint: {
          "fill-color": ["match", ["get", "class"],
            "residential", P.pemukiman,
            "commercial_area", P.niaga,
            "industrial", P.industri,
            "hospital", P.rumahSakit,
            "school", P.sekolah,
            "airport", P.bandara,
            "parking", P.parkir,
            P.pemukiman],
          "fill-opacity": ["interpolate", ["linear"], ["zoom"], 8, 0, 10, 1]
        } },
      { id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
        layout: { visibility: tampak(alam) },
        filter: isClass(["park", "grass", "wood", "scrub", "agriculture", "pitch", "cemetery", "sand", "glacier"]),
        paint: {
          "fill-color": ["match", ["get", "class"],
            "park", P.taman,
            "pitch", P.taman,
            "wood", P.hutan,
            ["grass", "scrub"], P.rumput,
            "agriculture", P.tani,
            "cemetery", P.makam,
            "sand", P.pasir,
            "glacier", P.es,
            P.taman],
          "fill-opacity": o.medan ? 1 : 0.9
        } },
      { id: "air", type: "fill", source: "jalan", "source-layer": "water",
        layout: { visibility: tampak(alam) },
        paint: { "fill-color": P.air } },
      { id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
        layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": P.sungai,
          "line-width": ["interpolate", ["exponential", 1.3], ["zoom"], 8,
            ["match", ["get", "class"], ["river", "canal"], 0.8, 0.3],
            17, ["match", ["get", "class"], ["river", "canal"], 6, 2]]
        } },
      { id: "kontur", type: "line", source: "kontur", "source-layer": "contour", minzoom: 11,
        layout: { visibility: tampak(o.medan && alam), "line-join": "round" },
        paint: {
          "line-color": P.kontur,
          "line-opacity": ["match", ["get", "index"], [5, 10], 0.9, 0.55],
          "line-width": ["match", ["get", "index"], [5, 10], 1, 0.5]
        } },

      { id: "batas-kabupaten", type: "line", source: "jalan", "source-layer": "admin", minzoom: 7,
        filter: ["all", ["==", ["get", "admin_level"], 2], ["!=", ["get", "maritime"], "true"]],
        layout: { "line-join": "round" },
        paint: {
          "line-color": P.batasKab,
          "line-dasharray": [1, 2],
          "line-width": ["interpolate", ["linear"], ["zoom"], 7, 0.5, 12, 1, 16, 1.6]
        } },
      { id: "batas-provinsi", type: "line", source: "jalan", "source-layer": "admin",
        filter: ["all", ["==", ["get", "admin_level"], 1], ["!=", ["get", "maritime"], "true"]],
        layout: { "line-join": "round" },
        paint: {
          "line-color": P.batasProvinsi,
          "line-dasharray": [2.5, 2],
          "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 8, 1.2, 14, 2]
        } },
      { id: "batas-negara", type: "line", source: "jalan", "source-layer": "admin",
        filter: ["all", ["==", ["get", "admin_level"], 0], ["!=", ["get", "disputed"], "true"]],
        layout: { "line-join": "round" },
        paint: {
          "line-color": P.batasNegara,
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.8, 8, 1.6, 14, 2.6]
        } },

      { id: "jalan-kecil-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: isClass(JALAN), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.tepiKecil, "line-opacity": terowongan,
          "line-width": lebar([13, 1.4, 16, 6, 18, 15]) } },
      { id: "jalan-sedang-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
        filter: isClass(SEDANG), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.tepiSedang, "line-opacity": terowongan,
          "line-width": lebar([10, 1.4, 14, 4.6, 18, 17]) } },
      { id: "arteri-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
        filter: isClass(ARTERI), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["match", ["get", "class"], PRIMER, P.tepiPrimer, P.tepiSekunder],
          "line-opacity": ["step", ["zoom"],
            ["match", ["get", "class"], PRIMER, terowongan, 0], 9, terowongan],
          "line-width": lebar([7, 1.6, 12, 5, 18, 21]) } },
      { id: "tol-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
        filter: isClass(TOL), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.tepiTol, "line-opacity": terowongan,
          "line-width": lebar([4, 1.8, 10, 5.8, 18, 24]) } },

      { id: "jalan-kecil", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.isiKecil, "line-opacity": terowongan,
          "line-width": lebar([13, 0.6, 16, 4.4, 18, 12.5]) } },
      { id: "jalan-sedang", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
        filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.isiSedang, "line-opacity": terowongan,
          "line-width": lebar([10, 0.6, 14, 2.9, 18, 14]) } },
      { id: "arteri", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
        filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["match", ["get", "class"], PRIMER, P.isiPrimer, P.isiSekunder],
          "line-opacity": ["step", ["zoom"],
            ["match", ["get", "class"], PRIMER, terowongan, 0], 9, terowongan],
          "line-width": lebar([7, 0.8, 12, 3.4, 18, 18]) } },
      { id: "tol", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
        filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": P.isiTol, "line-opacity": terowongan,
          "line-width": lebar([4, 1, 10, 4, 18, 20.5]) } },

      { id: "apron", type: "fill", source: "jalan", "source-layer": "aeroway", minzoom: 11,
        filter: ["in", ["get", "type"], ["literal", ["apron", "helipad"]]],
        layout: { visibility: tampak(alam) },
        paint: { "fill-color": P.apron } },
      { id: "landasan", type: "line", source: "jalan", "source-layer": "aeroway", minzoom: 10,
        filter: ["in", ["get", "type"], ["literal", ["runway", "taxiway"]]],
        layout: { visibility: tampak(alam) },
        paint: {
          "line-color": P.landasan,
          "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
            10, ["match", ["get", "type"], "runway", 1.6, 0.6],
            16, ["match", ["get", "type"], "runway", 14, 5]]
        } },
      { id: "rel", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
        filter: ["==", ["get", "class"], "major_rail"],
        paint: { "line-color": P.rel, "line-width": ["interpolate", ["linear"], ["zoom"], 10, 0.8, 18, 3.2] } },
      { id: "rel-palang", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: ["==", ["get", "class"], "major_rail"],
        paint: {
          "line-color": P.relPalang, "line-dasharray": [2, 3],
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 18, 2]
        } },

      { id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
        filter: ["!=", ["get", "underground"], "true"],
        layout: { visibility: tampak(alam && !o.tiga) },
        paint: {
          "fill-color": P.gedung,
          "fill-outline-color": P.gedungTepi,
          "fill-opacity": ["interpolate", ["linear"], ["zoom"], 14, 0, 15, 1]
        } },
      { id: "gedung3d", type: "fill-extrusion", source: "jalan", "source-layer": "building", minzoom: 13.5,
        filter: ["all", ["==", ["get", "extrude"], "true"], ["!=", ["get", "underground"], "true"]],
        layout: { visibility: tampak(alam && o.tiga) },
        paint: {
          "fill-extrusion-color": ["interpolate", ["linear"], ["get", "height"],
            0, P.gedung3d[0], 3, P.gedung3d[1], 6, P.gedung3d[2], 14, P.gedung3d[3], 40, P.gedung3d[4]],
          "fill-extrusion-height": ["coalesce", ["get", "height"], 6],
          "fill-extrusion-base": ["coalesce", ["get", "min_height"], 0],
          "fill-extrusion-opacity": 0.92,
          "fill-extrusion-vertical-gradient": true
        } },

      { id: "panah-searah", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 16,
        filter: ["all", ["==", ["get", "oneway"], "true"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
        layout: {
          "symbol-placement": "line",
          "symbol-spacing": 120,
          "text-field": "→",
          "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 16, 10, 18, 13],
          "text-allow-overlap": true,
          "text-ignore-placement": true,
          "text-rotation-alignment": "map",
          "text-keep-upright": false,
          "text-padding": 0
        },
        paint: { "text-color": P.panah } },
      { id: "angka-kontur", type: "symbol", source: "kontur", "source-layer": "contour", minzoom: 12,
        filter: ["match", ["get", "index"], [5, 10], true, false],
        layout: {
          visibility: tampak(o.medan && alam),
          "symbol-placement": "line",
          "symbol-spacing": 320,
          "text-field": ["concat", ["to-string", ["get", "ele"]], " m"],
          "text-font": reguler,
          "text-size": 10,
          "text-max-angle": 25,
          "text-padding": 6
        },
        paint: { "text-color": P.konturTeks, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

      { id: "nama-poi", type: "symbol", source: "jalan", "source-layer": "poi_label", minzoom: 14.5,
        filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 15.5, 2, 16.5, 3, 17.5, 4]],
        layout: {
          "icon-image": ["concat", "hk-poi-", kelompokPoi()],
          "icon-size": ["interpolate", ["linear"], ["zoom"], 14.5, 0.8, 17, 1],
          "text-font": sedang,
          "text-size": ["interpolate", ["linear"], ["zoom"], 14.5, 10.5, 18, 12.5],
          "text-variable-anchor": ["left", "right", "top", "bottom"],
          "text-radial-offset": 1.05,
          "text-justify": "auto",
          "text-max-width": 8,
          "text-optional": true,
          "symbol-sort-key": ["to-number", ["get", "sizerank"], 30]
        },
        paint: { "text-color": warnaTeksPoi(o.gelap, o.satelit), "text-halo-color": P.halo, "text-halo-width": 1.6 } },
      { id: "nama-transit", type: "symbol", source: "jalan", "source-layer": "transit_stop_label", minzoom: 12.5,
        filter: ["all", ["==", ["get", "stop_type"], "station"],
          ["in", ["get", "mode"], ["literal", ["rail", "metro_rail", "light_rail", "monorail", "tram"]]]],
        layout: {
          "icon-image": "hk-poi-transit",
          "icon-size": ["interpolate", ["linear"], ["zoom"], 12.5, 0.8, 16, 1],
          "text-font": sedang,
          "text-size": ["interpolate", ["linear"], ["zoom"], 12.5, 10.5, 18, 12.5],
          "text-variable-anchor": ["left", "right", "top", "bottom"],
          "text-radial-offset": 1.05,
          "text-justify": "auto",
          "text-max-width": 8,
          "text-optional": true
        },
        paint: {
          "text-color": o.satelit ? "#ffffff" : (o.gelap ? POI.transit.teksGelap : POI.transit.teks),
          "text-halo-color": P.halo, "text-halo-width": 1.6
        } },
      { id: "nama-bandara", type: "symbol", source: "jalan", "source-layer": "airport_label", minzoom: 8,
        filter: ["<=", ["to-number", ["get", "sizerank"], 10], ["step", ["zoom"], 12, 10, 16]],
        layout: {
          "icon-image": "hk-poi-bandara",
          "text-font": sedang,
          "text-size": ["interpolate", ["linear"], ["zoom"], 8, 10.5, 14, 12.5],
          "text-variable-anchor": ["left", "right", "top", "bottom"],
          "text-radial-offset": 1.05,
          "text-justify": "auto",
          "text-max-width": 9,
          "text-optional": true
        },
        paint: {
          "text-color": o.satelit ? "#ffffff" : (o.gelap ? POI.bandara.teksGelap : POI.bandara.teks),
          "text-halo-color": P.halo, "text-halo-width": 1.6
        } },
      { id: "nama-gunung", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 9,
        filter: ["all", ["==", ["get", "class"], "landform"], ["in", ["get", "maki"], ["literal", ["mountain", "volcano"]]]],
        layout: {
          "text-font": reguler,
          "text-size": 11,
          "text-max-width": 8,
          "text-line-height": 1.25,
          "symbol-sort-key": ["to-number", ["get", "sizerank"], 20]
        },
        paint: { "text-color": P.teksGunung, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

      { id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 3,
        filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay", "water"]]],
        layout: {
          "text-font": miring,
          "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10.5, 10, 13.5],
          "text-letter-spacing": 0.05,
          "text-max-width": 8
        },
        paint: { "text-color": P.teksAlam, "text-halo-color": o.satelit ? P.halo : P.air, "text-halo-width": 0.8 } },

      { id: "nama-kelurahan", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 12,
        filter: ["==", ["get", "class"], "settlement_subdivision"],
        layout: {
          "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 12, 10.5, 16, 12.5],
          "text-max-width": 8,
          "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
        },
        paint: { "text-color": P.teksKelurahan, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

      { id: "nama-kota", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 3,
        filter: ["all",
          ["==", ["get", "class"], "settlement"],
          ["<=", ["to-number", ["get", "filterrank"], 5],
            ["step", ["zoom"], 2, 5, 3, 7, 4, 9, 5]]],
        layout: {
          "text-font": ["step", ["to-number", ["get", "symbolrank"], 20], ["literal", sedang], 12, ["literal", reguler]],
          "text-size": ["interpolate", ["linear"], ["zoom"],
            4, ["step", ["to-number", ["get", "symbolrank"], 20], 13, 7, 11],
            9, ["step", ["to-number", ["get", "symbolrank"], 20], 16, 10, 13],
            14, ["step", ["to-number", ["get", "symbolrank"], 20], 18, 12, 15]],
          "text-max-width": 8,
          "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
        },
        paint: { "text-color": P.teksKota, "text-halo-color": P.halo, "text-halo-width": 1.6 } },
      { id: "nama-jalan", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 13,
        filter: ["all", ["has", "name"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
        layout: {
          "symbol-placement": "line",
          "symbol-spacing": 280,
          "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 13, 10.5, 18, 13],
          "text-max-angle": 35,
          "text-padding": 3,
          "text-rotation-alignment": "map"
        },
        paint: { "text-color": P.teksJalan, "text-halo-color": P.halo, "text-halo-width": 1.6 } },

      { id: "nama-provinsi", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 5, maxzoom: 11,
        filter: ["==", ["get", "class"], "state"],
        layout: {
          "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10.5, 8, 13],
          "text-letter-spacing": 0.06,
          "text-max-width": 9
        },
        paint: { "text-color": P.teksProvinsi, "text-halo-color": P.halo, "text-halo-width": 1.4 } },
      { id: "nama-provinsi-id", type: "symbol", source: "provinsi", minzoom: 5, maxzoom: 10.5,
        layout: {
          "text-font": reguler,
          "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10.5, 8, 13.5],
          "text-letter-spacing": 0.06,
          "text-max-width": 9
        },
        paint: { "text-color": P.teksProvinsi, "text-halo-color": P.halo, "text-halo-width": 1.6 } },
      { id: "nama-negara", type: "symbol", source: "jalan", "source-layer": "place_label", maxzoom: 6,
        filter: ["==", ["get", "class"], "country"],
        layout: {
          "text-font": sedang,
          "text-size": ["interpolate", ["linear"], ["zoom"], 2, 12, 6, 17],
          "text-max-width": 8
        },
        paint: { "text-color": P.teksNegara, "text-halo-color": P.halo, "text-halo-width": 1.8 } }
    ]
  });
}
