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
      en: "Open the map, pick a point, and the parking fee comes out following the local rule. The formula lives in one place only, and outside the data area the answer is blank, not a guess.",
      id: "Buka petanya, pilih titiknya, tarif parkir langsung keluar sesuai aturan daerah. Rumus tarifnya cuma ada di satu tempat, dan di luar wilayah datanya jawabannya kosong, bukan tebakan.",
    },
    tags: ["FastAPI", "PostGIS", "MapLibre", "Docker"],
    meta: {
      en: "I did: the database, the API and the map screen",
      id: "Saya kerjakan: basis data, API, dan tampilan petanya",
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
      en: "Daily fire dots from satellites are grouped into single events. The maps show where a fire started, which way it ran, and which land burns again every year.",
      id: "Titik api harian dari satelit dikelompokkan jadi satu kejadian. Petanya menunjukkan api mulai di mana, larinya ke mana, dan lahan mana yang terbakar lagi tiap tahun.",
    },
    tags: ["Python", "GeoPandas", "Matplotlib"],
    meta: {
      en: "The result: a set of figures, light and dark version",
      id: "Hasilnya: kumpulan gambar, versi terang dan gelap",
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
      en: "Every possible site gets a score. What counts: water depth, shelter from waves, the road in, and how many people live nearby.",
      id: "Tiap calon lokasi diberi nilai. Yang ditimbang: kedalaman laut, tempat berlindung dari ombak, jalan menuju lokasi, dan jumlah warga di sekitarnya.",
    },
    tags: ["QGIS", "GDAL", "Rasterio"],
    meta: {
      en: "The result: a score map and the Selat Lampa map sheet",
      id: "Hasilnya: peta nilai lokasi dan lembar peta Selat Lampa",
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
      en: "How far people have to travel along the roads to reach a service. Then a closer look at two possible fishing port spots, Fandoi and Bosnik.",
      id: "Berapa jauh warga harus menempuh jalan untuk sampai ke layanan, dihitung lewat jaringan jalan. Lalu dua calon lokasi pelabuhan ikan, Fandoi dan Bosnik, dilihat lebih dekat.",
    },
    tags: ["QGIS", "Network analysis", "Layout"],
    meta: {
      en: "The result: three map sheets, print and digital",
      id: "Hasilnya: tiga lembar peta, cetak dan digital",
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
      en: "Satellite images sorted into land cover classes, then laid out as a print ready map sheet. The colours are picked so they are easy to tell apart, and the source and image date are written down.",
      id: "Citra satelit dipilah jadi kelas tutupan lahan, lalu ditata jadi lembar peta siap cetak. Warnanya dipilih supaya jelas dibedakan, dan sumber serta tanggal citranya ditulis.",
    },
    tags: ["QGIS", "Raster", "Layout"],
    meta: { en: "The result: PDF and PNG map sheets", id: "Hasilnya: lembar peta PDF dan PNG" },
    featured: false,
  },
  {
    id: "sheet",
    cover: "sheet",
    categories: ["design"],
    badge: { en: "Print map", id: "Peta cetak" },
    title: { en: "Land Map Sheet, Mimika", id: "Lembar Peta Pertanahan, Mimika" },
    body: {
      en: "A large land map sheet: how the sheets are split, the grid lines, and a map face that is still readable once printed.",
      id: "Lembar peta pertanahan ukuran besar: pembagian lembar, garis grid, dan isi peta yang tetap terbaca setelah dicetak.",
    },
    tags: ["QGIS", "Print layout", "EPSG:32749"],
    meta: { en: "The result: one large print sheet", id: "Hasilnya: satu lembar peta cetak ukuran besar" },
    featured: false,
  },
];

export const PROJECT_PAGE = {
  title: { en: "Project", id: "Proyek" } as Copy,
  filterAria: { en: "Filter by kind", id: "Saring menurut jenis" } as Copy,
  empty: { en: "Nothing here yet for this kind.", id: "Belum ada proyek di jenis ini." } as Copy,
  ctaTitle: { en: "Curious how it works?", id: "Penasaran cara kerjanya?" } as Copy,
};
