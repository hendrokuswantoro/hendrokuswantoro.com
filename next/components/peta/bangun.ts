import type { IControl, LngLatBounds, Map as MapLibreMap, Marker, Popup } from "maplibre-gl";
import { PROJECTS, type Category } from "@/content/projects";
import { DEM, FALLBACK_STYLE, PALET, TOKEN, mapboxStyle, tambahIkon, type OpsiGaya } from "./gaya";

type Pustaka = typeof import("maplibre-gl");
type Teks = { en: string; ind: string };
type Dasar = "peta" | "satelit" | "medan";

type Karya = Teks & { id: string; kind: Category; lng: number; lat: number; at: Teks; foto: string };
type Entry = { item: Karya; marker: Marker; popup: Popup };

const TEMPAT: Record<string, Teks> = {
  parking: { en: "Yogyakarta", ind: "Yogyakarta" },
  landcover: { en: "Yogyakarta", ind: "Yogyakarta" },
  fire: { en: "Central Kalimantan", ind: "Kalimantan Tengah" },
  fish: { en: "Natuna, Riau Islands", ind: "Natuna, Kepulauan Riau" },
  pickup: { en: "Jakarta", ind: "Jakarta" },
  reach: { en: "Biak Numfor, Papua", ind: "Biak Numfor, Papua" },
  mimika: { en: "Mimika, Central Papua", ind: "Mimika, Papua Tengah" },
};

const WORK: Karya[] = PROJECTS.map((p) => ({
  id: p.id,
  kind: p.categories[0],
  lng: p.point.lng,
  lat: p.point.lat,
  en: p.title.en,
  ind: p.title.id,
  at: TEMPAT[p.id] ?? { en: "", ind: "" },
  foto: p.image,
}));

const KIND: Record<Category, Teks & { glyph: string }> = {
  app: { en: "Map app", ind: "Aplikasi peta",
    glyph: "M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 3v12h10V5zm5 13.3a1.1 1.1 0 1 0 0 2.2 1.1 1.1 0 0 0 0-2.2z" },
  analysis: { en: "Map analysis", ind: "Analisis peta",
    glyph: "M3 20h18v2H3zM5 11h3.2v7.5H5zM10.4 5h3.2v13.5h-3.2zM15.8 13h3.2v5.5h-3.2z" },
  satellite: { en: "Satellite data", ind: "Data satelit",
    glyph: "M12 8.2 15.8 12 12 15.8 8.2 12zM5.6 2.2l4 4-3.4 3.4-4-4zM18.4 14.4l4 4-3.4 3.4-4-4zM9.9 7.5l1.2-1.2 1.9 1.9-1.2 1.2zM14.8 12.4l1.2-1.2 1.9 1.9-1.2 1.2z" },
  design: { en: "Map design", ind: "Desain peta",
    glyph: "M12 2.5 22 8 12 13.5 2 8zM4.3 11.4 12 15.6l7.7-4.2L22 12.7 12 18.2 2 12.7zM4.3 15.6 12 19.8l7.7-4.2L22 16.9 12 22.4 2 16.9z" },
};

const KUNCI_KIND = Object.keys(KIND) as Category[];

const AWALAN_HASH = "#peta-";

export function idDariHash(): string | null {
  const hash = window.location.hash || "";
  if (hash.indexOf(AWALAN_HASH) !== 0) return null;
  const id = hash.slice(AWALAN_HASH.length);
  return WORK.some((item) => item.id === id) ? id : null;
}

function tulisHash(id: string | null) {
  if (!window.history || !window.history.replaceState) return;
  if (id && window.location.hash === AWALAN_HASH + id) return;
  if (!id && !window.location.hash) return;
  const alamat = id ? AWALAN_HASH + id : window.location.pathname + window.location.search;
  try {
    window.history.replaceState(null, "", alamat);
  } catch {
  }
}

const TEXT = {
  tour: { en: "Tour", ind: "Jelajah" },
  open: { en: "See the project", ind: "Lihat proyek" },
  home: { en: "Back to the starting view", ind: "Kembali ke posisi semula" },
  search: { en: "Search the work map", ind: "Cari di peta karya" },
  clear: { en: "Clear search", ind: "Hapus pencarian" },
  kinds: { en: "Filter works by type", ind: "Saring karya menurut jenis" },
  inView: { en: "%n of %t works in view", ind: "%n dari %t karya terlihat" },
  noMatch: { en: "No work matches “%q”", ind: "Tidak ada karya yang cocok dengan “%q”" },
  layers: { en: "Layers", ind: "Lapisan" },
  map: { en: "Map", ind: "Peta" },
  satellite: { en: "Satellite", ind: "Satelit" },
  terrain: { en: "Terrain", ind: "Medan" },
  three: { en: "3D view", ind: "Tampilan 3D" },
  copy: { en: "Copy link", ind: "Salin tautan" },
  copied: { en: "Link copied", ind: "Tautan tersalin" },
  copyFail: { en: "Copy failed", ind: "Gagal menyalin" },
  close: { en: "Close", ind: "Tutup" },
  zoomIn: { en: "Zoom in", ind: "Perbesar" },
  zoomOut: { en: "Zoom out", ind: "Perkecil" },
  north: { en: "Face north", ind: "Hadapkan ke utara" },
  full: { en: "Full screen", ind: "Layar penuh" },
  unfull: { en: "Exit full screen", ind: "Keluar dari layar penuh" },
  ctrlHint: { en: "Hold ctrl and scroll to zoom the map", ind: "Tahan ctrl sambil menggulir untuk memperbesar peta" },
  cmdHint: { en: "Hold ⌘ and scroll to zoom the map", ind: "Tahan ⌘ sambil menggulir untuk memperbesar peta" },
  touchHint: { en: "Use two fingers to move the map", ind: "Pakai dua jari untuk menggeser peta" },
  layerOn: { en: "%l view.", ind: "Tampilan %l." },
  filterOn: { en: "%k. %n of %t works shown.", ind: "%k. %n dari %t karya ditampilkan." },
  filterOff: { en: "Filter off. All %t works shown.", ind: "Saringan mati. Semua %t karya ditampilkan." },
  focus: { en: "%w, centred on the map.", ind: "%w, dipusatkan di peta." },
};

function sentuh(): boolean {
  return Boolean(window.matchMedia && window.matchMedia("(hover: none) and (pointer: coarse)").matches);
}

function mac(): boolean {
  return /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent || "");
}

function ms(duration: number): number {
  const kurang = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  return kurang ? 0 : duration;
}

function isId(): boolean {
  return document.documentElement.getAttribute("lang") === "id";
}

function temaGelap(): boolean {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function say(entry: Teks): string {
  return isId() ? entry.ind : entry.en;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, kelas?: string, teks?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (kelas) node.className = kelas;
  if (teks) node.textContent = teks;
  return node;
}

function svg(isi: string, kelas?: string): HTMLSpanElement {
  const wadah = document.createElement("span");
  wadah.className = kelas || "peta__ikon";
  wadah.setAttribute("aria-hidden", "true");
  wadah.innerHTML = `<svg viewBox="0 0 24 24" focusable="false">${isi}</svg>`;
  return wadah;
}

const IKON = {
  cari: '<path d="M10.5 3a7.5 7.5 0 0 1 5.96 12.06l4.24 4.24-1.4 1.4-4.24-4.24A7.5 7.5 0 1 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"></path>',
  silang: '<path d="M6.4 5 12 10.6 17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4-5.6-5.6L6.4 19 5 17.6l5.6-5.6L5 6.4z"></path>',
  rumah: '<path d="M12 3.2 3 10.4V21h6.5v-6h5v6H21V10.4zm0 2.6 7 5.6V19h-2.5v-6h-9v6H5v-7.6z"></path>',
  main: '<path d="M8 5.5v13l10.5-6.5z"></path>',
  henti: '<path d="M7 6h3.5v12H7zM13.5 6H17v12h-3.5z"></path>',
  tautan: '<path d="M10.6 13.4a1 1 0 0 1 0-1.4l3.4-3.4a1 1 0 1 1 1.4 1.4L12 13.4a1 1 0 0 1-1.4 0zM8.2 18.6a3.4 3.4 0 0 1-4.8-4.8l2.9-2.9 1.4 1.4-2.9 2.9a1.4 1.4 0 0 0 2 2l2.9-2.9 1.4 1.4zm9.5-6.1-1.4-1.4 2.9-2.9a1.4 1.4 0 0 0-2-2l-2.9 2.9-1.4-1.4 2.9-2.9a3.4 3.4 0 0 1 4.8 4.8z"></path>',
  buka: '<path d="M14 4h6v6h-2V7.4l-7.3 7.3-1.4-1.4L16.6 6H14zM5 6h6v2H6v10h10v-5h2v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z"></path>',
  lokasi: '<path d="M12 2a7 7 0 0 1 7 7c0 5.2-7 13-7 13S5 14.2 5 9a7 7 0 0 1 7-7zm0 4.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"></path>',
};

const GAMBAR_LAPISAN: Record<Dasar, string> = {
  peta:
    '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
    '<rect width="64" height="64" fill="#f1f3f4"></rect>' +
    '<path d="M0 44c10-6 18-4 26 2s18 8 38-6v24H0z" fill="#9fcbf5"></path>' +
    '<path d="M40 0h24v22c-8 2-16-2-20-8S40 6 40 0z" fill="#c9e9cf"></path>' +
    '<path d="M-2 22 66 34" stroke="#dd9d2c" stroke-width="6"></path>' +
    '<path d="M-2 22 66 34" stroke="#fbc95a" stroke-width="4"></path>' +
    '<path d="M22 -2 30 66M4 8l54 50" stroke="#ffffff" stroke-width="2.6"></path>' +
    "</svg>",
  satelit:
    '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
    '<rect width="64" height="64" fill="#3c5a3a"></rect>' +
    '<path d="M0 0h30c-6 10-2 18 6 22S44 36 40 44 20 52 0 50z" fill="#56733f"></path>' +
    '<path d="M34 0h30v30c-8-2-14 2-20-2s-8-14-10-28z" fill="#2f4a36"></path>' +
    '<path d="M0 50c14 2 30-4 40-8s16-2 24 2v20H0z" fill="#1f4f6b"></path>' +
    '<circle cx="18" cy="20" r="7" fill="#7a8a55"></circle>' +
    '<path d="M-2 26 66 36" stroke="#e8d9a8" stroke-width="2" stroke-opacity=".8"></path>' +
    '<path d="M24 -2 32 66" stroke="#ffffff" stroke-width="1.4" stroke-opacity=".55"></path>' +
    "</svg>",
  medan:
    '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
    '<rect width="64" height="64" fill="#eeede6"></rect>' +
    '<path d="M0 64V40c10-10 18-22 30-22s20 14 34 16v30z" fill="#d4eed9"></path>' +
    '<path d="M8 64c4-14 12-30 22-30s16 12 26 14" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
    '<path d="M14 64c4-10 10-22 17-22s11 8 18 10" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
    '<path d="M20 64c3-6 7-14 11-14s7 4 11 6" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
    '<path d="M30 18c-6 0-12 8-16 16 8-6 14-6 16-2 4-8 8-10 12-8-3-4-7-6-12-6z" fill="#9aa3ad" fill-opacity=".35"></path>' +
    "</svg>",
};

function pinSvg(kind: Category): string {
  return (
    '<svg class="peta__pin-svg" viewBox="0 0 28 40" focusable="false" aria-hidden="true">' +
    '<ellipse class="peta__pin-bayang" cx="14" cy="38.4" rx="5" ry="1.6"></ellipse>' +
    '<path class="peta__pin-bentuk" d="M14 1C6.8 1 1 6.7 1 13.8 1 23.4 14 38 14 38s13-14.6 13-24.2C27 6.7 21.2 1 14 1z"></path>' +
    '<g transform="translate(7.6 7.2) scale(.533)"><path class="peta__pin-glyph" fill-rule="evenodd" d="' +
    KIND[kind].glyph + '"></path></g></svg>'
  );
}

function ikonKind(kind: Category): string {
  return `<svg viewBox="0 0 24 24" focusable="false"><path fill-rule="evenodd" d="${KIND[kind].glyph}"></path></svg>`;
}

function koordinat(lat: number, lng: number): string {
  const id = isId();
  const angka = (n: number) => {
    const teks = Math.abs(n).toFixed(4);
    return id ? teks.replace(".", ",") : teks;
  };
  const ns = lat < 0 ? (id ? "LS" : "S") : id ? "LU" : "N";
  const ew = lng < 0 ? (id ? "BB" : "W") : id ? "BT" : "E";
  return `${angka(lat)}° ${ns}, ${angka(lng)}° ${ew}`;
}

function polos(teks: string): string {
  return String(teks || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

function tuneBasemap(map: MapLibreMap, gelap: boolean) {
  const P = PALET[gelap ? "gelap" : "terang"];
  const tweaks: [string, string, string][] = [
    ["background", "background-color", P.latar],
    ["water", "fill-color", P.air],
    ["water_shadow", "fill-color", P.air],
    ["landcover_wood", "fill-color", P.hutan],
    ["landcover_grass", "fill-color", P.rumput],
    ["landuse_residential", "fill-color", P.pemukiman],
    ["building", "fill-color", P.gedung],
  ];
  tweaks.forEach(([id, sifat, nilai]) => {
    try {
      if (map.getLayer(id)) map.setPaintProperty(id, sifat as never, nilai as never);
    } catch {
    }
  });
}

function applyRelief(map: MapLibreMap, three: boolean) {
  const run = () => {
    try {
      if (!map.getSource("dem")) map.addSource("dem", DEM);
      map.setTerrain(three ? { source: "dem", exaggeration: 1.3 } : null);
      return true;
    } catch {
      return false;
    }
  };
  if (run()) return;
  map.once("styledata", run);
  map.once("idle", run);
}

class Kontrol implements IControl {
  private wrap: HTMLElement | null = null;
  constructor(private isi: () => HTMLElement) {}
  onAdd() {
    this.wrap = this.isi();
    return this.wrap;
  }
  onRemove() {
    this.wrap?.remove();
  }
}

function markerElement(item: Karya): HTMLButtonElement {
  const pin = el("button", "peta__pin");
  pin.type = "button";
  pin.setAttribute("data-work", item.id);
  pin.setAttribute("data-kind", item.kind);
  pin.title = say(item);
  pin.setAttribute("aria-label", say(item));
  pin.innerHTML = pinSvg(item.kind);
  const nama = el("span", "peta__pin-nama", say(item));
  nama.setAttribute("aria-hidden", "true");
  pin.appendChild(nama);
  return pin;
}

function kartu(entry: Entry, umumkan: (teks: string) => void): HTMLElement {
  const item = entry.item;
  const box = el("div", "peta__kartu");

  const tutup = el("button", "peta__tutup");
  tutup.type = "button";
  tutup.title = say(TEXT.close);
  tutup.setAttribute("aria-label", say(TEXT.close));
  tutup.appendChild(svg(IKON.silang));
  tutup.addEventListener("click", () => entry.popup.remove());
  box.appendChild(tutup);

  if (item.foto) {
    const foto = document.createElement("img");
    foto.className = "peta__foto";
    foto.setAttribute("data-src", item.foto);
    foto.alt = "";
    foto.width = 320;
    foto.height = 150;
    foto.decoding = "async";
    box.appendChild(foto);
  }

  const isi = el("div", "peta__isi");
  isi.appendChild(el("strong", "peta__judul", say(item)));

  const jenis = el("p", "peta__jenis");
  const titik = el("i", "peta__titik");
  titik.setAttribute("data-kind", item.kind);
  jenis.append(titik, el("span", `peta__kind peta__kind--${item.kind}`, say(KIND[item.kind])),
    el("span", "peta__sela", "·"), el("span", "", say(item.at)));
  isi.appendChild(jenis);

  const letak = el("p", "peta__koordinat");
  letak.append(svg(IKON.lokasi), el("span", "", koordinat(item.lat, item.lng)));
  isi.appendChild(letak);

  const aksi = el("div", "peta__aksi");
  const lihat = el("a", "peta__tombol peta__tombol--utama");
  lihat.href = `#karya-${item.id}`;
  lihat.append(svg(IKON.buka), el("span", "", say(TEXT.open)));
  aksi.appendChild(lihat);

  const salin = el("button", "peta__tombol");
  salin.type = "button";
  const salinTeks = el("span", "", say(TEXT.copy));
  salin.append(svg(IKON.tautan), salinTeks);
  salin.addEventListener("click", () => {
    const alamat = window.location.origin + window.location.pathname + AWALAN_HASH + item.id;
    const tanda = (teks: string) => {
      salinTeks.textContent = teks;
      umumkan(teks);
      window.setTimeout(() => {
        salinTeks.textContent = say(TEXT.copy);
      }, 2200);
    };
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(alamat).then(() => tanda(say(TEXT.copied)), () => tanda(say(TEXT.copyFail)));
    } else {
      tanda(say(TEXT.copyFail));
    }
  });
  aksi.appendChild(salin);
  isi.appendChild(aksi);
  box.appendChild(isi);
  return box;
}

const LAPISAN_KEY = "hk-peta-lapisan";

function bacaLapisan(): Dasar {
  try {
    const nilai = window.localStorage.getItem(LAPISAN_KEY);
    return nilai === "satelit" || nilai === "medan" ? nilai : "peta";
  } catch {
    return "peta";
  }
}

function tulisLapisan(nilai: Dasar) {
  try {
    window.localStorage.setItem(LAPISAN_KEY, nilai);
  } catch {
  }
}

type State = {
  dasar: () => Dasar;
  setDasar: (dasar: Dasar) => void;
  setThree: (three: boolean) => void;
  filter: (kind: Category) => void;
  buka: (id: string) => boolean;
  toggleTour: () => void;
  stopTour: () => void;
  flyTo: (entry: Entry, openPopup: boolean) => void;
  home: () => void;
  reset: () => void;
};

function buildUi(map: MapLibreMap, frame: HTMLElement, markers: Entry[], state: State) {
  const atas = el("div", "peta__atas");

  const cari = el("div", "peta__cari");
  cari.setAttribute("role", "search");
  const isian = document.createElement("input");
  isian.type = "search";
  isian.className = "peta__cari-isian";
  isian.id = "peta-cari";
  isian.autocomplete = "off";
  isian.spellcheck = false;
  isian.setAttribute("role", "combobox");
  isian.setAttribute("aria-autocomplete", "list");
  isian.setAttribute("aria-expanded", "false");
  isian.setAttribute("aria-controls", "peta-saran");
  const hapus = el("button", "peta__cari-hapus");
  hapus.type = "button";
  hapus.hidden = true;
  hapus.appendChild(svg(IKON.silang));
  const saran = el("div", "peta__saran");
  saran.id = "peta-saran";
  saran.setAttribute("role", "listbox");
  saran.hidden = true;
  cari.append(svg(IKON.cari, "peta__ikon peta__cari-ikon"), isian, hapus, saran);
  atas.appendChild(cari);

  const kategori = el("div", "peta__kategori");
  kategori.setAttribute("role", "group");
  const rows = {} as Record<Category, HTMLButtonElement>;
  KUNCI_KIND.forEach((key) => {
    const row = el("button", "peta__baris");
    row.type = "button";
    row.setAttribute("data-kind", key);
    row.setAttribute("aria-pressed", "false");
    const ikon = el("i");
    ikon.setAttribute("aria-hidden", "true");
    ikon.innerHTML = ikonKind(key);
    row.append(ikon, el("span", "peta__nama"), el("span", "peta__angka", "0"));
    row.addEventListener("click", () => state.filter(key));
    kategori.appendChild(row);
    rows[key] = row;
  });
  const tour = el("button", "peta__chip");
  tour.type = "button";
  tour.setAttribute("aria-pressed", "false");
  const tourIkon = svg(IKON.main);
  const tourTeks = el("span");
  tour.append(tourIkon, tourTeks);
  tour.addEventListener("click", () => state.toggleTour());
  kategori.appendChild(tour);
  atas.appendChild(kategori);
  frame.appendChild(atas);

  let lapisan: HTMLElement | null = null;
  const pilihanLapisan = {} as Record<Dasar, HTMLButtonElement>;
  const utama = el("button", "peta__lapisan-utama");
  const utamaGambar = el("span", "peta__lapisan-gambar");
  const utamaTeks = el("span", "peta__lapisan-teks");
  if (TOKEN) {
    lapisan = el("div", "peta__lapisan");
    utama.type = "button";
    utama.append(utamaGambar, utamaTeks);
    utama.addEventListener("click", () => state.setDasar(state.dasar() === "satelit" ? "peta" : "satelit"));
    const daftar = el("div", "peta__lapisan-pilihan");
    daftar.setAttribute("role", "group");
    (["peta", "satelit", "medan"] as Dasar[]).forEach((nama) => {
      const opsi = el("button", "peta__lapisan-opsi");
      opsi.type = "button";
      opsi.setAttribute("data-lapisan", nama);
      opsi.setAttribute("aria-pressed", "false");
      const gambar = el("span", "peta__lapisan-gambar");
      gambar.innerHTML = GAMBAR_LAPISAN[nama];
      opsi.append(gambar, el("span", "peta__lapisan-label"));
      opsi.addEventListener("click", () => state.setDasar(nama));
      daftar.appendChild(opsi);
      pilihanLapisan[nama] = opsi;
    });
    lapisan.append(utama, daftar);
    frame.appendChild(lapisan);
  }

  const petunjuk = el("div", "peta__petunjuk");
  petunjuk.setAttribute("aria-hidden", "true");
  const petunjukTeks = el("span");
  petunjuk.appendChild(petunjukTeks);
  frame.appendChild(petunjuk);

  let aktif = -1;
  let hasil: Entry[] = [];

  const mati = (entry: Entry) => entry.marker.getElement().classList.contains("is-off");

  function cocok(item: Karya, q: string): number {
    const bidang = [item.en, item.ind, item.at.en, item.at.ind, KIND[item.kind].en, KIND[item.kind].ind]
      .map(polos).join(" | ");
    if (polos(say(item)).indexOf(q) === 0) return 3;
    if (bidang.indexOf(q) === 0 || bidang.indexOf(" " + q) !== -1) return 2;
    return bidang.indexOf(q) !== -1 ? 1 : 0;
  }

  function terlihat(): Entry[] {
    const view = map.getBounds();
    return markers.filter((entry) => !mati(entry) && view.contains([entry.item.lng, entry.item.lat]));
  }

  function tutupSaran() {
    saran.hidden = true;
    isian.setAttribute("aria-expanded", "false");
    isian.removeAttribute("aria-activedescendant");
    cari.classList.remove("is-terbuka");
    aktif = -1;
  }

  function tandaiAktif() {
    saran.querySelectorAll<HTMLElement>(".peta__opsi").forEach((opsi, i) => {
      const ya = i === aktif;
      opsi.setAttribute("aria-selected", ya ? "true" : "false");
      opsi.classList.toggle("is-aktif", ya);
      if (ya) {
        isian.setAttribute("aria-activedescendant", opsi.id);
        opsi.scrollIntoView?.({ block: "nearest" });
      }
    });
    if (aktif < 0) isian.removeAttribute("aria-activedescendant");
  }

  function pilih(entry: Entry) {
    isian.value = say(entry.item);
    hapus.hidden = false;
    tutupSaran();
    state.buka(entry.item.id);
  }

  function isiSaran() {
    const q = polos(isian.value.trim());
    saran.replaceChildren();
    const judul = el("p", "peta__saran-judul");
    if (!q) {
      hasil = terlihat();
      const total = markers.filter((entry) => !mati(entry)).length;
      judul.textContent = say(TEXT.inView).replace("%n", String(hasil.length)).replace("%t", String(total));
    } else {
      hasil = markers
        .map((entry) => ({ entry, skor: cocok(entry.item, q) }))
        .filter((x) => x.skor > 0)
        .sort((a, b) => b.skor - a.skor)
        .map((x) => x.entry);
      if (!hasil.length) judul.textContent = say(TEXT.noMatch).replace("%q", isian.value.trim());
    }
    if (judul.textContent) saran.appendChild(judul);

    hasil.forEach((entry, i) => {
      const opsi = el("div", "peta__opsi");
      opsi.id = `peta-saran-${entry.item.id}`;
      opsi.setAttribute("role", "option");
      opsi.setAttribute("aria-selected", "false");
      opsi.setAttribute("data-kind", entry.item.kind);
      const ikon = el("i", "peta__opsi-ikon");
      ikon.setAttribute("aria-hidden", "true");
      ikon.innerHTML = ikonKind(entry.item.kind);
      const teks = el("span", "peta__opsi-teks");
      teks.append(el("span", "peta__opsi-nama", say(entry.item)),
        el("span", "peta__opsi-ket", `${say(KIND[entry.item.kind])} · ${say(entry.item.at)}`));
      opsi.append(ikon, teks);
      opsi.addEventListener("mousedown", (event) => event.preventDefault());
      opsi.addEventListener("click", () => pilih(entry));
      opsi.addEventListener("mousemove", () => {
        if (aktif !== i) {
          aktif = i;
          tandaiAktif();
        }
      });
      saran.appendChild(opsi);
    });

    aktif = q && hasil.length ? 0 : -1;
    saran.hidden = false;
    cari.classList.add("is-terbuka");
    isian.setAttribute("aria-expanded", "true");
    tandaiAktif();
  }

  isian.addEventListener("focus", () => {
    state.stopTour();
    isiSaran();
  });
  isian.addEventListener("input", () => {
    hapus.hidden = !isian.value;
    isiSaran();
  });
  isian.addEventListener("blur", () => {
    window.setTimeout(tutupSaran, 120);
  });
  isian.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (saran.hidden) isiSaran();
      if (!hasil.length) return;
      const arah = event.key === "ArrowDown" ? 1 : -1;
      aktif = (aktif + arah + hasil.length) % hasil.length;
      tandaiAktif();
    } else if (event.key === "Enter") {
      event.preventDefault();
      const entry = hasil[aktif >= 0 ? aktif : 0];
      if (entry) pilih(entry);
    } else if (event.key === "Escape") {
      if (!saran.hidden) {
        event.preventDefault();
        tutupSaran();
      } else if (isian.value) {
        isian.value = "";
        hapus.hidden = true;
      }
    }
  });
  hapus.addEventListener("click", () => {
    isian.value = "";
    hapus.hidden = true;
    isian.focus();
    isiSaran();
  });

  let jedaPetunjuk = 0;
  function tunjukkan(teks: string) {
    petunjukTeks.textContent = teks;
    petunjuk.classList.add("is-tampil");
    window.clearTimeout(jedaPetunjuk);
    jedaPetunjuk = window.setTimeout(() => petunjuk.classList.remove("is-tampil"), 1400);
  }

  function markDasar(dasar: Dasar) {
    if (!lapisan) return;
    const berikut: Dasar = dasar === "satelit" ? "peta" : "satelit";
    utamaGambar.innerHTML = GAMBAR_LAPISAN[berikut];
    utamaTeks.textContent = say(berikut === "satelit" ? TEXT.satellite : TEXT.map);
    utama.title = `${say(TEXT.layers)}: ${utamaTeks.textContent}`;
    utama.setAttribute("aria-label", utama.title);
    (Object.keys(pilihanLapisan) as Dasar[]).forEach((nama) => {
      pilihanLapisan[nama].setAttribute("aria-pressed", nama === dasar ? "true" : "false");
    });
    frame.setAttribute("data-dasar", dasar);
  }

  function label() {
    isian.placeholder = say(TEXT.search);
    isian.setAttribute("aria-label", say(TEXT.search));
    hapus.title = say(TEXT.clear);
    hapus.setAttribute("aria-label", say(TEXT.clear));
    kategori.setAttribute("aria-label", say(TEXT.kinds));
    tourTeks.textContent = say(TEXT.tour);
    KUNCI_KIND.forEach((key) => {
      const nama = rows[key].querySelector(".peta__nama");
      if (nama) nama.textContent = say(KIND[key]);
    });
    if (lapisan) {
      lapisan.setAttribute("aria-label", say(TEXT.layers));
      (Object.keys(pilihanLapisan) as Dasar[]).forEach((nama) => {
        const teks = pilihanLapisan[nama].querySelector(".peta__lapisan-label");
        if (teks) teks.textContent = say(nama === "peta" ? TEXT.map : nama === "satelit" ? TEXT.satellite : TEXT.terrain);
      });
      markDasar(state.dasar());
    }
    if (!saran.hidden) isiSaran();
  }

  function count() {
    const view = map.getBounds();
    const seen: Record<Category, number> = { app: 0, analysis: 0, satellite: 0, design: 0 };
    markers.forEach((entry) => {
      if (mati(entry)) return;
      if (!view.contains([entry.item.lng, entry.item.lat])) return;
      seen[entry.item.kind] += 1;
    });
    KUNCI_KIND.forEach((key) => {
      const angka = rows[key].querySelector(".peta__angka");
      if (angka) angka.textContent = String(seen[key]);
      rows[key].classList.toggle("is-empty", seen[key] === 0);
    });
    frame.classList.toggle("is-dekat", map.getZoom() >= 9);
    if (!saran.hidden && !isian.value.trim()) isiSaran();
  }

  let pending = 0;
  function countSoon() {
    if (pending) return;
    pending = window.requestAnimationFrame(() => {
      pending = 0;
      count();
    });
  }

  label();
  map.on("move", countSoon);
  map.on("moveend", count);
  map.on("zoom", countSoon);

  return {
    label,
    count,
    tunjukkan,
    markDasar,
    markTour(running: boolean) {
      tour.setAttribute("aria-pressed", running ? "true" : "false");
      tourIkon.innerHTML = `<svg viewBox="0 0 24 24" focusable="false">${running ? IKON.henti : IKON.main}</svg>`;
    },
    markFilter(kind: Category | null) {
      KUNCI_KIND.forEach((key) => rows[key].setAttribute("aria-pressed", kind === key ? "true" : "false"));
      atas.classList.toggle("is-filtered", Boolean(kind));
    },
  };
}

export type PetaHidup = {
  map: MapLibreMap;
  state: State;
  gantiBahasa: () => void;
  hapus: () => void;
};

export function bangun(maplibregl: Pustaka, container: HTMLElement): PetaHidup {
  const bounds: LngLatBounds = new maplibregl.LngLatBounds();
  WORK.forEach((item) => bounds.extend([item.lng, item.lat]));

  const frame = container.parentElement as HTMLElement;
  const section = frame.parentElement as HTMLElement;
  const current = {
    three: false,
    filter: null as Category | null,
    tour: 0,
    tourAt: 0,
    dasar: (TOKEN ? bacaLapisan() : "peta") as Dasar,
    gelap: temaGelap(),
  };

  const pilihanGaya = (): OpsiGaya => ({
    gelap: current.gelap,
    satelit: current.dasar === "satelit",
    medan: current.dasar === "medan",
    tiga: current.three,
    lang: isId() ? "id" : "en",
  });

  const map = new maplibregl.Map({
    container,
    style: TOKEN ? mapboxStyle(pilihanGaya()) : FALLBACK_STYLE,
    bounds,
    fitBoundsOptions: { padding: 64, maxZoom: 6 },
    minZoom: 2.5,
    maxZoom: 18,
    maxPitch: 75,
    attributionControl: false,
    cooperativeGestures: sentuh(),
    scrollZoom: sentuh(),
    locale: {
      "CooperativeGesturesHandler.MobileHelpText": say(TEXT.touchHint),
      "CooperativeGesturesHandler.WindowsHelpText": say(TEXT.ctrlHint),
      "CooperativeGesturesHandler.MacHelpText": say(TEXT.cmdHint),
    },
  });

  map.touchZoomRotate.disableRotation();
  map.dragRotate.disable();

  map.on("styleimagemissing", (event: { id?: string }) => {
    if (event?.id && event.id.indexOf("hk-poi-") === 0) tambahIkon(map, event.id);
  });

  let tigaTombol: HTMLButtonElement | null = null;
  map.addControl(new maplibregl.FullscreenControl({ container: frame }), "top-right");
  map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 96, unit: "metric" }), "bottom-right");
  map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "bottom-right");
  map.addControl(new Kontrol(() => {
    const wrap = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
    const button = el("button", "peta__rumah");
    button.type = "button";
    button.appendChild(svg(IKON.rumah, "peta__ikon-kontrol"));
    button.addEventListener("click", () => state.home());
    wrap.appendChild(button);
    return wrap;
  }), "bottom-right");
  map.addControl(new Kontrol(() => {
    const wrap = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
    const tombol = el("button", "peta__tiga", "3D");
    tombol.type = "button";
    tombol.setAttribute("aria-pressed", "false");
    tombol.addEventListener("click", () => state.setThree(!current.three));
    wrap.appendChild(tombol);
    tigaTombol = tombol;
    return wrap;
  }), "bottom-right");

  function terjemahkanKontrol() {
    const judul: [string, Teks][] = [
      [".maplibregl-ctrl-zoom-in", TEXT.zoomIn],
      [".maplibregl-ctrl-zoom-out", TEXT.zoomOut],
      [".maplibregl-ctrl-compass", TEXT.north],
      [".peta__rumah", TEXT.home],
      [".peta__tiga", TEXT.three],
    ];
    judul.forEach(([pilih, teks]) => {
      const node = frame.querySelector<HTMLElement>(pilih);
      if (!node) return;
      node.title = say(teks);
      node.setAttribute("aria-label", say(teks));
    });
    const layar = frame.querySelector<HTMLElement>(".maplibregl-ctrl-fullscreen, .maplibregl-ctrl-shrink");
    if (layar) {
      layar.title = say(layar.classList.contains("maplibregl-ctrl-shrink") ? TEXT.unfull : TEXT.full);
      layar.setAttribute("aria-label", layar.title);
    }
  }

  const kabar = document.createElement("p");
  kabar.className = "peta__kabar visually-hidden";
  kabar.setAttribute("aria-live", "polite");

  function umumkan(teks: string) {
    kabar.textContent = "";
    window.setTimeout(() => {
      kabar.textContent = teks;
    }, 60);
  }

  const markers: Entry[] = WORK.map((item) => {
    const popup = new maplibregl.Popup({
      anchor: "bottom",
      offset: [0, -44],
      closeButton: false,
      focusAfterOpen: false,
      maxWidth: "320px",
      className: "peta__popup",
    });
    const marker = new maplibregl.Marker({ element: markerElement(item), anchor: "bottom" })
      .setLngLat([item.lng, item.lat])
      .setPopup(popup)
      .addTo(map);
    const entry: Entry = { item, marker, popup };
    popup.setDOMContent(kartu(entry, umumkan));
    popup.on("open", () => {
      marker.getElement().classList.add("is-aktif");
      const foto = popup.getElement()?.querySelector<HTMLImageElement>(".peta__foto[data-src]");
      if (foto) {
        foto.src = foto.getAttribute("data-src") ?? "";
        foto.removeAttribute("data-src");
      }
    });
    popup.on("close", () => marker.getElement().classList.remove("is-aktif"));
    marker.getElement().addEventListener("click", (event) => {
      const lewatPapan = event.detail === 0;
      window.setTimeout(() => {
        state.flyTo(entry, false);
        if (lewatPapan && popup.isOpen()) {
          popup.getElement()?.querySelector<HTMLElement>(".peta__tutup")?.focus({ preventScroll: true });
        }
      }, 0);
    });
    return entry;
  });

  let sudahDipusatkan = false;

  const cari = (id: string) => markers.find((entry) => entry.item.id === id) ?? null;
  const mati = (entry: Entry) => entry.marker.getElement().classList.contains("is-off");

  function terapkan() {
    if (TOKEN) {
      map.setStyle(mapboxStyle(pilihanGaya()), { diff: true });
    } else {
      tuneBasemap(map, current.gelap);
      applyRelief(map, current.three);
    }
    frame.classList.toggle("is-tiga", current.three);
    frame.classList.toggle("is-gelap", current.gelap);
  }

  function flyToWork(entry: Entry, openPopup: boolean) {
    map.flyTo({
      center: [entry.item.lng, entry.item.lat],
      offset: [0, Math.round(Math.min(160, frame.clientHeight * 0.3))],
      zoom: 15.2,
      pitch: current.three ? 62 : 0,
      bearing: current.three ? -22 : 0,
      speed: 0.9,
      curve: 1.5,
      duration: ms(2600),
    });
    if (openPopup && !entry.popup.isOpen()) entry.marker.togglePopup();
    tulisHash(entry.item.id);
  }

  const state: State = {
    dasar: () => current.dasar,
    setDasar(dasar) {
      if (!TOKEN || dasar === current.dasar) return;
      current.dasar = dasar;
      tulisLapisan(dasar);
      ui.markDasar(dasar);
      terapkan();
      umumkan(say(TEXT.layerOn).replace("%l",
        say(dasar === "satelit" ? TEXT.satellite : dasar === "medan" ? TEXT.terrain : TEXT.map)));
    },
    setThree(three) {
      if (three === current.three) return;
      current.three = three;
      tigaTombol?.setAttribute("aria-pressed", three ? "true" : "false");
      terapkan();
      if (three) map.dragRotate.enable();
      else map.dragRotate.disable();
      window.requestAnimationFrame(() => {
        map.easeTo({ pitch: three ? 58 : 0, bearing: three ? -18 : 0, duration: ms(900) });
      });
    },
    filter(kind) {
      state.stopTour();
      current.filter = current.filter === kind ? null : kind;
      ui.markFilter(current.filter);
      const visible = new maplibregl.LngLatBounds();
      markers.forEach((entry) => {
        const show = !current.filter || entry.item.kind === current.filter;
        entry.marker.getElement().classList.toggle("is-off", !show);
        if (!show && entry.popup.isOpen()) entry.popup.remove();
        if (show) visible.extend([entry.item.lng, entry.item.lat]);
      });
      map.fitBounds(current.filter ? visible : bounds, {
        padding: 64,
        maxZoom: current.filter ? 7 : 6,
        duration: ms(700),
      });
      ui.count();
      const tampil = markers.filter((entry) => !mati(entry)).length;
      umumkan(current.filter
        ? say(TEXT.filterOn)
            .replace("%k", say(KIND[current.filter]))
            .replace("%n", String(tampil))
            .replace("%t", String(markers.length))
        : say(TEXT.filterOff).replace("%t", String(markers.length)));
    },
    buka(id) {
      const entry = cari(id);
      if (!entry) return false;
      sudahDipusatkan = true;
      state.stopTour();
      if (current.filter && entry.item.kind !== current.filter) state.filter(current.filter);
      flyToWork(entry, true);
      umumkan(say(TEXT.focus).replace("%w", say(entry.item)));
      return true;
    },
    toggleTour() {
      if (current.tour) {
        state.stopTour();
        return;
      }
      current.tourAt = 0;
      const step = () => {
        const entry = markers[current.tourAt % markers.length];
        current.tourAt += 1;
        if (!mati(entry)) flyToWork(entry, true);
      };
      step();
      current.tour = window.setInterval(step, 7000);
      ui.markTour(true);
    },
    stopTour() {
      if (!current.tour) return;
      window.clearInterval(current.tour);
      current.tour = 0;
      ui.markTour(false);
    },
    flyTo: flyToWork,
    home() {
      state.stopTour();
      if (current.filter) {
        current.filter = null;
        ui.markFilter(null);
        markers.forEach((entry) => entry.marker.getElement().classList.remove("is-off"));
      }
      markers.forEach((entry) => {
        if (entry.popup.isOpen()) entry.popup.remove();
      });
      map.easeTo({ pitch: current.three ? 58 : 0, bearing: current.three ? -18 : 0, duration: ms(500) });
      map.fitBounds(bounds, { padding: 64, maxZoom: 6, duration: ms(750) });
      ui.count();
      tulisHash(null);
    },
    reset() {
      state.home();
    },
  };

  const ui = buildUi(map, frame, markers, state);
  ui.markDasar(current.dasar);
  section.insertBefore(kabar, section.querySelector(".peta__ket"));
  frame.classList.toggle("is-gelap", current.gelap);
  terjemahkanKontrol();

  let sudahSiap = false;
  function siap() {
    if (sudahSiap) return;
    sudahSiap = true;
    if (!TOKEN) {
      tuneBasemap(map, current.gelap);
      applyRelief(map, current.three);
    }
    map.resize();
    if (!sudahDipusatkan) map.fitBounds(bounds, { padding: 64, maxZoom: 6, duration: 0 });
    frame.classList.add("is-ready");
    terjemahkanKontrol();
    window.requestAnimationFrame(() => {
      ui.count();
      const id = idDariHash();
      if (id) state.buka(id);
    });
  }

  map.on("load", siap);
  map.on("styledata", siap);
  map.on("idle", siap);
  const jaring = window.setTimeout(siap, 4000);

  const dengarAlamat = () => {
    const id = idDariHash();
    if (id) state.buka(id);
  };
  window.addEventListener("hashchange", dengarAlamat);

  const tema = new MutationObserver(() => {
    const gelap = temaGelap();
    if (gelap === current.gelap) return;
    current.gelap = gelap;
    terapkan();
  });
  tema.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  const layarBerubah = () => window.setTimeout(terjemahkanKontrol, 0);
  document.addEventListener("fullscreenchange", layarBerubah);

  const tanganDiPeta = () => state.stopTour();
  if (!sentuh()) {
    container.addEventListener("wheel", (event) => {
      if (event.ctrlKey || event.metaKey) {
        map.scrollZoom.enable();
      } else {
        map.scrollZoom.disable();
        ui.tunjukkan(say(mac() ? TEXT.cmdHint : TEXT.ctrlHint));
      }
    }, { capture: true, passive: true });
  }
  container.addEventListener("pointerdown", tanganDiPeta, true);
  container.addEventListener("wheel", tanganDiPeta, { capture: true, passive: true });
  container.addEventListener("keydown", tanganDiPeta, true);
  frame.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    markers.forEach((entry) => {
      if (entry.popup.isOpen()) entry.popup.remove();
    });
  });
  map.on("dragstart", tanganDiPeta);
  map.on("rotateend", () => {
    if (!current.three && Math.abs(map.getBearing()) > 0.01) map.setBearing(0);
  });

  function gantiBahasa() {
    ui.label();
    ui.count();
    terjemahkanKontrol();
    if (TOKEN) terapkan();
    markers.forEach((entry) => {
      entry.popup.setDOMContent(kartu(entry, umumkan));
      const pin = entry.marker.getElement();
      pin.title = say(entry.item);
      pin.setAttribute("aria-label", say(entry.item));
      const nama = pin.querySelector(".peta__pin-nama");
      if (nama) nama.textContent = say(entry.item);
    });
  }

  function hapus() {
    state.stopTour();
    window.clearTimeout(jaring);
    window.removeEventListener("hashchange", dengarAlamat);
    document.removeEventListener("fullscreenchange", layarBerubah);
    tema.disconnect();
    kabar.remove();
    frame.querySelectorAll(".peta__atas, .peta__lapisan, .peta__petunjuk").forEach((node) => node.remove());
    map.remove();
  }

  return { map, state, gantiBahasa, hapus };
}
