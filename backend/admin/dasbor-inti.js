/* Skrip dashboard admin, bagian 1 dari 4: keadaan bersama, masuk, passkey.

   Keempat bagiannya dimuat berurutan dari index.html: dasbor-inti.js,
   dasbor-panel.js, dasbor-penyunting.js, lalu dasbor.js yang memasang
   semuanya. Dipecah 26 September 2026 dari satu berkas 1.237 baris.


   Dipisah dari index.html sejak 19 September 2026. Sebelumnya ia satu blok
   <script> sebaris sepanjang 44 KB, dan CSP produksi untuk /admin menolaknya
   seluruhnya: script-src di sana 'self' ditambah satu hash sha256 milik skrip
   tema tiga baris di situs publik, bukan milik skrip ini.

   Akibatnya dashboard mati total di balik nginx, dan gagalnya sunyi: tombol
   Masuk tidak melakukan apa apa, dan satu satunya jejaknya ada di konsol
   peramban. Terukur, bukan dikhawatirkan.

   Sesudah dipisah, script-src 'self' sudah cukup, dan tidak ada hash yang
   perlu dijaga tetap sama dengan isinya. Berkas ini dimuat dengan defer, jadi
   seluruh elemen sudah ada saat ia jalan, sama seperti dulu ketika <script>
   duduk di akhir <body>. */

/* Token akses disimpan di variabel biasa, bukan localStorage.
   Token di localStorage bisa diambil satu XSS; yang di memori ikut hilang
   saat tab ditutup, dan itu justru yang diinginkan. Yang bertahan antar
   kunjungan adalah cookie refresh yang HttpOnly, yang tidak bisa dibaca
   JavaScript sama sekali. */
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

  /* Access token berumur 15 menit. Kalau kedaluwarsa di tengah menulis,
     sekali coba perpanjang lalu ulangi, supaya tulisannya tidak hilang. */
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

/* --- masuk ---------------------------------------------------------- */

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

/* Satu tempat untuk semua yang terjadi sesudah masuk, apa pun jalannya.
   Sebelumnya langkahnya disalin di tiga tempat, dan salinan ketiga sudah
   lupa mengosongkan kolom sandi. */
async function sesudahMasuk(isi) {
  AKSES = isi.akses;
  sembunyikanSandiLagi();
  $("siapa").textContent = isi.nama;
  // Huruf depan untuk lingkaran di bilah atas. Ditulis ke atribut, lalu CSS
  // yang menggambarnya lewat attr(), jadi tidak ada gaya yang ditulis dari
  // sini.
  $("siapa").dataset.awal = String(isi.nama || "?").trim().charAt(0).toUpperCase() || "?";
  document.body.classList.add("sudah-masuk");
  $("keluar").classList.remove("sembunyi");
  $("layar-masuk").classList.add("sembunyi");
  for (const id of ("layar-ringkasan layar-perangkat layar-jejak").split(" ")) {
    $(id).classList.remove("sembunyi");
  }
  await muatDaftar();

  /* Penyegaran dashboard sengaja TIDAK ditunggu, dan ini bukan soal kecepatan.
     Sebelumnya ia ditunggu di sini, dan akibatnya masuk dengan passkey
     berhenti di tengah tanpa satu pun pesan: layar tetap di halaman masuk,
     kotak kabar kosong, konsol bersih. Yang menahannya penyegaran itu,
     terbukti dengan melepasnya lalu ujinya lolos.
     Jalan masuk tidak boleh bergantung pada panel yang cuma menampilkan
     angka. Kalau penyegarannya gagal, yang benar panelnya berkata tidak
     terbaca, bukan pemiliknya gagal masuk. */
  /* Ditunda sebentar, dan penundaan ini bagian dari perbaikannya.
     Penyegaran yang menyusul persis di detik masuk berlomba dengan alur
     otentikasi yang belum selesai menata diri, dan yang kalah justru
     otentikasinya: masuk dengan passkey berhenti di tengah tanpa satu pun
     pesan. Sesudah satu detik, jalan masuknya sudah tuntas dan tidak ada lagi
     yang bisa ditahannya. */
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

/* --- passkey -------------------------------------------------------- */

/* WebAuthn mengirim dan menerima ArrayBuffer, JSON hanya mengenal teks, jadi
   base64url adalah jembatannya. Dua fungsi ini yang paling sering ditulis
   salah di contoh contoh di internet: padding "=" harus dikembalikan sebelum
   atob, dan dibuang lagi sesudah btoa. */
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

/* Kenapa passkey tidak bisa dipakai di alamat ini, kalau memang tidak bisa.
   Mengembalikan null berarti tidak ada yang menghalangi.

   WebAuthn menuntut rp_id berupa NAMA DOMAIN, dan alamat IP bukan nama
   domain. Peramban menolaknya sebelum satu pun permintaan dikirim, dengan
   SecurityError berbunyi "This is an invalid domain." Sudah diperiksa di
   Chromium dari http://127.0.0.1, dan rp_id "127.0.0.1" pun ditolak sama
   persis, jadi tidak ada nilai rp_id mana pun yang menyelamatkannya.

   "localhost" adalah nama, bukan alamat, dan ia diizinkan. Keduanya menunjuk
   mesin yang sama, dan justru itu yang membuat cacat ini mahal: kedua alamat
   terlihat setara, tombolnya terlihat hidup, lalu gagal dengan kalimat
   berbahasa Inggris yang tidak menyebutkan apa yang harus dilakukan. */
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

/* Satu tempat untuk menuliskannya, supaya masuk dan mendaftar tidak berbeda
   kalimat untuk sebab yang sama. */
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
    /* Dibatalkan pengguna bukan kegagalan, dan menampilkannya sebagai galat
       merah hanya membuat orang mengira ada yang rusak. */
    if (galat.name === "SecurityError") {
      /* Datang dari peramban, bukan dari server, dan bunyinya "This is an
         invalid domain." Benar, tetapi tidak memberi tahu apa yang harus
         dikerjakan. */
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
