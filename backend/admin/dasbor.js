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
  try { isian.setSelectionRange(mulai, akhir); } catch {  }
};

function sembunyikanSandiLagi() {
  const isian = $("sandi");
  isian.value = "";
  isian.type = "password";
  $("lihat-sandi").setAttribute("aria-pressed", "false");
  $("lihat-sandi").setAttribute("aria-label", "Tampilkan sandi");
  $("lihat-sandi").setAttribute("title", "Tampilkan sandi");
}

$("tombol-segarkan").onclick = () => { kabar(""); segarkan(); };

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


const MENU = [...document.querySelectorAll(".menu .menu__tautan")];

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

(async () => {
  if (!adaPasskey()) return;
  const siap = await fetch("/api/v1/auth/passkey/siap").then((j) => j.json()).catch(() => null);
  if (!siap || !siap.siap) return;
  $("blok-passkey").classList.remove("sembunyi");

  const halangan = kendalaPasskey();
  if (!halangan) return;
  $("tombol-passkey").disabled = true;
  const catatan = $("kendala-passkey");
  catatan.textContent = pesanKendala(halangan);
  catatan.classList.remove("sembunyi");
})();

(async () => {
  const putar = await fetch("/api/v1/auth/refresh", { method: "POST", credentials: "same-origin" });
  if (!putar.ok) return;
  await sesudahMasuk(await putar.json());
})();
