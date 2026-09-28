(function () {
  "use strict";

  var DATA = window.HK_PARKIR_DATA;
  var TOKEN = (window.HK_KONFIG && window.HK_KONFIG.mapboxToken) || "";
  var AMBANG_M = 30;
  var PUSAT = [110.3657, -7.7949];
  var BATAS = [[109.95, -8.2], [110.8, -7.45]];
  var JAM_MAKS = 24;

  var WARNA = {
    terang: { I: "#9e2b25", II: "#8a5500", aset: "#1e7b34", halo: "#ffffff", sorot: "#202124" },
    gelap: { I: "#ff8a80", II: "#fdd663", aset: "#8fd9a8", halo: "#1f2023", sorot: "#e8eaed" }
  };

  var KENDARAAN = {
    "Sepeda motor": { en: "Motorbike", ind: "Motor" },
    "Sedan, jip, pickup, station wagon, kendaraan roda tiga": { en: "Car", ind: "Mobil" },
    "Truk sedang atau box": { en: "Medium truck", ind: "Truk sedang" },
    "Truk besar": { en: "Large truck", ind: "Truk besar" },
    "Truk gandengan sumbu III atau lebih": { en: "Trailer truck", ind: "Truk gandeng" },
    "Bus sedang": { en: "Medium bus", ind: "Bus sedang" },
    "Bus besar": { en: "Large bus", ind: "Bus besar" },
    "Sepeda listrik": { en: "E-bike", ind: "Sepeda listrik" },
    "Sepeda": { en: "Bicycle", ind: "Sepeda" },
    "Andong": { en: "Horse cart", ind: "Andong" },
    "Becak": { en: "Pedicab", ind: "Becak" }
  };

  var LAYANAN = {
    reguler: { en: "Regular", ind: "Biasa" },
    insidental: { en: "Event", ind: "Acara" },
    pasar: { en: "Market", ind: "Pasar" }
  };

  var TEXT = {
    search: { en: "Search a street", ind: "Cari nama jalan" },
    clear: { en: "Clear", ind: "Hapus" },
    noMatch: { en: "No street called “%q”", ind: "Jalan “%q” tidak ketemu" },
    zone: { en: "Zone %k", ind: "Kawasan %k" },
    fromStreet: { en: "%m m from the street", ind: "%m m dari jalan" },
    zoneThree: { en: "Zone III street", ind: "Jalan Kawasan III" },
    zoneThreeNote: { en: "The cheapest zone", ind: "Kawasan paling murah" },
    outside: { en: "Outside Yogyakarta city", ind: "Di luar Kota Yogyakarta" },
    outsideNote: {
      en: "These fees only apply in Yogyakarta city, so there is no fee here.",
      ind: "Tarif ini cuma berlaku di Kota Yogyakarta, jadi di sini tidak ada tarifnya."
    },
    once: { en: "Zone %k. Pay once, however long you stay.", ind: "Kawasan %k. Bayar sekali, berapa lama pun." },
    market: { en: "Market fee. Pay once each visit.", ind: "Tarif pasar. Bayar sekali tiap parkir." },
    firstTwo: { en: "Rp%a for the first 2 hours", ind: "Rp%a untuk 2 jam pertama" },
    thenHours: { en: ", then %j h × Rp%b", ind: ", lalu %j jam × Rp%b" },
    proposal: {
      en: "This street is only proposed for Zone I and not decided yet. Check the fee board on site.",
      ind: "Jalan ini baru diusulkan masuk Kawasan I dan belum ditetapkan. Cek papan tarif di lokasi, ya."
    },
    vehicle: { en: "Vehicle", ind: "Kendaraan" },
    hours: { en: "How long", ind: "Lama parkir" },
    hourUnit: { en: "%j h", ind: "%j jam" },
    less: { en: "1 hour less", ind: "Kurangi 1 jam" },
    more: { en: "1 hour more", ind: "Tambah 1 jam" },
    service: { en: "Parking type", ind: "Jenis parkir" },
    legendOne: { en: "Zone I", ind: "Kawasan I" },
    legendTwo: { en: "Zone II", ind: "Kawasan II" },
    legendProposal: { en: "Still a proposal", ind: "Masih usulan" },
    legendAsset: { en: "Provincial parking", ind: "Parkir Pemda DIY" },
    legendRest: { en: "Other streets in the city are Zone III.", ind: "Jalan lain di kota masuk Kawasan III." },
    assetNote: {
      en: "Fees here are different, set by Pergub DIY 46/2024.",
      ind: "Tarif di sini beda, diatur Pergub DIY 46/2024."
    },
    spaces: { en: "%n motorbike spots", ind: "%n tempat motor" },
    announce: { en: "%r. %f.", ind: "%r. %f." },
    noFee: { en: "No fee listed", ind: "Tarif tidak tersedia" },
    zoomIn: { en: "Zoom in", ind: "Perbesar" },
    zoomOut: { en: "Zoom out", ind: "Perkecil" },
    north: { en: "Face north", ind: "Hadap utara" },
    full: { en: "Full screen", ind: "Layar penuh" },
    unfull: { en: "Exit full screen", ind: "Keluar layar penuh" },
    close: { en: "Close", ind: "Tutup" },
    legend: { en: "Map key", ind: "Keterangan" },
    legendTitle: { en: "Map key", ind: "Keterangan peta" },
    legendHint: { en: "Tap to show or hide.", ind: "Ketuk untuk tampilkan atau sembunyikan." },
    legendHide: { en: "Close", ind: "Tutup" },
    moreDetails: { en: "Show options", ind: "Tampilkan pilihan" },
    lessDetails: { en: "Hide options", ind: "Sembunyikan pilihan" },
    nearest: { en: "Nearest provincial parking", ind: "Parkir Pemda DIY terdekat" },
    here: { en: "here", ind: "di sini" },
    goThere: { en: "Go to %n, %d", ind: "Ke %n, %d" }
  };

  function isId() {
    return document.documentElement.getAttribute("lang") === "id";
  }

  function say(entry) {
    return isId() ? entry.ind : entry.en;
  }

  function temaGelap() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function sentuh() {
    return Boolean(window.matchMedia
      && window.matchMedia("(hover: none) and (pointer: coarse)").matches);
  }

  function reducedMotion() {
    return Boolean(window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function rupiah(n) {
    return Number(n).toLocaleString(isId() ? "id-ID" : "en-US");
  }

  function el(tag, kelas, teks) {
    var node = document.createElement(tag);
    if (kelas) node.className = kelas;
    if (teks) node.textContent = teks;
    return node;
  }

  function polos(teks) {
    return String(teks || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function meterPerDerajat(lat) {
    return { x: 111320 * Math.cos(lat * Math.PI / 180), y: 110540 };
  }

  function jarakKeSegmen(p, a, b, m) {
    var px = (p[0] - a[0]) * m.x;
    var py = (p[1] - a[1]) * m.y;
    var bx = (b[0] - a[0]) * m.x;
    var by = (b[1] - a[1]) * m.y;
    var kuadrat = bx * bx + by * by;
    var t = kuadrat === 0 ? 0 : Math.max(0, Math.min(1, (px * bx + py * by) / kuadrat));
    return Math.hypot(px - t * bx, py - t * by);
  }

  function diDalamCincin(x, y, cincin) {
    var dalam = false;
    for (var i = 0, j = cincin.length - 1; i < cincin.length; j = i++) {
      var x1 = cincin[j][0], y1 = cincin[j][1], x2 = cincin[i][0], y2 = cincin[i][1];
      if ((y1 > y) !== (y2 > y) && x < x1 + (y - y1) * (x2 - x1) / (y2 - y1)) dalam = !dalam;
    }
    return dalam;
  }

  function diDalamCakupan(lat, lon) {
    var cincin = DATA.cakupan.geometry.coordinates;
    if (!diDalamCincin(lon, lat, cincin[0])) return false;
    for (var i = 1; i < cincin.length; i++) {
      if (diDalamCincin(lon, lat, cincin[i])) return false;
    }
    return true;
  }

  function cariKawasan(lat, lon) {
    if (!diDalamCakupan(lat, lon)) {
      return { kawasan: null, ruas: null, jarak: null, usulan: false, luar: true, fitur: null };
    }
    var m = meterPerDerajat(lat);
    var terbaik = { jarak: Infinity, fitur: null };
    DATA.kawasan.features.forEach(function (fitur, indeks) {
      var c = fitur.geometry.coordinates;
      for (var i = 0; i < c.length - 1; i++) {
        var d = jarakKeSegmen([lon, lat], c[i], c[i + 1], m);
        if (d < terbaik.jarak) terbaik = { jarak: d, fitur: indeks };
      }
    });
    if (terbaik.jarak > AMBANG_M) {
      return { kawasan: "III", ruas: null, jarak: null, usulan: false, luar: false, fitur: null };
    }
    var p = DATA.kawasan.features[terbaik.fitur].properties;
    return {
      kawasan: p.k, ruas: p.n, jarak: Math.round(terbaik.jarak * 10) / 10,
      usulan: p.u === 1, luar: false, fitur: terbaik.fitur
    };
  }

  function cariTarif(kendaraan, kawasan, layanan) {
    var kw = layanan === "pasar" ? "-" : kawasan;
    for (var i = 0; i < DATA.tarif.length; i++) {
      var t = DATA.tarif[i];
      if (t.layanan === layanan && t.kendaraan === kendaraan && t.kawasan === kw) return t;
    }
    return null;
  }

  function hitungTarif(kendaraan, kawasan, jam, layanan) {
    if (!kawasan) return null;
    var baris = cariTarif(kendaraan, kawasan, layanan);
    if (!baris) return null;
    var awal = baris.tarif_2jam_pertama;
    var lanjut = baris.tarif_per_jam_lanjut;
    if (!baris.progresif || lanjut === null) {
      return { total: awal, progresif: false, jamLanjut: 0, awal: awal, lanjut: null };
    }
    var jamLanjut = Math.max(Math.ceil(jam) - 2, 0);
    return { total: awal + jamLanjut * lanjut, progresif: true, jamLanjut: jamLanjut, awal: awal, lanjut: lanjut };
  }

  var DAFTAR_KENDARAAN = Object.keys(KENDARAAN).filter(function (nama) {
    return DATA.tarif.some(function (t) { return t.kendaraan === nama; });
  });

  var DAFTAR_RUAS = (function () {
    var per = {};
    DATA.kawasan.features.forEach(function (fitur) {
      var nama = fitur.properties.n;
      var c = fitur.geometry.coordinates;
      var panjang = 0;
      for (var i = 0; i < c.length - 1; i++) panjang += Math.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1]);
      if (!per[nama] || panjang > per[nama].panjang) {
        var tengah = c[Math.floor((c.length - 1) / 2)];
        var berikut = c[Math.min(c.length - 1, Math.floor((c.length - 1) / 2) + 1)];
        per[nama] = {
          nama: nama, panjang: panjang,
          titik: [(tengah[0] + berikut[0]) / 2, (tengah[1] + berikut[1]) / 2]
        };
      }
    });
    return Object.keys(per).sort().map(function (nama) { return per[nama]; });
  })();

  function geojsonAset() {
    return {
      type: "FeatureCollection",
      features: DATA.titik.map(function (t, i) {
        return {
          type: "Feature",
          id: i,
          geometry: { type: "Point", coordinates: [t.lon, t.lat] },
          properties: { i: i }
        };
      })
    };
  }

  var SIMPAN = "hk-parkir";

  function bacaSetelan() {
    try {
      var nilai = JSON.parse(window.localStorage.getItem(SIMPAN) || "{}");
      return nilai && typeof nilai === "object" ? nilai : {};
    } catch (e) {
      return {};
    }
  }

  function simpanSetelan(kunci, nilai) {
    var setelan = bacaSetelan();
    setelan[kunci] = nilai;
    try {
      window.localStorage.setItem(SIMPAN, JSON.stringify(setelan));
    } catch (e) {
      return;
    }
  }

  function susun(induk, anak) {
    anak.forEach(function (a) { induk.appendChild(a); });
    return induk;
  }

  function ikon(kelas, svg) {
    var node = el("span", "parkir__ikon" + (kelas ? " " + kelas : ""));
    node.setAttribute("aria-hidden", "true");
    node.innerHTML = svg;
    return node;
  }

  function kedip(node, kelas) {
    node.classList.remove(kelas);
    void node.offsetWidth;
    node.classList.add(kelas);
  }

  function jarakTeks(meter) {
    if (meter < 15) return say(TEXT.here);
    if (meter < 1000) return rupiah(Math.round(meter / 10) * 10) + " m";
    return (meter / 1000).toLocaleString(isId() ? "id-ID" : "en-US", { maximumFractionDigits: 1 }) + " km";
  }

  function asetTerdekat(lat, lon) {
    var m = meterPerDerajat(lat);
    var terbaik = null;
    DATA.titik.forEach(function (t, i) {
      var d = Math.hypot((t.lon - lon) * m.x, (t.lat - lat) * m.y);
      if (!terbaik || d < terbaik.jarak) terbaik = { indeks: i, jarak: d };
    });
    return terbaik;
  }

  var DEKAT_M = 2500;

  var LEGENDA = [
    { kunci: "I", tanda: "parkir__garis parkir__garis--satu", teks: "legendOne" },
    { kunci: "II", tanda: "parkir__garis parkir__garis--dua", teks: "legendTwo" },
    { kunci: "usulan", tanda: "parkir__garis parkir__garis--usulan", teks: "legendProposal" },
    { kunci: "aset", tanda: "parkir__bulatan", teks: "legendAsset" }
  ];

  var IKON = {
    cari: '<svg viewBox="0 0 24 24" focusable="false"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>',
    hapus: '<svg viewBox="0 0 24 24" focusable="false"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"></path></svg>',
    lapis: '<svg viewBox="0 0 24 24" focusable="false"><path d="m11.99 18.54-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"></path></svg>',
    lipat: '<svg viewBox="0 0 24 24" focusable="false"><path d="M7.41 15.41 12 10.83l4.59 4.58L18 14l-6-6-6 6z"></path></svg>',
    tempat: '<svg viewBox="0 0 24 24" focusable="false"><path d="M13 3H6v18h4v-6h3c3.31 0 6-2.69 6-6s-2.69-6-6-6zm.2 8H10V7h3.2c1.1 0 2 .9 2 2s-.9 2-2 2z"></path></svg>',
    cek: '<svg viewBox="0 0 24 24" focusable="false"><path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"></path></svg>'
  };

  function lapisanParkir(w, tampil) {
    var tebal = ["interpolate", ["linear"], ["zoom"], 12, 2, 15, 4.5, 18, 9];
    var tebalHalo = ["interpolate", ["linear"], ["zoom"], 12, 4, 15, 7.5, 18, 13];
    var tebalSorot = ["interpolate", ["linear"], ["zoom"], 12, 9, 15, 14, 18, 22];
    var warna = ["match", ["get", "k"], "I", w.I, w.II];
    var zona = ["I", "II"].filter(function (k) { return tampil[k]; });
    var tetap = ["all", ["==", ["get", "u"], 0], ["in", ["get", "k"], ["literal", zona]]];
    var usul = ["all", ["==", ["get", "u"], 1], Boolean(tampil.usulan)];
    return [
      { id: "parkir-sorot", type: "line", source: "parkir-terpilih",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": w.sorot, "line-opacity": 0.22, "line-width": tebalSorot } },
      { id: "parkir-halo", type: "line", source: "parkir", filter: ["any", tetap, usul],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": w.halo, "line-width": tebalHalo } },
      { id: "parkir-tetap", type: "line", source: "parkir", filter: tetap,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": warna, "line-width": tebal } },
      { id: "parkir-usulan", type: "line", source: "parkir", filter: usul,
        layout: { "line-cap": "butt", "line-join": "round" },
        paint: { "line-color": warna, "line-width": tebal, "line-dasharray": [0.6, 1.2] } },
      { id: "parkir-aset", type: "circle", source: "parkir-aset",
        layout: { visibility: tampil.aset ? "visible" : "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 5, 17, 9],
          "circle-color": w.aset,
          "circle-stroke-color": w.halo,
          "circle-stroke-width": 2.5
        } }
    ];
  }

  function build(container) {
    var frame = container.parentNode;
    var section = frame.closest("[data-parkir]");
    var map = null;
    var dasarCadangan = null;
    var setelan = bacaSetelan();
    var layarLebar = window.matchMedia("(min-width: 860px)");
    var keadaan = {
      kendaraan: "Sepeda motor", layanan: "reguler", jam: 1,
      posisi: null, titik: PUSAT, gelap: temaGelap(),
      tampil: { I: true, II: true, usulan: true, aset: true },
      legenda: typeof setelan.legenda === "boolean"
        ? setelan.legenda
        : window.matchMedia("(min-width: 1200px)").matches,
      ringkas: setelan.ringkas === true
    };

    var samping = el("div", "parkir__samping");
    var cari = el("div", "parkir__cari");
    cari.setAttribute("role", "search");
    var isian = el("input", "parkir__cari-isian");
    isian.type = "search";
    isian.id = "parkir-cari";
    isian.autocomplete = "off";
    isian.spellcheck = false;
    isian.setAttribute("role", "combobox");
    isian.setAttribute("aria-autocomplete", "list");
    isian.setAttribute("aria-expanded", "false");
    isian.setAttribute("aria-controls", "parkir-saran");
    var hapus = el("button", "parkir__cari-hapus");
    hapus.type = "button";
    hapus.hidden = true;
    hapus.appendChild(ikon("", IKON.hapus));
    var saran = el("ul", "parkir__saran");
    saran.id = "parkir-saran";
    saran.setAttribute("role", "listbox");
    saran.hidden = true;
    susun(cari, [ikon("parkir__cari-ikon", IKON.cari), isian, hapus, saran]);

    var kartu = el("div", "parkir__kartu");
    var lipat = el("button", "parkir__lipat");
    lipat.type = "button";
    lipat.setAttribute("aria-controls", "parkir-atur");
    lipat.appendChild(ikon("", IKON.lipat));

    var ringkasan = el("div", "parkir__ringkasan");
    var lokasi = el("p", "parkir__lokasi");
    var titikWarna = el("i", "parkir__titik");
    titikWarna.setAttribute("aria-hidden", "true");
    var namaRuas = el("strong", "parkir__ruas");
    susun(lokasi, [titikWarna, namaRuas]);
    var ketLokasi = el("p", "parkir__ket");
    var harga = el("p", "parkir__harga");
    var subHarga = el("p", "parkir__sub");
    var usulan = el("p", "parkir__usulan");
    usulan.hidden = true;
    susun(ringkasan, [lokasi, ketLokasi, harga, subHarga, usulan]);

    var atur = el("div", "parkir__atur");
    atur.id = "parkir-atur";

    var bidangKendaraan = el("label", "parkir__bidang");
    var labelKendaraan = el("span");
    var pilihKendaraan = el("select", "parkir__pilih");
    susun(bidangKendaraan, [labelKendaraan, pilihKendaraan]);

    var bidangJam = el("div", "parkir__bidang parkir__bidang--jam");
    var labelJam = el("span");
    labelJam.id = "parkir-label-jam";
    var langkah = el("div", "parkir__langkah");
    langkah.setAttribute("role", "group");
    langkah.setAttribute("aria-labelledby", "parkir-label-jam");
    var kurang = el("button", "parkir__bulat", "−");
    kurang.type = "button";
    var nilaiJam = el("output", "parkir__jam");
    var tambah = el("button", "parkir__bulat", "+");
    tambah.type = "button";
    susun(langkah, [kurang, nilaiJam, tambah]);
    susun(bidangJam, [labelJam, langkah]);

    var bidangLayanan = el("div", "parkir__layanan");
    bidangLayanan.setAttribute("role", "group");
    var tombolLayanan = {};
    Object.keys(LAYANAN).forEach(function (kunci) {
      var b = el("button", "parkir__chip");
      b.type = "button";
      b.addEventListener("click", function () {
        keadaan.layanan = kunci;
        tampilkan();
      });
      bidangLayanan.appendChild(b);
      tombolLayanan[kunci] = b;
    });

    var terdekat = el("button", "parkir__terdekat");
    terdekat.type = "button";
    terdekat.hidden = true;
    var teksTerdekat = el("span", "parkir__terdekat-teks");
    var labelTerdekat = el("small");
    var namaTerdekat = el("strong");
    susun(teksTerdekat, [labelTerdekat, namaTerdekat]);
    var jarakTerdekat = el("span", "parkir__terdekat-jarak");
    susun(terdekat, [ikon("parkir__terdekat-ikon", IKON.tempat), teksTerdekat, jarakTerdekat]);

    susun(atur, [bidangKendaraan, bidangJam, bidangLayanan, terdekat]);
    susun(kartu, [lipat, ringkasan, atur]);
    susun(samping, [cari, kartu]);

    var bungkus = el("div", "parkir__bungkus");
    frame.parentNode.insertBefore(bungkus, frame);
    susun(bungkus, [frame, samping]);

    var pin = el("div", "parkir__pin");
    pin.setAttribute("aria-hidden", "true");
    pin.innerHTML = '<span class="parkir__denyut"></span><svg viewBox="0 0 26 34" focusable="false"><path d="M13 0C5.8 0 0 5.8 0 13c0 9.7 13 21 13 21s13-11.3 13-21C26 5.8 20.2 0 13 0z"></path><circle cx="13" cy="12.6" r="4.6"></circle></svg>';
    frame.appendChild(pin);

    var legendaKotak = el("div", "parkir__legenda-kotak");
    var isiLegenda = el("div", "parkir__legenda-isi");
    isiLegenda.id = "parkir-legenda";
    var kepalaLegenda = el("div", "parkir__legenda-kepala");
    var judulLegenda = el("p", "parkir__legenda-judul");
    var tutupLegenda = el("button", "parkir__legenda-tutup");
    tutupLegenda.type = "button";
    tutupLegenda.appendChild(ikon("", IKON.hapus));
    susun(kepalaLegenda, [judulLegenda, tutupLegenda]);
    var petunjukLegenda = el("p", "parkir__legenda-petunjuk");
    var legenda = el("ul", "parkir__legenda");
    var tombolLapis = {};
    LEGENDA.forEach(function (item) {
      var b = el("button", "parkir__lapis");
      b.type = "button";
      b.setAttribute("data-lapis", item.kunci);
      var tanda = el("i", item.tanda);
      tanda.setAttribute("aria-hidden", "true");
      var nama = el("span", "parkir__lapis-nama");
      susun(b, [tanda, nama, ikon("parkir__lapis-cek", IKON.cek)]);
      b.addEventListener("click", function () {
        keadaan.tampil[item.kunci] = !keadaan.tampil[item.kunci];
        tandaiLapis();
        terapkan();
      });
      legenda.appendChild(susun(el("li"), [b]));
      tombolLapis[item.kunci] = { tombol: b, nama: nama, teks: TEXT[item.teks] };
    });
    var catatanLegenda = el("p", "parkir__catatan");
    susun(isiLegenda, [kepalaLegenda, petunjukLegenda, legenda, catatanLegenda]);
    var tombolLegenda = el("button", "parkir__legenda-tombol");
    tombolLegenda.type = "button";
    tombolLegenda.setAttribute("aria-controls", "parkir-legenda");
    var teksLegenda = el("span");
    susun(tombolLegenda, [ikon("", IKON.lapis), teksLegenda]);
    susun(legendaKotak, [isiLegenda, tombolLegenda]);
    frame.appendChild(legendaKotak);

    var kabar = el("p", "parkir__kabar visually-hidden");
    kabar.setAttribute("aria-live", "polite");
    section.insertBefore(kabar, bungkus.nextSibling);

    function aturLetak() {
      var lebar = layarLebar.matches;
      var kiri = lebar ? samping.offsetWidth + 24 : 0;
      var atas = lebar ? 0 : cari.offsetHeight + 12;
      bungkus.style.setProperty("--parkir-kiri", kiri + "px");
      bungkus.style.setProperty("--parkir-tepi", (lebar ? kiri : 12) + "px");
      bungkus.style.setProperty("--parkir-atas", atas + "px");
      if (map) map.setPadding({ top: atas, right: 0, bottom: 0, left: kiri });
    }

    function aturLegenda(buka, fokus) {
      keadaan.legenda = buka;
      isiLegenda.hidden = !buka;
      tombolLegenda.hidden = buka;
      tombolLegenda.setAttribute("aria-expanded", String(buka));
      legendaKotak.classList.toggle("is-buka", buka);
      if (fokus) (buka ? tutupLegenda : tombolLegenda).focus();
    }

    function labelLipat() {
      var teks = say(keadaan.ringkas ? TEXT.moreDetails : TEXT.lessDetails);
      lipat.setAttribute("aria-label", teks);
      lipat.title = teks;
    }

    function aturRingkas(ringkas) {
      keadaan.ringkas = ringkas;
      kartu.setAttribute("data-ringkas", ringkas ? "ya" : "tidak");
      atur.hidden = ringkas;
      lipat.setAttribute("aria-expanded", String(!ringkas));
      labelLipat();
    }

    function tandaiLapis() {
      Object.keys(tombolLapis).forEach(function (kunci) {
        tombolLapis[kunci].tombol.setAttribute("aria-pressed", String(keadaan.tampil[kunci]));
      });
    }

    tombolLegenda.addEventListener("click", function () {
      aturLegenda(true, true);
      simpanSetelan("legenda", true);
    });
    tutupLegenda.addEventListener("click", function () {
      aturLegenda(false, true);
      simpanSetelan("legenda", false);
    });
    isiLegenda.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      aturLegenda(false, true);
      simpanSetelan("legenda", false);
    });
    lipat.addEventListener("click", function () {
      aturRingkas(!keadaan.ringkas);
      simpanSetelan("ringkas", keadaan.ringkas);
    });

    function isiKendaraan() {
      var terpilih = keadaan.kendaraan;
      pilihKendaraan.replaceChildren();
      DAFTAR_KENDARAAN.forEach(function (nama) {
        var opsi = el("option", "", say(KENDARAAN[nama]));
        opsi.value = nama;
        opsi.selected = nama === terpilih;
        pilihKendaraan.appendChild(opsi);
      });
    }

    pilihKendaraan.addEventListener("change", function () {
      keadaan.kendaraan = pilihKendaraan.value;
      tampilkan();
    });
    kurang.addEventListener("click", function () {
      keadaan.jam = Math.max(1, keadaan.jam - 1);
      tampilkan();
    });
    tambah.addEventListener("click", function () {
      keadaan.jam = Math.min(JAM_MAKS, keadaan.jam + 1);
      tampilkan();
    });

    function label() {
      isian.placeholder = say(TEXT.search);
      isian.setAttribute("aria-label", say(TEXT.search));
      hapus.setAttribute("aria-label", say(TEXT.clear));
      labelKendaraan.textContent = say(TEXT.vehicle);
      labelJam.textContent = say(TEXT.hours);
      kurang.setAttribute("aria-label", say(TEXT.less));
      tambah.setAttribute("aria-label", say(TEXT.more));
      bidangLayanan.setAttribute("aria-label", say(TEXT.service));
      Object.keys(tombolLayanan).forEach(function (kunci) {
        tombolLayanan[kunci].textContent = say(LAYANAN[kunci]);
      });
      teksLegenda.textContent = say(TEXT.legend);
      judulLegenda.textContent = say(TEXT.legendTitle);
      petunjukLegenda.textContent = say(TEXT.legendHint);
      tutupLegenda.setAttribute("aria-label", say(TEXT.legendHide));
      tutupLegenda.title = say(TEXT.legendHide);
      Object.keys(tombolLapis).forEach(function (kunci) {
        tombolLapis[kunci].nama.textContent = say(tombolLapis[kunci].teks);
      });
      catatanLegenda.textContent = say(TEXT.legendRest);
      labelTerdekat.textContent = say(TEXT.nearest);
      labelLipat();
      isiKendaraan();
    }

    function teksTarif(h) {
      if (h.progresif) {
        var teks = say(TEXT.firstTwo).replace("%a", rupiah(h.awal));
        if (h.jamLanjut) {
          teks += say(TEXT.thenHours).replace("%j", h.jamLanjut).replace("%b", rupiah(h.lanjut));
        }
        return teks;
      }
      if (keadaan.layanan === "pasar") return say(TEXT.market);
      return say(TEXT.once).replace("%k", keadaan.posisi.kawasan);
    }

    var tundaKabar = 0;
    function umumkan(teks) {
      window.clearTimeout(tundaKabar);
      tundaKabar = window.setTimeout(function () { kabar.textContent = teks; }, 700);
    }

    var hargaKini = null;
    var hargaBingkai = 0;
    function pasangHarga(total) {
      window.cancelAnimationFrame(hargaBingkai);
      var angka = document.createTextNode("");
      harga.replaceChildren(el("span", "parkir__rp", "Rp"), angka);
      var dari = hargaKini;
      hargaKini = total;
      if (dari === null || dari === total || reducedMotion()) {
        angka.nodeValue = rupiah(total);
        return;
      }
      var awal = null;
      function langkahHarga(waktu) {
        if (awal === null) awal = waktu;
        var k = Math.min(1, (waktu - awal) / 420);
        var mulus = 1 - Math.pow(1 - k, 3);
        angka.nodeValue = rupiah(k < 1 ? Math.round((dari + (total - dari) * mulus) / 100) * 100 : total);
        if (k < 1) hargaBingkai = window.requestAnimationFrame(langkahHarga);
      }
      hargaBingkai = window.requestAnimationFrame(langkahHarga);
    }

    function tampilTerdekat(p) {
      var dekat = p.luar ? null : asetTerdekat(keadaan.titik[1], keadaan.titik[0]);
      if (!dekat || dekat.jarak > DEKAT_M) {
        terdekat.hidden = true;
        return;
      }
      var nama = DATA.titik[dekat.indeks].nama;
      var jarak = jarakTeks(dekat.jarak);
      terdekat.hidden = false;
      terdekat.setAttribute("data-indeks", String(dekat.indeks));
      namaTerdekat.textContent = nama;
      jarakTerdekat.textContent = jarak;
      terdekat.setAttribute("aria-label", say(TEXT.goThere).replace("%n", nama).replace("%d", jarak));
    }

    var kunciTampil = null;
    function tampilkan() {
      var w = WARNA[keadaan.gelap ? "gelap" : "terang"];
      var p = keadaan.posisi;
      nilaiJam.textContent = say(TEXT.hourUnit).replace("%j", keadaan.jam);
      kurang.disabled = keadaan.jam <= 1;
      tambah.disabled = keadaan.jam >= JAM_MAKS;
      Object.keys(tombolLayanan).forEach(function (kunci) {
        tombolLayanan[kunci].setAttribute("aria-pressed", String(kunci === keadaan.layanan));
      });
      if (!p) return;

      var kunci = p.luar ? "luar" : (p.ruas || "") + "|" + p.kawasan;
      if (kunciTampil !== null && kunci !== kunciTampil) kedip(ringkasan, "is-baru");
      kunciTampil = kunci;

      var h = hitungTarif(keadaan.kendaraan, p.kawasan, keadaan.jam, keadaan.layanan);
      kartu.setAttribute("data-kawasan", p.luar ? "luar" : p.kawasan);
      titikWarna.style.background = p.luar ? "transparent" : p.kawasan === "III" ? "var(--ink-3)" : w[p.kawasan];

      if (p.luar) {
        namaRuas.textContent = say(TEXT.outside);
        ketLokasi.textContent = say(TEXT.outsideNote);
      } else if (!p.ruas) {
        namaRuas.textContent = say(TEXT.zoneThree);
        ketLokasi.textContent = say(TEXT.zoneThreeNote);
      } else {
        namaRuas.textContent = p.ruas;
        ketLokasi.textContent = say(TEXT.zone).replace("%k", p.kawasan) + " · "
          + say(TEXT.fromStreet).replace("%m", Math.round(p.jarak));
      }

      usulan.hidden = !p.usulan;
      usulan.textContent = p.usulan ? say(TEXT.proposal) : "";

      if (!h) {
        window.cancelAnimationFrame(hargaBingkai);
        hargaKini = null;
        harga.replaceChildren(el("span", "parkir__rp", "—"));
        subHarga.textContent = p.luar ? "" : say(TEXT.noFee);
      } else {
        pasangHarga(h.total);
        subHarga.textContent = teksTarif(h);
      }
      tampilTerdekat(p);
      umumkan(say(TEXT.announce)
        .replace("%r", namaRuas.textContent)
        .replace("%f", h ? "Rp" + rupiah(h.total) : say(TEXT.outside)));
    }

    function posisiDari(lng, lat) {
      keadaan.titik = [lng, lat];
      keadaan.posisi = cariKawasan(lat, lng);
      if (map && map.getSource("parkir-terpilih")) map.getSource("parkir-terpilih").setData(terpilih());
      tampilkan();
    }

    function terpilih() {
      var p = keadaan.posisi;
      if (!p || p.fitur === null) return { type: "FeatureCollection", features: [] };
      return { type: "FeatureCollection", features: [DATA.kawasan.features[p.fitur]] };
    }

    function gabung(gaya) {
      var w = WARNA[keadaan.gelap ? "gelap" : "terang"];
      gaya.sources.parkir = { type: "geojson", data: DATA.kawasan };
      gaya.sources["parkir-terpilih"] = { type: "geojson", data: terpilih() };
      gaya.sources["parkir-aset"] = { type: "geojson", data: geojsonAset() };
      var sebelum = gaya.layers.findIndex(function (l) { return l.type === "symbol"; });
      if (sebelum < 0) sebelum = gaya.layers.length;
      Array.prototype.splice.apply(gaya.layers, [sebelum, 0].concat(lapisanParkir(w, keadaan.tampil)));
      return gaya;
    }

    function gayaBaru() {
      if (TOKEN) {
        return Promise.resolve(gabung(window.HK_PETA.gaya({
          gelap: keadaan.gelap, satelit: false, medan: false, tiga: false
        })));
      }
      var dasar = dasarCadangan
        ? Promise.resolve(dasarCadangan)
        : fetch(window.HK_PETA.cadangan).then(function (r) { return r.json(); })
          .then(function (json) { dasarCadangan = json; return json; });
      return dasar.then(function (json) { return gabung(JSON.parse(JSON.stringify(json))); });
    }

    function terapkan() {
      if (!map) return;
      gayaBaru().then(function (gaya) { map.setStyle(gaya, { diff: true }); });
    }

    function terjemahkanKontrol() {
      [[".maplibregl-ctrl-zoom-in", TEXT.zoomIn], [".maplibregl-ctrl-zoom-out", TEXT.zoomOut],
       [".maplibregl-ctrl-compass", TEXT.north]].forEach(function (p) {
        var node = frame.querySelector(p[0]);
        if (!node) return;
        node.title = say(p[1]);
        node.setAttribute("aria-label", say(p[1]));
      });
      var layar = frame.querySelector(".maplibregl-ctrl-fullscreen, .maplibregl-ctrl-shrink");
      if (layar) {
        layar.title = say(layar.classList.contains("maplibregl-ctrl-shrink") ? TEXT.unfull : TEXT.full);
        layar.setAttribute("aria-label", layar.title);
      }
    }

    function terbangKe(titik, zoom, durasi) {
      if (!map) {
        posisiDari(titik[0], titik[1]);
        return;
      }
      map.flyTo({
        center: titik, zoom: Math.max(map.getZoom(), zoom),
        duration: reducedMotion() ? 0 : durasi
      });
    }

    terdekat.addEventListener("click", function () {
      var t = DATA.titik[Number(terdekat.getAttribute("data-indeks"))];
      if (!t) return;
      if (!keadaan.tampil.aset) {
        keadaan.tampil.aset = true;
        tandaiLapis();
        terapkan();
      }
      terbangKe([t.lon, t.lat], 17, 1200);
    });

    var aktif = -1;
    var hasil = [];

    function tutupSaran() {
      saran.hidden = true;
      isian.setAttribute("aria-expanded", "false");
      isian.removeAttribute("aria-activedescendant");
      aktif = -1;
    }

    function tandai() {
      Array.prototype.forEach.call(saran.children, function (li, i) {
        var ya = i === aktif;
        li.setAttribute("aria-selected", String(ya));
        li.classList.toggle("is-aktif", ya);
        if (ya) isian.setAttribute("aria-activedescendant", li.id);
      });
    }

    function pilih(ruas) {
      isian.value = ruas.nama;
      hapus.hidden = false;
      tutupSaran();
      isian.blur();
      if (map) map.flyTo({ center: ruas.titik, zoom: 17, duration: reducedMotion() ? 0 : 1400 });
      else posisiDari(ruas.titik[0], ruas.titik[1]);
    }

    function isiSaran() {
      var q = polos(isian.value.trim());
      hapus.hidden = !isian.value;
      saran.replaceChildren();
      if (!q) { tutupSaran(); return; }
      hasil = DAFTAR_RUAS.filter(function (r) { return polos(r.nama).indexOf(q) !== -1; }).slice(0, 8);
      if (!hasil.length) {
        var kosong = el("li", "parkir__saran-kosong", say(TEXT.noMatch).replace("%q", isian.value.trim()));
        kosong.setAttribute("role", "presentation");
        saran.appendChild(kosong);
      }
      hasil.forEach(function (ruas, i) {
        var li = el("li", "parkir__opsi", ruas.nama);
        li.id = "parkir-saran-" + i;
        li.setAttribute("role", "option");
        li.addEventListener("mousedown", function (e) { e.preventDefault(); });
        li.addEventListener("click", function () { pilih(ruas); });
        saran.appendChild(li);
      });
      aktif = hasil.length ? 0 : -1;
      saran.hidden = false;
      isian.setAttribute("aria-expanded", "true");
      tandai();
    }

    isian.addEventListener("input", isiSaran);
    isian.addEventListener("blur", function () { window.setTimeout(tutupSaran, 120); });
    isian.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!hasil.length) return;
        aktif = (aktif + (e.key === "ArrowDown" ? 1 : -1) + hasil.length) % hasil.length;
        tandai();
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (hasil[aktif]) pilih(hasil[aktif]);
      } else if (e.key === "Escape") {
        tutupSaran();
      }
    });
    hapus.addEventListener("click", function () {
      isian.value = "";
      hapus.hidden = true;
      tutupSaran();
      isian.focus();
    });

    label();
    tandaiLapis();
    aturLegenda(keadaan.legenda, false);
    aturRingkas(keadaan.ringkas);
    aturLetak();
    posisiDari(PUSAT[0], PUSAT[1]);
    if ("ResizeObserver" in window) new ResizeObserver(aturLetak).observe(bungkus);
    else window.addEventListener("resize", aturLetak);

    if (!window.maplibregl || !window.HK_PETA) {
      section.classList.add("is-failed");
      return;
    }

    function pasangPetunjuk() {
      var tip = new maplibregl.Popup({
        closeButton: false, closeOnClick: false, className: "parkir__tip", offset: 12, maxWidth: "240px"
      });
      var tipKunci = "";
      function tunjuk(e) {
        var f = e.features && e.features[0];
        if (!f || map.isMoving()) return;
        var p = f.properties;
        var kunci = p.n + "|" + p.k + "|" + p.u;
        if (kunci !== tipKunci) {
          tipKunci = kunci;
          var isi = el("div", "parkir__tip-isi");
          isi.appendChild(el("strong", "", p.n));
          isi.appendChild(el("span", "", Number(p.u) === 1 ? say(TEXT.legendProposal) : say(TEXT.zone).replace("%k", p.k)));
          tip.setDOMContent(isi);
        }
        tip.setLngLat(e.lngLat);
        if (!tip.isOpen()) tip.addTo(map);
        map.getCanvas().style.cursor = "pointer";
      }
      function lepas() {
        tip.remove();
        tipKunci = "";
        map.getCanvas().style.cursor = "";
      }
      ["parkir-tetap", "parkir-usulan"].forEach(function (id) {
        map.on("mousemove", id, tunjuk);
        map.on("mouseleave", id, lepas);
      });
      map.on("movestart", lepas);
    }

    function mulai(gaya) {
      map = new maplibregl.Map({
        container: container,
        style: gaya,
        center: PUSAT,
        zoom: 15.5,
        minZoom: 11,
        maxZoom: 19,
        maxBounds: BATAS,
        maxPitch: 0,
        attributionControl: false,
        cooperativeGestures: sentuh(),
        scrollZoom: sentuh()
      });
      map.dragRotate.disable();
      map.touchZoomRotate.disableRotation();
      map.on("styleimagemissing", function (e) {
        if (e && e.id && e.id.indexOf("hk-poi-") === 0) window.HK_PETA.ikon(map, e.id);
      });
      map.addControl(new maplibregl.FullscreenControl({ container: bungkus }), "top-right");
      map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
      map.addControl(new maplibregl.ScaleControl({ maxWidth: 96, unit: "metric" }), "bottom-right");
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

      aturLetak();

      var sudahSiap = false;
      function siap() {
        if (sudahSiap) return;
        sudahSiap = true;
        map.resize();
        frame.classList.add("is-ready");
        terjemahkanKontrol();
        var c = map.getCenter();
        posisiDari(c.lng, c.lat);
      }
      map.on("load", siap);
      map.on("styledata", siap);
      map.on("idle", siap);
      window.setTimeout(siap, 4000);

      map.on("movestart", function () { pin.classList.add("is-geser"); });
      map.on("moveend", function () {
        pin.classList.remove("is-geser");
        kedip(pin, "is-mendarat");
        var c = map.getCenter();
        posisiDari(c.lng, c.lat);
      });

      map.on("click", function (e) {
        if (map.getLayer("parkir-aset")
          && map.queryRenderedFeatures(e.point, { layers: ["parkir-aset"] }).length) return;
        map.easeTo({ center: e.lngLat, duration: reducedMotion() ? 0 : 650 });
      });

      map.on("click", "parkir-aset", function (e) {
        var t = DATA.titik[e.features[0].properties.i];
        var isi = el("div", "parkir__popup");
        isi.appendChild(el("strong", "", t.nama));
        isi.appendChild(el("span", "", t.jenis + (t.jam ? " · " + t.jam : "")));
        if (t.srp_roda2) isi.appendChild(el("span", "", say(TEXT.spaces).replace("%n", rupiah(t.srp_roda2))));
        isi.appendChild(el("small", "", say(TEXT.assetNote)));
        new maplibregl.Popup({ className: "parkir__popup-bungkus", maxWidth: "260px" })
          .setLngLat(e.lngLat).setDOMContent(isi).addTo(map);
      });
      map.on("mouseenter", "parkir-aset", function () { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "parkir-aset", function () { map.getCanvas().style.cursor = ""; });

      if (!sentuh()) {
        pasangPetunjuk();
        container.addEventListener("wheel", function (event) {
          if (event.ctrlKey || event.metaKey) map.scrollZoom.enable();
          else map.scrollZoom.disable();
        }, { capture: true, passive: true });
      }

      window.HK_PARKIR_MAP = map;
    }

    gayaBaru().then(mulai).catch(function () {
      section.classList.add("is-failed");
    });

    document.addEventListener("hk:lang", function () {
      label();
      tampilkan();
      terjemahkanKontrol();
      terapkan();
    });
    document.addEventListener("hk:tema", function (event) {
      var gelap = Boolean(event && event.detail && event.detail.tema === "dark");
      if (gelap === keadaan.gelap) return;
      keadaan.gelap = gelap;
      tampilkan();
      terapkan();
    });
    document.addEventListener("fullscreenchange", function () {
      window.setTimeout(terjemahkanKontrol, 0);
    });
  }

  window.HK_PARKIR = {
    build: build,
    cariKawasan: cariKawasan,
    hitungTarif: hitungTarif,
    kendaraan: DAFTAR_KENDARAAN
  };
})();
