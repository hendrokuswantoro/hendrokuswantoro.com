import type { Copy } from "./i18n";

export type Tile = {
  icon: "globe" | "chart" | "satellite" | "map" | "database" | "survey";
  label: Copy;
};

export const HOME = {
  eyebrow: { en: "Maps and data", id: "Peta dan data" } as Copy,
  title: { en: "I make maps and map apps.", id: "Saya bikin peta dan aplikasi peta." } as Copy,
  lede: {
    en: "Hi, I am Hendro. I work with maps in Yogyakarta. I turn location data into something you can open, read and use.",
    id: "Halo, saya Hendro. Saya kerja dengan peta di Yogyakarta. Data lokasi saya ubah jadi sesuatu yang bisa Anda buka, baca, dan pakai.",
  } as Copy,
  seeWork: { en: "See my work", id: "Lihat karya saya" } as Copy,
  meta: [
    { en: "Yogyakarta, Indonesia", id: "Yogyakarta, Indonesia" },
    { en: "Studied geodesy at UGM", id: "Belajar geodesi di UGM" },
    { en: "Open to work together", id: "Siap kerja bareng" },
  ] as Copy[],
  cardAlt: {
    en: "A green map with a route and three points on it",
    id: "Peta hijau dengan rute dan tiga titik di atasnya",
  } as Copy,
  cardLive: { en: "Maps that run", id: "Peta yang jalan" } as Copy,
  cardStack: { en: "PostGIS, MapLibre, FastAPI", id: "PostGIS, MapLibre, FastAPI" } as Copy,

  doEyebrow: { en: "What I do", id: "Yang saya kerjakan" } as Copy,
  doTitle: { en: "Six things I do", id: "Enam hal yang saya kerjakan" } as Copy,
  doLede: {
    en: "From taking data in the field to a map that runs on your phone. All with open tools.",
    id: "Mulai dari ambil data di lapangan sampai peta yang jalan di ponsel. Semua pakai perkakas terbuka.",
  } as Copy,
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
  workLede: {
    en: "The full list is on the Project page.",
    id: "Daftar lengkapnya ada di halaman Proyek.",
  } as Copy,
  seeAll: { en: "See all projects", id: "Lihat semua proyek" } as Copy,

  howEyebrow: { en: "How I work", id: "Cara kerja saya" } as Copy,
  howTitle: { en: "Just three steps", id: "Tiga langkah saja" } as Copy,
  steps: [
    {
      number: "01",
      title: { en: "Ask first", id: "Tanya dulu" },
      body: {
        en: "I start with one thing: what do you need to decide, and what data do you already have.",
        id: "Saya mulai dari satu hal: keputusan apa yang mau Anda ambil, dan data apa yang sudah ada di tangan.",
      },
    },
    {
      number: "02",
      title: { en: "Build and check", id: "Bikin dan cek" },
      body: {
        en: "Built bit by bit and tested with real data. Every number can be traced back to where it came from.",
        id: "Dibangun sedikit demi sedikit, diuji dengan data asli. Tiap angka bisa dilacak datangnya dari mana.",
      },
    },
    {
      number: "03",
      title: { en: "Hand it over", id: "Serahkan" },
      body: {
        en: "You get the code and the notes, so somebody else can run it again without me.",
        id: "Anda dapat kode dan catatannya, supaya orang lain bisa menjalankannya lagi tanpa saya.",
      },
    },
  ] as { number: string; title: Copy; body: Copy }[],

  ctaTitle: { en: "Want to see more?", id: "Mau lihat lebih banyak?" } as Copy,
  ctaBody: {
    en: "The Project page has the full list. The blog has short notes on how the work is done.",
    id: "Halaman Proyek memuat daftar lengkapnya. Blog berisi catatan singkat tentang cara kerjanya.",
  } as Copy,
};
