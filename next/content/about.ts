import type { Copy } from "./i18n";

export const ABOUT = {
  eyebrow: { en: "About", id: "Tentang" } as Copy,
  title: "Spatial Data & Systems Architect",
  lede: {
    en: "I am Hendro Kuswantoro, based in Yogyakarta. I design spatial data and the systems that use it, from the database to the map on the screen.",
    id: "Saya Hendro Kuswantoro, dari Yogyakarta. Saya merancang data spasial dan sistem yang memakainya, dari basis data sampai peta di layar.",
  } as Copy,

  skillsEyebrow: { en: "Skills", id: "Keahlian" } as Copy,
  skillsTitle: { en: "What I work on", id: "Yang saya kerjakan" } as Copy,
  skills: [
    {
      title: { en: "Spatial databases", id: "Basis data spasial" },
      body: {
        en: "Schema design, indexes, migrations, and PostGIS queries that stay fast as the data grows.",
        id: "Rancangan skema, indeks, migrasi, dan kueri PostGIS yang tetap cepat waktu datanya membesar.",
      },
    },
    {
      title: { en: "Map apps", id: "Aplikasi peta" },
      body: {
        en: "An API at the back and a map in the browser, including the empty, error and out of coverage states.",
        id: "API di belakang dan peta di peramban, lengkap dengan keadaan kosong, galat, dan batas cakupan.",
      },
    },
    {
      title: { en: "Spatial analysis", id: "Analisis spasial" },
      body: {
        en: "Multi criteria models, road networks, service reach, and site selection.",
        id: "Multikriteria, jaringan jalan, jangkauan layanan, dan pemilihan lokasi.",
      },
    },
    {
      title: { en: "Satellite data", id: "Data satelit" },
      body: {
        en: "Time series, event detection, and raster processing at volume.",
        id: "Deret waktu, deteksi kejadian, dan pemrosesan raster dalam jumlah besar.",
      },
    },
    {
      title: { en: "Cartography", id: "Kartografi" },
      body: {
        en: "Print map sheets, clear hierarchy, colours with contrast that has been calculated.",
        id: "Lembar peta cetak, hierarki yang jelas, warna yang kontrasnya dihitung.",
      },
    },
    {
      title: { en: "Pipelines and delivery", id: "Alur data dan rilis" },
      body: {
        en: "Python automation, Docker packaging, and a handover somebody else can run again.",
        id: "Otomasi dengan Python, kemasan Docker, dan penyerahan yang bisa dijalankan ulang orang lain.",
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
