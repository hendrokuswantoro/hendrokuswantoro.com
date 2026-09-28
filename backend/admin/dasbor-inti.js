let AKSES = null;
let SLUG_KINI = null;
let STATUS_KINI = null;

const $ = (id) => document.getElementById(id);
const KOLOM = ["slug","tanggal","judul_en","judul_id","ringkas_en","ringkas_id",
  "keterangan_en","keterangan_id","lede_en","lede_id","tag_en","tag_id",
  "baca_en","baca_id","isi_en","isi_id"];

function kabar(teks, jenis = "salah") {
  const k = $("kabar");
  k.textContent = teks;
  k.className = "kabar " + jenis;
  if (!teks) k.classList.add("sembunyi");
}

async function panggil(jalur, pilihan = {}) {
  const kepala = { "Content-Type": "application/json", ...(pilihan.headers || {}) };
  if (AKSES) kepala.Authorization = "Bearer " + AKSES;

  let jawaban = await fetch(jalur, { ...pilihan, headers: kepala, credentials: "same-origin" });

  if (jawaban.status === 401 && AKSES) {
    const putar = await fetch("/api/v1/auth/refresh", { method: "POST", credentials: "same-origin" });
    if (putar.ok) {
      AKSES = (await putar.json()).akses;
      kepala.Authorization = "Bearer " + AKSES;
      jawaban = await fetch(jalur, { ...pilihan, headers: kepala, credentials: "same-origin" });
    }
  }
  return jawaban;
}

function pesanGalat(isi) {
  if (!isi) return "gagal";
  if (typeof isi.detail === "string") return isi.detail;
  if (Array.isArray(isi.detail)) {
    return isi.detail.map((d) => (d.loc ? d.loc.slice(1).join(".") + ": " : "") + d.msg).join("\n");
  }
  return JSON.stringify(isi);
}


async function masuk() {
  kabar("");
  const jawaban = await fetch("/api/v1/auth/login", {
    method: "POST", credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: $("email").value.trim(), sandi: $("sandi").value }),
  });
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) { kabar(pesanGalat(isi)); return; }

  await sesudahMasuk(isi);
}

async function sesudahMasuk(isi) {
  AKSES = isi.akses;
  sembunyikanSandiLagi();
  $("siapa").textContent = isi.nama;
  $("siapa").dataset.awal = String(isi.nama || "?").trim().charAt(0).toUpperCase() || "?";
  document.body.classList.add("sudah-masuk");
  $("keluar").classList.remove("sembunyi");
  $("layar-masuk").classList.add("sembunyi");
  for (const id of ("layar-ringkasan layar-keamanan layar-perangkat layar-jejak").split(" ")) {
    $(id).classList.remove("sembunyi");
  }
  await muatKeamanan();
  await muatDaftar();
  await konfirmasiDariAlamat();

  setTimeout(() => {
    segarkan();
    mulaiSegarBerkala();
  }, 1200);
}

async function keluar() {
  hentikanSegarBerkala();
  await panggil("/api/v1/auth/logout", { method: "POST" });
  AKSES = null;
  location.reload();
}


function keBuffer(teks) {
  const dasar = teks.replace(/-/g, "+").replace(/_/g, "/");
  const penuh = dasar + "===".slice((dasar.length + 3) % 4);
  const biner = atob(penuh);
  const bita = new Uint8Array(biner.length);
  for (let i = 0; i < biner.length; i++) bita[i] = biner.charCodeAt(i);
  return bita.buffer;
}

function keTeks(buffer) {
  let biner = "";
  for (const b of new Uint8Array(buffer)) biner += String.fromCharCode(b);
  return btoa(biner).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function adaPasskey() {
  return typeof window.PublicKeyCredential === "function" &&
         typeof navigator.credentials?.create === "function";
}

function kendalaPasskey() {
  const host = location.hostname;
  const ipv4 = /^\d{1,3}(\.\d{1,3}){3}$/.test(host);
  const ipv6 = host.includes(":") || (host.startsWith("[") && host.endsWith("]"));

  if (ipv4 || ipv6) {
    const saran = location.protocol + "//localhost" +
                  (location.port ? ":" + location.port : "") + location.pathname;
    return {
      sebab: "alamat-ip",
      pesan: "Passkey tidak bisa dipakai lewat alamat " + host + ".",
      saran: saran,
    };
  }
  if (!window.isSecureContext) {
    return { sebab: "tanpa-https", pesan: "Passkey butuh https.", saran: "" };
  }
  return null;
}

function pesanKendala(k) {
  return k.saran
    ? k.pesan + " Buka " + k.saran + ", mesinnya sama, cuma namanya yang berbeda."
    : k.pesan;
}

async function masukPasskey() {
  kabar("");
  const halangan = kendalaPasskey();
  if (halangan) { kabar(pesanKendala(halangan)); return; }
  try {
    const mulai = await fetch("/api/v1/auth/passkey/masuk/mulai", { method: "POST" });
    if (!mulai.ok) { kabar(pesanGalat(await mulai.json().catch(() => null))); return; }

    const pilihan = JSON.parse((await mulai.json()).pilihan);
    pilihan.challenge = keBuffer(pilihan.challenge);
    for (const k of pilihan.allowCredentials || []) k.id = keBuffer(k.id);

    const kredensial = await navigator.credentials.get({ publicKey: pilihan });
    const jawaban = await fetch("/api/v1/auth/passkey/masuk/selesai", {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jawaban: {
        id: kredensial.id,
        rawId: keTeks(kredensial.rawId),
        type: kredensial.type,
        response: {
          clientDataJSON: keTeks(kredensial.response.clientDataJSON),
          authenticatorData: keTeks(kredensial.response.authenticatorData),
          signature: keTeks(kredensial.response.signature),
          userHandle: kredensial.response.userHandle
            ? keTeks(kredensial.response.userHandle) : null,
        },
        clientExtensionResults: kredensial.getClientExtensionResults(),
      } }),
    });

    const isi = await jawaban.json().catch(() => null);
    if (!jawaban.ok) { kabar(pesanGalat(isi)); return; }
    await sesudahMasuk(isi);
  } catch (galat) {
    if (galat.name === "SecurityError") {
      const lagi = kendalaPasskey();
      kabar(lagi ? pesanKendala(lagi)
                 : "Alamat halaman ini tidak bisa dipakai untuk passkey.");
      return;
    }
    if (galat.name !== "NotAllowedError" && galat.name !== "AbortError") {
      kabar("passkey gagal: " + galat.message);
    }
  }
}

async function daftarkanKunci() {
  kabar("");
  const halangan = kendalaPasskey();
  if (halangan) { kabar(pesanKendala(halangan)); return; }
  const nama = prompt("Nama untuk perangkat ini", "Laptop kerja");
  if (nama === null) return;

  try {
    const mulai = await panggil("/api/v1/auth/passkey/daftar/mulai", { method: "POST" });
    if (!mulai.ok) { kabar(pesanGalat(await mulai.json().catch(() => null))); return; }

    const pilihan = JSON.parse((await mulai.json()).pilihan);
    pilihan.challenge = keBuffer(pilihan.challenge);
    pilihan.user.id = keBuffer(pilihan.user.id);
    for (const k of pilihan.excludeCredentials || []) k.id = keBuffer(k.id);

    const kredensial = await navigator.credentials.create({ publicKey: pilihan });
    const jawaban = await panggil("/api/v1/auth/passkey/daftar/selesai", {
      method: "POST",
      body: JSON.stringify({ nama, jawaban: {
        id: kredensial.id,
        rawId: keTeks(kredensial.rawId),
        type: kredensial.type,
        response: {
          clientDataJSON: keTeks(kredensial.response.clientDataJSON),
          attestationObject: keTeks(kredensial.response.attestationObject),
          transports: kredensial.response.getTransports
            ? kredensial.response.getTransports() : [],
        },
        clientExtensionResults: kredensial.getClientExtensionResults(),
      } }),
    });

    if (!jawaban.ok) { kabar(pesanGalat(await jawaban.json().catch(() => null))); return; }
    kabar("perangkat terdaftar", "baik");
    await muatKunci();
  } catch (galat) {
    if (galat.name === "InvalidStateError") {
      kabar("perangkat ini sudah terdaftar");
    } else if (galat.name === "SecurityError") {
      const lagi = kendalaPasskey();
      kabar(lagi ? pesanKendala(lagi)
                 : "Alamat halaman ini tidak bisa dipakai untuk passkey.");
    } else if (galat.name !== "NotAllowedError" && galat.name !== "AbortError") {
      kabar("pendaftaran gagal: " + galat.message);
    }
  }
}
