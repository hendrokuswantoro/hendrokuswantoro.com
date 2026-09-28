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
    "Sepeda motor": { en: "Motorcycle", ind: "Sepeda motor" },
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
    reguler: { en: "Regular", ind: "Reguler" },
    insidental: { en: "Event", ind: "Insidental" },
    pasar: { en: "Market", ind: "Di pasar" }
  };

  var TEXT = {
    search: { en: "Search a street in Yogyakarta", ind: "Cari jalan di Yogyakarta" },
    clear: { en: "Clear search", ind: "Hapus pencarian" },
    noMatch: { en: "No street matches “%q”", ind: "Tidak ada jalan yang cocok dengan “%q”" },
    zone: { en: "Zone %k", ind: "Kawasan %k" },
    fromStreet: { en: "%m m from the street", ind: "%m m dari ruas" },
    zoneThree: { en: "Outside Zone I and II", ind: "Di luar Kawasan I dan II" },
    zoneThreeNote: { en: "Zone III, the lowest fee", ind: "Kawasan III, tarif terendah" },
    outside: { en: "Outside the data coverage", ind: "Di luar cakupan data" },
    outsideNote: {
      en: "These fees only apply in Yogyakarta city, so the map does not guess one here.",
      ind: "Tarif ini hanya berlaku di Kota Yogyakarta, jadi peta tidak menebak angka di sini."
    },
    once: { en: "Zone %k, once, however long you stay", ind: "Kawasan %k, sekali parkir berapa pun lamanya" },
    market: { en: "Market fee, once per visit", ind: "Tarif kawasan pasar, sekali parkir" },
    firstTwo: { en: "Rp%a for the first two hours", ind: "Rp%a untuk dua jam pertama" },
    thenHours: { en: ", then %j h × Rp%b", ind: ", lalu %j jam × Rp%b" },
    proposal: {
      en: "This street is proposed for Zone I as a Malioboro side street. It is not decided yet, so check the fee board on site.",
      ind: "Ruas ini diusulkan masuk Kawasan I sebagai sirip Malioboro. Belum ditetapkan, jadi periksa papan tarif di lokasi."
    },
    vehicle: { en: "Vehicle", ind: "Kendaraan" },
    hours: { en: "Hours", ind: "Lama parkir" },
    hourUnit: { en: "%j h", ind: "%j jam" },
    less: { en: "One hour less", ind: "Kurangi satu jam" },
    more: { en: "One hour more", ind: "Tambah satu jam" },
    service: { en: "Service", ind: "Layanan" },
    legendOne: { en: "Zone I", ind: "Kawasan I" },
    legendTwo: { en: "Zone II", ind: "Kawasan II" },
    legendProposal: { en: "Proposed, not decided", ind: "Usulan, belum ditetapkan" },
    legendAsset: { en: "Provincial parking", ind: "Parkir aset Pemda DIY" },
    legendRest: { en: "Any other street in the city is Zone III.", ind: "Ruas lain di dalam kota termasuk Kawasan III." },
    assetNote: {
      en: "Provincial parking has its own fees, set by Pergub DIY 46/2024.",
      ind: "Parkir aset provinsi punya tarif sendiri, diatur Pergub DIY 46/2024."
    },
    spaces: { en: "%n motorcycle spaces", ind: "%n SRP roda dua" },
    announce: { en: "%r. %f.", ind: "%r. %f." },
    noFee: { en: "No fee", ind: "Tanpa tarif" },
    zoomIn: { en: "Zoom in", ind: "Perbesar" },
    zoomOut: { en: "Zoom out", ind: "Perkecil" },
    north: { en: "Face north", ind: "Hadapkan ke utara" },
    full: { en: "Full screen", ind: "Layar penuh" },
    unfull: { en: "Exit full screen", ind: "Keluar dari layar penuh" },
    close: { en: "Close", ind: "Tutup" }
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

  function lapisanParkir(w) {
    var tebal = ["interpolate", ["linear"], ["zoom"], 12, 2, 15, 4.5, 18, 9];
    var tebalHalo = ["interpolate", ["linear"], ["zoom"], 12, 4, 15, 7.5, 18, 13];
    var tebalSorot = ["interpolate", ["linear"], ["zoom"], 12, 9, 15, 14, 18, 22];
    var warna = ["match", ["get", "k"], "I", w.I, w.II];
    return [
      { id: "parkir-sorot", type: "line", source: "parkir-terpilih",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": w.sorot, "line-opacity": 0.22, "line-width": tebalSorot } },
      { id: "parkir-halo", type: "line", source: "parkir",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": w.halo, "line-width": tebalHalo } },
      { id: "parkir-tetap", type: "line", source: "parkir", filter: ["==", ["get", "u"], 0],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": warna, "line-width": tebal } },
      { id: "parkir-usulan", type: "line", source: "parkir", filter: ["==", ["get", "u"], 1],
        layout: { "line-cap": "butt", "line-join": "round" },
        paint: { "line-color": warna, "line-width": tebal, "line-dasharray": [0.6, 1.2] } },
      { id: "parkir-aset", type: "circle", source: "parkir-aset",
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
    var keadaan = {
      kendaraan: "Sepeda motor", layanan: "reguler", jam: 1,
      posisi: null, gelap: temaGelap()
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
    var saran = el("ul", "parkir__saran");
    saran.id = "parkir-saran";
    saran.setAttribute("role", "listbox");
    saran.hidden = true;
    cari.appendChild(isian);
    cari.appendChild(saran);

    var kartu = el("div", "parkir__kartu");
    var lokasi = el("p", "parkir__lokasi");
    var titikWarna = el("i", "parkir__titik");
    titikWarna.setAttribute("aria-hidden", "true");
    var namaRuas = el("strong", "parkir__ruas");
    lokasi.appendChild(titikWarna);
    lokasi.appendChild(namaRuas);
    var ketLokasi = el("p", "parkir__ket");
    var harga = el("p", "parkir__harga");
    var subHarga = el("p", "parkir__sub");
    var usulan = el("p", "parkir__usulan");
    usulan.hidden = true;

    var bidangKendaraan = el("label", "parkir__bidang");
    var labelKendaraan = el("span");
    var pilihKendaraan = el("select", "parkir__pilih");
    bidangKendaraan.appendChild(labelKendaraan);
    bidangKendaraan.appendChild(pilihKendaraan);

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
    langkah.appendChild(kurang);
    langkah.appendChild(nilaiJam);
    langkah.appendChild(tambah);
    bidangJam.appendChild(labelJam);
    bidangJam.appendChild(langkah);

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

    var legenda = el("ul", "parkir__legenda");
    var itemLegenda = {};
    [["one", "parkir__garis parkir__garis--satu"], ["two", "parkir__garis parkir__garis--dua"],
     ["proposal", "parkir__garis parkir__garis--usulan"], ["asset", "parkir__bulatan"]].forEach(function (p) {
      var li = el("li");
      var tanda = el("i", p[1]);
      tanda.setAttribute("aria-hidden", "true");
      li.appendChild(tanda);
      li.appendChild(el("span"));
      legenda.appendChild(li);
      itemLegenda[p[0]] = li.lastChild;
    });
    var catatanLegenda = el("p", "parkir__catatan");

    kartu.appendChild(lokasi);
    kartu.appendChild(ketLokasi);
    kartu.appendChild(harga);
    kartu.appendChild(subHarga);
    kartu.appendChild(usulan);
    kartu.appendChild(bidangKendaraan);
    kartu.appendChild(bidangJam);
    kartu.appendChild(bidangLayanan);
    kartu.appendChild(legenda);
    kartu.appendChild(catatanLegenda);
    samping.appendChild(cari);
    samping.appendChild(kartu);

    var bungkus = el("div", "parkir__bungkus");
    frame.parentNode.insertBefore(bungkus, frame);
    bungkus.appendChild(frame);
    bungkus.appendChild(samping);

    var pin = el("div", "parkir__pin");
    pin.setAttribute("aria-hidden", "true");
    pin.innerHTML = '<svg viewBox="0 0 26 34" focusable="false"><path d="M13 0C5.8 0 0 5.8 0 13c0 9.7 13 21 13 21s13-11.3 13-21C26 5.8 20.2 0 13 0z"></path><circle cx="13" cy="12.6" r="4.6"></circle></svg>';
    frame.appendChild(pin);

    var kabar = el("p", "parkir__kabar visually-hidden");
    kabar.setAttribute("aria-live", "polite");
    section.insertBefore(kabar, bungkus.nextSibling);

    var layarLebar = window.matchMedia("(min-width: 860px)");

    function aturLetak() {
      var kiri = layarLebar.matches ? samping.offsetWidth + 24 : 0;
      pin.style.left = "calc(" + kiri + "px + (100% - " + kiri + "px) / 2)";
      if (map) map.setPadding({ top: 0, right: 0, bottom: 0, left: kiri });
    }

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
      labelKendaraan.textContent = say(TEXT.vehicle);
      labelJam.textContent = say(TEXT.hours);
      kurang.setAttribute("aria-label", say(TEXT.less));
      tambah.setAttribute("aria-label", say(TEXT.more));
      bidangLayanan.setAttribute("aria-label", say(TEXT.service));
      Object.keys(tombolLayanan).forEach(function (kunci) {
        tombolLayanan[kunci].textContent = say(LAYANAN[kunci]);
      });
      itemLegenda.one.textContent = say(TEXT.legendOne);
      itemLegenda.two.textContent = say(TEXT.legendTwo);
      itemLegenda.proposal.textContent = say(TEXT.legendProposal);
      itemLegenda.asset.textContent = say(TEXT.legendAsset);
      catatanLegenda.textContent = say(TEXT.legendRest);
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
        harga.innerHTML = "";
        harga.appendChild(el("span", "parkir__rp", "—"));
        subHarga.textContent = p.luar ? "" : say(TEXT.noFee);
      } else {
        harga.replaceChildren(el("span", "parkir__rp", "Rp"), document.createTextNode(rupiah(h.total)));
        subHarga.textContent = teksTarif(h);
      }
      umumkan(say(TEXT.announce)
        .replace("%r", namaRuas.textContent)
        .replace("%f", h ? "Rp" + rupiah(h.total) : say(TEXT.outside)));
    }

    function posisiDari(lng, lat) {
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
      Array.prototype.splice.apply(gaya.layers, [sebelum, 0].concat(lapisanParkir(w)));
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
      isian.value = "";
      tutupSaran();
      if (map) {
        map.flyTo({ center: ruas.titik, zoom: 17, duration: reducedMotion() ? 0 : 1400 });
      } else {
        posisiDari(ruas.titik[0], ruas.titik[1]);
      }
    }

    function isiSaran() {
      var q = polos(isian.value.trim());
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

    label();
    aturLetak();
    posisiDari(PUSAT[0], PUSAT[1]);

    if (!window.maplibregl || !window.HK_PETA) {
      section.classList.add("is-failed");
      return;
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
      if ("ResizeObserver" in window) new ResizeObserver(aturLetak).observe(bungkus);
      else window.addEventListener("resize", aturLetak);

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
        var c = map.getCenter();
        posisiDari(c.lng, c.lat);
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
