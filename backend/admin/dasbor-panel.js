/* Dashboard admin, bagian 2 dari 4: panel yang menampilkan keadaan.

   Ringkasan, perangkat yang masuk, jejak keamanan, passkey, dan daftar
   tulisan. Memakai $, panggil, kabar, dan AKSES dari dasbor-inti.js, yang
   dimuat lebih dulu. Urutan keempat berkasnya ada di index.html. */

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
