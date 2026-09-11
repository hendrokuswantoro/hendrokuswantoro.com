import type { Copy } from "./i18n";

export type Category = "app" | "analysis" | "satellite" | "design";
export type CoverKind = "parking" | "fire" | "fish" | "reach" | "landcover" | "sheet";

export type Project = {
  id: string;
  cover: CoverKind;
  categories: Category[];
  badge: Copy;
  title: Copy;
  body: Copy;
  tags: string[];
  meta: Copy;
  featured: boolean;
};

export const FILTERS: { key: Category | "all"; label: Copy }[] = [
  { key: "all", label: { en: "All", id: "Semua" } },
  { key: "app", label: { en: "Map apps", id: "Aplikasi peta" } },
  { key: "analysis", label: { en: "Map analysis", id: "Analisis peta" } },
  { key: "satellite", label: { en: "Satellite data", id: "Data satelit" } },
  { key: "design", label: { en: "Map design", id: "Desain peta" } },
];

export const PROJECTS: Project[] = [
  {
    id: "parking",
    cover: "parking",
    categories: ["app"],
    badge: { en: "Map app", id: "Aplikasi peta" },
    title: { en: "Yogyakarta Parking Map", id: "Peta Parkir Yogyakarta" },
    body: {
      en: "Pick a point on the map. The zone and the fee show up. Outside the city the app shows nothing, because the rule does not apply there.",
      id: "Pilih titik di peta. Zona dan tarifnya muncul. Di luar kota aplikasinya tidak menampilkan apa apa, sebab aturannya tidak berlaku di sana.",
    },
    tags: ["FastAPI", "PostGIS", "MapLibre", "Docker"],
    meta: {
      en: "I built the database, the API and the map screen",
      id: "Saya bikin basis data, API, dan tampilan petanya",
    },
    featured: true,
  },
  {
    id: "fire",
    cover: "fire",
    categories: ["satellite", "analysis"],
    badge: { en: "Satellite data", id: "Data satelit" },
    title: { en: "Kalimantan Fire Maps", id: "Peta Kebakaran Kalimantan" },
    body: {
      en: "Fire dots from satellites, grouped into one event. The map shows where the fire started, where it moved, and which land burns again every year.",
      id: "Titik api dari satelit digabung jadi satu kejadian. Petanya menunjukkan api mulai di mana, pindah ke mana, dan lahan mana yang terbakar lagi tiap tahun.",
    },
    tags: ["Python", "GeoPandas", "Matplotlib"],
    meta: {
      en: "The result is a set of figures, light and dark",
      id: "Hasilnya kumpulan gambar, terang dan gelap",
    },
    featured: true,
  },
  {
    id: "fish",
    cover: "fish",
    categories: ["analysis"],
    badge: { en: "Map analysis", id: "Analisis peta" },
    title: { en: "Fish Landing Sites, Natuna", id: "Lokasi Pendaratan Ikan, Natuna" },
    body: {
      en: "Each spot gets a score. The map weighs sea depth, shelter from waves, the road in, and how many people live nearby.",
      id: "Tiap lokasi diberi nilai. Yang dihitung kedalaman laut, tempat teduh dari ombak, jalan masuk, dan jumlah warga di dekatnya.",
    },
    tags: ["QGIS", "GDAL", "Rasterio"],
    meta: {
      en: "The result is a score map and one map sheet",
      id: "Hasilnya peta nilai lokasi dan satu lembar peta",
    },
    featured: true,
  },
  {
    id: "reach",
    cover: "reach",
    categories: ["analysis", "design"],
    badge: { en: "Service reach", id: "Jangkauan layanan" },
    title: { en: "Service Reach, Biak Numfor", id: "Jangkauan Layanan, Biak Numfor" },
    body: {
      en: "How far people travel on the road to reach a service. Then a closer look at two spots for a fishing port, Fandoi and Bosnik.",
      id: "Seberapa jauh warga menempuh jalan untuk sampai ke layanan. Lalu dua calon lokasi pelabuhan ikan, Fandoi dan Bosnik, dilihat lebih dekat.",
    },
    tags: ["QGIS", "Network analysis", "Layout"],
    meta: {
      en: "The result is three map sheets",
      id: "Hasilnya tiga lembar peta",
    },
    featured: false,
  },
  {
    id: "landcover",
    cover: "landcover",
    categories: ["design", "satellite"],
    badge: { en: "Map design", id: "Desain peta" },
    title: { en: "Yogyakarta Land Cover Map", id: "Peta Tutupan Lahan Yogyakarta" },
    body: {
      en: "Satellite images sorted into land cover classes, then laid out as a map sheet ready to print.",
      id: "Citra satelit dipilah jadi kelas tutupan lahan, lalu ditata jadi lembar peta siap cetak.",
    },
    tags: ["QGIS", "Raster", "Layout"],
    meta: { en: "The result is a map sheet in PDF and PNG", id: "Hasilnya lembar peta PDF dan PNG" },
    featured: false,
  },
  {
    id: "sheet",
    cover: "sheet",
    categories: ["design"],
    badge: { en: "Print map", id: "Peta cetak" },
    title: { en: "Land Map Sheet, Mimika", id: "Lembar Peta Pertanahan, Mimika" },
    body: {
      en: "A large land map sheet. The sheet split, the grid lines, and a map that stays readable in print.",
      id: "Lembar peta pertanahan ukuran besar. Pembagian lembar, garis grid, dan peta yang tetap terbaca waktu dicetak.",
    },
    tags: ["QGIS", "Print layout", "UTM 49S"],
    meta: { en: "The result is one large print sheet", id: "Hasilnya satu lembar peta cetak ukuran besar" },
    featured: false,
  },
];

export const PROJECT_PAGE = {
  title: { en: "Project", id: "Proyek" } as Copy,
  filterAria: { en: "Filter by kind", id: "Saring menurut jenis" } as Copy,
  empty: { en: "Nothing here yet for this kind.", id: "Belum ada proyek di jenis ini." } as Copy,
  ctaTitle: { en: "Curious how it works?", id: "Penasaran cara kerjanya?" } as Copy,
};
