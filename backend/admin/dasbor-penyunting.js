/* Dashboard admin, bagian 3 dari 4: penyunting tulisan.

   Kolom tulisan, bilah format, pustaka foto dan video, dan pratinjau yang
   dirakit server. Memakai dasbor-inti.js dan dasbor-panel.js. */

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
