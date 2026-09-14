import type { Copy } from "./i18n";

export type Category = "app" | "analysis" | "satellite" | "design";

export type Project = {
  id: string;
  image: string;
  alt: Copy;
  point: { lng: number; lat: number };
  categories: Category[];
  badge: Copy;
  title: Copy;
  body: Copy;
  tags: string[];
  meta: Copy;
  /* Jalur studi kasusnya, kalau ada. Hanya satu proyek yang punya sekarang,
     dan kartu proyek lain tidak menampilkan tautan apa pun. */
  studiKasus?: string;
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
    point: { lng: 110.3656, lat: -7.7925 },
    image: "/assets/img/work/parking.webp",
    alt: { en: "Screenshot of the parking map app showing the zone and the fee for Jalan Malioboro", id: "Tangkapan layar aplikasi peta parkir, menampilkan zona dan tarif di Jalan Malioboro" },
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
    studiKasus: "/parkir-jogja/",
    featured: true,
  },
  {
    id: "fire",
    point: { lng: 113.2, lat: -1.6 },
    image: "/assets/img/work/fire.webp",
    alt: { en: "Six small maps of Kalimantan showing where fires ignited through the 2026 season", id: "Enam peta kecil Kalimantan yang menunjukkan titik api sepanjang musim 2026" },
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
    point: { lng: 108.22, lat: 3.7 },
    image: "/assets/img/work/fish.webp",
    alt: { en: "Poster with suitability maps and charts for fish landing sites in Natuna", id: "Poster berisi peta kesesuaian dan grafik lokasi pendaratan ikan di Natuna" },
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
    id: "pickup",
    point: { lng: 106.82, lat: -6.21 },
    image: "/assets/img/work/pickup.webp",
    alt: {
      en: "Map of common pickup points from driver GPS pings in Jakarta",
      id: "Peta titik jemput umum dari ping GPS pengemudi di Jakarta",
    },
    categories: ["analysis"],
    badge: { en: "Map analysis", id: "Analisis peta" },
    title: {
      en: "Pickup Points from GPS Pings, Jakarta",
      id: "Titik Jemput dari Ping GPS, Jakarta",
    },
    body: {
      en: "Three thousand driver pings around three buildings in Jakarta, grouped into the spots where people actually wait. Each group gets one node at its geometric median.",
      id: "Tiga ribu ping pengemudi di sekitar tiga gedung di Jakarta dikelompokkan jadi titik tempat orang benar benar menunggu. Tiap kelompok diberi satu simpul di median geometrisnya.",
    },
    tags: ["Python", "DBSCAN", "QGIS"],
    meta: {
      en: "The result is one map sheet with three close ups",
      id: "Hasilnya satu lembar peta dengan tiga perbesaran",
    },
    featured: false,
  },
  {
    id: "reach",
    point: { lng: 136.08, lat: -1.18 },
    image: "/assets/img/work/reach.webp",
    alt: { en: "Map sheet of service accessibility in Biak Numfor", id: "Lembar peta aksesibilitas layanan di Biak Numfor" },
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
    point: { lng: 110.405, lat: -7.755 },
    image: "/assets/img/work/landcover.webp",
    alt: { en: "Land cover map sheet of the Yogyakarta urban area", id: "Lembar peta tutupan lahan kawasan perkotaan Yogyakarta" },
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
    id: "mimika",
    point: { lng: 137.0, lat: -4.35 },
    image: "/assets/img/work/mimika.webp",
    alt: { en: "Map of mining excavations and forest cover loss in Mimika", id: "Peta bukaan tambang dan kehilangan tutupan hutan di Mimika" },
    categories: ["satellite", "design"],
    badge: { en: "Satellite data", id: "Data satelit" },
    title: { en: "Mining and Forest Loss, Mimika", id: "Tambang dan Hutan Hilang, Mimika" },
    body: {
      en: "Open pit mining areas mapped year by year, next to the forest lost around them. One sheet, with close ups of the biggest pits.",
      id: "Bukaan tambang dipetakan tahun demi tahun, bersama hutan yang hilang di sekitarnya. Satu lembar peta, dengan perbesaran di bukaan terbesar.",
    },
    tags: ["QGIS", "Raster", "Print layout"],
    meta: { en: "The result is one large print sheet", id: "Hasilnya satu lembar peta cetak ukuran besar" },
    featured: false,
  },
];

export const PROJECT_PAGE = {
  title: { en: "Project", id: "Proyek" } as Copy,
  filterAria: { en: "Filter by kind", id: "Saring menurut jenis" } as Copy,
  empty: { en: "Nothing here yet for this kind.", id: "Belum ada proyek di jenis ini." } as Copy,
  ctaTitle: { en: "Curious how it works?", id: "Penasaran cara kerjanya?" } as Copy,
  mapNote: {
    en: "Marker points, not study area boundaries. Map tiles from Mapbox and OpenStreetMap.",
    id: "Titik penanda, bukan batas wilayah kajian. Ubin peta dari Mapbox dan OpenStreetMap.",
  } as Copy,
  seeProject: { en: "See the project", id: "Lihat proyek" } as Copy,
  showOnMap: { en: "Show on map", id: "Lihat di peta" } as Copy,
  readCaseStudy: { en: "Read the case study", id: "Baca studi kasusnya" } as Copy,
  mapEyebrow: { en: "The work map", id: "Peta karya" } as Copy,
  mapTitle: { en: "Seven works, one map", id: "Tujuh karya, satu peta" } as Copy,
  mapIntro: {
    en: "Every project below is on this map. Click a point to see the work.",
    id: "Tiap proyek di bawah ada di peta ini. Klik satu titik untuk melihat karyanya.",
  } as Copy,
  /* Dibacakan pembaca layar, tidak pernah tampil di layar. */
  filterOn: {
    en: "%k. %n of %t works shown.",
    id: "%k. %n dari %t karya ditampilkan.",
  } as Copy,
  filterOff: {
    en: "Filter off. All %t works shown.",
    id: "Saringan mati. Semua %t karya ditampilkan.",
  } as Copy,
  mapFocus: { en: "%w, centred on the map.", id: "%w, dipusatkan di peta." } as Copy,
};
