import type { Map as MapLibreMap, MapLayerMouseEvent, StyleSpecification } from "maplibre-gl";
import { FALLBACK_STYLE, TOKEN, mapboxStyle, tambahIkon } from "./gaya";
import {
  asetTerdekat,
  cariKawasan,
  daftarRuas,
  hitungTarif,
  type DataParkir,
  type Layanan,
  type Posisi,
  type Ruas,
  type Tarif,
} from "./parkir-hitung";

type Pustaka = typeof import("maplibre-gl");
type Teks = { en: string; ind: string };

const WARNA = {
  terang: { I: "#9e2b25", II: "#8a5500", aset: "#1e7b34", halo: "#ffffff", sorot: "#202124" },
  gelap: { I: "#ff8a80", II: "#fdd663", aset: "#8fd9a8", halo: "#1f2023", sorot: "#e8eaed" }
};

const KENDARAAN: Record<string, Teks> = {
  "Sepeda motor": { en: "Motorbike", ind: "Motor" },
  "Sedan, jip, pickup, station wagon, kendaraan roda tiga": { en: "Car", ind: "Mobil" },
  "Truk sedang atau box": { en: "Medium truck", ind: "Truk sedang" },
  "Truk besar": { en: "Large truck", ind: "Truk besar" },
  "Truk gandengan sumbu III atau lebih": { en: "Trailer truck", ind: "Truk gandeng" },
  "Bus sedang": { en: "Medium bus", ind: "Bus sedang" },
  "Bus besar": { en: "Large bus", ind: "Bus besar" },
  "Sepeda listrik": { en: "E-bike", ind: "Sepeda listrik" },
  "Sepeda": { en: "Bicycle", ind: "Sepeda" },
  "Andong": { en: "Horse cart", ind: "Andong" },
  "Becak": { en: "Pedicab", ind: "Becak" }
};

const LAYANAN: Record<Layanan, Teks> = {
  reguler: { en: "Regular", ind: "Biasa" },
  insidental: { en: "Event", ind: "Acara" },
  pasar: { en: "Market", ind: "Pasar" }
};

const TEXT = {
  search: { en: "Search a street", ind: "Cari nama jalan" },
  clear: { en: "Clear", ind: "Hapus" },
  noMatch: { en: "No street called “%q”", ind: "Jalan “%q” tidak ketemu" },
  zone: { en: "Zone %k", ind: "Kawasan %k" },
  fromStreet: { en: "%m m from the street", ind: "%m m dari jalan" },
  zoneThree: { en: "Zone III street", ind: "Jalan Kawasan III" },
  zoneThreeNote: { en: "The cheapest zone", ind: "Kawasan paling murah" },
  outside: { en: "Outside Yogyakarta city", ind: "Di luar Kota Yogyakarta" },
  outsideNote: {
    en: "These fees only apply in Yogyakarta city, so there is no fee here.",
    ind: "Tarif ini cuma berlaku di Kota Yogyakarta, jadi di sini tidak ada tarifnya."
  },
  once: { en: "Zone %k. Pay once, however long you stay.", ind: "Kawasan %k. Bayar sekali, berapa lama pun." },
  market: { en: "Market fee. Pay once each visit.", ind: "Tarif pasar. Bayar sekali tiap parkir." },
  firstTwo: { en: "Rp%a for the first 2 hours", ind: "Rp%a untuk 2 jam pertama" },
  thenHours: { en: ", then %j h × Rp%b", ind: ", lalu %j jam × Rp%b" },
  proposal: {
    en: "This street is only proposed for Zone I and not decided yet. Check the fee board on site.",
    ind: "Jalan ini baru diusulkan masuk Kawasan I dan belum ditetapkan. Cek papan tarif di lokasi, ya."
  },
  vehicle: { en: "Vehicle", ind: "Kendaraan" },
  hours: { en: "How long", ind: "Lama parkir" },
  hourUnit: { en: "%j h", ind: "%j jam" },
  less: { en: "1 hour less", ind: "Kurangi 1 jam" },
  more: { en: "1 hour more", ind: "Tambah 1 jam" },
  service: { en: "Parking type", ind: "Jenis parkir" },
  legendOne: { en: "Zone I", ind: "Kawasan I" },
  legendTwo: { en: "Zone II", ind: "Kawasan II" },
  legendProposal: { en: "Still a proposal", ind: "Masih usulan" },
  legendAsset: { en: "Provincial parking", ind: "Parkir Pemda DIY" },
  legendRest: { en: "Other streets in the city are Zone III.", ind: "Jalan lain di kota masuk Kawasan III." },
  assetNote: {
    en: "Fees here are different, set by Pergub DIY 46/2024.",
    ind: "Tarif di sini beda, diatur Pergub DIY 46/2024."
  },
  spaces: { en: "%n motorbike spots", ind: "%n tempat motor" },
  announce: { en: "%r. %f.", ind: "%r. %f." },
  noFee: { en: "No fee listed", ind: "Tarif tidak tersedia" },
  zoomIn: { en: "Zoom in", ind: "Perbesar" },
  zoomOut: { en: "Zoom out", ind: "Perkecil" },
  north: { en: "Face north", ind: "Hadap utara" },
  full: { en: "Full screen", ind: "Layar penuh" },
  unfull: { en: "Exit full screen", ind: "Keluar layar penuh" },
  close: { en: "Close", ind: "Tutup" },
  legend: { en: "Map key", ind: "Keterangan" },
  legendTitle: { en: "Map key", ind: "Keterangan" },
  legendHint: { en: "Tap to show or hide.", ind: "Ketuk untuk tampilkan atau sembunyikan." },
  legendHide: { en: "Close", ind: "Tutup" },
  moreDetails: { en: "Show options", ind: "Tampilkan pilihan" },
  lessDetails: { en: "Hide options", ind: "Sembunyikan pilihan" },
  nearest: { en: "Nearest provincial parking", ind: "Parkir Pemda DIY terdekat" },
  here: { en: "here", ind: "di sini" },
  goThere: { en: "Go to %n, %d", ind: "Ke %n, %d" }
};

const IKON = {
  cari: '<svg viewBox="0 0 24 24" focusable="false"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>',
  hapus: '<svg viewBox="0 0 24 24" focusable="false"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path></svg>',
  lapis: '<svg viewBox="0 0 24 24" focusable="false"><path d="m11.99 18.54-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"></path></svg>',
  lipat: '<svg viewBox="0 0 24 24" focusable="false"><path d="M7.41 15.41 12 10.83l4.59 4.58L18 14l-6-6-6 6z"></path></svg>',
  tempat: '<svg viewBox="0 0 24 24" focusable="false"><path d="M13 3H6v18h4v-6h3c3.31 0 6-2.69 6-6s-2.69-6-6-6zm.2 8H10V7h3.2c1.1 0 2 .9 2 2s-.9 2-2 2z"></path></svg>',
  cek: '<svg viewBox="0 0 24 24" focusable="false"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>'
};

const SIMPAN = "hk-parkir";
const DEKAT_M = 2500;
const PUSAT: [number, number] = [110.3657, -7.7949];
const BATAS: [[number, number], [number, number]] = [[109.95, -8.2], [110.8, -7.45]];
const JAM_MAKS = 24;

const LEGENDA: { kunci: KunciLapis; tanda: string; teks: keyof typeof TEXT }[] = [
  { kunci: "I", tanda: "parkir__garis parkir__garis--satu", teks: "legendOne" },
  { kunci: "II", tanda: "parkir__garis parkir__garis--dua", teks: "legendTwo" },
  { kunci: "usulan", tanda: "parkir__garis parkir__garis--usulan", teks: "legendProposal" },
  { kunci: "aset", tanda: "parkir__bulatan", teks: "legendAsset" },
];

function isId(): boolean {
  return document.documentElement.getAttribute("lang") === "id";
}

function say(entry: Teks): string {
  return isId() ? entry.ind : entry.en;
}

function temaGelap(): boolean {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function sentuh(): boolean {
  return Boolean(window.matchMedia && window.matchMedia("(hover: none) and (pointer: coarse)").matches);
}

function reducedMotion(): boolean {
  return Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
}

function rupiah(n: number): string {
  return Number(n).toLocaleString(isId() ? "id-ID" : "en-US");
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, kelas?: string, teks?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (kelas) node.className = kelas;
  if (teks) node.textContent = teks;
  return node;
}

function polos(teks: string): string {
  return String(teks || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

function bacaSetelan(): Record<string, unknown> {
  try {
    const nilai = JSON.parse(window.localStorage.getItem(SIMPAN) || "{}");
    return nilai && typeof nilai === "object" ? nilai : {};
  } catch {
    return {};
  }
}

function simpanSetelan(kunci: string, nilai: unknown) {
  const setelan = bacaSetelan();
  setelan[kunci] = nilai;
  try {
    window.localStorage.setItem(SIMPAN, JSON.stringify(setelan));
  } catch {
    return;
  }
}

function susun<T extends HTMLElement>(induk: T, anak: Node[]): T {
  anak.forEach((a) => induk.appendChild(a));
  return induk;
}

function ikon(kelas: string, isi: string): HTMLSpanElement {
  const node = el("span", "parkir__ikon" + (kelas ? " " + kelas : ""));
  node.setAttribute("aria-hidden", "true");
  node.innerHTML = isi;
  return node;
}

function kedip(node: HTMLElement, kelas: string) {
  node.classList.remove(kelas);
  void node.offsetWidth;
  node.classList.add(kelas);
}

function jarakTeks(meter: number): string {
  if (meter < 15) return say(TEXT.here);
  if (meter < 1000) return rupiah(Math.round(meter / 10) * 10) + " m";
  return (meter / 1000).toLocaleString(isId() ? "id-ID" : "en-US", { maximumFractionDigits: 1 }) + " km";
}

type KunciLapis = "I" | "II" | "usulan" | "aset";
type Warna = (typeof WARNA)["terang"];
type Lapis = Record<string, unknown> & { id: string; type: string };
type GayaGabung = Record<string, unknown> & { sources: Record<string, unknown>; layers: Lapis[] };

function lapisanParkir(w: Warna, tampil: Record<KunciLapis, boolean>): Lapis[] {
  const tebal = ["interpolate", ["linear"], ["zoom"], 12, 2, 15, 4.5, 18, 9];
  const tebalHalo = ["interpolate", ["linear"], ["zoom"], 12, 4, 15, 7.5, 18, 13];
  const tebalSorot = ["interpolate", ["linear"], ["zoom"], 12, 9, 15, 14, 18, 22];
  const warna = ["match", ["get", "k"], "I", w.I, w.II];
  const zona = (["I", "II"] as const).filter((k) => tampil[k]);
  const tetap = ["all", ["==", ["get", "u"], 0], ["in", ["get", "k"], ["literal", zona]]];
  const usul = ["all", ["==", ["get", "u"], 1], Boolean(tampil.usulan)];
  return [
    { id: "parkir-sorot", type: "line", source: "parkir-terpilih",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": w.sorot, "line-opacity": 0.22, "line-width": tebalSorot } },
    { id: "parkir-halo", type: "line", source: "parkir", filter: ["any", tetap, usul],
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": w.halo, "line-width": tebalHalo } },
    { id: "parkir-tetap", type: "line", source: "parkir", filter: tetap,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": warna, "line-width": tebal } },
    { id: "parkir-usulan", type: "line", source: "parkir", filter: usul,
      layout: { "line-cap": "butt", "line-join": "round" },
      paint: { "line-color": warna, "line-width": tebal, "line-dasharray": [0.6, 1.2] } },
    { id: "parkir-aset", type: "circle", source: "parkir-aset",
      layout: { visibility: tampil.aset ? "visible" : "none" },
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 9],
        "circle-color": w.aset,
        "circle-stroke-color": w.halo,
        "circle-stroke-width": 2.5,
      } },
  ];
}

export type ParkirHidup = {
  peta: () => MapLibreMap | null;
  gantiBahasa: () => void;
  hapus: () => void;
};

export function bangunParkir(maplibregl: Pustaka, container: HTMLElement, DATA: DataParkir): ParkirHidup {
  const frame = container.parentElement as HTMLElement;
  const bungkus = frame.parentElement as HTMLElement;
  const section = bungkus.parentElement as HTMLElement;
  const DAFTAR_KENDARAAN = Object.keys(KENDARAAN).filter((nama) => DATA.tarif.some((t) => t.kendaraan === nama));
  const DAFTAR_RUAS = daftarRuas(DATA);
  let map: MapLibreMap | null = null;
  let dasarCadangan: GayaGabung | null = null;
  let dihapus = false;
  const setelan = bacaSetelan();
  const layarLebar = window.matchMedia("(min-width: 860px)");
  const keadaan = {
    kendaraan: "Sepeda motor",
    layanan: "reguler" as Layanan,
    jam: 1,
    posisi: null as Posisi | null,
    titik: PUSAT as [number, number],
    gelap: temaGelap(),
    tampil: { I: true, II: true, usulan: true, aset: true } as Record<KunciLapis, boolean>,
    legenda: typeof setelan.legenda === "boolean"
      ? setelan.legenda
      : window.matchMedia("(min-width: 1200px)").matches,
    ringkas: setelan.ringkas === true,
  };

  const samping = el("div", "parkir__samping");
  const cari = el("div", "parkir__cari");
  cari.setAttribute("role", "search");
  const isian = el("input", "parkir__cari-isian");
  isian.type = "search";
  isian.id = "parkir-cari";
  isian.autocomplete = "off";
  isian.spellcheck = false;
  isian.setAttribute("role", "combobox");
  isian.setAttribute("aria-autocomplete", "list");
  isian.setAttribute("aria-expanded", "false");
  isian.setAttribute("aria-controls", "parkir-saran");
  const hapusCari = el("button", "parkir__cari-hapus");
  hapusCari.type = "button";
  hapusCari.hidden = true;
  hapusCari.appendChild(ikon("", IKON.hapus));
  const saran = el("ul", "parkir__saran");
  saran.id = "parkir-saran";
  saran.setAttribute("role", "listbox");
  saran.hidden = true;
  susun(cari, [ikon("parkir__cari-ikon", IKON.cari), isian, hapusCari, saran]);

  const kartu = el("div", "parkir__kartu");
  const lipat = el("button", "parkir__lipat");
  lipat.type = "button";
  lipat.setAttribute("aria-controls", "parkir-atur");
  lipat.appendChild(ikon("", IKON.lipat));

  const ringkasan = el("div", "parkir__ringkasan");
  const lokasi = el("p", "parkir__lokasi");
  const titikWarna = el("i", "parkir__titik");
  titikWarna.setAttribute("aria-hidden", "true");
  const namaRuas = el("strong", "parkir__ruas");
  susun(lokasi, [titikWarna, namaRuas]);
  const ketLokasi = el("p", "parkir__ket");
  const harga = el("p", "parkir__harga");
  const subHarga = el("p", "parkir__sub");
  const usulan = el("p", "parkir__usulan");
  usulan.hidden = true;
  susun(ringkasan, [lokasi, ketLokasi, harga, subHarga, usulan]);

  const atur = el("div", "parkir__atur");
  atur.id = "parkir-atur";

  const bidangKendaraan = el("label", "parkir__bidang");
  const labelKendaraan = el("span");
  const pilihKendaraan = el("select", "parkir__pilih");
  susun(bidangKendaraan, [labelKendaraan, pilihKendaraan]);

  const bidangJam = el("div", "parkir__bidang parkir__bidang--jam");
  const labelJam = el("span");
  labelJam.id = "parkir-label-jam";
  const langkah = el("div", "parkir__langkah");
  langkah.setAttribute("role", "group");
  langkah.setAttribute("aria-labelledby", "parkir-label-jam");
  const kurang = el("button", "parkir__bulat", "−");
  kurang.type = "button";
  const nilaiJam = el("output", "parkir__jam");
  const tambah = el("button", "parkir__bulat", "+");
  tambah.type = "button";
  susun(langkah, [kurang, nilaiJam, tambah]);
  susun(bidangJam, [labelJam, langkah]);

  const bidangLayanan = el("div", "parkir__layanan");
  bidangLayanan.setAttribute("role", "group");
  const tombolLayanan = {} as Record<Layanan, HTMLButtonElement>;
  (Object.keys(LAYANAN) as Layanan[]).forEach((kunci) => {
    const b = el("button", "parkir__chip");
    b.type = "button";
    b.addEventListener("click", () => {
      keadaan.layanan = kunci;
      tampilkan();
    });
    bidangLayanan.appendChild(b);
    tombolLayanan[kunci] = b;
  });

  const terdekat = el("button", "parkir__terdekat");
  terdekat.type = "button";
  terdekat.hidden = true;
  const teksTerdekat = el("span", "parkir__terdekat-teks");
  const labelTerdekat = el("small");
  const namaTerdekat = el("strong");
  susun(teksTerdekat, [labelTerdekat, namaTerdekat]);
  const jarakTerdekat = el("span", "parkir__terdekat-jarak");
  susun(terdekat, [ikon("parkir__terdekat-ikon", IKON.tempat), teksTerdekat, jarakTerdekat]);

  susun(atur, [bidangKendaraan, bidangJam, bidangLayanan, terdekat]);
  susun(kartu, [lipat, ringkasan, atur]);
  susun(samping, [cari, kartu]);
  bungkus.appendChild(samping);

  const pin = el("div", "parkir__pin");
  pin.setAttribute("aria-hidden", "true");
  pin.innerHTML =
    '<span class="parkir__denyut"></span><svg viewBox="0 0 26 34" focusable="false"><path d="M13 0C5.8 0 0 5.8 0 13c0 9.7 13 21 13 21s13-11.3 13-21C26 5.8 20.2 0 13 0z"></path><circle cx="13" cy="12.6" r="4.6"></circle></svg>';
  frame.appendChild(pin);

  const legendaKotak = el("div", "parkir__legenda-kotak");
  const isiLegenda = el("div", "parkir__legenda-isi");
  isiLegenda.id = "parkir-legenda";
  const kepalaLegenda = el("div", "parkir__legenda-kepala");
  const judulLegenda = el("p", "parkir__legenda-judul");
  const tutupLegenda = el("button", "parkir__legenda-tutup");
  tutupLegenda.type = "button";
  tutupLegenda.appendChild(ikon("", IKON.hapus));
  susun(kepalaLegenda, [judulLegenda, tutupLegenda]);
  const petunjukLegenda = el("p", "parkir__legenda-petunjuk");
  const legenda = el("ul", "parkir__legenda");
  const tombolLapis = {} as Record<KunciLapis, { tombol: HTMLButtonElement; nama: HTMLSpanElement; teks: Teks }>;
  LEGENDA.forEach((item) => {
    const b = el("button", "parkir__lapis");
    b.type = "button";
    b.setAttribute("data-lapis", item.kunci);
    const tanda = el("i", item.tanda);
    tanda.setAttribute("aria-hidden", "true");
    const nama = el("span", "parkir__lapis-nama");
    susun(b, [tanda, nama, ikon("parkir__lapis-cek", IKON.cek)]);
    b.addEventListener("click", () => {
      keadaan.tampil[item.kunci] = !keadaan.tampil[item.kunci];
      tandaiLapis();
      terapkan();
    });
    legenda.appendChild(susun(el("li"), [b]));
    tombolLapis[item.kunci] = { tombol: b, nama, teks: TEXT[item.teks] };
  });
  const catatanLegenda = el("p", "parkir__catatan");
  susun(isiLegenda, [kepalaLegenda, petunjukLegenda, legenda, catatanLegenda]);
  const tombolLegenda = el("button", "parkir__legenda-tombol");
  tombolLegenda.type = "button";
  tombolLegenda.setAttribute("aria-controls", "parkir-legenda");
  const teksLegenda = el("span");
  susun(tombolLegenda, [ikon("", IKON.lapis), teksLegenda]);
  susun(legendaKotak, [isiLegenda, tombolLegenda]);
  frame.appendChild(legendaKotak);

  const kabar = el("p", "parkir__kabar visually-hidden");
  kabar.setAttribute("aria-live", "polite");
  section.insertBefore(kabar, bungkus.nextSibling);

  function aturLetak() {
    const lebar = layarLebar.matches;
    const kiri = lebar ? samping.offsetWidth + 24 : 0;
    const atas = lebar ? 0 : cari.offsetHeight + 12;
    bungkus.style.setProperty("--parkir-kiri", kiri + "px");
    bungkus.style.setProperty("--parkir-tepi", (lebar ? kiri : 12) + "px");
    bungkus.style.setProperty("--parkir-atas", atas + "px");
    if (map) map.setPadding({ top: atas, right: 0, bottom: 0, left: kiri });
  }

  function aturLegenda(buka: boolean, fokus: boolean) {
    keadaan.legenda = buka;
    isiLegenda.hidden = !buka;
    tombolLegenda.hidden = buka;
    tombolLegenda.setAttribute("aria-expanded", String(buka));
    legendaKotak.classList.toggle("is-buka", buka);
    if (fokus) (buka ? tutupLegenda : tombolLegenda).focus();
  }

  function labelLipat() {
    const teks = say(keadaan.ringkas ? TEXT.moreDetails : TEXT.lessDetails);
    lipat.setAttribute("aria-label", teks);
    lipat.title = teks;
  }

  function aturRingkas(ringkas: boolean) {
    keadaan.ringkas = ringkas;
    kartu.setAttribute("data-ringkas", ringkas ? "ya" : "tidak");
    atur.hidden = ringkas;
    lipat.setAttribute("aria-expanded", String(!ringkas));
    labelLipat();
  }

  function tandaiLapis() {
    (Object.keys(tombolLapis) as KunciLapis[]).forEach((kunci) => {
      tombolLapis[kunci].tombol.setAttribute("aria-pressed", String(keadaan.tampil[kunci]));
    });
  }

  tombolLegenda.addEventListener("click", () => {
    aturLegenda(true, true);
    simpanSetelan("legenda", true);
  });
  tutupLegenda.addEventListener("click", () => {
    aturLegenda(false, true);
    simpanSetelan("legenda", false);
  });
  isiLegenda.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    aturLegenda(false, true);
    simpanSetelan("legenda", false);
  });
  lipat.addEventListener("click", () => {
    aturRingkas(!keadaan.ringkas);
    simpanSetelan("ringkas", keadaan.ringkas);
  });

  function isiKendaraan() {
    const terpilih = keadaan.kendaraan;
    pilihKendaraan.replaceChildren();
    DAFTAR_KENDARAAN.forEach((nama) => {
      const opsi = el("option", "", say(KENDARAAN[nama]));
      opsi.value = nama;
      opsi.selected = nama === terpilih;
      pilihKendaraan.appendChild(opsi);
    });
  }

  pilihKendaraan.addEventListener("change", () => {
    keadaan.kendaraan = pilihKendaraan.value;
    tampilkan();
  });
  kurang.addEventListener("click", () => {
    keadaan.jam = Math.max(1, keadaan.jam - 1);
    tampilkan();
  });
  tambah.addEventListener("click", () => {
    keadaan.jam = Math.min(JAM_MAKS, keadaan.jam + 1);
    tampilkan();
  });

  function label() {
    isian.placeholder = say(TEXT.search);
    isian.setAttribute("aria-label", say(TEXT.search));
    hapusCari.setAttribute("aria-label", say(TEXT.clear));
    labelKendaraan.textContent = say(TEXT.vehicle);
    labelJam.textContent = say(TEXT.hours);
    kurang.setAttribute("aria-label", say(TEXT.less));
    tambah.setAttribute("aria-label", say(TEXT.more));
    bidangLayanan.setAttribute("aria-label", say(TEXT.service));
    (Object.keys(tombolLayanan) as Layanan[]).forEach((kunci) => {
      tombolLayanan[kunci].textContent = say(LAYANAN[kunci]);
    });
    teksLegenda.textContent = say(TEXT.legend);
    judulLegenda.textContent = say(TEXT.legendTitle);
    petunjukLegenda.textContent = say(TEXT.legendHint);
    tutupLegenda.setAttribute("aria-label", say(TEXT.legendHide));
    tutupLegenda.title = say(TEXT.legendHide);
    (Object.keys(tombolLapis) as KunciLapis[]).forEach((kunci) => {
      tombolLapis[kunci].nama.textContent = say(tombolLapis[kunci].teks);
    });
    catatanLegenda.textContent = say(TEXT.legendRest);
    labelTerdekat.textContent = say(TEXT.nearest);
    labelLipat();
    isiKendaraan();
  }

  function teksTarif(h: Tarif): string {
    if (h.progresif) {
      let teks = say(TEXT.firstTwo).replace("%a", rupiah(h.awal));
      if (h.jamLanjut) {
        teks += say(TEXT.thenHours).replace("%j", String(h.jamLanjut)).replace("%b", rupiah(h.lanjut ?? 0));
      }
      return teks;
    }
    if (keadaan.layanan === "pasar") return say(TEXT.market);
    return say(TEXT.once).replace("%k", keadaan.posisi?.kawasan ?? "");
  }

  let tundaKabar = 0;
  function umumkan(teks: string) {
    window.clearTimeout(tundaKabar);
    tundaKabar = window.setTimeout(() => {
      kabar.textContent = teks;
    }, 700);
  }

  let hargaKini: number | null = null;
  let hargaBingkai = 0;
  function pasangHarga(total: number) {
    window.cancelAnimationFrame(hargaBingkai);
    const angka = document.createTextNode("");
    harga.replaceChildren(el("span", "parkir__rp", "Rp"), angka);
    const dari = hargaKini;
    hargaKini = total;
    if (dari === null || dari === total || reducedMotion()) {
      angka.nodeValue = rupiah(total);
      return;
    }
    let awal: number | null = null;
    const mulaiDari = dari;
    function langkahHarga(waktu: number) {
      if (awal === null) awal = waktu;
      const k = Math.min(1, (waktu - awal) / 420);
      const mulus = 1 - Math.pow(1 - k, 3);
      angka.nodeValue = rupiah(k < 1 ? Math.round((mulaiDari + (total - mulaiDari) * mulus) / 100) * 100 : total);
      if (k < 1) hargaBingkai = window.requestAnimationFrame(langkahHarga);
    }
    hargaBingkai = window.requestAnimationFrame(langkahHarga);
  }

  function tampilTerdekat(p: Posisi) {
    const dekat = p.luar ? null : asetTerdekat(DATA, keadaan.titik[1], keadaan.titik[0]);
    if (!dekat || dekat.jarak > DEKAT_M) {
      terdekat.hidden = true;
      return;
    }
    const nama = DATA.titik[dekat.indeks].nama;
    const jarak = jarakTeks(dekat.jarak);
    terdekat.hidden = false;
    terdekat.setAttribute("data-indeks", String(dekat.indeks));
    namaTerdekat.textContent = nama;
    jarakTerdekat.textContent = jarak;
    terdekat.setAttribute("aria-label", say(TEXT.goThere).replace("%n", nama).replace("%d", jarak));
  }

  let kunciTampil: string | null = null;
  function tampilkan() {
    const w = WARNA[keadaan.gelap ? "gelap" : "terang"];
    const p = keadaan.posisi;
    nilaiJam.textContent = say(TEXT.hourUnit).replace("%j", String(keadaan.jam));
    kurang.disabled = keadaan.jam <= 1;
    tambah.disabled = keadaan.jam >= JAM_MAKS;
    (Object.keys(tombolLayanan) as Layanan[]).forEach((kunci) => {
      tombolLayanan[kunci].setAttribute("aria-pressed", String(kunci === keadaan.layanan));
    });
    if (!p) return;

    const kunci = p.luar ? "luar" : (p.ruas || "") + "|" + p.kawasan;
    if (kunciTampil !== null && kunci !== kunciTampil) kedip(ringkasan, "is-baru");
    kunciTampil = kunci;

    const h = hitungTarif(DATA, keadaan.kendaraan, p.kawasan, keadaan.jam, keadaan.layanan);
    kartu.setAttribute("data-kawasan", p.luar ? "luar" : String(p.kawasan));
    titikWarna.style.background = p.luar
      ? "transparent"
      : p.kawasan === "III"
        ? "var(--ink-3)"
        : w[p.kawasan as "I" | "II"];

    if (p.luar) {
      namaRuas.textContent = say(TEXT.outside);
      ketLokasi.textContent = say(TEXT.outsideNote);
    } else if (!p.ruas) {
      namaRuas.textContent = say(TEXT.zoneThree);
      ketLokasi.textContent = say(TEXT.zoneThreeNote);
    } else {
      namaRuas.textContent = p.ruas;
      ketLokasi.textContent =
        say(TEXT.zone).replace("%k", String(p.kawasan)) +
        " · " +
        say(TEXT.fromStreet).replace("%m", String(Math.round(p.jarak ?? 0)));
    }

    usulan.hidden = !p.usulan;
    usulan.textContent = p.usulan ? say(TEXT.proposal) : "";

    if (!h) {
      window.cancelAnimationFrame(hargaBingkai);
      hargaKini = null;
      harga.replaceChildren(el("span", "parkir__rp", "—"));
      subHarga.textContent = p.luar ? "" : say(TEXT.noFee);
    } else {
      pasangHarga(h.total);
      subHarga.textContent = teksTarif(h);
    }
    tampilTerdekat(p);
    umumkan(
      say(TEXT.announce)
        .replace("%r", namaRuas.textContent || "")
        .replace("%f", h ? "Rp" + rupiah(h.total) : say(TEXT.outside)),
    );
  }

  function terpilih() {
    const p = keadaan.posisi;
    if (!p || p.fitur === null) return { type: "FeatureCollection", features: [] };
    return { type: "FeatureCollection", features: [DATA.kawasan.features[p.fitur]] };
  }

  function posisiDari(lng: number, lat: number) {
    keadaan.titik = [lng, lat];
    keadaan.posisi = cariKawasan(DATA, lat, lng);
    const sumber = map?.getSource("parkir-terpilih") as { setData?: (d: unknown) => void } | undefined;
    sumber?.setData?.(terpilih());
    tampilkan();
  }

  function geojsonAset() {
    return {
      type: "FeatureCollection",
      features: DATA.titik.map((t, i) => ({
        type: "Feature",
        id: i,
        geometry: { type: "Point", coordinates: [t.lon, t.lat] },
        properties: { i },
      })),
    };
  }

  function gabung(gaya: GayaGabung): GayaGabung {
    const w = WARNA[keadaan.gelap ? "gelap" : "terang"];
    gaya.sources.parkir = { type: "geojson", data: DATA.kawasan };
    gaya.sources["parkir-terpilih"] = { type: "geojson", data: terpilih() };
    gaya.sources["parkir-aset"] = { type: "geojson", data: geojsonAset() };
    let sebelum = gaya.layers.findIndex((l) => l.type === "symbol");
    if (sebelum < 0) sebelum = gaya.layers.length;
    gaya.layers.splice(sebelum, 0, ...lapisanParkir(w, keadaan.tampil));
    return gaya;
  }

  function gayaBaru(): Promise<StyleSpecification> {
    if (TOKEN) {
      const dasar = mapboxStyle({
        gelap: keadaan.gelap, satelit: false, medan: false, tiga: false, lang: isId() ? "id" : "en",
      }) as unknown as GayaGabung;
      return Promise.resolve(gabung(dasar) as unknown as StyleSpecification);
    }
    const dasar = dasarCadangan
      ? Promise.resolve(dasarCadangan)
      : fetch(FALLBACK_STYLE)
          .then((r) => r.json())
          .then((json: GayaGabung) => {
            dasarCadangan = json;
            return json;
          });
    return dasar.then((json) => gabung(JSON.parse(JSON.stringify(json))) as unknown as StyleSpecification);
  }

  function terapkan() {
    if (!map) return;
    const peta = map;
    void gayaBaru().then((gaya) => {
      if (!dihapus) peta.setStyle(gaya, { diff: true });
    });
  }

  function terjemahkanKontrol() {
    ([
      [".maplibregl-ctrl-zoom-in", TEXT.zoomIn],
      [".maplibregl-ctrl-zoom-out", TEXT.zoomOut],
      [".maplibregl-ctrl-compass", TEXT.north],
    ] as [string, Teks][]).forEach(([pilih, teks]) => {
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

  function terbangKe(titik: [number, number], zoom: number, durasi: number) {
    if (!map) {
      posisiDari(titik[0], titik[1]);
      return;
    }
    map.flyTo({ center: titik, zoom: Math.max(map.getZoom(), zoom), duration: reducedMotion() ? 0 : durasi });
  }

  terdekat.addEventListener("click", () => {
    const t = DATA.titik[Number(terdekat.getAttribute("data-indeks"))];
    if (!t) return;
    if (!keadaan.tampil.aset) {
      keadaan.tampil.aset = true;
      tandaiLapis();
      terapkan();
    }
    terbangKe([t.lon, t.lat], 17, 1200);
  });

  let aktif = -1;
  let hasil: Ruas[] = [];

  function tutupSaran() {
    saran.hidden = true;
    isian.setAttribute("aria-expanded", "false");
    isian.removeAttribute("aria-activedescendant");
    aktif = -1;
  }

  function tandai() {
    Array.from(saran.children).forEach((li, i) => {
      const ya = i === aktif;
      li.setAttribute("aria-selected", String(ya));
      li.classList.toggle("is-aktif", ya);
      if (ya) isian.setAttribute("aria-activedescendant", li.id);
    });
  }

  function pilih(ruas: Ruas) {
    isian.value = ruas.nama;
    hapusCari.hidden = false;
    tutupSaran();
    isian.blur();
    if (map) map.flyTo({ center: ruas.titik, zoom: 17, duration: reducedMotion() ? 0 : 1400 });
    else posisiDari(ruas.titik[0], ruas.titik[1]);
  }

  function isiSaran() {
    const q = polos(isian.value.trim());
    hapusCari.hidden = !isian.value;
    saran.replaceChildren();
    if (!q) {
      tutupSaran();
      return;
    }
    hasil = DAFTAR_RUAS.filter((r) => polos(r.nama).indexOf(q) !== -1).slice(0, 8);
    if (!hasil.length) {
      const kosong = el("li", "parkir__saran-kosong", say(TEXT.noMatch).replace("%q", isian.value.trim()));
      kosong.setAttribute("role", "presentation");
      saran.appendChild(kosong);
    }
    hasil.forEach((ruas, i) => {
      const li = el("li", "parkir__opsi", ruas.nama);
      li.id = "parkir-saran-" + i;
      li.setAttribute("role", "option");
      li.addEventListener("mousedown", (e) => e.preventDefault());
      li.addEventListener("click", () => pilih(ruas));
      saran.appendChild(li);
    });
    aktif = hasil.length ? 0 : -1;
    saran.hidden = false;
    isian.setAttribute("aria-expanded", "true");
    tandai();
  }

  isian.addEventListener("input", isiSaran);
  isian.addEventListener("blur", () => window.setTimeout(tutupSaran, 120));
  isian.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!hasil.length) return;
      aktif = (aktif + (e.key === "ArrowDown" ? 1 : -1) + hasil.length) % hasil.length;
      tandai();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (hasil[aktif]) pilih(hasil[aktif]);
    } else if (e.key === "Escape") {
      tutupSaran();
    }
  });
  hapusCari.addEventListener("click", () => {
    isian.value = "";
    hapusCari.hidden = true;
    tutupSaran();
    isian.focus();
  });

  label();
  tandaiLapis();
  aturLegenda(keadaan.legenda, false);
  aturRingkas(keadaan.ringkas);
  aturLetak();
  posisiDari(PUSAT[0], PUSAT[1]);
  const pengamat = new ResizeObserver(aturLetak);
  pengamat.observe(bungkus);

  let jaring = 0;

  function pasangPetunjuk(peta: MapLibreMap) {
    const tip = new maplibregl.Popup({
      closeButton: false, closeOnClick: false, className: "parkir__tip", offset: 12, maxWidth: "240px",
    });
    let tipKunci = "";
    const tunjuk = (e: MapLayerMouseEvent) => {
      const f = e.features && e.features[0];
      if (!f || peta.isMoving()) return;
      const p = f.properties as { n: string; k: string; u: number };
      const kunci = p.n + "|" + p.k + "|" + p.u;
      if (kunci !== tipKunci) {
        tipKunci = kunci;
        const isi = el("div", "parkir__tip-isi");
        isi.appendChild(el("strong", "", p.n));
        isi.appendChild(el("span", "", Number(p.u) === 1 ? say(TEXT.legendProposal) : say(TEXT.zone).replace("%k", p.k)));
        tip.setDOMContent(isi);
      }
      tip.setLngLat(e.lngLat);
      if (!tip.isOpen()) tip.addTo(peta);
      peta.getCanvas().style.cursor = "pointer";
    };
    const lepas = () => {
      tip.remove();
      tipKunci = "";
      peta.getCanvas().style.cursor = "";
    };
    ["parkir-tetap", "parkir-usulan"].forEach((id) => {
      peta.on("mousemove", id, tunjuk);
      peta.on("mouseleave", id, lepas);
    });
    peta.on("movestart", lepas);
  }

  function mulai(gaya: StyleSpecification) {
    if (dihapus) return;
    const peta = new maplibregl.Map({
      container,
      style: gaya,
      center: PUSAT,
      zoom: 15.5,
      minZoom: 11,
      maxZoom: 19,
      maxBounds: BATAS,
      maxPitch: 0,
      attributionControl: false,
      cooperativeGestures: sentuh(),
      scrollZoom: sentuh(),
    });
    map = peta;
    peta.dragRotate.disable();
    peta.touchZoomRotate.disableRotation();
    peta.on("styleimagemissing", (e: { id?: string }) => {
      if (e && e.id && e.id.indexOf("hk-poi-") === 0) tambahIkon(peta, e.id);
    });
    peta.addControl(new maplibregl.FullscreenControl({ container: bungkus }), "top-right");
    peta.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    peta.addControl(new maplibregl.ScaleControl({ maxWidth: 96, unit: "metric" }), "bottom-right");
    peta.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    aturLetak();

    let sudahSiap = false;
    const siap = () => {
      if (sudahSiap || dihapus) return;
      sudahSiap = true;
      peta.resize();
      frame.classList.add("is-ready");
      terjemahkanKontrol();
      const c = peta.getCenter();
      posisiDari(c.lng, c.lat);
    };
    peta.on("load", siap);
    peta.on("styledata", siap);
    peta.on("idle", siap);
    jaring = window.setTimeout(siap, 4000);

    peta.on("movestart", () => pin.classList.add("is-geser"));
    peta.on("moveend", () => {
      pin.classList.remove("is-geser");
      kedip(pin, "is-mendarat");
      const c = peta.getCenter();
      posisiDari(c.lng, c.lat);
    });

    peta.on("click", (e) => {
      if (peta.getLayer("parkir-aset") && peta.queryRenderedFeatures(e.point, { layers: ["parkir-aset"] }).length) return;
      peta.easeTo({ center: e.lngLat, duration: reducedMotion() ? 0 : 650 });
    });

    peta.on("click", "parkir-aset", (e: MapLayerMouseEvent) => {
      const f = e.features && e.features[0];
      if (!f) return;
      const t = DATA.titik[Number((f.properties as { i: number }).i)];
      const isi = el("div", "parkir__popup");
      isi.appendChild(el("strong", "", t.nama));
      isi.appendChild(el("span", "", t.jenis + (t.jam ? " · " + t.jam : "")));
      if (t.srp_roda2) isi.appendChild(el("span", "", say(TEXT.spaces).replace("%n", rupiah(t.srp_roda2))));
      isi.appendChild(el("small", "", say(TEXT.assetNote)));
      new maplibregl.Popup({ className: "parkir__popup-bungkus", maxWidth: "260px" })
        .setLngLat(e.lngLat)
        .setDOMContent(isi)
        .addTo(peta);
    });
    peta.on("mouseenter", "parkir-aset", () => {
      peta.getCanvas().style.cursor = "pointer";
    });
    peta.on("mouseleave", "parkir-aset", () => {
      peta.getCanvas().style.cursor = "";
    });

    if (!sentuh()) {
      pasangPetunjuk(peta);
      container.addEventListener(
        "wheel",
        (event) => {
          if (event.ctrlKey || event.metaKey) peta.scrollZoom.enable();
          else peta.scrollZoom.disable();
        },
        { capture: true, passive: true },
      );
    }

    (window as Window & { HK_PARKIR_MAP?: MapLibreMap }).HK_PARKIR_MAP = peta;
  }

  gayaBaru()
    .then(mulai)
    .catch(() => section.classList.add("is-failed"));

  const tema = new MutationObserver(() => {
    const gelap = temaGelap();
    if (gelap === keadaan.gelap) return;
    keadaan.gelap = gelap;
    tampilkan();
    terapkan();
  });
  tema.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  const layarBerubah = () => window.setTimeout(terjemahkanKontrol, 0);
  document.addEventListener("fullscreenchange", layarBerubah);

  function gantiBahasa() {
    label();
    tampilkan();
    terjemahkanKontrol();
    terapkan();
  }

  function hapus() {
    dihapus = true;
    window.clearTimeout(jaring);
    window.clearTimeout(tundaKabar);
    window.cancelAnimationFrame(hargaBingkai);
    pengamat.disconnect();
    tema.disconnect();
    document.removeEventListener("fullscreenchange", layarBerubah);
    samping.remove();
    pin.remove();
    legendaKotak.remove();
    kabar.remove();
    frame.classList.remove("is-ready");
    map?.remove();
    map = null;
  }

  return { peta: () => map, gantiBahasa, hapus };
}
