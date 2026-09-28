const SIMPAN_PERANGKAT = "hk-admin-perangkat";
const PILIHAN_JEDA = [
  { nilai: 0, label: "Segera" },
  { nilai: 60, label: "Setelah 1 menit" },
  { nilai: 1800, label: "Setelah 30 menit" },
];
const DIAM_SEBELUM_KELUAR_MS = 30 * 60 * 1000;
const JEDA_PERIKSA_MS = 30 * 1000;
const TENANG_SESUDAH_DIBUKA_MS = 1500;
const GERAKAN = ["pointerdown", "pointermove", "keydown", "scroll", "wheel"];

const GARIS = {
  perisai: '<path d="M12 3 5 6v5.5c0 4.3 3 7.9 7 9.5 4-1.6 7-5.2 7-9.5V6z"></path><path d="m9 12 2 2 4-4"></path>',
  lonceng: '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"></path><path d="M10 20.5a2.2 2.2 0 0 0 4 0"></path>',
  gembok: '<rect x="5" y="10.5" width="14" height="10" rx="2"></rect><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5M12 14.5v2"></path>',
  geser: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"></path><circle cx="16" cy="7" r="2"></circle><circle cx="10" cy="17" r="2"></circle>',
  jam: '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path>',
  surat: '<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m4 7 8 6 8-6"></path>',
  ponsel: '<rect x="7" y="2.5" width="10" height="19" rx="2"></rect><path d="M11 18h2"></path>',
  sidik: '<path d="M7.5 18.5c.8-1.5 1.2-3.3 1.2-5.2a3.3 3.3 0 0 1 6.6 0c0 1.2-.1 2.4-.3 3.5"></path><path d="M5 15.5c.4-1 .6-2.1.6-3.2a6.4 6.4 0 0 1 12.8 0c0 2-.3 4-.9 5.8"></path><path d="M12 13.3c0 2.6-.6 5-1.8 7.2"></path><path d="M7 5.5A8.4 8.4 0 0 1 17 5.5"></path>',
  wajah: '<circle cx="12" cy="12" r="8.5"></circle><path d="M9 10v.5M15 10v.5M9 15c1.7 1.4 4.3 1.4 6 0"></path>',
  sandi: '<path d="M4 18h16"></path><path d="M6 9v5M4 10.5l4 2M4 12.5l4-2M12 9v5M10 10.5l4 2M10 12.5l4-2M18 9v5M16 10.5l4 2M16 12.5l4-2"></path>',
  perangkat: '<rect x="4" y="5" width="16" height="11" rx="1.5"></rect><path d="M2.5 19h19"></path>',
  panah: '<path d="m9 6 6 6-6 6"></path>',
  kembali: '<path d="M19 12H5M11 6l-6 6 6 6"></path>',
  nyala: '<path d="m6.5 12.5 3.5 3.5 7.5-8"></path>',
  mati: '<path d="M7 12h10"></path>',
};

let KEADAAN = null;
let BAGIAN = "menu";
let TOTP_PASANG = null;
let KODE_PEMULIHAN = null;
let SIBUK = false;
let KABAR_KEAMANAN = null;
let KUNCI_DINILAI = false;
let TERSEMBUNYI_SEJAK = null;
let DIBUKA_PADA = 0;
let GERAK_TERAKHIR = Date.now();
let JAM_KELUAR = null;

function bacaPerangkat() {
  try {
    const isi = JSON.parse(localStorage.getItem(SIMPAN_PERANGKAT) || "null") || {};
    return {
      kunci: isi.kunci === true,
      jeda: PILIHAN_JEDA.some((p) => p.nilai === isi.jeda) ? isi.jeda : 0,
      keluarOtomatis: isi.keluarOtomatis === true,
    };
  } catch {
    return { kunci: false, jeda: 0, keluarOtomatis: false };
  }
}

function ubahPerangkat(perubahan) {
  const baru = { ...bacaPerangkat(), ...perubahan };
  try {
    localStorage.setItem(SIMPAN_PERANGKAT, JSON.stringify(baru));
  } catch {
    return;
  }
  aturKeluarOtomatis();
}

function labelJeda(jeda) {
  const p = PILIHAN_JEDA.find((x) => x.nilai === jeda);
  return p ? p.label : "Segera";
}

function akses() {
  if (!KEADAAN) return { penuh: false, bolehMendaftar: false };
  const kuat = !KEADAAN.faktor_kedua_wajib || KEADAAN.sesi_kuat;
  const punya = KEADAAN.totp_aktif || KEADAAN.passkey > 0 || KEADAAN.wajah_terdaftar;
  return { penuh: kuat, bolehMendaftar: kuat || !punya };
}

function buat(tag, kelas, teks) {
  const node = document.createElement(tag);
  if (kelas) node.className = kelas;
  if (teks !== undefined && teks !== null) node.textContent = teks;
  return node;
}

function ikon(nama, kelas) {
  const s = buat("span", kelas || "ikon-baris");
  s.setAttribute("aria-hidden", "true");
  s.innerHTML = '<svg viewBox="0 0 24 24">' + GARIS[nama] + "</svg>";
  return s;
}

function beriKabar(teks, jenis) {
  KABAR_KEAMANAN = teks ? { teks, jenis: jenis || "salah" } : null;
  const kotak = document.querySelector("#isi-keamanan .kabar-keamanan");
  if (!kotak) return;
  kotak.textContent = teks || "";
  kotak.className = "kabar kabar-keamanan " + (KABAR_KEAMANAN ? KABAR_KEAMANAN.jenis : "sembunyi");
}

function kotakKabar() {
  const k = buat("div", "kabar kabar-keamanan sembunyi");
  k.setAttribute("role", "status");
  if (KABAR_KEAMANAN) {
    k.textContent = KABAR_KEAMANAN.teks;
    k.className = "kabar kabar-keamanan " + KABAR_KEAMANAN.jenis;
  }
  return k;
}

function terkunciTeks() {
  return buat("p", "kabar salah", "Dikunci. Masuk ulang pakai authenticator atau sidik jari untuk membukanya.");
}

function pindah(ke) {
  BAGIAN = ke;
  KABAR_KEAMANAN = null;
  renderKeamanan();
  const judul = document.querySelector("#isi-keamanan h2, #isi-keamanan h3");
  if (judul) judul.focus({ preventScroll: true });
}

async function jalankan(kerja) {
  beriKabar("");
  SIBUK = true;
  renderKeamanan();
  try {
    await kerja();
  } catch (galat) {
    KABAR_KEAMANAN = { teks: galat.message || "gagal", jenis: "salah" };
  } finally {
    SIBUK = false;
    renderKeamanan();
  }
}

async function minta(jalur, pilihan) {
  const jawaban = await panggil(jalur, pilihan || {});
  const isi = await jawaban.json().catch(() => null);
  if (!jawaban.ok) throw new Error(pesanGalat(isi));
  return isi;
}

function barisMenu(nama, judul, sub, buka) {
  const li = buat("li");
  const b = buat("button", "baris-menu");
  b.type = "button";
  const teks = buat("span", "setelan-teks");
  teks.append(buat("strong", "", judul), buat("small", "", sub));
  b.append(ikon(nama), teks, ikon("panah", "panah-baris"));
  b.onclick = buka;
  li.appendChild(b);
  return li;
}

function sakelar(nyala, mati, labelId, ubah) {
  const b = buat("button", "sakelar");
  b.type = "button";
  b.setAttribute("role", "switch");
  b.setAttribute("aria-checked", String(nyala));
  b.setAttribute("aria-labelledby", labelId);
  b.disabled = Boolean(mati);
  const bulat = buat("span", "sakelar__bulat");
  bulat.setAttribute("aria-hidden", "true");
  bulat.innerHTML = '<svg viewBox="0 0 24 24">' + (nyala ? GARIS.nyala : GARIS.mati) + "</svg>";
  b.appendChild(bulat);
  b.onclick = () => ubah(!nyala);
  return b;
}

let NOMOR_LABEL = 0;
function barisSakelar(judul, keterangan, nyala, mati, ubah) {
  const li = buat("li", "baris-sakelar");
  const id = "sakelar-" + (++NOMOR_LABEL);
  const teks = buat("div", "setelan-teks");
  const kuat = buat("strong", "", judul);
  kuat.id = id;
  teks.append(kuat, buat("span", "ket-sakelar", keterangan));
  li.append(teks, sakelar(nyala, mati, id, ubah));
  return li;
}

function barisLipat(nama, judul, sub, tanda, baik, isi) {
  const li = buat("li");
  const d = buat("details", "baris-lipat");
  const ringkas = buat("summary");
  const teks = buat("span", "setelan-teks");
  teks.append(buat("strong", "", judul), buat("small", "", sub));
  ringkas.append(ikon(nama), teks);
  if (tanda) ringkas.appendChild(buat("span", "tanda" + (baik ? " terbit" : ""), tanda));
  ringkas.appendChild(ikon("panah", "panah-baris"));
  const dalam = buat("div", "lipat-isi");
  isi.forEach((n) => n && dalam.appendChild(n));
  d.append(ringkas, dalam);
  li.appendChild(d);
  return li;
}

function kepala(judul) {
  const k = buat("div", "halaman-kepala");
  const kembali = buat("button", "kembali");
  kembali.type = "button";
  kembali.setAttribute("aria-label", "Kembali");
  kembali.appendChild(ikon("kembali", "ikon-kembali"));
  kembali.onclick = () => pindah("menu");
  const h = buat("h3", "", judul);
  h.tabIndex = -1;
  k.append(kembali, h);
  return k;
}

function pahlawan(nama, teks) {
  const p = buat("div", "pahlawan");
  p.appendChild(ikon(nama, "pahlawan__ikon"));
  if (teks) p.appendChild(teks);
  return p;
}

function aksi(...tombol) {
  const d = buat("div", "aksi-baris");
  tombol.forEach((t) => t && d.appendChild(t));
  return d;
}

function tombol(teks, kelas, tekan, mati) {
  const b = buat("button", kelas || "", teks);
  b.type = "button";
  b.disabled = Boolean(mati) || SIBUK;
  b.onclick = tekan;
  return b;
}

function isianKode(id, label) {
  const i = buat("input", "isian-kode");
  i.id = id;
  i.inputMode = "numeric";
  i.autocomplete = "one-time-code";
  i.placeholder = "000000";
  i.setAttribute("aria-label", label);
  return i;
}

function halamanMenu() {
  const p = bacaPerangkat();
  const k = KEADAAN;
  const duaLangkah = k.totp_aktif || k.passkey > 0 || k.wajah_terdaftar;
  const kabarSub = k.kabar_masuk && k.kabar_perubahan ? "Email aktif"
    : (k.kabar_masuk || k.kabar_perubahan) ? "Sebagian aktif" : "Mati";
  const daftar = buat("ul", "daftar-setelan");
  daftar.append(
    barisMenu("perisai", "Verifikasi dua langkah", duaLangkah ? "Aktif" : "Belum aktif", () => pindah("dua-langkah")),
    barisMenu("lonceng", "Notifikasi keamanan", kabarSub, () => pindah("notifikasi")),
    barisMenu("gembok", "Kunci aplikasi", p.kunci ? "Sidik jari, " + labelJeda(p.jeda).toLowerCase() : "Mati", () => pindah("kunci")),
    barisMenu("geser", "Lanjutan", k.mode_ketat ? "Mode ketat aktif" : "Mode ketat mati", () => pindah("lanjutan")),
    barisMenu("jam", "Aktivitas akun", "Masuk, gagal masuk, dan perubahan", () => {
      const s = $("layar-jejak");
      if (s) s.scrollIntoView({ block: "start" });
    }),
  );
  const judul = buat("h2", "kartu__judul", "Keamanan akun");
  judul.tabIndex = -1;
  return [judul, kotakKabar(), daftar];
}

function barisEmail() {
  const k = KEADAAN;
  const isi = [buat("p", "penjelasan", "Email ini dipakai buat bantu kamu masuk kalau cara lain tidak bisa. Buktikan dulu lewat tautan yang kami kirim.")];
  if (!k.surat_siap) isi.push(buat("p", "kabar salah", "Email belum bisa dikirim. Isi SMTP_HOST, SMTP_PENGGUNA, SMTP_SANDI, dan SURAT_DARI di .env dulu."));
  isi.push(aksi(tombol(k.email_terverifikasi ? "Kirim ulang tautan" : "Kirim tautan", "", () => jalankan(async () => {
    const hasil = await minta("/api/v1/keamanan/email/kirim", { method: "POST" });
    KABAR_KEAMANAN = hasil.terkirim
      ? { teks: "Tautan sudah dikirim. Cek email kamu.", jenis: "baik" }
      : { teks: hasil.catatan, jenis: "salah" };
  }))));
  return barisLipat("surat", "Email", k.email, k.email_terverifikasi ? "terbukti" : "belum", k.email_terverifikasi, isi);
}

function barisAuthenticator() {
  const k = KEADAAN;
  const a = akses();
  const isi = [];
  if (!k.kunci_kolom_siap) isi.push(buat("p", "kabar salah", "Belum bisa dipasang. Isi KUNCI_KOLOM di .env dulu."));
  if (KODE_PEMULIHAN) {
    isi.push(buat("p", "penjelasan", "Simpan 8 kode ini sekarang. Kodenya cuma muncul sekali. Pakai kalau HP kamu hilang, dan simpan di tempat selain HP itu."));
    const grid = buat("ul", "kode-grid");
    KODE_PEMULIHAN.forEach((kode) => { const li = buat("li"); li.appendChild(buat("code", "", kode)); grid.appendChild(li); });
    isi.push(grid, aksi(tombol("Sudah saya simpan", "", () => { KODE_PEMULIHAN = null; renderKeamanan(); })));
  } else if (k.totp_aktif) {
    isi.push(buat("p", "penjelasan", "Sudah aktif. Mau matikan? Ketik kode dari aplikasi. Kode cadangan ikut terhapus."));
    if (!a.penuh) isi.push(terkunciTeks());
    const kode = isianKode("kode-matikan", "Kode dari aplikasi");
    isi.push(aksi(kode, tombol("Matikan", "bahaya", () => jalankan(async () => {
      await minta("/api/v1/keamanan/totp/matikan", { method: "POST", body: JSON.stringify({ kode: kode.value.trim() }) });
      KABAR_KEAMANAN = { teks: "Authenticator dimatikan. Kode cadangan ikut terhapus.", jenis: "baik" };
      await muatKeamanan();
    }), !a.penuh)));
  } else if (TOTP_PASANG) {
    isi.push(buat("p", "penjelasan", "Pindai kode ini pakai aplikasi authenticator, lalu ketik 6 angkanya."));
    const qr = buat("div", "qr");
    const svg = new DOMParser().parseFromString(TOTP_PASANG.qr || "", "image/svg+xml").documentElement;
    if (svg && svg.nodeName === "svg") qr.appendChild(document.importNode(svg, true));
    const cadangan = buat("p", "ket", "Tidak bisa memindai? Ketik kode ini: ");
    cadangan.appendChild(buat("code", "", TOTP_PASANG.rahasia));
    const kode = isianKode("kode-totp", "Enam angka dari aplikasi");
    isi.push(qr, cadangan, aksi(kode, tombol("Aktifkan", "utama", () => jalankan(async () => {
      const hasil = await minta("/api/v1/keamanan/totp/aktifkan", { method: "POST", body: JSON.stringify({ kode: kode.value.trim() }) });
      KODE_PEMULIHAN = hasil.kode_pemulihan;
      TOTP_PASANG = null;
      await muatKeamanan();
    })), tombol("Batal", "", () => { TOTP_PASANG = null; renderKeamanan(); })));
  } else {
    isi.push(buat("p", "penjelasan", "Kode 6 angka dari aplikasi di HP kamu, berganti tiap 30 detik. Bisa pakai Aegis, Google Authenticator, atau 1Password."));
    if (!a.bolehMendaftar) isi.push(terkunciTeks());
    isi.push(aksi(tombol("Pasang authenticator", "utama", () => jalankan(async () => {
      TOTP_PASANG = await minta("/api/v1/keamanan/totp/mulai", { method: "POST" });
    }), !a.bolehMendaftar || !k.kunci_kolom_siap)));
  }
  const sub = k.totp_aktif ? "Aktif, " + k.pemulihan_sisa + " kode cadangan tersisa" : "Belum dipasang";
  const baris = barisLipat("ponsel", "Aplikasi authenticator", sub, k.totp_aktif ? "aktif" : "belum", k.totp_aktif, isi);
  if (TOTP_PASANG || KODE_PEMULIHAN) baris.querySelector("details").open = true;
  return baris;
}

function barisPasskey() {
  const k = KEADAAN;
  const isi = [
    buat("p", "penjelasan", "Masuk pakai sidik jari, wajah di HP, atau PIN perangkat. Kuncinya tidak pernah keluar dari perangkat kamu."),
    aksi(tombol("Kelola sidik jari", "", () => {
      const s = $("layar-kunci");
      if (s) { s.classList.remove("sembunyi"); s.scrollIntoView({ block: "start" }); }
    })),
  ];
  return barisLipat("sidik", "Sidik jari dan passkey", k.passkey ? k.passkey + " perangkat terdaftar" : "Belum ada",
    k.passkey ? "aktif" : "belum", k.passkey > 0, isi);
}

function barisWajah() {
  const k = KEADAAN;
  const a = akses();
  const isi = [
    buat("p", "penjelasan", "Kamera ambil 3 foto sambil kamu menoleh. Fotonya tidak disimpan, cuma 128 angka yang dikunci."),
    buat("p", "penjelasan", "Perlu kamu tahu: cara ini bisa ditembus rekaman video wajah kamu. Yang paling aman tetap sidik jari."),
  ];
  if (k.wajah_terdaftar) {
    if (!a.penuh) isi.push(terkunciTeks());
    isi.push(aksi(tombol("Hapus wajah", "bahaya", () => jalankan(async () => {
      await minta("/api/v1/keamanan/wajah/hapus", { method: "POST" });
      KABAR_KEAMANAN = { teks: "Wajah sudah dihapus dari server.", jenis: "baik" };
      await muatKeamanan();
    }), !a.penuh)));
  } else {
    isi.push(buat("p", "ket", "Daftarkan wajah lewat dashboard Next, sebab butuh kamera. Dashboard ini hanya bisa menghapusnya."));
  }
  return barisLipat("wajah", "Verifikasi wajah", k.wajah_terdaftar ? "Aktif" : "Belum didaftarkan",
    k.wajah_terdaftar ? "aktif" : "belum", k.wajah_terdaftar, isi);
}

function halamanDuaLangkah() {
  const k = KEADAAN;
  const aktif = k.totp_aktif || k.passkey > 0 || k.wajah_terdaftar;
  const status = buat("div", "status-baris");
  status.append(buat("strong", "", "Verifikasi dua langkah"), buat("span", "tanda" + (aktif ? " terbit" : ""), aktif ? "aktif" : "belum aktif"));
  const metode = buat("ul", "daftar-setelan");
  metode.append(
    barisEmail(),
    barisAuthenticator(),
    barisPasskey(),
    barisWajah(),
    barisLipat("sandi", "Kata sandi", "••••••••••", k.punya_sandi ? "aktif" : "belum", k.punya_sandi,
      [buat("p", "penjelasan", "Sandi dipakai di langkah pertama. Untuk menggantinya, jalankan python backend/db/buat_admin.py di server.")]),
  );
  const perangkat = buat("ul", "daftar-setelan");
  perangkat.appendChild(barisMenu("perangkat", "Perangkat yang masuk", "Lihat dan keluarkan perangkat", () => {
    const s = $("layar-perangkat");
    if (s) s.scrollIntoView({ block: "start" });
  }));
  return [
    kepala("Verifikasi dua langkah"),
    pahlawan("perisai", buat("p", "penjelasan", "Tambah lapisan pengaman. Selain sandi, kamu butuh satu cara lagi untuk masuk.")),
    kotakKabar(), status, buat("p", "label-bagian", "Metode verifikasi"), metode,
    buat("p", "label-bagian", "Perangkat tepercaya"), perangkat,
  ];
}

async function ubahSetelan(perubahan, pesan) {
  await jalankan(async () => {
    await minta("/api/v1/keamanan/setelan", { method: "PATCH", body: JSON.stringify(perubahan) });
    await muatKeamanan();
    KABAR_KEAMANAN = { teks: pesan, jenis: "baik" };
  });
}

function halamanNotifikasi() {
  const k = KEADAAN;
  const mati = SIBUK || !akses().penuh;
  const simpan = k.surat_siap ? "Tersimpan. Kami juga kirim email soal perubahan ini." : "Tersimpan.";
  const pengantar = buat("p", "penjelasan", "Kami kirim email ke ");
  pengantar.append(buat("strong", "", k.email), document.createTextNode(" kalau ada hal penting di akun kamu."));
  const daftar = buat("ul", "daftar-setelan");
  daftar.append(
    barisSakelar("Masuk dari perangkat baru", "Dapat email kalau akun kamu dibuka dari HP atau laptop yang belum pernah dipakai.",
      k.kabar_masuk, mati, (nilai) => ubahSetelan({ kabar_masuk: nilai }, simpan)),
    barisSakelar("Perubahan keamanan", "Dapat email kalau authenticator, sidik jari, atau wajah ditambah atau dihapus.",
      k.kabar_perubahan, mati, (nilai) => ubahSetelan({ kabar_perubahan: nilai }, simpan)),
  );
  const hasil = [kepala("Notifikasi keamanan"), pahlawan("lonceng", pengantar), kotakKabar()];
  if (!k.surat_siap) hasil.push(buat("p", "kabar salah", "Email belum bisa dikirim. Isi SMTP_HOST dan SURAT_DARI di .env dulu."));
  if (!akses().penuh) hasil.push(terkunciTeks());
  hasil.push(daftar, buat("p", "ket", "Mematikan notifikasi juga selalu dikabarkan lewat email. Jadi orang lain tidak bisa mematikannya diam diam."));
  return hasil;
}

function halamanKunci() {
  const k = KEADAAN;
  const p = bacaPerangkat();
  const halangan = adaPasskey() ? kendalaPasskey() : null;
  const bisa = k.passkey > 0 && adaPasskey() && !halangan;
  const daftar = buat("ul", "daftar-setelan");
  daftar.appendChild(barisSakelar("Buka kunci pakai sidik jari",
    "Kalau nyala, dashboard harus dibuka pakai sidik jari, wajah di HP, atau PIN perangkat.",
    p.kunci, SIBUK || (!p.kunci && !bisa), (nilai) => {
      if (!nilai) {
        ubahPerangkat({ kunci: false });
        KABAR_KEAMANAN = { teks: "Kunci aplikasi dimatikan di perangkat ini.", jenis: "baik" };
        renderKeamanan();
        return;
      }
      jalankan(async () => {
        try {
          await bukaKunciLayar();
        } catch (galat) {
          if (galat && (galat.name === "NotAllowedError" || galat.name === "AbortError")) return;
          throw galat;
        }
        ubahPerangkat({ kunci: true });
        KABAR_KEAMANAN = { teks: "Kunci aplikasi nyala. Buka pakai sidik jari tiap kali terkunci.", jenis: "baik" };
      });
    }));
  const hasil = [kepala("Kunci aplikasi"), kotakKabar(), daftar];
  if (k.passkey === 0) hasil.push(buat("p", "ket", "Daftarkan sidik jari dulu di Verifikasi dua langkah."));
  else if (halangan) hasil.push(buat("p", "ket", pesanKendala(halangan)));
  else if (!adaPasskey()) hasil.push(buat("p", "ket", "Browser ini belum bisa membaca sidik jari."));
  hasil.push(buat("p", "label-bagian", "Kunci secara otomatis"));
  const pilihan = buat("fieldset", "pilihan-jeda");
  pilihan.disabled = !p.kunci;
  const legenda = buat("legend", "tersembunyi", "Kunci secara otomatis");
  pilihan.appendChild(legenda);
  PILIHAN_JEDA.forEach((j) => {
    const label = buat("label", "radio");
    const r = buat("input");
    r.type = "radio";
    r.name = "jeda-kunci";
    r.value = String(j.nilai);
    r.checked = p.jeda === j.nilai;
    r.onchange = () => { ubahPerangkat({ jeda: j.nilai }); renderKeamanan(); };
    label.append(r, buat("span", "", j.label));
    pilihan.appendChild(label);
  });
  hasil.push(pilihan, buat("p", "ket", "Waktunya dihitung sejak kamu pindah ke tab atau aplikasi lain. Setelan ini cuma berlaku di perangkat ini."));
  return hasil;
}

function halamanLanjutan() {
  const k = KEADAAN;
  const p = bacaPerangkat();
  const kuat = k.totp_aktif || k.passkey > 0;
  const daftar = buat("ul", "daftar-setelan");
  daftar.append(
    barisSakelar("Mode ketat", "Masuk cuma bisa pakai authenticator atau sidik jari. Wajah tidak bisa lagi dipakai untuk masuk.",
      k.mode_ketat, SIBUK || !akses().penuh || (!k.mode_ketat && !kuat),
      (nilai) => ubahSetelan({ mode_ketat: nilai }, nilai ? "Mode ketat nyala." : "Mode ketat dimatikan.")),
    barisSakelar("Keluar otomatis", "Keluar sendiri kalau dashboard tidak dipakai 30 menit. Berlaku di perangkat ini.",
      p.keluarOtomatis, false, (nilai) => { ubahPerangkat({ keluarOtomatis: nilai }); renderKeamanan(); }),
  );
  const hasil = [kepala("Lanjutan"), kotakKabar()];
  if (!akses().penuh) hasil.push(terkunciTeks());
  hasil.push(daftar);
  if (!kuat) hasil.push(buat("p", "ket", "Mode ketat butuh authenticator atau sidik jari. Pasang salah satunya dulu."));
  return hasil;
}

function renderKeamanan() {
  const wadah = $("isi-keamanan");
  if (!wadah) return;
  if (!KEADAAN) {
    wadah.replaceChildren(buat("p", "ket", "Sebentar..."));
    return;
  }
  const halaman = {
    "menu": halamanMenu,
    "dua-langkah": halamanDuaLangkah,
    "notifikasi": halamanNotifikasi,
    "kunci": halamanKunci,
    "lanjutan": halamanLanjutan,
  }[BAGIAN] || halamanMenu;
  const bagian = buat("div", "halaman-keamanan");
  halaman().forEach((n) => n && bagian.appendChild(n));
  wadah.replaceChildren(bagian);
}

async function muatKeamanan() {
  const jawaban = await panggil("/api/v1/keamanan");
  if (!jawaban.ok) {
    const wadah = $("isi-keamanan");
    if (wadah) wadah.replaceChildren(buat("p", "kabar salah", pesanGalat(await jawaban.json().catch(() => null))));
    return;
  }
  KEADAAN = await jawaban.json();
  renderKeamanan();
  if (!KUNCI_DINILAI) {
    KUNCI_DINILAI = true;
    const p = bacaPerangkat();
    if (p.kunci && KEADAAN.passkey > 0) kunciLayar();
  }
  aturKeluarOtomatis();
}

async function konfirmasiDariAlamat() {
  const alamat = new URL(location.href);
  const fragmen = new URLSearchParams(alamat.hash.slice(1));
  const token = fragmen.get("verifikasi") || alamat.searchParams.get("verifikasi");
  if (!token) return;
  alamat.searchParams.delete("verifikasi");
  alamat.hash = "";
  history.replaceState(null, "", alamat.toString());
  try {
    await minta("/api/v1/keamanan/email/konfirmasi", { method: "POST", body: JSON.stringify({ token }) });
    KABAR_KEAMANAN = { teks: "Email kamu sudah terbukti.", jenis: "baik" };
    await muatKeamanan();
  } catch (galat) {
    KABAR_KEAMANAN = { teks: galat.message || "Tautan tidak berlaku.", jenis: "salah" };
    renderKeamanan();
  }
}

async function bukaKunciLayar() {
  const awal = await minta("/api/v1/auth/passkey/buka/mulai", { method: "POST" });
  const pilihan = JSON.parse(awal.pilihan);
  pilihan.challenge = keBuffer(pilihan.challenge);
  for (const k of pilihan.allowCredentials || []) k.id = keBuffer(k.id);
  const kredensial = await navigator.credentials.get({ publicKey: pilihan });
  await minta("/api/v1/auth/passkey/buka/selesai", {
    method: "POST",
    body: JSON.stringify({ jawaban: {
      id: kredensial.id,
      rawId: keTeks(kredensial.rawId),
      type: kredensial.type,
      response: {
        clientDataJSON: keTeks(kredensial.response.clientDataJSON),
        authenticatorData: keTeks(kredensial.response.authenticatorData),
        signature: keTeks(kredensial.response.signature),
        userHandle: kredensial.response.userHandle ? keTeks(kredensial.response.userHandle) : null,
      },
      clientExtensionResults: kredensial.getClientExtensionResults(),
    } }),
  });
}

function kunciLayar() {
  const layar = $("kunci-layar");
  if (!layar || !AKSES) return;
  $("kabar-kunci").classList.add("sembunyi");
  layar.classList.remove("sembunyi");
  document.body.classList.add("terkunci");
  $("tombol-buka-kunci").focus();
}

function bukaLayar() {
  DIBUKA_PADA = Date.now();
  TERSEMBUNYI_SEJAK = null;
  $("kunci-layar").classList.add("sembunyi");
  document.body.classList.remove("terkunci");
}

async function tekanBukaKunci() {
  const tombolBuka = $("tombol-buka-kunci");
  const kabarKunci = $("kabar-kunci");
  kabarKunci.classList.add("sembunyi");
  tombolBuka.disabled = true;
  tombolBuka.textContent = "Sebentar...";
  try {
    await bukaKunciLayar();
    bukaLayar();
  } catch (galat) {
    if (!galat || (galat.name !== "NotAllowedError" && galat.name !== "AbortError")) {
      kabarKunci.textContent = (galat && galat.message) || "Sidik jari tidak terbaca.";
      kabarKunci.classList.remove("sembunyi");
    }
  } finally {
    tombolBuka.disabled = false;
    tombolBuka.textContent = "Buka kunci";
  }
}

document.addEventListener("visibilitychange", () => {
  const p = bacaPerangkat();
  if (!p.kunci || !AKSES) return;
  if (document.visibilityState === "hidden") {
    TERSEMBUNYI_SEJAK = Date.now();
    return;
  }
  const baruDibuka = Date.now() - DIBUKA_PADA < TENANG_SESUDAH_DIBUKA_MS;
  if (!baruDibuka && TERSEMBUNYI_SEJAK !== null && Date.now() - TERSEMBUNYI_SEJAK >= p.jeda * 1000) kunciLayar();
  TERSEMBUNYI_SEJAK = null;
});

function catatGerak() {
  GERAK_TERAKHIR = Date.now();
}

function periksaDiam() {
  if (AKSES && bacaPerangkat().keluarOtomatis && Date.now() - GERAK_TERAKHIR >= DIAM_SEBELUM_KELUAR_MS) keluar();
}

function aturKeluarOtomatis() {
  const nyala = bacaPerangkat().keluarOtomatis && Boolean(AKSES);
  if (nyala && !JAM_KELUAR) {
    GERAK_TERAKHIR = Date.now();
    for (const jenis of GERAKAN) window.addEventListener(jenis, catatGerak, { passive: true });
    document.addEventListener("visibilitychange", periksaDiam);
    JAM_KELUAR = setInterval(periksaDiam, JEDA_PERIKSA_MS);
  } else if (!nyala && JAM_KELUAR) {
    for (const jenis of GERAKAN) window.removeEventListener(jenis, catatGerak);
    document.removeEventListener("visibilitychange", periksaDiam);
    clearInterval(JAM_KELUAR);
    JAM_KELUAR = null;
  }
}

window.addEventListener("storage", (e) => {
  if (e.key === SIMPAN_PERANGKAT) {
    aturKeluarOtomatis();
    renderKeamanan();
  }
});
