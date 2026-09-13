/**
 * Passkey di sisi peramban.
 *
 * WebAuthn mengirim dan menerima ArrayBuffer, JSON hanya mengenal teks, jadi
 * base64url adalah jembatannya. Dua fungsi konversi di bawah adalah bagian
 * yang paling sering ditulis salah di contoh contoh yang beredar: padding "="
 * harus dikembalikan sebelum atob, dan dibuang lagi sesudah btoa.
 *
 * Tidak ada satu pun keputusan keamanan di berkas ini. Tantangan lahir di
 * server, diverifikasi di server, dan apa pun yang dikirim dari sini
 * diperlakukan server sebagai tidak dipercaya.
 */

import { DASAR_KOSONG, panggil, pesanGalat, type Sesi } from "./api";

export function keBuffer(teks: string): ArrayBuffer {
  const dasar = teks.replace(/-/g, "+").replace(/_/g, "/");
  const penuh = dasar + "===".slice((dasar.length + 3) % 4);
  const biner = atob(penuh);
  const bita = new Uint8Array(biner.length);
  for (let i = 0; i < biner.length; i += 1) bita[i] = biner.charCodeAt(i);
  return bita.buffer;
}

export function keTeks(buffer: ArrayBuffer): string {
  let biner = "";
  for (const b of new Uint8Array(buffer)) biner += String.fromCharCode(b);
  return btoa(biner).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function didukung(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.PublicKeyCredential === "function" &&
    typeof navigator.credentials?.create === "function"
  );
}

/** Dibatalkan pengguna bukan kegagalan. Menampilkannya sebagai galat merah
 *  hanya membuat orang mengira ada yang rusak. */
export function dibatalkan(galat: unknown): boolean {
  const nama = (galat as { name?: string })?.name;
  return nama === "NotAllowedError" || nama === "AbortError";
}

export type Kunci = {
  id: string;
  nama: string;
  jenis_perangkat: string;
  tercadang: boolean;
  transportasi: string[];
  dibuat_pada: string;
  dipakai_pada: string | null;
};

export async function siap(): Promise<boolean> {
  if (!didukung()) return false;
  try {
    const jawaban = await fetch(`${DASAR_KOSONG}/api/v1/auth/passkey/siap`);
    if (!jawaban.ok) return false;
    return Boolean(((await jawaban.json()) as { siap?: boolean }).siap);
  } catch {
    return false;
  }
}

export async function masuk(): Promise<Sesi> {
  const mulai = await fetch(`${DASAR_KOSONG}/api/v1/auth/passkey/masuk/mulai`, {
    method: "POST",
  });
  const awal = await mulai.json().catch(() => null);
  if (!mulai.ok) throw new Error(pesanGalat(awal));

  const pilihan = JSON.parse((awal as { pilihan: string }).pilihan);
  pilihan.challenge = keBuffer(pilihan.challenge);
  for (const k of pilihan.allowCredentials ?? []) k.id = keBuffer(k.id);

  const kredensial = (await navigator.credentials.get({
    publicKey: pilihan,
  })) as PublicKeyCredential;
  const jawab = kredensial.response as AuthenticatorAssertionResponse;

  const selesai = await fetch(`${DASAR_KOSONG}/api/v1/auth/passkey/masuk/selesai`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jawaban: {
        id: kredensial.id,
        rawId: keTeks(kredensial.rawId),
        type: kredensial.type,
        response: {
          clientDataJSON: keTeks(jawab.clientDataJSON),
          authenticatorData: keTeks(jawab.authenticatorData),
          signature: keTeks(jawab.signature),
          userHandle: jawab.userHandle ? keTeks(jawab.userHandle) : null,
        },
        clientExtensionResults: kredensial.getClientExtensionResults(),
      },
    }),
  });

  const isi = await selesai.json().catch(() => null);
  if (!selesai.ok) throw new Error(pesanGalat(isi));
  return isi as Sesi;
}

/**
 * `jenis` menentukan authenticator mana yang diminta.
 *
 * "perangkat" berarti sensor yang menempel pada perangkatnya sendiri: sidik
 * jari di ponsel, Touch ID, Windows Hello. Itu yang orang maksud dengan
 * "masuk pakai sidik jari". "kunci" berarti kunci fisik yang dicolokkan.
 *
 * Yang perlu diluruskan: sidik jarinya tidak pernah sampai ke server ini, dan
 * tidak akan pernah. Perangkatnya yang memeriksa, lalu menandatangani dengan
 * kunci privat yang tidak pernah keluar dari sana. Yang diterima server cuma
 * tanda tangan dan satu bendera bahwa pemiliknya sudah diperiksa. Itu justru
 * lebih kuat daripada mengirim sidik jari: tidak ada biometrik yang disimpan
 * di sini, jadi tidak ada yang bisa bocor dari sini, dan sidik jari yang bocor
 * tidak bisa diganti seperti kata sandi.
 */
export async function daftarkan(nama: string, jenis: "perangkat" | "kunci" = "perangkat"): Promise<void> {
  const mulai = await panggil(
    `/api/v1/auth/passkey/daftar/mulai?jenis=${encodeURIComponent(jenis)}`,
    { method: "POST" },
  );
  const awal = await mulai.json().catch(() => null);
  if (!mulai.ok) throw new Error(pesanGalat(awal));

  const pilihan = JSON.parse((awal as { pilihan: string }).pilihan);
  pilihan.challenge = keBuffer(pilihan.challenge);
  pilihan.user.id = keBuffer(pilihan.user.id);
  for (const k of pilihan.excludeCredentials ?? []) k.id = keBuffer(k.id);

  const kredensial = (await navigator.credentials.create({
    publicKey: pilihan,
  })) as PublicKeyCredential;
  const jawab = kredensial.response as AuthenticatorAttestationResponse;

  const selesai = await panggil("/api/v1/auth/passkey/daftar/selesai", {
    method: "POST",
    body: JSON.stringify({
      nama,
      jawaban: {
        id: kredensial.id,
        rawId: keTeks(kredensial.rawId),
        type: kredensial.type,
        response: {
          clientDataJSON: keTeks(jawab.clientDataJSON),
          attestationObject: keTeks(jawab.attestationObject),
          transports: jawab.getTransports ? jawab.getTransports() : [],
        },
        clientExtensionResults: kredensial.getClientExtensionResults(),
      },
    }),
  });

  if (!selesai.ok) throw new Error(pesanGalat(await selesai.json().catch(() => null)));
}
