export type Kawasan = "I" | "II" | "III";
export type Layanan = "reguler" | "insidental" | "pasar";
export type Titik = [number, number];

export type FiturKawasan = {
  type: "Feature";
  properties: { n: string; k: "I" | "II"; u: number };
  geometry: { type: "LineString"; coordinates: Titik[] };
};

export type BarisTarif = {
  layanan: string;
  kendaraan: string;
  kawasan: string;
  tarif_2jam_pertama: number;
  tarif_per_jam_lanjut: number | null;
  progresif: boolean;
};

export type TitikAset = {
  nama: string;
  jenis: string;
  srp_roda2: number | null;
  jam: string | null;
  lat: number;
  lon: number;
};

export type DataParkir = {
  kawasan: { type: "FeatureCollection"; features: FiturKawasan[] };
  tarif: BarisTarif[];
  titik: TitikAset[];
  cakupan: { type: "Feature"; geometry: { type: "Polygon"; coordinates: Titik[][] } };
};

export type Posisi = {
  kawasan: Kawasan | null;
  ruas: string | null;
  jarak: number | null;
  usulan: boolean;
  luar: boolean;
  fitur: number | null;
};

export type Tarif = {
  total: number;
  progresif: boolean;
  jamLanjut: number;
  awal: number;
  lanjut: number | null;
};

const AMBANG_M = 30;

function meterPerDerajat(lat: number) {
  return { x: 111320 * Math.cos((lat * Math.PI) / 180), y: 110540 };
}

function jarakKeSegmen(p: Titik, a: Titik, b: Titik, m: { x: number; y: number }): number {
  const px = (p[0] - a[0]) * m.x;
  const py = (p[1] - a[1]) * m.y;
  const bx = (b[0] - a[0]) * m.x;
  const by = (b[1] - a[1]) * m.y;
  const kuadrat = bx * bx + by * by;
  const t = kuadrat === 0 ? 0 : Math.max(0, Math.min(1, (px * bx + py * by) / kuadrat));
  return Math.hypot(px - t * bx, py - t * by);
}

function diDalamCincin(x: number, y: number, cincin: Titik[]): boolean {
  let dalam = false;
  for (let i = 0, j = cincin.length - 1; i < cincin.length; j = i++) {
    const [x1, y1] = cincin[j];
    const [x2, y2] = cincin[i];
    if (y1 > y !== y2 > y && x < x1 + ((y - y1) * (x2 - x1)) / (y2 - y1)) dalam = !dalam;
  }
  return dalam;
}

function diDalamCakupan(data: DataParkir, lat: number, lon: number): boolean {
  const cincin = data.cakupan.geometry.coordinates;
  if (!diDalamCincin(lon, lat, cincin[0])) return false;
  for (let i = 1; i < cincin.length; i++) {
    if (diDalamCincin(lon, lat, cincin[i])) return false;
  }
  return true;
}

export function cariKawasan(data: DataParkir, lat: number, lon: number): Posisi {
  if (!diDalamCakupan(data, lat, lon)) {
    return { kawasan: null, ruas: null, jarak: null, usulan: false, luar: true, fitur: null };
  }
  const m = meterPerDerajat(lat);
  let terbaik = { jarak: Infinity, fitur: -1 };
  data.kawasan.features.forEach((fitur, indeks) => {
    const c = fitur.geometry.coordinates;
    for (let i = 0; i < c.length - 1; i++) {
      const d = jarakKeSegmen([lon, lat], c[i], c[i + 1], m);
      if (d < terbaik.jarak) terbaik = { jarak: d, fitur: indeks };
    }
  });
  if (terbaik.jarak > AMBANG_M) {
    return { kawasan: "III", ruas: null, jarak: null, usulan: false, luar: false, fitur: null };
  }
  const p = data.kawasan.features[terbaik.fitur].properties;
  return {
    kawasan: p.k,
    ruas: p.n,
    jarak: Math.round(terbaik.jarak * 10) / 10,
    usulan: p.u === 1,
    luar: false,
    fitur: terbaik.fitur,
  };
}

function cariTarif(data: DataParkir, kendaraan: string, kawasan: string, layanan: string): BarisTarif | null {
  const kw = layanan === "pasar" ? "-" : kawasan;
  return (
    data.tarif.find((t) => t.layanan === layanan && t.kendaraan === kendaraan && t.kawasan === kw) ?? null
  );
}

export function hitungTarif(
  data: DataParkir,
  kendaraan: string,
  kawasan: string | null,
  jam: number,
  layanan: string,
): Tarif | null {
  if (!kawasan) return null;
  const baris = cariTarif(data, kendaraan, kawasan, layanan);
  if (!baris) return null;
  const awal = baris.tarif_2jam_pertama;
  const lanjut = baris.tarif_per_jam_lanjut;
  if (!baris.progresif || lanjut === null) {
    return { total: awal, progresif: false, jamLanjut: 0, awal, lanjut: null };
  }
  const jamLanjut = Math.max(Math.ceil(jam) - 2, 0);
  return { total: awal + jamLanjut * lanjut, progresif: true, jamLanjut, awal, lanjut };
}

export function asetTerdekat(data: DataParkir, lat: number, lon: number): { indeks: number; jarak: number } | null {
  const m = meterPerDerajat(lat);
  let terbaik: { indeks: number; jarak: number } | null = null;
  data.titik.forEach((t, indeks) => {
    const jarak = Math.hypot((t.lon - lon) * m.x, (t.lat - lat) * m.y);
    if (!terbaik || jarak < terbaik.jarak) terbaik = { indeks, jarak };
  });
  return terbaik;
}

export type Ruas = { nama: string; panjang: number; titik: Titik };

export function daftarRuas(data: DataParkir): Ruas[] {
  const per: Record<string, Ruas> = {};
  data.kawasan.features.forEach((fitur) => {
    const nama = fitur.properties.n;
    const c = fitur.geometry.coordinates;
    let panjang = 0;
    for (let i = 0; i < c.length - 1; i++) panjang += Math.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]);
    if (!per[nama] || panjang > per[nama].panjang) {
      const tengah = c[Math.floor((c.length - 1) / 2)];
      const berikut = c[Math.min(c.length - 1, Math.floor((c.length - 1) / 2) + 1)];
      per[nama] = { nama, panjang, titik: [(tengah[0] + berikut[0]) / 2, (tengah[1] + berikut[1]) / 2] };
    }
  });
  return Object.keys(per)
    .sort()
    .map((nama) => per[nama]);
}
