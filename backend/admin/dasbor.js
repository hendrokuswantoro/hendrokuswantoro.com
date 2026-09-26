/* Skrip dashboard admin.

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

/* --- dashboard yang hidup -------------------------------------------- */

/* Selang penyegaran. Lima belas detik cukup untuk terasa hidup dan cukup
   jarang untuk tidak membebani apa pun. Yang lebih penting: penyegarannya
   BERHENTI saat tab tidak terlihat. Tab yang ditinggalkan terbuka berhari
   hari tidak boleh terus mengetuk server, dan peramban sendiri sudah
   memperlambat timer di tab tersembunyi sehingga hasilnya cuma antrean
   permintaan yang menumpuk lalu meledak sekaligus saat tab dibuka lagi. */
const SELANG_SEGAR_MS = 15000;
let jamSegar = null;

function waktuPendek(iso) {
  if (!iso) return "belum";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleString("id-ID", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

/* Angka yang belum bisa dibaca ditulis "?", bukan 0.
   Nol adalah bacaan, ketiadaan data bukan, dan perbedaan itu wajib terlihat
   oleh yang membacanya. */
function pasangAngka(id, nilai) {
  $(id).textContent = (nilai === null || nilai === undefined) ? "?" : String(nilai);
}

function tandaKeadaan(nama, keadaan, keterangan) {
  const s = document.createElement("span");
  s.className = keadaan;
  s.textContent = nama;
  if (keterangan) s.title = keterangan;
  return s;
}

async function muatRingkasan() {
  /* Diminta BERURUTAN, dan itu keputusan yang dibayar mahal untuk dipelajari.
     Versi pertama memintanya berbarengan dengan Promise.all, tujuh permintaan
     sekaligus bersama dua panel lain. Akibatnya masuk dengan passkey berhenti
     di tengah tanpa satu pun pesan: kotak kabar kosong, konsol bersih, dan
     halamannya tetap di layar masuk. Dipersempit satu per satu, tiap panel
     sendirian lolos dan ketiganya bersama gagal, jadi yang mematikan memang
     ledakan permintaannya. Peramban hanya membuka enam sambungan sekaligus ke
     satu asal, dan permintaan yang mengantre di belakangnya ikut menahan alur
     yang sedang berjalan.
     Dashboard yang menyegar tiap lima belas detik tidak butuh paralel. */
  const ambil = async (jalur, pakaiToken = true) => {
    try {
      const j = pakaiToken ? await panggil(jalur) : await fetch(jalur);
      return j.ok ? await j.json() : null;
    } catch {
      return null;
    }
  };

  const tulisan = await ambil("/api/v1/admin/blog");
  const kunci = await ambil("/api/v1/auth/passkey");
  const sesi = await ambil("/api/v1/auth/sesi");
  const keamanan = await ambil("/api/v1/keamanan");
  const sehat = await ambil("/health", false);

  const isi = tulisan && tulisan.isi;
  pasangAngka("ubin-terbit", isi ? isi.filter((t) => t.status === "terbit").length : null);
  pasangAngka("ubin-draf", isi ? isi.filter((t) => t.status !== "terbit").length : null);
  pasangAngka("ubin-passkey", kunci ? kunci.daftar.length : null);
  pasangAngka("ubin-sesi", sesi ? sesi.jumlah : null);

  /* Keadaan sistem. Yang belum siap disebut apa adanya beserta nama
     variabelnya, sebab tombol yang diam diam gagal lebih buruk daripada
     tombol yang menjelaskan kenapa ia belum bisa dipakai. */
  const kotak = $("keadaan-sistem");
  kotak.replaceChildren();

  if (sehat) {
    kotak.appendChild(tandaKeadaan("basis data", sehat.basis_data ? "baik" : "buruk"));
    kotak.appendChild(tandaKeadaan("cache", sehat.cache ? "baik" : "belum"));
  } else {
    kotak.appendChild(tandaKeadaan("kesehatan tidak terbaca", "buruk"));
  }

  if (keamanan) {
    kotak.appendChild(tandaKeadaan(
      keamanan.totp_aktif ? "authenticator aktif" : "authenticator mati",
      keamanan.totp_aktif ? "baik" : "belum",
    ));
    kotak.appendChild(tandaKeadaan(
      keamanan.email_terverifikasi ? "email terbukti" : "email belum terbukti",
      keamanan.email_terverifikasi ? "baik" : "belum",
    ));
    /* Kekuatan sesi ini sendiri. Tanpa penanda ini, tombol Simpan yang
       menolak dengan 403 terlihat seperti kerusakan, bukan seperti aturan. */
    if (keamanan.faktor_kedua_wajib) {
      kotak.appendChild(tandaKeadaan(
        keamanan.sesi_kuat ? "sesi kuat" : "sesi lemah, tidak bisa menulis",
        keamanan.sesi_kuat ? "baik" : "buruk",
        keamanan.sesi_kuat
          ? "Sesi ini lahir lewat faktor kedua, jadi jalur tulis terbuka."
          : "Pasang authenticator atau passkey, lalu masuk lagi. Sampai itu, "
            + "menulis dan mengunggah ditolak.",
      ));
    }

    /* Pencabutan segera. Tanpa Redis, tombol keluarkan perangkat lain hanya
       mematikan refresh token-nya, dan token aksesnya masih hidup sampai
       lima belas menit berikutnya. Disebutkan, bukan didiamkan. */
    if (!keamanan.pencabutan_segera_siap) {
      kotak.appendChild(tandaKeadaan("pencabutan tertunda 15 menit", "belum",
        "REDIS_URL belum diisi. Tanpa itu, sesi yang dicabut baru benar benar "
        + "mati saat token aksesnya kedaluwarsa."));
    }

    if (!keamanan.surat_siap) {
      kotak.appendChild(tandaKeadaan("SMTP belum diisi", "belum",
        "Isi SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, dan SURAT_DARI di .env"));
    }
    if (!keamanan.kunci_kolom_siap) {
      kotak.appendChild(tandaKeadaan("KUNCI_KOLOM belum diisi", "belum",
        "Tanpa itu authenticator tidak bisa dipasang"));
    }
    if (!keamanan.wajah_siap) {
      kotak.appendChild(tandaKeadaan("model wajah belum diunduh", "belum",
        "Jalankan tools/ambil_model.py"));
    }
    if (keamanan.totp_aktif && keamanan.pemulihan_sisa === 0) {
      kotak.appendChild(tandaKeadaan("kode pemulihan habis", "buruk",
        "Buat ulang sebelum perangkatnya hilang"));
    }
  }

  $("waktu-segar").textContent = "diperbarui " +
    new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

async function muatSesi() {
  const jawaban = await panggil("/api/v1/auth/sesi");
  const badan = $("daftar-sesi");
  badan.replaceChildren();

  if (!jawaban.ok) {
    const baris = document.createElement("tr");
    const sel = document.createElement("td");
    sel.colSpan = 3;
    sel.className = "kosong";
    sel.textContent = "daftar perangkat tidak terbaca";
    baris.appendChild(sel);
    badan.appendChild(baris);
    return;
  }

  for (const s of (await jawaban.json()).sesi) {
    const baris = document.createElement("tr");

    const mulai = document.createElement("td");
    mulai.textContent = waktuPendek(s.dibuat_pada);

    const sampai = document.createElement("td");
    sampai.textContent = waktuPendek(s.kadaluarsa);

    const tanda = document.createElement("td");
    if (s.perangkat_ini) {
      const p = document.createElement("span");
      p.className = "ini-perangkat";
      p.textContent = "perangkat ini";
      tanda.appendChild(p);
    }

    baris.append(mulai, sampai, tanda);
    badan.appendChild(baris);
  }
}

/* Nama peristiwa diterjemahkan, tidak ditampilkan apa adanya.
   Yang tidak ada di kamus ditulis apa adanya, bukan dibuang: peristiwa
   keamanan yang hilang dari layar lebih buruk daripada yang namanya jelek. */
const NAMA_PERISTIWA = {
  masuk: "Masuk",
  verifikasi_email: "Verifikasi email",
  verifikasi_email_dikirim: "Tautan verifikasi dikirim",
  otp_dikirim: "Kode dikirim lewat email",
  otp_salah: "Kode email salah",
  totp_aktifkan: "Authenticator dinyalakan",
  totp_matikan: "Authenticator dimatikan",
  totp_salah: "Kode authenticator salah",
  kode_pemulihan: "Kode pemulihan dipakai",
  wajah_daftar: "Wajah didaftarkan",
  wajah_hapus: "Wajah dihapus",
  wajah_cocok: "Verifikasi wajah",
  wajah_salah: "Verifikasi wajah gagal",
};

async function muatJejak() {
  const jawaban = await panggil("/api/v1/keamanan/peristiwa");
  const badan = $("daftar-jejak");
  badan.replaceChildren();

  const kosong = (teks) => {
    const baris = document.createElement("tr");
    const sel = document.createElement("td");
    sel.colSpan = 3;
    sel.className = "kosong";
    sel.textContent = teks;
    baris.appendChild(sel);
    badan.appendChild(baris);
  };

  if (!jawaban.ok) { kosong("jejak keamanan tidak terbaca"); return; }

  const daftar = (await jawaban.json()).peristiwa || [];
  if (!daftar.length) { kosong("belum ada satu pun aktivitas tercatat"); return; }

  for (const p of daftar) {
    const baris = document.createElement("tr");

    const waktu = document.createElement("td");
    waktu.textContent = waktuPendek(p.pada);

    const apa = document.createElement("td");
    apa.textContent = NAMA_PERISTIWA[p.jenis] || p.jenis;
    /* Keterangannya ditaruh di title, bukan di kolom sendiri: isinya pendek
       dan tidak selalu ada, dan kolom yang sering kosong cuma memperlebar
       tabel tanpa memberi tahu apa apa. */
    if (p.keterangan) apa.title = p.keterangan;

    const hasil = document.createElement("td");
    const tanda = document.createElement("span");
    tanda.className = "tanda" + (p.berhasil ? " terbit" : "");
    if (!p.berhasil) tanda.style.color = "var(--bahaya)";
    if (!p.berhasil) tanda.style.borderColor = "var(--bahaya)";
    tanda.textContent = p.berhasil ? "berhasil" : "gagal";
    hasil.appendChild(tanda);

    baris.append(waktu, apa, hasil);
    badan.appendChild(baris);
  }
}

async function segarkan() {
  /* Berurutan, bukan berbarengan. Alasannya sama dengan di muatRingkasan:
     ledakan permintaan serentak menahan alur lain yang sedang berjalan.
     Galat tiap pemuat ditahan di sini supaya satu panel yang gagal tidak
     menjatuhkan dua panel lain; masing masing sudah menulis keadaan gagalnya
     sendiri di layar. */
  for (const muat of [muatRingkasan, muatSesi, muatJejak]) {
    try { await muat(); } catch { /* panelnya sendiri yang mengabarkan */ }
  }
}

function mulaiSegarBerkala() {
  hentikanSegarBerkala();
  jamSegar = setInterval(() => {
    if (document.hidden) return;
    segarkan();
  }, SELANG_SEGAR_MS);
}

function hentikanSegarBerkala() {
  if (jamSegar) { clearInterval(jamSegar); jamSegar = null; }
}

/* Begitu tab dibuka lagi, disegarkan sekali di luar giliran. Menunggu sampai
   lima belas detik berikutnya berarti angka yang pertama dilihat orang adalah
   angka basi dari sebelum ia pergi. */
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && AKSES) segarkan();
});

async function muatKunci() {
  if (!adaPasskey()) return;
  const jawaban = await panggil("/api/v1/auth/passkey");
  if (!jawaban.ok) return;

  const badan = $("daftar-kunci");
  badan.replaceChildren();

  for (const k of (await jawaban.json()).daftar) {
    const baris = document.createElement("tr");

    const nama = document.createElement("td");
    nama.textContent = k.nama;

    const jenis = document.createElement("td");
    jenis.textContent = k.jenis_perangkat === "multi_device"
      ? "tersinkron" : "satu perangkat";

    const dipakai = document.createElement("td");
    dipakai.textContent = k.dipakai_pada ? k.dipakai_pada.slice(0, 10) : "belum pernah";

    const aksi = document.createElement("td");
    const tombol = document.createElement("button");
    tombol.className = "bahaya";
    tombol.textContent = "Cabut";
    tombol.onclick = () => cabutKunci(k.id, k.nama);
    aksi.appendChild(tombol);

    baris.append(nama, jenis, dipakai, aksi);
    badan.appendChild(baris);
  }

  $("layar-kunci").classList.remove("sembunyi");
}

async function cabutKunci(id, nama) {
  if (!confirm(`Cabut passkey "${nama}"? Perangkat itu tidak bisa dipakai masuk lagi.`)) return;
  const jawaban = await panggil("/api/v1/auth/passkey/" + encodeURIComponent(id),
                                { method: "DELETE" });
  if (!jawaban.ok) { kabar(pesanGalat(await jawaban.json().catch(() => null))); return; }
  kabar("passkey dicabut", "baik");
  await muatKunci();
}

/* --- daftar --------------------------------------------------------- */

async function muatDaftar() {
  const jawaban = await panggil("/api/v1/admin/blog");
  if (!jawaban.ok) { kabar(pesanGalat(await jawaban.json().catch(() => null))); return; }

  const isi = (await jawaban.json()).isi;
  const badan = $("daftar");
  badan.replaceChildren();

  for (const t of isi) {
    const baris = document.createElement("tr");

    const judul = document.createElement("td");
    judul.textContent = t.judul_id || t.judul_en;

    const status = document.createElement("td");
    const tanda = document.createElement("span");
    tanda.className = "tanda" + (t.status === "terbit" ? " terbit" : "");
    tanda.textContent = t.status;
    status.appendChild(tanda);

    const tanggal = document.createElement("td");
    tanggal.textContent = t.terbit_pada || "belum";

    const aksi = document.createElement("td");
    const tombol = document.createElement("button");
    tombol.textContent = "Sunting";
    tombol.onclick = () => bukaSunting(t.slug);
    aksi.appendChild(tombol);

    baris.append(judul, status, tanggal, aksi);
    badan.appendChild(baris);
  }

  $("layar-daftar").classList.remove("sembunyi");
  $("layar-sunting").classList.add("sembunyi");
  await muatKunci();
}

/* --- penyunting ----------------------------------------------------- */

function kosongkan() {
  for (const k of KOLOM) if ($(k)) $(k).value = "";
  $("tanggal").value = new Date().toISOString().slice(0, 10);
}

function bukaBaru() {
  SLUG_KINI = null; STATUS_KINI = null;
  kosongkan();
  $("judul-sunting").textContent = "Tulisan baru";
  $("tanda-status").textContent = "belum disimpan";
  $("tanda-status").className = "tanda";
  $("slug").disabled = false;
  $("tombol-terbit").classList.add("sembunyi");
  $("tombol-hapus").classList.add("sembunyi");
  $("layar-daftar").classList.add("sembunyi");
  $("layar-kunci").classList.add("sembunyi");
  $("layar-sunting").classList.remove("sembunyi");
  perbarui();
  window.scrollTo({ top: 0 });
}

async function bukaSunting(slug) {
  const jawaban = await panggil("/api/v1/blog/" + slug);
  let isi = null;
  if (jawaban.ok) {
    const t = await jawaban.json();
    isi = {
      slug: t.slug, tanggal: t.tanggal,
      judul_en: t.judul.en, judul_id: t.judul.id,
      ringkas_en: t.ringkas.en, ringkas_id: t.ringkas.id,
      keterangan_en: t.keterangan.en, keterangan_id: t.keterangan.id,
      lede_en: t.lede.en, lede_id: t.lede.id,
      tag_en: t.tag.en, tag_id: t.tag.id,
      baca_en: t.baca.en, baca_id: t.baca.id,
      isi_en: t.isi_en, isi_id: t.isi_id,
    };
  }
  if (!isi) { kabar("Draf belum bisa dibuka lewat jalur publik. Terbitkan dulu, atau buat baru."); return; }

  SLUG_KINI = slug;
  for (const k of KOLOM) if ($(k)) $(k).value = isi[k] ?? "";
  $("slug").disabled = true;
  $("judul-sunting").textContent = "Sunting";
  $("tombol-terbit").classList.remove("sembunyi");
  $("tombol-hapus").classList.remove("sembunyi");
  $("layar-daftar").classList.add("sembunyi");
  $("layar-kunci").classList.add("sembunyi");
  $("layar-sunting").classList.remove("sembunyi");
  perbarui();
  window.scrollTo({ top: 0 });
}

function kumpulkan() {
  const isi = {};
  for (const k of KOLOM) if ($(k)) isi[k] = $(k).value;
  return isi;
}

async function simpan() {
  kabar("");
  const isi = kumpulkan();

  const jawaban = SLUG_KINI
    ? await panggil("/api/v1/admin/blog/" + SLUG_KINI, {
        method: "PATCH",
        body: JSON.stringify(Object.fromEntries(
          Object.entries(isi).filter(([k]) => k !== "slug"))),
      })
    : await panggil("/api/v1/admin/blog", { method: "POST", body: JSON.stringify(isi) });

  const hasil = await jawaban.json().catch(() => null);
  if (!jawaban.ok) { kabar(pesanGalat(hasil)); return; }

  SLUG_KINI = hasil.slug;
  STATUS_KINI = hasil.status;
  $("slug").disabled = true;
  $("tanda-status").textContent = hasil.status;
  $("tombol-terbit").classList.remove("sembunyi");
  $("tombol-hapus").classList.remove("sembunyi");
  kabar("Tersimpan sebagai " + hasil.status + ".", "baik");
}

async function terbitkan() {
  if (!SLUG_KINI) { kabar("Simpan dulu."); return; }
  const jawaban = await panggil("/api/v1/admin/blog/" + SLUG_KINI + "/status", {
    method: "POST", body: JSON.stringify({ status: "terbit" }),
  });
  const hasil = await jawaban.json().catch(() => null);
  if (!jawaban.ok) { kabar(pesanGalat(hasil)); return; }
  $("tanda-status").textContent = "terbit";
  $("tanda-status").className = "tanda terbit";
  kabar("Terbit. Jalankan pembangkit situs supaya halamannya ikut terbit.", "baik");
}

async function hapus() {
  if (!SLUG_KINI) return;
  if (!confirm("Hapus tulisan ini? Tidak bisa dibatalkan.")) return;
  const jawaban = await panggil("/api/v1/admin/blog/" + SLUG_KINI, { method: "DELETE" });
  if (!jawaban.ok) { kabar("gagal menghapus"); return; }
  await muatDaftar();
}

/* --- penghitung blok, bilah format, pustaka berkas, pratinjau -------- */

/* Penghitung blok di bawah: kasar, dan memang cuma itu tugasnya.
   Ia menghitung paragraf sambil diketik supaya peringatan "jumlah bloknya
   tidak sama" muncul sebelum ada yang menekan Simpan. Ia TIDAK membangun
   HTML, dan itu disengaja: yang membangun HTML satu pengurai saja, di server,
   yaitu yang sama dengan yang dipakai Simpan dan yang membangun halaman blog
   yang sudah terbit. Dua pengurai untuk satu bahasa markah akan berpisah, dan
   yang berpisah membuat layar pratinjau berbohong. */
function blok(teks) {
  const hasil = [];
  let kumpul = [], jenis = "p";
  const tutup = () => { if (kumpul.length) hasil.push({ jenis, teks: kumpul.join(" ") }); kumpul = []; jenis = "p"; };

  for (const baris of (teks || "").split("\n")) {
    const b = baris.trim();
    if (!b) { tutup(); continue; }
    if (b.startsWith("## ")) { tutup(); hasil.push({ jenis: "h2", teks: b.slice(3) }); continue; }
    if (b.startsWith("!")) { tutup(); hasil.push({ jenis: "media", teks: b }); continue; }
    if (b.startsWith(">")) { if (jenis !== "quote") { tutup(); jenis = "quote"; } kumpul.push(b.slice(1).trim()); continue; }
    if (/^([-*+]|\d{1,3}\.)\s/.test(b)) {
      const ini = /^\d/.test(b) ? "ol" : "ul";
      if (jenis !== ini) { tutup(); jenis = ini; }
      kumpul.push(b);
      continue;
    }
    if (jenis === "ul" || jenis === "ol") tutup();
    kumpul.push(b);
  }
  tutup();
  return hasil;
}

/* Menulis ke dalam textarea lewat execCommand, bukan lewat value.
   execCommand sudah ditandai usang, dan tetap dipakai karena satu hal yang
   belum ada penggantinya: ia menyisipkan ke dalam tumpukan urung peramban.
   Menyetel value langsung membuang tumpukan itu, sehingga Ctrl+Z sesudah
   menekan Tebal membatalkan bukan penebalannya melainkan seluruh paragraf
   yang baru diketik. */
function sisipkan(kotak, teks) {
  kotak.focus();
  let berhasil = false;
  try { berhasil = document.execCommand("insertText", false, teks); } catch { berhasil = false; }
  if (!berhasil) {
    const a = kotak.selectionStart, b = kotak.selectionEnd;
    kotak.value = kotak.value.slice(0, a) + teks + kotak.value.slice(b);
    kotak.selectionStart = kotak.selectionEnd = a + teks.length;
  }
  perbarui();
}

let KOTAK_TERAKHIR = "isi_en";

function kotakAktif() { return $(KOTAK_TERAKHIR); }

function terapkanSebaris(kotak, depan, belakang, contoh) {
  const dipilih = kotak.value.slice(kotak.selectionStart, kotak.selectionEnd) || contoh;
  sisipkan(kotak, depan + dipilih + belakang);
}

function terapkanBaris(kotak, depan, contoh) {
  const nilai = kotak.value;
  const sebelum = nilai.lastIndexOf("\n", Math.max(0, kotak.selectionStart - 1));
  const mulai = sebelum === -1 ? 0 : sebelum + 1;
  const habis = nilai.indexOf("\n", kotak.selectionEnd);
  const akhir = habis === -1 ? nilai.length : habis;
  const baris = nilai.slice(mulai, akhir);

  kotak.selectionStart = mulai;
  kotak.selectionEnd = akhir;
  /* Menekan tombol yang sama dua kali mencabut tandanya lagi, seperti tombol
     tebal di pengolah kata. */
  if (baris.startsWith(depan)) sisipkan(kotak, baris.slice(depan.length));
  else sisipkan(kotak, depan + (baris || contoh));
}

for (const tombol of document.querySelectorAll(".bilah button[data-sisip], .bilah button[data-baris]")) {
  tombol.addEventListener("mousedown", (e) => e.preventDefault());
  tombol.addEventListener("click", () => {
    const kotak = kotakAktif();
    if (tombol.dataset.sisip) {
      const [depan, belakang, contoh] = tombol.dataset.sisip.split("|");
      terapkanSebaris(kotak, depan, belakang, contoh);
    } else {
      const [depan, contoh] = tombol.dataset.baris.split("|");
      terapkanBaris(kotak, depan, contoh);
    }
  });
}

/* Pintasan dipasang pada kotaknya, bukan pada dokumen: Ctrl+B di kolom judul
   tidak boleh diam diam menulis bintang. */
for (const nama of ["isi_en", "isi_id"]) {
  const kotak = $(nama);
  kotak.addEventListener("focus", () => { KOTAK_TERAKHIR = nama; });
  kotak.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
    const pilihan = { b: ["**", "**", "tebal"], i: ["*", "*", "miring"], k: ["[", "](/blog/)", "teks"] };
    const sisip = pilihan[e.key.toLowerCase()];
    if (!sisip) return;
    e.preventDefault();
    terapkanSebaris(kotak, sisip[0], sisip[1], sisip[2]);
  });
}

/* --- pustaka foto dan video ----------------------------------------- */

function ukuranTerbaca(bita) {
  if (bita < 1024) return bita + " B";
  if (bita < 1048576) return Math.round(bita / 1024) + " KB";
  return (bita / 1048576).toFixed(1) + " MB";
}

function kabarBerkas(teks, baik) {
  const k = $("kabar-berkas");
  k.textContent = teks;
  k.className = "kabar " + (baik ? "baik" : "salah");
}

async function muatBerkas() {
  const jawaban = await panggil("/api/v1/admin/berkas");
  if (!jawaban.ok) { kabarBerkas("gagal memuat daftar berkas", false); return; }
  const hasil = await jawaban.json();

  const petak = $("petak-berkas");
  petak.replaceChildren();
  if (!hasil.isi.length) {
    const kosong = document.createElement("li");
    kosong.className = "kosong";
    kosong.textContent = "Belum ada berkas yang diunggah.";
    petak.appendChild(kosong);
    return;
  }

  for (const b of hasil.isi) {
    const li = document.createElement("li");

    const tombol = document.createElement("button");
    tombol.type = "button";
    tombol.className = "sisip";
    tombol.title = "Sisipkan " + b.nama_asal;
    const gambar = document.createElement(b.jenis === "gambar" ? "img" : "video");
    gambar.src = b.alamat;
    if (b.jenis === "gambar") { gambar.alt = ""; gambar.loading = "lazy"; }
    else { gambar.preload = "metadata"; gambar.muted = true; }
    tombol.appendChild(gambar);
    tombol.onclick = () => sisipBerkas(b);
    li.appendChild(tombol);

    const nama = document.createElement("p");
    nama.className = "nama";
    nama.textContent = b.nama_asal;
    nama.title = b.nama_asal;
    li.appendChild(nama);

    const ket = document.createElement("p");
    ket.className = "petunjuk";
    ket.style.margin = "0";
    ket.textContent = (b.lebar ? b.lebar + "\u00d7" + b.tinggi + " \u00b7 " : "") + ukuranTerbaca(b.bita);
    li.appendChild(ket);

    const buang = document.createElement("button");
    buang.type = "button";
    buang.className = "bahaya";
    buang.textContent = "Hapus";
    buang.onclick = () => hapusBerkas(b);
    li.appendChild(buang);

    petak.appendChild(li);
  }
}

/* Disisipkan ke KEDUA bahasa sekaligus. Bukan kenyamanan: dua bahasa wajib
   sebangun blok demi blok, jadi gambar yang hanya masuk ke satu bahasa
   langsung membuat tulisannya ditolak. */
function sisipBerkas(b) {
  const baris = (b.jenis === "video" ? "!video[](" : "![](") + b.alamat + ")";
  for (const nama of ["isi_en", "isi_id"]) {
    const kotak = $(nama);
    const perlu = kotak.value && !kotak.value.endsWith("\n\n");
    kotak.focus();
    kotak.selectionStart = kotak.selectionEnd = kotak.value.length;
    sisipkan(kotak, (perlu ? "\n\n" : "") + baris + "\n\n");
  }
  kabarBerkas(b.nama_asal + " disisipkan ke kedua bahasa. Isi keterangannya di dalam kurung siku.", true);
}

async function hapusBerkas(b) {
  if (!confirm("Hapus " + b.nama_asal + "? Ini tidak bisa dibatalkan.")) return;
  const jawaban = await panggil("/api/v1/admin/berkas/" + encodeURIComponent(b.nama), { method: "DELETE" });
  if (!jawaban.ok) {
    const isi = await jawaban.json().catch(() => null);
    kabarBerkas((isi && isi.detail) || "gagal menghapus", false);
    return;
  }
  kabarBerkas(b.nama_asal + " dihapus", true);
  await muatBerkas();
}

/* Memakai XMLHttpRequest, bukan fetch, dan itu satu satunya alasannya: fetch
   belum bisa melaporkan berapa bita yang sudah terkirim. Untuk video delapan
   puluh megabita di sambungan rumahan, bilah yang bergerak adalah beda antara
   menunggu dan mengira aplikasinya menggantung.

   Content-Type sengaja tidak dipasang. Peramban menuliskannya sendiri beserta
   boundary multipart-nya, dan boundary yang ditulis tangan hampir selalu
   salah. */
function unggahSatu(berkas) {
  return new Promise((selesai, gagal) => {
    const bentuk = new FormData();
    bentuk.append("berkas", berkas, berkas.name);
    bentuk.append("buang_metadata", $("buang-metadata").checked ? "true" : "false");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/admin/berkas");
    xhr.withCredentials = true;
    if (AKSES) xhr.setRequestHeader("Authorization", "Bearer " + AKSES);

    const laju = $("laju");
    laju.classList.remove("sembunyi");
    xhr.upload.onprogress = (p) => {
      if (!p.lengthComputable) return;
      const persen = Math.round((p.loaded / p.total) * 100);
      laju.firstElementChild.style.width = persen + "%";
      laju.setAttribute("aria-valuenow", String(persen));
    };
    xhr.onload = () => {
      laju.classList.add("sembunyi");
      let isi = null;
      try { isi = JSON.parse(xhr.responseText); } catch { isi = null; }
      selesai({ status: xhr.status, isi });
    };
    xhr.onerror = () => { laju.classList.add("sembunyi"); gagal(new Error("sambungan terputus")); };
    xhr.send(bentuk);
  });
}

async function kirimBerkas(daftar) {
  if (!daftar || !daftar.length) return;
  /* Satu per satu, bukan sekaligus: enam video yang berangkat bersamaan
     berebut sambungan yang sama dan tidak ada satu pun yang selesai lebih
     cepat karenanya. */
  for (const satu of Array.from(daftar)) {
    try {
      const hasil = await unggahSatu(satu);
      if (hasil.status < 200 || hasil.status >= 300) {
        kabarBerkas(satu.name + ": " + ((hasil.isi && hasil.isi.detail) || "gagal mengunggah"), false);
        continue;
      }
      kabarBerkas(
        hasil.isi.sudah_ada
          ? hasil.isi.nama_asal + " sudah pernah diunggah, yang dipakai yang lama"
          : hasil.isi.nama_asal + " masuk",
        true,
      );
    } catch (galat) {
      kabarBerkas(satu.name + ": " + galat.message, false);
    }
  }
  await muatBerkas();
}

$("buka-berkas").onclick = async () => {
  const kartu = $("kartu-berkas");
  const buka = kartu.classList.contains("sembunyi");
  kartu.classList.toggle("sembunyi", !buka);
  if (buka) await muatBerkas();
};
$("pilih-berkas").onclick = () => $("berkas-masuk").click();
$("berkas-masuk").onchange = async (e) => {
  await kirimBerkas(e.target.files);
  e.target.value = "";
};

const JATUH = $("jatuh");
JATUH.addEventListener("dragover", (e) => { e.preventDefault(); JATUH.classList.add("aktif"); });
JATUH.addEventListener("dragleave", () => JATUH.classList.remove("aktif"));
JATUH.addEventListener("drop", async (e) => {
  e.preventDefault();
  JATUH.classList.remove("aktif");
  await kirimBerkas(e.dataTransfer.files);
});

/* --- pratinjau ------------------------------------------------------ */

let TUNDA_PRATINJAU = null;

function perbarui() {
  const en = blok($("isi_en").value);
  const id = blok($("isi_id").value);
  $("hitung_en").textContent = en.length + " blok";
  $("hitung_id").textContent = id.length + " blok";

  const c = $("cocok");
  if (en.length !== id.length) {
    c.textContent = "Jumlah blok tidak sama: Inggris " + en.length + ", Indonesia " + id.length +
                    ". Tulisan seperti ini akan ditolak saat disimpan.";
    c.className = "kabar salah";
  } else {
    const beda = en.findIndex((x, i) => id[i] && x.jenis !== id[i].jenis);
    if (beda >= 0) {
      c.textContent = "Blok ke " + (beda + 1) + " beda jenis: " + en[beda].jenis + " lawan " + id[beda].jenis + ".";
      c.className = "kabar salah";
    } else {
      c.className = "kabar sembunyi";
    }
  }

  /* Pratinjaunya dibangun server, oleh pembangkit yang sama dengan yang
     membangun halaman blog yang sudah terbit. Jadi yang terlihat di sini
     memang yang akan terbit, dan markah yang ditolak di sini adalah markah
     yang akan ditolak Simpan, dengan kalimat yang sama.

     Ditunda 500 ms sesudah ketikan terakhir. Tanpa penundaan, tiap huruf
     mengirim satu permintaan, dan yang sampai duluan belum tentu yang
     terakhir diketik. */
  if (TUNDA_PRATINJAU) clearTimeout(TUNDA_PRATINJAU);
  TUNDA_PRATINJAU = setTimeout(mintaPratinjau, 500);
}

async function mintaPratinjau() {
  const p = $("pratinjau");
  const isi_en = $("isi_en").value, isi_id = $("isi_id").value;
  if (!isi_en && !isi_id) { p.replaceChildren(); $("hitung-kata").textContent = ""; return; }

  const jawaban = await panggil("/api/v1/admin/pratinjau", {
    method: "POST",
    body: JSON.stringify({ isi_en, isi_id }),
  });
  const hasil = await jawaban.json().catch(() => null);

  if (!jawaban.ok) {
    /* Alasannya ditulis sebagai teks, bukan sebagai HTML: ia memuat potongan
       baris yang baru saja diketik orangnya. */
    p.replaceChildren();
    const galat = document.createElement("p");
    galat.className = "kabar salah";
    galat.textContent = (hasil && hasil.detail) || "markahnya belum bisa dibaca";
    p.appendChild(galat);
    $("hitung-kata").textContent = "";
    return;
  }

  /* innerHTML dengan sengaja, dan aman justru karena sumbernya.

     HTML ini tidak datang dari orang dan tidak datang dari peramban. Ia
     dibangun tools/markah.py di server, yaitu pengurai yang meng-escape
     seluruh teks, menolak HTML mentah dengan galat, dan menolak skema tautan
     selain http, https, dan mailto. Membersihkannya lagi di sini berarti dua
     aturan untuk satu hal, dan dua aturan akan berpisah.

     Sampai 18 September 2026 pratinjau ini dirakit dengan createElement dari
     pengurai kecil di halaman ini sendiri. Yang menggantikannya bukan
     kelonggaran melainkan penghapusan pengurai kedua itu. */
  p.innerHTML = hasil.html;
  $("hitung-kata").textContent = hasil.kata_en + " kata";
}

/* --- pasang --------------------------------------------------------- */

/* Saklar lihat sandi.
   Mengganti `type` adalah satu satunya cara yang benar benar bekerja di
   seluruh peramban, dan ia menyimpan isinya: nilai `value` tidak tersentuh.
   Yang perlu dijaga cuma tempat kursor, sebab mengganti type memindahkannya
   ke akhir di sebagian peramban dan itu terasa seperti ketikan yang lompat. */
$("lihat-sandi").onclick = () => {
  const isian = $("sandi");
  const tampil = isian.type === "password";
  const mulai = isian.selectionStart;
  const akhir = isian.selectionEnd;

  isian.type = tampil ? "text" : "password";
  $("lihat-sandi").setAttribute("aria-pressed", String(tampil));
  const label = tampil ? "Sembunyikan sandi" : "Tampilkan sandi";
  $("lihat-sandi").setAttribute("aria-label", label);
  $("lihat-sandi").setAttribute("title", label);

  isian.focus();
  try { isian.setSelectionRange(mulai, akhir); } catch { /* type lama menolak */ }
};

/* Sandi tidak boleh tertinggal terbaca di layar.
   Begitu sesinya dibuka, isiannya dikosongkan dan saklarnya dikembalikan ke
   tersembunyi, supaya sandi yang tadi ditampilkan tidak tinggal di halaman
   yang mungkin ditinggalkan pemiliknya. */
function sembunyikanSandiLagi() {
  const isian = $("sandi");
  isian.value = "";
  isian.type = "password";
  $("lihat-sandi").setAttribute("aria-pressed", "false");
  $("lihat-sandi").setAttribute("aria-label", "Tampilkan sandi");
  $("lihat-sandi").setAttribute("title", "Tampilkan sandi");
}

$("tombol-segarkan").onclick = () => { kabar(""); segarkan(); };

/* Keluarkan perangkat lain.
   Ditanyakan dulu, sebab ini memutus sesi di perangkat lain milik orang yang
   sama dan tidak bisa dibatalkan. Yang di sini sengaja disisakan: tombol yang
   ikut mengeluarkan pemiliknya akan ragu ragu ditekan, padahal justru saat
   curiga ia harus ditekan cepat. */
$("tombol-cabut-lain").onclick = async () => {
  if (!confirm("Keluarkan semua perangkat lain? Perangkat ini tetap masuk.")) return;
  const jawaban = await panggil("/api/v1/auth/sesi/cabut-lain", { method: "POST" });
  if (!jawaban.ok) { kabar(pesanGalat(await jawaban.json().catch(() => null))); return; }
  const jumlah = (await jawaban.json()).sesi_dicabut;
  kabar(jumlah ? `${jumlah} perangkat dikeluarkan` : "tidak ada perangkat lain", "baik");
  await segarkan();
};

$("tombol-masuk").onclick = masuk;
$("tombol-passkey").onclick = masukPasskey;
$("tombol-daftar-kunci").onclick = daftarkanKunci;
$("sandi").onkeydown = (e) => { if (e.key === "Enter") masuk(); };
$("keluar").onclick = keluar;
$("tombol-baru").onclick = bukaBaru;
$("tombol-kembali").onclick = muatDaftar;

/* --- menu samping ---------------------------------------------------- */

/* Tautannya sauh biasa ke #id panelnya, dan tanpa berkas ini pun ia tetap
   bekerja. Yang ditambahkan di sini hanya dua hal yang tidak bisa dikerjakan
   sauh sendirian. */
const MENU = [...document.querySelectorAll(".menu .menu__tautan")];

/* Satu: daftar tulisan dan passkey ditutup selama penyunting terbuka, dan
   sauh ke panel yang tertutup tidak membawa ke mana mana. Menunya menutup
   penyunting lewat jalan yang sama dengan tombol Kembali. */
for (const tautan of MENU) {
  tautan.addEventListener("click", async (e) => {
    const sasaran = $(tautan.hash.slice(1));
    if (!sasaran || !sasaran.classList.contains("sembunyi")) return;
    if ($("layar-sunting").classList.contains("sembunyi")) return;
    e.preventDefault();
    await muatDaftar();
    sasaran.scrollIntoView({ block: "start" });
  });
}

/* Dua: menandai panel yang sedang di layar. Pita pengamatannya sempit di
   sepertiga atas layar, supaya yang ditandai panel yang sedang dibaca, bukan
   panel yang baru mengintip di bawah. */
if ("IntersectionObserver" in window) {
  const pengamat = new IntersectionObserver((catatan) => {
    for (const c of catatan) {
      if (!c.isIntersecting) continue;
      for (const t of MENU) {
        t.setAttribute("aria-current", t.hash === "#" + c.target.id ? "true" : "false");
      }
    }
  }, { rootMargin: "-15% 0px -70% 0px" });
  for (const t of MENU) {
    const panel = $(t.hash.slice(1));
    if (panel) pengamat.observe(panel);
  }
}
$("tombol-simpan").onclick = simpan;
$("tombol-terbit").onclick = terbitkan;
$("tombol-hapus").onclick = hapus;
$("isi_en").oninput = perbarui;
$("isi_id").oninput = perbarui;

/* Tombol passkey baru muncul kalau peramban mendukungnya DAN server sudah
   dikonfigurasi. Tombol yang selalu ada lalu selalu gagal lebih buruk
   daripada tombol yang tidak ada. */
(async () => {
  if (!adaPasskey()) return;
  const siap = await fetch("/api/v1/auth/passkey/siap").then((j) => j.json()).catch(() => null);
  if (!siap || !siap.siap) return;
  $("blok-passkey").classList.remove("sembunyi");

  /* Kalau alamat halaman ini memang tidak bisa dipakai, tombolnya tetap
     terlihat tetapi mati, dan alasannya tertulis di bawahnya. Menyembunyikan
     tombolnya akan menyembunyikan sebabnya juga, lalu orang mengira passkey
     belum dipasang di server padahal ia sudah siap. */
  const halangan = kendalaPasskey();
  if (!halangan) return;
  $("tombol-passkey").disabled = true;
  const catatan = $("kendala-passkey");
  catatan.textContent = pesanKendala(halangan);
  catatan.classList.remove("sembunyi");
})();

/* Kalau cookie refresh masih hidup, langsung masuk tanpa menanyakan sandi. */
(async () => {
  const putar = await fetch("/api/v1/auth/refresh", { method: "POST", credentials: "same-origin" });
  if (!putar.ok) return;
  await sesudahMasuk(await putar.json());
})();
