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

export function dibatalkan(galat: unknown): boolean {
  const nama = (galat as { name?: string })?.name;
  return nama === "NotAllowedError" || nama === "AbortError";
}

export type Kendala = { sebab: "alamat-ip" | "tanpa-https"; pesan: string; saran: string };

export function kendala(): Kendala | null {
  if (typeof window === "undefined") return null;

  const host = window.location.hostname;
  const ipv4 = /^\d{1,3}(\.\d{1,3}){3}$/.test(host);
  const ipv6 = host.includes(":") || (host.startsWith("[") && host.endsWith("]"));

  if (ipv4 || ipv6) {
    return {
      sebab: "alamat-ip",
      pesan: `Sidik jari tidak bisa dipakai lewat alamat ${host}.`,
      saran: alamatLocalhost(),
    };
  }

  if (!window.isSecureContext) {
    return {
      sebab: "tanpa-https",
      pesan: "Sidik jari butuh https.",
      saran: "",
    };
  }

  return null;
}

function alamatLocalhost(): string {
  if (typeof window === "undefined") return "";
  const l = window.location;
  return `${l.protocol}//localhost${l.port ? `:${l.port}` : ""}${l.pathname}`;
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

export async function bukaKunci(): Promise<void> {
  const mulai = await panggil("/api/v1/auth/passkey/buka/mulai", { method: "POST" });
  const awal = await mulai.json().catch(() => null);
  if (!mulai.ok) throw new Error(pesanGalat(awal));

  const pilihan = JSON.parse((awal as { pilihan: string }).pilihan);
  pilihan.challenge = keBuffer(pilihan.challenge);
  for (const k of pilihan.allowCredentials ?? []) k.id = keBuffer(k.id);

  const kredensial = (await navigator.credentials.get({
    publicKey: pilihan,
  })) as PublicKeyCredential;
  const jawab = kredensial.response as AuthenticatorAssertionResponse;

  const selesai = await panggil("/api/v1/auth/passkey/buka/selesai", {
    method: "POST",
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
  if (!selesai.ok) throw new Error(pesanGalat(await selesai.json().catch(() => null)));
}

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
