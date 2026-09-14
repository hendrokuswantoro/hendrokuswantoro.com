import type { Copy } from "./i18n";

export type Tile = {
  icon: "globe" | "chart" | "satellite" | "map" | "database" | "survey";
  label: Copy;
};

export const HOME = {
  eyebrow: { en: "Maps and data", id: "Peta dan data" } as Copy,
  title: { en: "I make maps and map apps.", id: "Saya bikin peta dan aplikasi peta." } as Copy,
  seeWork: { en: "See my work", id: "Lihat karya saya" } as Copy,
  cardAlt: {
    en: "A green map with a route and three points on it",
    id: "Peta hijau dengan rute dan tiga titik di atasnya",
  } as Copy,
  cardPoints: { en: "Survey points", id: "Titik survei" } as Copy,
  cardLive: { en: "Maps that run", id: "Peta yang jalan" } as Copy,
  cardStack: { en: "PostGIS, MapLibre, FastAPI", id: "PostGIS, MapLibre, FastAPI" } as Copy,

  doEyebrow: { en: "What I do", id: "Yang saya kerjakan" } as Copy,
  doTitle: { en: "Six things I do", id: "Enam hal yang saya kerjakan" } as Copy,
  tiles: [
    { icon: "globe", label: { en: "Map apps", id: "Aplikasi peta" } },
    { icon: "chart", label: { en: "Map analysis", id: "Analisis peta" } },
    { icon: "satellite", label: { en: "Satellite data", id: "Data satelit" } },
    { icon: "map", label: { en: "Map design", id: "Desain peta" } },
    { icon: "database", label: { en: "Data work", id: "Olah data" } },
    { icon: "survey", label: { en: "Field survey", id: "Survei lapangan" } },
  ] as Tile[],

  workEyebrow: { en: "My work", id: "Karya saya" } as Copy,
  workTitle: { en: "Three recent ones", id: "Tiga yang terbaru" } as Copy,
  seeAll: { en: "See all projects", id: "Lihat semua proyek" } as Copy,

  /* Cuplikan peta di beranda. Kalimatnya sengaja pendek dan menyuruh satu
     hal saja, sama seperti pengantar di halaman Proyek. */
  mapEyebrow: { en: "The work map", id: "Peta karya" } as Copy,
  mapTitle: { en: "See the work on a map", id: "Lihat karyanya di peta" } as Copy,
  mapBody: {
    en: "The Project page opens a map with all seven works on it. Click a point to see the work.",
    id: "Halaman Proyek membuka peta berisi tujuh karya. Klik satu titik untuk melihat karyanya.",
  } as Copy,
  mapOpen: { en: "Open the map", id: "Buka petanya" } as Copy,

  howEyebrow: { en: "How I work", id: "Cara kerja saya" } as Copy,
  howTitle: { en: "Just three steps", id: "Tiga langkah saja" } as Copy,
  steps: [
    {
      number: "01",
      title: { en: "Ask first", id: "Tanya dulu" },
      body: {
        en: "I ask what you need to decide and what data you have.",
        id: "Saya tanya apa yang mau Anda putuskan dan data apa yang sudah ada.",
      },
    },
    {
      number: "02",
      title: { en: "Build and check", id: "Bikin dan cek" },
      body: {
        en: "I build it in small steps and test it with real data.",
        id: "Saya bikin sedikit demi sedikit lalu menguji dengan data asli.",
      },
    },
    {
      number: "03",
      title: { en: "Hand it over", id: "Serahkan" },
      body: {
        en: "You get the code and the notes, so anyone can run it again.",
        id: "Anda dapat kode dan catatannya, supaya siapa pun bisa menjalankannya lagi.",
      },
    },
  ] as { number: string; title: Copy; body: Copy }[],

  ctaTitle: { en: "Want to see more?", id: "Mau lihat lebih banyak?" } as Copy,
};
