/**
 * Satu pintu ke API, dipakai seluruh halaman admin.
 *
 * Access token disimpan di variabel modul, **bukan** di localStorage. Token di
 * localStorage bisa diambil satu XSS dan tetap berlaku sesudah tabnya ditutup;
 * yang di memori ikut hilang begitu tab ditutup, dan itu justru yang
 * diinginkan. Yang bertahan antar kunjungan adalah cookie refresh yang
 * HttpOnly, yang tidak bisa dibaca JavaScript sama sekali.
 *
 * Access token berumur 15 menit. Kalau ia mati di tengah orang mengetik,
 * `panggil` memperpanjangnya sekali lalu mengulang permintaannya, sehingga
 * tulisannya tidak hilang hanya karena waktunya habis.
 */

/** Kosong berarti asal yang sama dengan halamannya. Diisi hanya kalau API-nya
 *  memang duduk di host lain, dan kalau begitu asalnya wajib ikut disebut di
 *  ASAL_DIIZINKAN pada sisi server. */
export const DASAR_KOSONG = process.env.NEXT_PUBLIC_API ?? "";
const DASAR = DASAR_KOSONG;

let AKSES: string | null = null;

export type Sesi = {
  akses: string;
  umur_detik: number;
  nama: string;
  peran: string;
};

/**
 * Jawaban masuk punya dua bentuk, dan `tahap` yang membedakannya.
 *
 * "selesai" berarti sesinya terbit. "faktor2" berarti sandinya benar dan
 * belum cukup: yang terbit tiket berumur lima menit, bukan sesi, dan `cara`
 * menyebut faktor kedua apa saja yang bisa dipakai.
 */
export type JawabanMasuk = Sesi & {
  tahap: "selesai" | "faktor2";
  tiket: string;
  cara: CaraFaktorKedua[];
};

export type CaraFaktorKedua = "totp" | "email" | "pemulihan" | "wajah";

export type KeadaanKeamanan = {
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

export function simpanAkses(nilai: string | null): void {
  AKSES = nilai;
}

export function adaAkses(): boolean {
  return AKSES !== null;
}

export class GagalApi extends Error {
  readonly status: number;

  constructor(pesan: string, status: number) {
    super(pesan);
    this.name = "GagalApi";
    this.status = status;
  }
}

/** FastAPI menjawab galat dalam tiga bentuk. Ketiganya diringkas jadi satu
 *  kalimat yang bisa dibaca manusia, bukan dilempar apa adanya ke layar. */
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

/** Memanggil lalu membaca JSON-nya, dan melempar kalau gagal. Dipakai di
 *  tempat yang memang tidak punya rencana lain selain menampilkan galatnya. */
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
  // Token hanya disimpan kalau sesinya memang sudah terbit. Tiket faktor
  // kedua TIDAK pernah masuk ke sini: ia bukan kunci, dan menaruhnya di
  // tempat kunci adalah cara paling mudah membuatnya diperlakukan sebagai
  // kunci oleh kode berikutnya.
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

// ----------------------------------------------------------- keamanan ---

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

/** Dipanggil sekali saat halaman dibuka. Kalau cookie refresh masih hidup,
 *  orangnya langsung masuk tanpa ditanya sandi lagi. */
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
