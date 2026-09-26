/* Dashboard admin, bagian 4 dari 4: memasang semuanya.

   Berkas ini SELALU dimuat paling akhir. Baris di bawah jalan saat skripnya
   dimuat dan merujuk fungsi dari ketiga berkas lain, jadi ketiganya harus
   sudah terbaca. Sampai 26 September 2026 keempatnya satu berkas sepanjang
   1.237 baris; dipecah menurut bagian yang memang sudah ada di dalamnya, dan
   urutannya tidak berubah. */

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
