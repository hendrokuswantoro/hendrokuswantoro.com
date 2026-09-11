import type { Copy } from "./i18n";

export const ABOUT = {
  eyebrow: { en: "About", id: "Tentang" } as Copy,
  title: "Spatial Data & Systems Architect",

  skillsEyebrow: { en: "Skills", id: "Keahlian" } as Copy,
  skillsTitle: { en: "What I work on", id: "Yang saya kerjakan" } as Copy,
  skills: [
    {
      title: { en: "Spatial databases", id: "Basis data spasial" },
      body: {
        en: "I design the database and keep it fast when the data grows.",
        id: "Saya rancang basis datanya dan menjaga tetap cepat waktu datanya besar.",
      },
    },
    {
      title: { en: "Map apps", id: "Aplikasi peta" },
      body: {
        en: "An API at the back, a map in front, and a clear message when there is no data.",
        id: "API di belakang, peta di depan, dan pesan yang jelas waktu datanya tidak ada.",
      },
    },
    {
      title: { en: "Spatial analysis", id: "Analisis spasial" },
      body: {
        en: "I weigh many things on one map to pick the best location.",
        id: "Saya timbang banyak hal di satu peta untuk memilih lokasi terbaik.",
      },
    },
    {
      title: { en: "Satellite data", id: "Data satelit" },
      body: {
        en: "I read change over time from satellite images.",
        id: "Saya baca perubahan dari waktu ke waktu lewat citra satelit.",
      },
    },
    {
      title: { en: "Cartography", id: "Kartografi" },
      body: {
        en: "Print maps that stay easy to read.",
        id: "Peta cetak yang tetap gampang dibaca.",
      },
    },
    {
      title: { en: "Pipelines and delivery", id: "Alur data dan rilis" },
      body: {
        en: "Python and Docker, so anyone can run the work again.",
        id: "Python dan Docker, supaya siapa pun bisa menjalankan pekerjaannya lagi.",
      },
    },
  ] as { title: Copy; body: Copy }[],

  toolsEyebrow: { en: "Tools", id: "Perkakas" } as Copy,
  toolsTitle: { en: "What I use most", id: "Yang sering saya pakai" } as Copy,
  tools: [
    {
      title: { en: "Data and databases", id: "Data dan basis data" },
      items: ["PostgreSQL", "PostGIS", "GDAL", "PROJ", "GeoPackage", "Redis"],
    },
    {
      title: { en: "Analysis", id: "Analisis" },
      items: ["Python", "GeoPandas", "Shapely", "Rasterio", "Xarray", "Dask", "QGIS"],
    },
    {
      title: { en: "Maps in the browser", id: "Peta di peramban" },
      items: ["MapLibre GL", "Mapbox GL", "Deck.gl", "CesiumJS", "PMTiles", "GeoServer"],
    },
    {
      title: { en: "Apps and operations", id: "Aplikasi dan operasional" },
      items: ["FastAPI", "TypeScript", "Next.js", "Docker", "Nginx", "GitHub Actions", "Git"],
    },
  ] as { title: Copy; items: string[] }[],

  ctaTitle: { en: "See the work", id: "Lihat hasilnya" } as Copy,
};
