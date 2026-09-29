export const DASAR_KOSONG = process.env.NEXT_PUBLIC_API ?? "";
const DASAR = DASAR_KOSONG;

let AKSES: string | null = null;

export type Sesi = {
  akses: string;
  umur_detik: number;
  nama: string;
  peran: string;
};

type JawabanMasuk = Sesi & {
  tahap: "selesai" | "faktor2";
  tiket: string;
  cara: CaraFaktorKedua[];
};

export type CaraFaktorKedua = "totp" | "email" | "pemulihan" | "wajah";

export type KeadaanKeamanan = {
  faktor_kedua_wajib: boolean;
  sesi_kuat: boolean;
  pencabutan_segera_siap: boolean;
  email: string;
  email_terverifikasi: boolean;
  email_terverifikasi_pada: string | null;
  totp_terpasang: boolean;
  totp_aktif: boolean;
  punya_sandi: boolean;
  passkey: number;
  pemulihan_sisa: number;
  wajah_terdaftar: boolean;
  surat_siap: boolean;
  kunci_kolom_siap: boolean;
  wajah_siap: boolean;
  kabar_masuk: boolean;
  kabar_perubahan: boolean;
  mode_ketat: boolean;
};

export type Setelan = Pick<KeadaanKeamanan, "kabar_masuk" | "kabar_perubahan" | "mode_ketat">;

export type SesiPerangkat = {
  id: string;
  dibuat_pada: string;
  kadaluarsa: string;
  perangkat_ini: boolean;
};

export type TantanganWajah = {
  tantangan: string;
  gerakan: string[];
  umur_detik: number;
};

export type Peristiwa = {
  jenis: string;
  berhasil: boolean;
  keterangan: string | null;
  alamat_ringkas: string | null;
  peramban: string | null;
  pada: string;
};

export class GagalApi extends Error {
  readonly status: number;

  constructor(pesan: string, status: number) {
    super(pesan);
    this.name = "GagalApi";
    this.status = status;
  }
}

export function pesanGalat(isi: unknown): string {
  if (!isi || typeof isi !== "object") return "gagal";
  const detail = (isi as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => {
        const tempat = Array.isArray(d.loc) ? d.loc.slice(1).join(".") : "";
        return tempat ? `${tempat}: ${d.msg ?? ""}` : (d.msg ?? "");
      })
      .join("\n");
  }
  const galat = (isi as { galat?: unknown }).galat;
  if (typeof galat === "string") return galat;
  return "gagal";
}

export function pesanDari(galat: unknown, cadangan = "Gagal menghubungi server. Coba lagi."): string {
  return galat instanceof Error && galat.message ? galat.message : cadangan;
}

async function sekaliJalan(jalur: string, pilihan: RequestInit): Promise<Response> {
  const kepala: Record<string, string> = {
    "Content-Type": "application/json",
    ...((pilihan.headers as Record<string, string> | undefined) ?? {}),
  };
  if (AKSES) kepala.Authorization = `Bearer ${AKSES}`;

  return fetch(`${DASAR}${jalur}`, {
    ...pilihan,
    headers: kepala,
    credentials: "same-origin",
  });
}

export async function panggil(jalur: string, pilihan: RequestInit = {}): Promise<Response> {
  let jawaban = await sekaliJalan(jalur, pilihan);

  if (jawaban.status === 401 && AKSES) {
    const putar = await fetch(`${DASAR}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (putar.ok) {
      AKSES = ((await putar.json()) as Sesi).akses;
      jawaban = await sekaliJalan(jalur, pilihan);
    }
  }
  return jawaban;
}

export async function ambil<T>(jalur: string, pilihan: RequestInit = {}): Promise<T> {
  const jawaban = await panggil(jalur, pilihan);
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GagalApi(pesanGalat(isi), jawaban.status);
  return isi as T;
}

export async function masukSandi(email: string, sandi: string): Promise<JawabanMasuk> {
  const jawaban = await fetch(`${DASAR}/api/v1/auth/login`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, sandi }),
  });
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GagalApi(pesanGalat(isi), jawaban.status);
  const hasil = isi as JawabanMasuk;
  if (hasil.tahap === "selesai") AKSES = hasil.akses;
  return hasil;
}

export async function selesaikanFaktorKedua(
  tiket: string,
  cara: CaraFaktorKedua,
  kode: string,
  wajah?: { tantangan: string; bingkai: string[] },
): Promise<Sesi> {
  const jawaban = await fetch(`${DASAR}/api/v1/auth/faktor-kedua`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tiket, cara, kode, ...(wajah ?? {}) }),
  });
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GagalApi(pesanGalat(isi), jawaban.status);
  AKSES = (isi as Sesi).akses;
  return isi as Sesi;
}

export async function kirimUlangKode(tiket: string): Promise<{ terkirim: boolean; catatan: string }> {
  const jawaban = await fetch(`${DASAR}/api/v1/auth/faktor-kedua/kirim-ulang`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tiket }),
  });
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GagalApi(pesanGalat(isi), jawaban.status);
  return isi as { terkirim: boolean; catatan: string };
}


export function keadaanKeamanan(): Promise<KeadaanKeamanan> {
  return ambil<KeadaanKeamanan>("/api/v1/keamanan");
}

export function kirimVerifikasiEmail(): Promise<{ terkirim: boolean; catatan: string }> {
  return ambil("/api/v1/keamanan/email/kirim", { method: "POST" });
}

export function konfirmasiEmail(token: string): Promise<{ terverifikasi: boolean }> {
  return ambil("/api/v1/keamanan/email/konfirmasi", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function mulaiTotp(): Promise<{ rahasia: string; otpauth: string }> {
  return ambil("/api/v1/keamanan/totp/mulai", { method: "POST" });
}

export function aktifkanTotp(kode: string): Promise<{ kode_pemulihan: string[]; catatan: string }> {
  return ambil("/api/v1/keamanan/totp/aktifkan", {
    method: "POST",
    body: JSON.stringify({ kode }),
  });
}

export function matikanTotp(kode: string): Promise<{ aktif: boolean }> {
  return ambil("/api/v1/keamanan/totp/matikan", {
    method: "POST",
    body: JSON.stringify({ kode }),
  });
}

export async function tantanganWajah(tiket: string): Promise<TantanganWajah> {
  const jawaban = await fetch(`${DASAR}/api/v1/auth/faktor-kedua/tantangan-wajah`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tiket }),
  });
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new GagalApi(pesanGalat(isi), jawaban.status);
  return isi as TantanganWajah;
}

export function daftarkanWajah(bingkai: string[]): Promise<{ terdaftar: boolean }> {
  return ambil("/api/v1/keamanan/wajah/daftar", {
    method: "POST",
    body: JSON.stringify({ bingkai }),
  });
}

export function hapusWajah(): Promise<{ terdaftar: boolean }> {
  return ambil("/api/v1/keamanan/wajah/hapus", { method: "POST" });
}

export function peristiwaKeamanan(): Promise<{ peristiwa: Peristiwa[] }> {
  return ambil("/api/v1/keamanan/peristiwa");
}

export function ubahSetelan(perubahan: Partial<Setelan>): Promise<Setelan> {
  return ambil("/api/v1/keamanan/setelan", {
    method: "PATCH",
    body: JSON.stringify(perubahan),
  });
}

export function daftarSesi(): Promise<{ sesi: SesiPerangkat[] }> {
  return ambil("/api/v1/auth/sesi");
}

export function keluarkanPerangkatLain(): Promise<{ sesi_dicabut: number }> {
  return ambil("/api/v1/auth/sesi/cabut-lain", { method: "POST" });
}


export type Berkas = {
  id: string;
  nama: string;
  nama_asal: string;
  jenis: "gambar" | "video";
  tipe_mime: string;
  bita: number;
  lebar: number | null;
  tinggi: number | null;
  dibuat_pada: string;
  alamat: string;
  markah: string;
};

type BerkasBaru = Berkas & { sudah_ada: boolean };

export function daftarBerkas(): Promise<{ jumlah: number; isi: Berkas[] }> {
  return ambil("/api/v1/admin/berkas");
}

export async function hapusBerkas(nama: string): Promise<void> {
  const jawaban = await panggil(`/api/v1/admin/berkas/${encodeURIComponent(nama)}`, {
    method: "DELETE",
  });
  if (!jawaban.ok) {
    throw new GagalApi(pesanGalat(await jawaban.json().catch(() => null)), jawaban.status);
  }
}

function sekaliUnggah(
  berkas: File,
  kemajuan?: (persen: number) => void,
  buangMetadata = false,
): Promise<{ status: number; isi: unknown }> {
  return new Promise((selesai, gagal) => {
    const bentuk = new FormData();
    bentuk.append("berkas", berkas, berkas.name);
    bentuk.append("buang_metadata", buangMetadata ? "true" : "false");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${DASAR}/api/v1/admin/berkas`);
    xhr.withCredentials = true;
    if (AKSES) xhr.setRequestHeader("Authorization", `Bearer ${AKSES}`);

    if (kemajuan) {
      xhr.upload.onprogress = (p) => {
        if (p.lengthComputable) kemajuan(Math.round((p.loaded / p.total) * 100));
      };
    }
    xhr.onload = () => {
      let isi: unknown = null;
      try {
        isi = JSON.parse(xhr.responseText);
      } catch {
        isi = null;
      }
      selesai({ status: xhr.status, isi });
    };
    xhr.onerror = () => gagal(new GagalApi("sambungan terputus saat mengunggah", 0));
    xhr.onabort = () => gagal(new GagalApi("unggahan dibatalkan", 0));
    xhr.send(bentuk);
  });
}

export async function unggahBerkas(
  berkas: File,
  kemajuan?: (persen: number) => void,
  buangMetadata = false,
): Promise<BerkasBaru> {
  let hasil = await sekaliUnggah(berkas, kemajuan, buangMetadata);

  if (hasil.status === 401 && AKSES) {
    const putar = await fetch(`${DASAR}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (putar.ok) {
      AKSES = ((await putar.json()) as Sesi).akses;
      hasil = await sekaliUnggah(berkas, kemajuan, buangMetadata);
    }
  }

  if (hasil.status < 200 || hasil.status >= 300) {
    throw new GagalApi(pesanGalat(hasil.isi), hasil.status);
  }
  return hasil.isi as BerkasBaru;
}


export type Pratinjau = {
  html: string;
  kata_en: number;
  kata_id: number;
  blok: number;
};

export function pratinjauTulisan(isi_en: string, isi_id: string): Promise<Pratinjau> {
  return ambil("/api/v1/admin/pratinjau", {
    method: "POST",
    body: JSON.stringify({ isi_en, isi_id }),
  });
}

export async function sesiYangMasihHidup(): Promise<Sesi | null> {
  const putar = await fetch(`${DASAR}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "same-origin",
  });
  if (!putar.ok) return null;
  const isi = (await putar.json()) as Sesi;
  AKSES = isi.akses;
  return isi;
}

export async function keluar(): Promise<void> {
  await panggil("/api/v1/auth/logout", { method: "POST" });
  AKSES = null;
}
