(function () {
  "use strict";

  var TOKEN = (window.HK_KONFIG && window.HK_KONFIG.mapboxToken) || "";

  var DEM = TOKEN
    ? {
        type: "raster-dem",
        tiles: ["https://api.mapbox.com/v4/mapbox.mapbox-terrain-dem-v1/{z}/{x}/{y}.pngraw?access_token=" + TOKEN],
        encoding: "mapbox",
        tileSize: 512,
        maxzoom: 14
      }
    : {
        type: "raster-dem",
        tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
        encoding: "terrarium",
        tileSize: 256,
        maxzoom: 14,
        attribution: "Elevation: Mapzen, AWS Open Data"
      };

  var MAPBOX_ATTRIBUTION =
    '&copy; <a href="https://www.mapbox.com/about/maps/" target="_blank" rel="noopener">Mapbox</a> ' +
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';

  var CITRA_ATTRIBUTION =
    '&copy; <a href="https://www.maxar.com/" target="_blank" rel="noopener">Maxar</a>';

  function labelField() {
    return isId()
      ? ["coalesce", ["get", "name"], ["get", "name_en"]]
      : ["coalesce", ["get", "name_en"], ["get", "name"]];
  }

  var PROVINSI_ID = {
    type: "FeatureCollection",
    features: [
      ["Aceh", "Aceh", 96.9, 4.7],
      ["Sumatera Utara", "North Sumatra", 99.0, 2.3],
      ["Sumatera Barat", "West Sumatra", 100.5, -0.8],
      ["Riau", "Riau", 101.6, 0.5],
      ["Kepulauan Riau", "Riau Islands", 104.6, 0.9],
      ["Jambi", "Jambi", 102.4, -1.7],
      ["Sumatera Selatan", "South Sumatra", 104.0, -3.3],
      ["Bengkulu", "Bengkulu", 102.3, -3.6],
      ["Lampung", "Lampung", 105.0, -4.9],
      ["Kepulauan Bangka Belitung", "Bangka Belitung Islands", 106.6, -2.7],
      ["Banten", "Banten", 106.1, -6.4],
      ["DKI Jakarta", "Jakarta", 106.83, -6.2],
      ["Jawa Barat", "West Java", 107.6, -7.0],
      ["Jawa Tengah", "Central Java", 110.0, -7.3],
      ["DI Yogyakarta", "Yogyakarta", 110.42, -7.92],
      ["Jawa Timur", "East Java", 112.5, -7.8],
      ["Bali", "Bali", 115.1, -8.4],
      ["Nusa Tenggara Barat", "West Nusa Tenggara", 117.4, -8.7],
      ["Nusa Tenggara Timur", "East Nusa Tenggara", 121.0, -8.9],
      ["Kalimantan Barat", "West Kalimantan", 110.0, 0.2],
      ["Kalimantan Tengah", "Central Kalimantan", 113.4, -1.8],
      ["Kalimantan Selatan", "South Kalimantan", 115.3, -2.9],
      ["Kalimantan Timur", "East Kalimantan", 116.5, 0.6],
      ["Kalimantan Utara", "North Kalimantan", 116.5, 3.2],
      ["Sulawesi Utara", "North Sulawesi", 124.5, 1.2],
      ["Gorontalo", "Gorontalo", 122.4, 0.7],
      ["Sulawesi Tengah", "Central Sulawesi", 120.6, -1.5],
      ["Sulawesi Barat", "West Sulawesi", 119.3, -2.6],
      ["Sulawesi Selatan", "South Sulawesi", 120.0, -4.2],
      ["Sulawesi Tenggara", "Southeast Sulawesi", 122.0, -4.3],
      ["Maluku", "Maluku", 129.3, -3.4],
      ["Maluku Utara", "North Maluku", 127.8, 0.9],
      ["Papua Barat", "West Papua", 132.6, -1.6],
      ["Papua Barat Daya", "Southwest Papua", 131.3, -1.0],
      ["Papua", "Papua", 139.5, -3.3],
      ["Papua Tengah", "Central Papua", 136.5, -3.9],
      ["Papua Pegunungan", "Highland Papua", 138.5, -4.3],
      ["Papua Selatan", "South Papua", 139.8, -7.3]
    ].map(function (p) {
      return {
        type: "Feature",
        properties: { name: p[0], name_en: p[1] },
        geometry: { type: "Point", coordinates: [p[2], p[3]] }
      };
    })
  };

  var PALET = {
    terang: {
      latar: "#f1f3f4", latarMedan: "#eeede6",
      pemukiman: "#e8eaed", niaga: "#f1ece4", industri: "#e9e6ee", rumahSakit: "#fbe3e3",
      sekolah: "#ece8f4", bandara: "#e4e7ec", parkir: "#e6e8eb",
      taman: "#c9e9cf", hutan: "#bfe2c6", rumput: "#d4eed9", tani: "#e5efdc", makam: "#d3e6d4",
      pasir: "#f6eed2", es: "#ffffff",
      air: "#9fcbf5", sungai: "#9fcbf5",
      bayanganGelap: "#9aa3ad", bayanganTerang: "#ffffff",
      kontur: "#a4865c", konturTeks: "#7a6242",
      batasNegara: "#8d949b", batasProvinsi: "#aab0b6", batasKab: "#c3c7cc",
      tepiKecil: "#dcdfe3", tepiSedang: "#d3d6db", tepiSekunder: "#d0d4d9", tepiPrimer: "#e3c16a", tepiTol: "#dd9d2c",
      isiKecil: "#ffffff", isiSedang: "#ffffff", isiSekunder: "#ffffff", isiPrimer: "#fde7a4", isiTol: "#fbc95a",
      apron: "#e3e6ea", landasan: "#d5d9df", rel: "#b9bec5", relPalang: "#ffffff",
      gedung: "#e7e8ec", gedungTepi: "#d6d8dd",
      gedung3d: ["#eceef1", "#e1e4e8", "#d6d9df", "#c9cdd4", "#b9bec7"],
      panah: "#a4aab1",
      teksKota: "#3c4043", teksKelurahan: "#7d8287", teksJalan: "#5f6368", teksProvinsi: "#80868b",
      teksNegara: "#3c4043", teksAlam: "#3f7fc1", teksGunung: "#6f6252", halo: "#ffffff",
      langit: "#bcd8f5", cakrawala: "#eaf2fb", kabut: "#f1f3f4"
    },
    gelap: {
      latar: "#1f2023", latarMedan: "#22221f",
      pemukiman: "#26282c", niaga: "#2b2925", industri: "#28272d", rumahSakit: "#3a2728",
      sekolah: "#2a2833", bandara: "#2a2d32", parkir: "#292b2f",
      taman: "#1f3526", hutan: "#1c3122", rumput: "#223829", tani: "#262f23", makam: "#233226",
      pasir: "#35311f", es: "#3a3d42",
      air: "#17314c", sungai: "#1d3a58",
      bayanganGelap: "#000000", bayanganTerang: "#4a4d52",
      kontur: "#7a6d58", konturTeks: "#b8a88c",
      batasNegara: "#80868b", batasProvinsi: "#5f6368", batasKab: "#4a4d52",
      tepiKecil: "#2b2d31", tepiSedang: "#2d2f33", tepiSekunder: "#2f3135", tepiPrimer: "#4d4432", tepiTol: "#5c4a24",
      isiKecil: "#3c3f44", isiSedang: "#45484d", isiSekunder: "#4b4e54", isiPrimer: "#6b5f40", isiTol: "#8a6c30",
      apron: "#2c2f34", landasan: "#3a3d43", rel: "#5f6368", relPalang: "#26282c",
      gedung: "#2d2f33", gedungTepi: "#373a3f",
      gedung3d: ["#34373c", "#3a3d43", "#41444a", "#484c53", "#51555d"],
      panah: "#6f747a",
      teksKota: "#e8eaed", teksKelurahan: "#9aa0a6", teksJalan: "#bdc1c6", teksProvinsi: "#9aa0a6",
      teksNegara: "#e8eaed", teksAlam: "#8ab4f8", teksGunung: "#c6b89e", halo: "#1f2023",
      langit: "#0e1a2b", cakrawala: "#2a3547", kabut: "#1f2023"
    }
  };

  var PALET_CITRA = {
    latar: "#0b0f14",
    batasNegara: "rgba(255, 255, 255, .85)", batasProvinsi: "rgba(255, 255, 255, .6)",
    batasKab: "rgba(255, 255, 255, .4)",
    isiKecil: "rgba(255, 255, 255, .32)", isiSedang: "rgba(255, 255, 255, .4)",
    isiSekunder: "rgba(255, 255, 255, .5)", isiPrimer: "rgba(255, 236, 170, .75)", isiTol: "rgba(251, 201, 90, .85)",
    rel: "rgba(255, 255, 255, .35)", relPalang: "rgba(0, 0, 0, 0)", panah: "rgba(255, 255, 255, .75)",
    teksKota: "#ffffff", teksKelurahan: "#e8eaed", teksJalan: "#ffffff", teksProvinsi: "#e8eaed",
    teksNegara: "#ffffff", teksAlam: "#cfe3ff", teksGunung: "#f1e7d3", halo: "rgba(0, 0, 0, .78)"
  };

  var POI = {
    makan: { kelas: ["food_and_drink", "food_and_drink_stores"], warna: "#f29900", teks: "#b06000", teksGelap: "#fdc56b",
      jalur: "M7 3v6a2 2 0 0 0 1.4 1.9V21h2.2V10.9A2 2 0 0 0 12 9V3h-1.3v5.2h-.9V3H8.2v5.2h-.9V3zM14.2 3c2.4 1 3.8 3.6 3.8 7v3h-1.6v8h-2.2z" },
    belanja: { kelas: ["store_like", "commercial_services"], warna: "#4285f4", teks: "#1a5fb4", teksGelap: "#8ab4f8",
      jalur: "M5.5 8h13l-1 13h-11zM8.8 8V6.8a3.2 3.2 0 0 1 6.4 0V8h-1.8V6.8a1.4 1.4 0 0 0-2.8 0V8z" },
    kesehatan: { kelas: ["medical"], warna: "#ea4335", teks: "#c5221f", teksGelap: "#f6aea9",
      jalur: "M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" },
    pendidikan: { kelas: ["education"], warna: "#8e6fd8", teks: "#5e45a8", teksGelap: "#c5b3f6",
      jalur: "M12 4 1.5 9.3 12 14.6l8.4-4.2V16H22V9.3zM6 12.6V16c0 1.6 2.8 3.4 6 3.4s6-1.8 6-3.4v-3.4l-6 3z" },
    taman: { kelas: ["park_like", "sport_and_leisure"], warna: "#34a853", teks: "#188038", teksGelap: "#81c995",
      jalur: "M12 2 5.8 11h3.1L4.8 17H11v5h2v-5h6.2l-4.1-6h3.1z" },
    ibadah: { kelas: ["religion"], warna: "#7c848c", teks: "#5f6368", teksGelap: "#bdc1c6",
      jalur: "M12 3l2.6 3.4V9H17l3 3.4V21h-5.4v-4.4a2.6 2.6 0 0 0-5.2 0V21H4v-8.6L7 9h2.4V6.4z" },
    wisata: { kelas: ["arts_and_entertainment", "historic", "landmark", "visitor_amenities"], warna: "#12b5cb", teks: "#0b7f8c", teksGelap: "#78d9ec",
      jalur: "M12 3l2.6 5.6 6.1.7-4.6 4.1 1.3 6L12 16.3l-5.4 3.1 1.3-6-4.6-4.1 6.1-.7z" },
    inap: { kelas: ["lodging"], warna: "#e8457c", teks: "#c2185b", teksGelap: "#f4a3c0",
      jalur: "M3 6h2v7h16v7h-2v-2H5v2H3zM6.5 10a2 2 0 1 0 4 0 2 2 0 0 0-4 0zM11.5 8H17a3 3 0 0 1 3 3v1h-8.5z" },
    transit: { kelas: [], warna: "#1a73e8", teks: "#1967d2", teksGelap: "#8ab4f8",
      jalur: "M7 3h10a2 2 0 0 1 2 2v10a3 3 0 0 1-2.1 2.9L18.1 20h-2.3l-1-2H9.2l-1 2H5.9l1.2-2.1A3 3 0 0 1 5 15V5a2 2 0 0 1 2-2zm0 3v4.2h10V6zm1.6 7a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6zm6.8 0a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6z" },
    bandara: { kelas: [], warna: "#1a73e8", teks: "#1967d2", teksGelap: "#8ab4f8",
      jalur: "M11 2.5a1 1 0 0 1 2 0V9l8 5v2l-8-2.5V19l2 1.5V22l-3-.9-3 .9v-1.5l2-1.5v-5.5L3 16v-2l8-5z" },
    umum: { kelas: [], warna: "#8a9199", teks: "#5f6368", teksGelap: "#bdc1c6",
      jalur: "M12 8.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z" }
  };

  var URUTAN_POI = ["makan", "belanja", "kesehatan", "pendidikan", "taman", "ibadah", "wisata", "inap"];

  function kelompokPoi() {
    var ungkapan = ["match", ["get", "class"]];
    URUTAN_POI.forEach(function (kunci) {
      ungkapan.push(POI[kunci].kelas, kunci);
    });
    ungkapan.push("umum");
    return ungkapan;
  }

  function warnaTeksPoi(gelap, satelit) {
    if (satelit) return "#ffffff";
    var ungkapan = ["match", kelompokPoi()];
    URUTAN_POI.forEach(function (kunci) {
      ungkapan.push(kunci, gelap ? POI[kunci].teksGelap : POI[kunci].teks);
    });
    ungkapan.push(gelap ? POI.umum.teksGelap : POI.umum.teks);
    return ungkapan;
  }

  function tambahIkon(map, id) {
    var kunci = id.replace("hk-poi-", "");
    var def = POI[kunci];
    if (!def || map.hasImage(id)) return;
    var ukuran = 44;
    var kanvas = document.createElement("canvas");
    kanvas.width = ukuran;
    kanvas.height = ukuran;
    var c = kanvas.getContext("2d");
    if (!c || typeof Path2D === "undefined") return;
    c.beginPath();
    c.arc(22, 22, 19, 0, Math.PI * 2);
    c.fillStyle = def.warna;
    c.fill();
    c.lineWidth = 3;
    c.strokeStyle = "#ffffff";
    c.stroke();
    c.save();
    c.translate(10, 10);
    c.fillStyle = "#ffffff";
    c.fill(new Path2D(def.jalur), "evenodd");
    c.restore();
    map.addImage(id, c.getImageData(0, 0, ukuran, ukuran), { pixelRatio: 2 });
  }

  var LAYER_NAMA = [
    "nama-poi", "nama-transit", "nama-bandara", "nama-gunung", "nama-alam", "nama-kelurahan",
    "nama-kota", "nama-jalan", "nama-provinsi", "nama-provinsi-id", "nama-negara"
  ];

  function teksNama(id) {
    var nama = labelField();
    if (id === "nama-gunung") {
      return ["concat", "▲ ", nama,
        ["case", ["has", "elevation_m"],
          ["concat", "\n", ["to-string", ["round", ["to-number", ["get", "elevation_m"]]]], " m"], ""]];
    }
    return nama;
  }

  function lengkapiGaya(o, gaya) {
    gaya.layers.forEach(function (lapis) {
      if (LAYER_NAMA.indexOf(lapis.id) !== -1) lapis.layout["text-field"] = teksNama(lapis.id);
    });
    if (o.tiga) gaya.terrain = { source: "dem", exaggeration: 1.3 };
    return gaya;
  }

  function mapboxStyle(o) {
    var P = {};
    var dasar = PALET[o.gelap ? "gelap" : "terang"];
    Object.keys(dasar).forEach(function (k) { P[k] = dasar[k]; });
    if (o.satelit) Object.keys(PALET_CITRA).forEach(function (k) { P[k] = PALET_CITRA[k]; });
    if (o.medan && !o.satelit) P.latar = dasar.latarMedan;

    var source = "https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN;
    var reguler = ["Roboto Regular", "Arial Unicode MS Regular"];
    var sedang = ["Roboto Medium", "Arial Unicode MS Regular"];
    var miring = ["Roboto Italic", "Arial Unicode MS Regular"];

    var TOL = ["motorway", "motorway_link", "trunk", "trunk_link"];
    var PRIMER = ["primary", "primary_link"];
    var ARTERI = ["primary", "primary_link", "secondary", "secondary_link"];
    var SEDANG = ["tertiary", "tertiary_link"];
    var JALAN = ["street", "street_limited", "residential", "service", "track"];

    function isClass(list) {
      return ["in", ["get", "class"], ["literal", list]];
    }

    function tampak(ya) {
      return ya ? "visible" : "none";
    }

    var terowongan = ["match", ["get", "structure"], "tunnel", 0.45, 1];
    var alam = !o.satelit;

    function lebar(stops) {
      return ["interpolate", ["exponential", 1.5], ["zoom"]].concat(stops);
    }

    return lengkapiGaya(o, {
      version: 8,
      glyphs: "https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=" + TOKEN,
      sources: {
        jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
        citra: {
          type: "raster", tileSize: 512, maxzoom: 19, attribution: CITRA_ATTRIBUTION,
          tiles: ["https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.webp?access_token=" + TOKEN]
        },
        kontur: {
          type: "vector", maxzoom: 15,
          tiles: ["https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN]
        },
        dem: DEM,
        provinsi: { type: "geojson", data: PROVINSI_ID }
      },
      sky: {
        "sky-color": o.satelit ? "#8fb7e3" : P.langit,
        "horizon-color": o.satelit ? "#dbe8f5" : P.cakrawala,
        "fog-color": o.satelit ? "#c9d6e3" : P.kabut,
        "sky-horizon-blend": 0.6,
        "horizon-fog-blend": 0.7,
        "fog-ground-blend": 0.9,
        "atmosphere-blend": 0
      },
      layers: [
        { id: "latar", type: "background", paint: { "background-color": P.latar } },
        { id: "citra", type: "raster", source: "citra", layout: { visibility: tampak(o.satelit) },
          paint: { "raster-fade-duration": 180, "raster-saturation": o.gelap ? -0.15 : 0, "raster-brightness-max": o.gelap ? 0.82 : 1 } },
        { id: "bayangan", type: "hillshade", source: "dem", layout: { visibility: tampak(alam) },
          paint: {
            "hillshade-exaggeration": o.medan ? 0.48 : 0.24,
            "hillshade-shadow-color": P.bayanganGelap,
            "hillshade-highlight-color": P.bayanganTerang,
            "hillshade-accent-color": P.bayanganGelap
          } },
        { id: "kawasan", type: "fill", source: "jalan", "source-layer": "landuse", minzoom: 8,
          layout: { visibility: tampak(alam) },
          filter: isClass(["residential", "commercial_area", "industrial", "hospital", "school", "airport", "parking", "facility"]),
          paint: {
            "fill-color": ["match", ["get", "class"],
              "residential", P.pemukiman,
              "commercial_area", P.niaga,
              "industrial", P.industri,
              "hospital", P.rumahSakit,
              "school", P.sekolah,
              "airport", P.bandara,
              "parking", P.parkir,
              P.pemukiman],
            "fill-opacity": ["interpolate", ["linear"], ["zoom"], 8, 0, 10, 1]
          } },
        { id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
          layout: { visibility: tampak(alam) },
          filter: isClass(["park", "grass", "wood", "scrub", "agriculture", "pitch", "cemetery", "sand", "glacier"]),
          paint: {
            "fill-color": ["match", ["get", "class"],
              "park", P.taman,
              "pitch", P.taman,
              "wood", P.hutan,
              ["grass", "scrub"], P.rumput,
              "agriculture", P.tani,
              "cemetery", P.makam,
              "sand", P.pasir,
              "glacier", P.es,
              P.taman],
            "fill-opacity": o.medan ? 1 : 0.9
          } },
        { id: "air", type: "fill", source: "jalan", "source-layer": "water",
          layout: { visibility: tampak(alam) },
          paint: { "fill-color": P.air } },
        { id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
          layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": P.sungai,
            "line-width": ["interpolate", ["exponential", 1.3], ["zoom"], 8,
              ["match", ["get", "class"], ["river", "canal"], 0.8, 0.3],
              17, ["match", ["get", "class"], ["river", "canal"], 6, 2]]
          } },
        { id: "kontur", type: "line", source: "kontur", "source-layer": "contour", minzoom: 10,
          layout: { visibility: tampak(o.medan && alam), "line-join": "round" },
          paint: {
            "line-color": P.kontur,
            "line-opacity": ["interpolate", ["linear"], ["zoom"], 10,
              ["match", ["get", "index"], [5, 10], 0.75, 0.4], 13,
              ["match", ["get", "index"], [5, 10], 0.95, 0.7]],
            "line-width": ["interpolate", ["linear"], ["zoom"], 10,
              ["match", ["get", "index"], [5, 10], 1, 0.5], 15,
              ["match", ["get", "index"], [5, 10], 1.8, 0.9]]
          } },

        { id: "batas-kabupaten", type: "line", source: "jalan", "source-layer": "admin", minzoom: 7,
          filter: ["all", ["==", ["get", "admin_level"], 2], ["!=", ["get", "maritime"], "true"]],
          layout: { "line-join": "round" },
          paint: {
            "line-color": P.batasKab,
            "line-dasharray": [1, 2],
            "line-width": ["interpolate", ["linear"], ["zoom"], 7, 0.5, 12, 1, 16, 1.6]
          } },
        { id: "batas-provinsi", type: "line", source: "jalan", "source-layer": "admin",
          filter: ["all", ["==", ["get", "admin_level"], 1], ["!=", ["get", "maritime"], "true"]],
          layout: { "line-join": "round" },
          paint: {
            "line-color": P.batasProvinsi,
            "line-dasharray": [2.5, 2],
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 8, 1.2, 14, 2]
          } },
        { id: "batas-negara", type: "line", source: "jalan", "source-layer": "admin",
          filter: ["all", ["==", ["get", "admin_level"], 0], ["!=", ["get", "disputed"], "true"]],
          layout: { "line-join": "round" },
          paint: {
            "line-color": P.batasNegara,
            "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.8, 8, 1.6, 14, 2.6]
          } },

        { id: "jalan-kecil-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: isClass(JALAN), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.tepiKecil, "line-opacity": terowongan,
            "line-width": lebar([13, 1.4, 16, 6, 18, 15]) } },
        { id: "jalan-sedang-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
          filter: isClass(SEDANG), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.tepiSedang, "line-opacity": terowongan,
            "line-width": lebar([10, 1.4, 14, 4.6, 18, 17]) } },
        { id: "arteri-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
          filter: isClass(ARTERI), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["match", ["get", "class"], PRIMER, P.tepiPrimer, P.tepiSekunder],
            "line-opacity": ["step", ["zoom"],
              ["match", ["get", "class"], PRIMER, terowongan, 0], 9, terowongan],
            "line-width": lebar([7, 1.6, 12, 5, 18, 21]) } },
        { id: "tol-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
          filter: isClass(TOL), layout: { visibility: tampak(alam), "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.tepiTol, "line-opacity": terowongan,
            "line-width": lebar([4, 1.8, 10, 5.8, 18, 24]) } },

        { id: "jalan-kecil", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.isiKecil, "line-opacity": terowongan,
            "line-width": lebar([13, 0.6, 16, 4.4, 18, 12.5]) } },
        { id: "jalan-sedang", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
          filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.isiSedang, "line-opacity": terowongan,
            "line-width": lebar([10, 0.6, 14, 2.9, 18, 14]) } },
        { id: "arteri", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
          filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["match", ["get", "class"], PRIMER, P.isiPrimer, P.isiSekunder],
            "line-opacity": ["step", ["zoom"],
              ["match", ["get", "class"], PRIMER, terowongan, 0], 9, terowongan],
            "line-width": lebar([7, 0.8, 12, 3.4, 18, 18]) } },
        { id: "tol", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
          filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": P.isiTol, "line-opacity": terowongan,
            "line-width": lebar([4, 1, 10, 4, 18, 20.5]) } },

        { id: "apron", type: "fill", source: "jalan", "source-layer": "aeroway", minzoom: 11,
          filter: ["in", ["get", "type"], ["literal", ["apron", "helipad"]]],
          layout: { visibility: tampak(alam) },
          paint: { "fill-color": P.apron } },
        { id: "landasan", type: "line", source: "jalan", "source-layer": "aeroway", minzoom: 10,
          filter: ["in", ["get", "type"], ["literal", ["runway", "taxiway"]]],
          layout: { visibility: tampak(alam) },
          paint: {
            "line-color": P.landasan,
            "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
              10, ["match", ["get", "type"], "runway", 1.6, 0.6],
              16, ["match", ["get", "type"], "runway", 14, 5]]
          } },
        { id: "rel", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
          filter: ["==", ["get", "class"], "major_rail"],
          paint: { "line-color": P.rel, "line-width": ["interpolate", ["linear"], ["zoom"], 10, 0.8, 18, 3.2] } },
        { id: "rel-palang", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: ["==", ["get", "class"], "major_rail"],
          paint: {
            "line-color": P.relPalang, "line-dasharray": [2, 3],
            "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 18, 2]
          } },

        { id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
          filter: ["!=", ["get", "underground"], "true"],
          layout: { visibility: tampak(alam && !o.tiga) },
          paint: {
            "fill-color": P.gedung,
            "fill-outline-color": P.gedungTepi,
            "fill-opacity": ["interpolate", ["linear"], ["zoom"], 14, 0, 15, 1]
          } },
        { id: "gedung3d", type: "fill-extrusion", source: "jalan", "source-layer": "building", minzoom: 13.5,
          filter: ["all", ["==", ["get", "extrude"], "true"], ["!=", ["get", "underground"], "true"]],
          layout: { visibility: tampak(alam && o.tiga) },
          paint: {
            "fill-extrusion-color": ["interpolate", ["linear"], ["get", "height"],
              0, P.gedung3d[0], 3, P.gedung3d[1], 6, P.gedung3d[2], 14, P.gedung3d[3], 40, P.gedung3d[4]],
            "fill-extrusion-height": ["coalesce", ["get", "height"], 6],
            "fill-extrusion-base": ["coalesce", ["get", "min_height"], 0],
            "fill-extrusion-opacity": 0.92,
            "fill-extrusion-vertical-gradient": true
          } },

        { id: "panah-searah", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 16,
          filter: ["all", ["==", ["get", "oneway"], "true"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
          layout: {
            "symbol-placement": "line",
            "symbol-spacing": 120,
            "text-field": "→",
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 16, 10, 18, 13],
            "text-allow-overlap": true,
            "text-ignore-placement": true,
            "text-rotation-alignment": "map",
            "text-keep-upright": false,
            "text-padding": 0
          },
          paint: { "text-color": P.panah } },
        { id: "angka-kontur", type: "symbol", source: "kontur", "source-layer": "contour", minzoom: 12,
          filter: ["match", ["get", "index"], [5, 10], true, false],
          layout: {
            visibility: tampak(o.medan && alam),
            "symbol-placement": "line",
            "symbol-spacing": 320,
            "text-field": ["concat", ["to-string", ["get", "ele"]], " m"],
            "text-font": reguler,
            "text-size": 10,
            "text-max-angle": 25,
            "text-padding": 6
          },
          paint: { "text-color": P.konturTeks, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

        { id: "nama-poi", type: "symbol", source: "jalan", "source-layer": "poi_label", minzoom: 14.5,
          filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 15.5, 2, 16.5, 3, 17.5, 4]],
          layout: {
            "icon-image": ["concat", "hk-poi-", kelompokPoi()],
            "icon-size": ["interpolate", ["linear"], ["zoom"], 14.5, 0.8, 17, 1],
            "text-font": sedang,
            "text-size": ["interpolate", ["linear"], ["zoom"], 14.5, 10.5, 18, 12.5],
            "text-variable-anchor": ["left", "right", "top", "bottom"],
            "text-radial-offset": 1.05,
            "text-justify": "auto",
            "text-max-width": 8,
            "text-optional": true,
            "symbol-sort-key": ["to-number", ["get", "sizerank"], 30]
          },
          paint: { "text-color": warnaTeksPoi(o.gelap, o.satelit), "text-halo-color": P.halo, "text-halo-width": 1.6 } },
        { id: "nama-transit", type: "symbol", source: "jalan", "source-layer": "transit_stop_label", minzoom: 12.5,
          filter: ["all", ["==", ["get", "stop_type"], "station"],
            ["in", ["get", "mode"], ["literal", ["rail", "metro_rail", "light_rail", "monorail", "tram"]]]],
          layout: {
            "icon-image": "hk-poi-transit",
            "icon-size": ["interpolate", ["linear"], ["zoom"], 12.5, 0.8, 16, 1],
            "text-font": sedang,
            "text-size": ["interpolate", ["linear"], ["zoom"], 12.5, 10.5, 18, 12.5],
            "text-variable-anchor": ["left", "right", "top", "bottom"],
            "text-radial-offset": 1.05,
            "text-justify": "auto",
            "text-max-width": 8,
            "text-optional": true
          },
          paint: {
            "text-color": o.satelit ? "#ffffff" : (o.gelap ? POI.transit.teksGelap : POI.transit.teks),
            "text-halo-color": P.halo, "text-halo-width": 1.6
          } },
        { id: "nama-bandara", type: "symbol", source: "jalan", "source-layer": "airport_label", minzoom: 8,
          filter: ["<=", ["to-number", ["get", "sizerank"], 10], ["step", ["zoom"], 12, 10, 16]],
          layout: {
            "icon-image": "hk-poi-bandara",
            "text-font": sedang,
            "text-size": ["interpolate", ["linear"], ["zoom"], 8, 10.5, 14, 12.5],
            "text-variable-anchor": ["left", "right", "top", "bottom"],
            "text-radial-offset": 1.05,
            "text-justify": "auto",
            "text-max-width": 9,
            "text-optional": true
          },
          paint: {
            "text-color": o.satelit ? "#ffffff" : (o.gelap ? POI.bandara.teksGelap : POI.bandara.teks),
            "text-halo-color": P.halo, "text-halo-width": 1.6
          } },
        { id: "nama-gunung", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 9,
          filter: ["all", ["==", ["get", "class"], "landform"], ["in", ["get", "maki"], ["literal", ["mountain", "volcano"]]]],
          layout: {
            "text-font": reguler,
            "text-size": 11,
            "text-max-width": 8,
            "text-line-height": 1.25,
            "symbol-sort-key": ["to-number", ["get", "sizerank"], 20]
          },
          paint: { "text-color": P.teksGunung, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

        { id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 3,
          filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay", "water"]]],
          layout: {
            "text-font": miring,
            "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10.5, 10, 13.5],
            "text-letter-spacing": 0.05,
            "text-max-width": 8
          },
          paint: { "text-color": P.teksAlam, "text-halo-color": o.satelit ? P.halo : P.air, "text-halo-width": 0.8 } },

        { id: "nama-kelurahan", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 12,
          filter: ["==", ["get", "class"], "settlement_subdivision"],
          layout: {
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 12, 10.5, 16, 12.5],
            "text-max-width": 8,
            "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
          },
          paint: { "text-color": P.teksKelurahan, "text-halo-color": P.halo, "text-halo-width": 1.4 } },

        { id: "nama-kota", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 3,
          filter: ["all",
            ["==", ["get", "class"], "settlement"],
            ["<=", ["to-number", ["get", "filterrank"], 5],
              ["step", ["zoom"], 2, 5, 3, 7, 4, 9, 5]]],
          layout: {
            "text-font": ["step", ["to-number", ["get", "symbolrank"], 20], ["literal", sedang], 12, ["literal", reguler]],
            "text-size": ["interpolate", ["linear"], ["zoom"],
              4, ["step", ["to-number", ["get", "symbolrank"], 20], 13, 7, 11],
              9, ["step", ["to-number", ["get", "symbolrank"], 20], 16, 10, 13],
              14, ["step", ["to-number", ["get", "symbolrank"], 20], 18, 12, 15]],
            "text-max-width": 8,
            "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
          },
          paint: { "text-color": P.teksKota, "text-halo-color": P.halo, "text-halo-width": 1.6 } },
        { id: "nama-jalan", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: ["all", ["has", "name"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
          layout: {
            "symbol-placement": "line",
            "symbol-spacing": 280,
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 13, 10.5, 18, 13],
            "text-max-angle": 35,
            "text-padding": 3,
            "text-rotation-alignment": "map"
          },
          paint: { "text-color": P.teksJalan, "text-halo-color": P.halo, "text-halo-width": 1.6 } },

        { id: "nama-provinsi", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 5, maxzoom: 11,
          filter: ["==", ["get", "class"], "state"],
          layout: {
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10.5, 8, 13],
            "text-letter-spacing": 0.06,
            "text-max-width": 9
          },
          paint: { "text-color": P.teksProvinsi, "text-halo-color": P.halo, "text-halo-width": 1.4 } },
        { id: "nama-provinsi-id", type: "symbol", source: "provinsi", minzoom: 5, maxzoom: 10.5,
          layout: {
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10.5, 8, 13.5],
            "text-letter-spacing": 0.06,
            "text-max-width": 9
          },
          paint: { "text-color": P.teksProvinsi, "text-halo-color": P.halo, "text-halo-width": 1.6 } },
        { id: "nama-negara", type: "symbol", source: "jalan", "source-layer": "place_label", maxzoom: 6,
          filter: ["==", ["get", "class"], "country"],
          layout: {
            "text-font": sedang,
            "text-size": ["interpolate", ["linear"], ["zoom"], 2, 12, 6, 17],
            "text-max-width": 8
          },
          paint: { "text-color": P.teksNegara, "text-halo-color": P.halo, "text-halo-width": 1.8 } }
      ]
    });
  }

  var FALLBACK_STYLE = "https://tiles.openfreemap.org/styles/positron";

  var KIND = {
    app: { colour: "#1a73e8", en: "Map app", ind: "Aplikasi peta",
      glyph: "M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm0 3v12h10V5zm5 13.3a1.1 1.1 0 1 0 0 2.2 1.1 1.1 0 0 0 0-2.2z" },
    analysis: { colour: "#8430ce", en: "Map analysis", ind: "Analisis peta",
      glyph: "M3 20h18v2H3zM5 11h3.2v7.5H5zM10.4 5h3.2v13.5h-3.2zM15.8 13h3.2v5.5h-3.2z" },
    satellite: { colour: "#d93025", en: "Satellite data", ind: "Data satelit",
      glyph: "M12 8.2 15.8 12 12 15.8 8.2 12zM5.6 2.2l4 4-3.4 3.4-4-4zM18.4 14.4l4 4-3.4 3.4-4-4zM9.9 7.5l1.2-1.2 1.9 1.9-1.2 1.2zM14.8 12.4l1.2-1.2 1.9 1.9-1.2 1.2z" },
    design: { colour: "#188038", en: "Map design", ind: "Desain peta",
      glyph: "M12 2.5 22 8 12 13.5 2 8zM4.3 11.4 12 15.6l7.7-4.2L22 12.7 12 18.2 2 12.7zM4.3 15.6 12 19.8l7.7-4.2L22 16.9 12 22.4 2 16.9z" }
  };

  var WORK = [
    { id: "parking", kind: "app", lng: 110.3656, lat: -7.7925,
      en: "Yogyakarta Parking Map", ind: "Peta Parkir Yogyakarta",
      at: { en: "Yogyakarta", ind: "Yogyakarta" } },
    { id: "landcover", kind: "design", lng: 110.4050, lat: -7.7550,
      en: "Yogyakarta Land Cover Map", ind: "Peta Tutupan Lahan Yogyakarta",
      at: { en: "Yogyakarta", ind: "Yogyakarta" } },
    { id: "fire", kind: "satellite", lng: 113.2000, lat: -1.6000,
      en: "Kalimantan Fire Maps", ind: "Peta Kebakaran Kalimantan",
      at: { en: "Central Kalimantan", ind: "Kalimantan Tengah" } },
    { id: "fish", kind: "analysis", lng: 108.2200, lat: 3.7000,
      en: "Fish Landing Sites, Natuna", ind: "Lokasi Pendaratan Ikan, Natuna",
      at: { en: "Natuna, Riau Islands", ind: "Natuna, Kepulauan Riau" } },
    { id: "pickup", kind: "analysis", lng: 106.8200, lat: -6.2100,
      en: "Pickup Points from GPS Pings, Jakarta", ind: "Titik Jemput dari Ping GPS, Jakarta",
      at: { en: "Jakarta", ind: "Jakarta" } },
    { id: "reach", kind: "analysis", lng: 136.0800, lat: -1.1800,
      en: "Service Reach, Biak Numfor", ind: "Jangkauan Layanan, Biak Numfor",
      at: { en: "Biak Numfor, Papua", ind: "Biak Numfor, Papua" } },
    { id: "mimika", kind: "satellite", lng: 137.0000, lat: -4.3500,
      en: "Mining and Forest Loss, Mimika", ind: "Tambang dan Hutan Hilang, Mimika",
      at: { en: "Mimika, Central Papua", ind: "Mimika, Papua Tengah" } }
  ];

  var AWALAN_HASH = "#peta-";

  function idDariHash() {
    var hash = window.location.hash || "";
    if (hash.indexOf(AWALAN_HASH) !== 0) return null;
    var id = hash.slice(AWALAN_HASH.length);
    return WORK.some(function (item) { return item.id === id; }) ? id : null;
  }

  function tulisHash(id) {
    if (!window.history || !window.history.replaceState) return;
    if (id && window.location.hash === AWALAN_HASH + id) return;
    if (!id && !window.location.hash) return;
    var alamat = id ? AWALAN_HASH + id : window.location.pathname + window.location.search;
    try {
      window.history.replaceState(null, "", alamat);
    } catch (e) {}
  }

  var TEXT = {
    tour: { en: "Tour", ind: "Jelajah" },
    open: { en: "See the project", ind: "Lihat proyek" },
    home: { en: "Back to the starting view", ind: "Kembali ke posisi semula" },
    search: { en: "Search the work map", ind: "Cari di peta karya" },
    clear: { en: "Clear search", ind: "Hapus pencarian" },
    kinds: { en: "Filter works by type", ind: "Saring karya menurut jenis" },
    inView: { en: "%n of %t works in view", ind: "%n dari %t karya terlihat" },
    noMatch: { en: "No work matches “%q”", ind: "Tidak ada karya yang cocok dengan “%q”" },
    layers: { en: "Layers", ind: "Lapisan" },
    map: { en: "Map", ind: "Peta" },
    satellite: { en: "Satellite", ind: "Satelit" },
    terrain: { en: "Terrain", ind: "Medan" },
    three: { en: "3D view", ind: "Tampilan 3D" },
    copy: { en: "Copy link", ind: "Salin tautan" },
    copied: { en: "Link copied", ind: "Tautan tersalin" },
    copyFail: { en: "Copy failed", ind: "Gagal menyalin" },
    close: { en: "Close", ind: "Tutup" },
    zoomIn: { en: "Zoom in", ind: "Perbesar" },
    zoomOut: { en: "Zoom out", ind: "Perkecil" },
    north: { en: "Face north", ind: "Hadapkan ke utara" },
    full: { en: "Full screen", ind: "Layar penuh" },
    unfull: { en: "Exit full screen", ind: "Keluar dari layar penuh" },
    group: { en: "%n works here. Select to zoom in.", ind: "%n karya di sini. Pilih untuk memperbesar." },
    groupShort: { en: "%n works", ind: "%n karya" },
    layerOn: { en: "%l view.", ind: "Tampilan %l." },
    filterOn: { en: "%k. %n of %t works shown.", ind: "%k. %n dari %t karya ditampilkan." },
    filterOff: { en: "Filter off. All %t works shown.", ind: "Saringan mati. Semua %t karya ditampilkan." },
    focus: { en: "%w, centred on the map.", ind: "%w, dipusatkan di peta." }
  };

  var NAMA_DASAR = { peta: TEXT.map, satelit: TEXT.satellite, medan: TEXT.terrain };

  function sentuh() {
    return Boolean(window.matchMedia
      && window.matchMedia("(hover: none) and (pointer: coarse)").matches);
  }

  function reducedMotion() {
    return Boolean(window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function ms(duration) {
    return reducedMotion() ? 0 : duration;
  }

  function isId() {
    return document.documentElement.getAttribute("lang") === "id";
  }

  function temaGelap() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  function say(entry) {
    return isId() ? entry.ind : entry.en;
  }

  function el(tag, kelas, teks) {
    var node = document.createElement(tag);
    if (kelas) node.className = kelas;
    if (teks) node.textContent = teks;
    return node;
  }

  function svg(isi, kelas) {
    var wadah = document.createElement("span");
    wadah.className = kelas || "peta__ikon";
    wadah.setAttribute("aria-hidden", "true");
    wadah.innerHTML = '<svg viewBox="0 0 24 24" focusable="false">' + isi + "</svg>";
    return wadah;
  }

  var IKON = {
    cari: '<path d="M10.5 3a7.5 7.5 0 0 1 5.96 12.06l4.24 4.24-1.4 1.4-4.24-4.24A7.5 7.5 0 1 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"></path>',
    silang: '<path d="M6.4 5 12 10.6 17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4-5.6-5.6L6.4 19 5 17.6l5.6-5.6L5 6.4z"></path>',
    rumah: '<path d="M12 3.2 3 10.4V21h6.5v-6h5v6H21V10.4zm0 2.6 7 5.6V19h-2.5v-6h-9v6H5v-7.6z"></path>',
    main: '<path d="M8 5.5v13l10.5-6.5z"></path>',
    henti: '<path d="M7 6h3.5v12H7zM13.5 6H17v12h-3.5z"></path>',
    tautan: '<path d="M10.6 13.4a1 1 0 0 1 0-1.4l3.4-3.4a1 1 0 1 1 1.4 1.4L12 13.4a1 1 0 0 1-1.4 0zM8.2 18.6a3.4 3.4 0 0 1-4.8-4.8l2.9-2.9 1.4 1.4-2.9 2.9a1.4 1.4 0 0 0 2 2l2.9-2.9 1.4 1.4zm9.5-6.1-1.4-1.4 2.9-2.9a1.4 1.4 0 0 0-2-2l-2.9 2.9-1.4-1.4 2.9-2.9a3.4 3.4 0 0 1 4.8 4.8z"></path>',
    buka: '<path d="M14 4h6v6h-2V7.4l-7.3 7.3-1.4-1.4L16.6 6H14zM5 6h6v2H6v10h10v-5h2v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z"></path>',
    lokasi: '<path d="M12 2a7 7 0 0 1 7 7c0 5.2-7 13-7 13S5 14.2 5 9a7 7 0 0 1 7-7zm0 4.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z"></path>',
    lapisan: '<path d="M12 3 22 8.5 12 14 2 8.5zm0 2.3L6.2 8.5 12 11.7l5.8-3.2zM4.2 11.8 12 16.1l7.8-4.3L22 13 12 18.5 2 13z"></path>',
    tiga: '<path d="M12 2.5 20.5 7v10L12 21.5 3.5 17V7zm0 2.3L6.6 7.7 12 10.6l5.4-2.9zM5.5 9.4v6.4l5.5 3v-6.4zm13 0L13 12.4v6.4l5.5-3z"></path>'
  };

  var GAMBAR_LAPISAN = {
    peta:
      '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
      '<rect width="64" height="64" fill="#f1f3f4"></rect>' +
      '<path d="M0 44c10-6 18-4 26 2s18 8 38-6v24H0z" fill="#9fcbf5"></path>' +
      '<path d="M40 0h24v22c-8 2-16-2-20-8S40 6 40 0z" fill="#c9e9cf"></path>' +
      '<path d="M-2 22 66 34" stroke="#dd9d2c" stroke-width="6"></path>' +
      '<path d="M-2 22 66 34" stroke="#fbc95a" stroke-width="4"></path>' +
      '<path d="M22 -2 30 66M4 8l54 50" stroke="#ffffff" stroke-width="2.6"></path>' +
      '<path d="M22 -2 30 66M4 8l54 50" stroke="#d3d6db" stroke-width=".6" stroke-dasharray="0"></path>' +
      "</svg>",
    satelit:
      '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
      '<rect width="64" height="64" fill="#3c5a3a"></rect>' +
      '<path d="M0 0h30c-6 10-2 18 6 22S44 36 40 44 20 52 0 50z" fill="#56733f"></path>' +
      '<path d="M34 0h30v30c-8-2-14 2-20-2s-8-14-10-28z" fill="#2f4a36"></path>' +
      '<path d="M0 50c14 2 30-4 40-8s16-2 24 2v20H0z" fill="#1f4f6b"></path>' +
      '<circle cx="18" cy="20" r="7" fill="#7a8a55"></circle>' +
      '<path d="M-2 26 66 36" stroke="#e8d9a8" stroke-width="2" stroke-opacity=".8"></path>' +
      '<path d="M24 -2 32 66" stroke="#ffffff" stroke-width="1.4" stroke-opacity=".55"></path>' +
      "</svg>",
    medan:
      '<svg viewBox="0 0 64 64" focusable="false" aria-hidden="true">' +
      '<rect width="64" height="64" fill="#eeede6"></rect>' +
      '<path d="M0 64V40c10-10 18-22 30-22s20 14 34 16v30z" fill="#d4eed9"></path>' +
      '<path d="M8 64c4-14 12-30 22-30s16 12 26 14" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
      '<path d="M14 64c4-10 10-22 17-22s11 8 18 10" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
      '<path d="M20 64c3-6 7-14 11-14s7 4 11 6" fill="none" stroke="#c7b89f" stroke-width="1.2"></path>' +
      '<path d="M30 18c-6 0-12 8-16 16 8-6 14-6 16-2 4-8 8-10 12-8-3-4-7-6-12-6z" fill="#9aa3ad" fill-opacity=".35"></path>' +
      "</svg>"
  };

  function pinSvg(kind) {
    return (
      '<svg class="peta__pin-svg" viewBox="0 0 28 40" focusable="false" aria-hidden="true">' +
      '<ellipse class="peta__pin-bayang" cx="14" cy="38.4" rx="5" ry="1.6"></ellipse>' +
      '<path class="peta__pin-bentuk" d="M14 1C6.8 1 1 6.7 1 13.8 1 23.4 14 38 14 38s13-14.6 13-24.2C27 6.7 21.2 1 14 1z"></path>' +
      '<g transform="translate(7.6 7.2) scale(.533)"><path class="peta__pin-glyph" fill-rule="evenodd" d="' +
      KIND[kind].glyph + '"></path></g></svg>'
    );
  }

  function ikonKind(kind) {
    return '<svg viewBox="0 0 24 24" focusable="false"><path fill-rule="evenodd" d="' + KIND[kind].glyph + '"></path></svg>';
  }

  function mati(entry) {
    return entry.marker.getElement().classList.contains("is-off");
  }

  function jumlahTampil(markers) {
    return markers.filter(function (entry) { return !mati(entry); }).length;
  }

  function tutupKartu(markers) {
    markers.forEach(function (entry) {
      if (entry.popup.isOpen()) entry.popup.remove();
    });
  }

  function sudutPandang(three, durasi) {
    return { pitch: three ? 58 : 0, bearing: three ? -18 : 0, duration: ms(durasi) };
  }

  function koordinat(lat, lng) {
    var id = isId();
    function angka(n) {
      var teks = Math.abs(n).toFixed(4);
      return id ? teks.replace(".", ",") : teks;
    }
    var ns = lat < 0 ? (id ? "LS" : "S") : (id ? "LU" : "N");
    var ew = lng < 0 ? (id ? "BB" : "W") : (id ? "BT" : "E");
    return angka(lat) + "° " + ns + ", " + angka(lng) + "° " + ew;
  }

  function polos(teks) {
    return String(teks || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function gambarKarya(id) {
    var img = document.querySelector("#karya-" + id + " .card__cover img");
    return img ? img.getAttribute("src") : "";
  }

  function tuneBasemap(map, gelap) {
    var P = PALET[gelap ? "gelap" : "terang"];
    var tweaks = [
      ["background", "background-color", P.latar],
      ["water", "fill-color", P.air],
      ["water_shadow", "fill-color", P.air],
      ["landcover_wood", "fill-color", P.hutan],
      ["landcover_grass", "fill-color", P.rumput],
      ["landuse_residential", "fill-color", P.pemukiman],
      ["building", "fill-color", P.gedung]
    ];
    tweaks.forEach(function (item) {
      try {
        if (map.getLayer(item[0])) map.setPaintProperty(item[0], item[1], item[2]);
      } catch (e) {}
    });
  }

  function applyRelief(map, three) {
    function run() {
      try {
        if (!map.getSource("dem")) map.addSource("dem", DEM);
        map.setTerrain(three ? { source: "dem", exaggeration: 1.3 } : null);
        return true;
      } catch (e) {
        return false;
      }
    }

    if (run()) return;
    map.once("styledata", run);
    map.once("idle", run);
  }

  function Kontrol(isi) {
    this._isi = isi;
  }

  Kontrol.prototype.onAdd = function () {
    this._wrap = this._isi();
    return this._wrap;
  };

  Kontrol.prototype.onRemove = function () {
    if (this._wrap && this._wrap.parentNode) this._wrap.parentNode.removeChild(this._wrap);
  };

  function tombolKontrol(kelas, ikon) {
    var button = el("button", kelas);
    button.type = "button";
    button.appendChild(svg(IKON[ikon], "peta__ikon-kontrol"));
    return button;
  }

  function markerElement(item) {
    var pin = el("button", "peta__pin");
    pin.type = "button";
    pin.setAttribute("data-work", item.id);
    pin.setAttribute("data-kind", item.kind);
    pin.title = say(item);
    pin.setAttribute("aria-label", say(item));
    pin.innerHTML = pinSvg(item.kind);
    var nama = el("span", "peta__pin-nama", say(item));
    nama.setAttribute("aria-hidden", "true");
    pin.appendChild(nama);
    return pin;
  }

  function kartu(entry, umumkan) {
    var item = entry.item;
    var box = el("div", "peta__kartu");

    var tutup = el("button", "peta__tutup");
    tutup.type = "button";
    tutup.title = say(TEXT.close);
    tutup.setAttribute("aria-label", say(TEXT.close));
    tutup.appendChild(svg(IKON.silang));
    tutup.addEventListener("click", function () { entry.popup.remove(); });
    box.appendChild(tutup);

    var src = gambarKarya(item.id);
    if (src) {
      var foto = document.createElement("img");
      foto.className = "peta__foto";
      foto.setAttribute("data-src", src);
      foto.alt = "";
      foto.width = 320;
      foto.height = 150;
      foto.decoding = "async";
      box.appendChild(foto);
    }

    var isi = el("div", "peta__isi");
    isi.appendChild(el("strong", "peta__judul", say(item)));

    var jenis = el("p", "peta__jenis");
    var titik = el("i", "peta__titik");
    titik.setAttribute("data-kind", item.kind);
    jenis.appendChild(titik);
    jenis.appendChild(el("span", "peta__kind peta__kind--" + item.kind, say(KIND[item.kind])));
    jenis.appendChild(el("span", "peta__sela", "·"));
    jenis.appendChild(el("span", "", say(item.at)));
    isi.appendChild(jenis);

    var letak = el("p", "peta__koordinat");
    letak.appendChild(svg(IKON.lokasi));
    letak.appendChild(el("span", "", koordinat(item.lat, item.lng)));
    isi.appendChild(letak);

    var aksi = el("div", "peta__aksi");
    var lihat = el("a", "peta__tombol peta__tombol--utama");
    lihat.href = "#karya-" + item.id;
    lihat.appendChild(svg(IKON.buka));
    lihat.appendChild(el("span", "", say(TEXT.open)));
    aksi.appendChild(lihat);

    var salin = el("button", "peta__tombol");
    salin.type = "button";
    salin.appendChild(svg(IKON.tautan));
    var salinTeks = el("span", "", say(TEXT.copy));
    salin.appendChild(salinTeks);
    salin.addEventListener("click", function () {
      var alamat = window.location.origin + window.location.pathname + AWALAN_HASH + item.id;
      function tanda(teks) {
        salinTeks.textContent = teks;
        umumkan(teks);
        window.setTimeout(function () { salinTeks.textContent = say(TEXT.copy); }, 2200);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(alamat).then(
          function () { tanda(say(TEXT.copied)); },
          function () { tanda(say(TEXT.copyFail)); });
      } else {
        tanda(say(TEXT.copyFail));
      }
    });
    aksi.appendChild(salin);
    isi.appendChild(aksi);
    box.appendChild(isi);
    return box;
  }

  var LAPISAN_KEY = "hk-peta-lapisan";

  function bacaLapisan() {
    try {
      var nilai = window.localStorage.getItem(LAPISAN_KEY);
      return nilai === "satelit" || nilai === "medan" ? nilai : "peta";
    } catch (e) { return "peta"; }
  }

  function tulisLapisan(nilai) {
    try { window.localStorage.setItem(LAPISAN_KEY, nilai); } catch (e) {}
  }

  function buildUi(map, frame, markers, state) {
    var atas = el("div", "peta__atas");

    var cari = el("div", "peta__cari");
    cari.setAttribute("role", "search");
    var ikonCari = svg(IKON.cari, "peta__ikon peta__cari-ikon");
    var isian = document.createElement("input");
    isian.type = "search";
    isian.className = "peta__cari-isian";
    isian.id = "peta-cari";
    isian.autocomplete = "off";
    isian.spellcheck = false;
    isian.setAttribute("role", "combobox");
    isian.setAttribute("aria-autocomplete", "list");
    isian.setAttribute("aria-expanded", "false");
    isian.setAttribute("aria-controls", "peta-saran");
    var hapus = el("button", "peta__cari-hapus");
    hapus.type = "button";
    hapus.hidden = true;
    hapus.appendChild(svg(IKON.silang));
    var saran = el("div", "peta__saran");
    saran.id = "peta-saran";
    saran.setAttribute("role", "listbox");
    saran.hidden = true;
    cari.appendChild(ikonCari);
    cari.appendChild(isian);
    cari.appendChild(hapus);
    cari.appendChild(saran);
    atas.appendChild(cari);

    var kategori = el("div", "peta__kategori");
    kategori.setAttribute("role", "group");
    var rows = {};
    Object.keys(KIND).forEach(function (key) {
      var row = el("button", "peta__baris");
      row.type = "button";
      row.setAttribute("data-kind", key);
      row.setAttribute("aria-pressed", "false");
      var ikon = el("i");
      ikon.setAttribute("aria-hidden", "true");
      ikon.innerHTML = ikonKind(key);
      row.appendChild(ikon);
      row.appendChild(el("span", "peta__nama"));
      row.appendChild(el("span", "peta__angka", "0"));
      row.addEventListener("click", function () { state.filter(key); });
      kategori.appendChild(row);
      rows[key] = row;
    });
    var tour = el("button", "peta__chip");
    tour.type = "button";
    tour.setAttribute("aria-pressed", "false");
    var tourIkon = svg(IKON.main);
    var tourTeks = el("span");
    tour.appendChild(tourIkon);
    tour.appendChild(tourTeks);
    tour.addEventListener("click", function () { state.toggleTour(); });
    kategori.appendChild(tour);
    atas.appendChild(kategori);
    frame.appendChild(atas);

    var lapisan = null;
    var pilihanLapisan = {};
    var utama;
    var utamaGambar;
    var utamaTeks;
    if (TOKEN) {
      lapisan = el("div", "peta__lapisan");
      utama = el("button", "peta__lapisan-utama");
      utama.type = "button";
      utamaGambar = el("span", "peta__lapisan-gambar");
      utamaTeks = el("span", "peta__lapisan-teks");
      utama.appendChild(utamaGambar);
      utama.appendChild(utamaTeks);
      utama.addEventListener("click", function () {
        state.setDasar(state.dasar() === "satelit" ? "peta" : "satelit");
      });
      var daftar = el("div", "peta__lapisan-pilihan");
      daftar.setAttribute("role", "group");
      Object.keys(NAMA_DASAR).forEach(function (nama) {
        var opsi = el("button", "peta__lapisan-opsi");
        opsi.type = "button";
        opsi.setAttribute("data-lapisan", nama);
        opsi.setAttribute("aria-pressed", "false");
        var gambar = el("span", "peta__lapisan-gambar");
        gambar.innerHTML = GAMBAR_LAPISAN[nama];
        opsi.appendChild(gambar);
        opsi.appendChild(el("span", "peta__lapisan-label"));
        opsi.addEventListener("click", function () { state.setDasar(nama); });
        daftar.appendChild(opsi);
        pilihanLapisan[nama] = opsi;
      });
      lapisan.appendChild(utama);
      lapisan.appendChild(daftar);
      frame.appendChild(lapisan);
    }

    var aktif = -1;
    var hasil = [];

    function cocok(item, q) {
      var bidang = [item.en, item.ind, item.at.en, item.at.ind, KIND[item.kind].en, KIND[item.kind].ind]
        .map(polos).join(" | ");
      if (polos(say(item)).indexOf(q) === 0) return 3;
      if (bidang.indexOf(q) === 0 || bidang.indexOf(" " + q) !== -1) return 2;
      return bidang.indexOf(q) !== -1 ? 1 : 0;
    }

    function terlihat() {
      var view = map.getBounds();
      return markers.filter(function (entry) {
        return !mati(entry) && view.contains([entry.item.lng, entry.item.lat]);
      });
    }

    function tutupSaran() {
      saran.hidden = true;
      isian.setAttribute("aria-expanded", "false");
      isian.removeAttribute("aria-activedescendant");
      cari.classList.remove("is-terbuka");
      aktif = -1;
    }

    function tandaiAktif() {
      var opsi = saran.querySelectorAll(".peta__opsi");
      for (var i = 0; i < opsi.length; i++) {
        var ya = i === aktif;
        opsi[i].setAttribute("aria-selected", ya ? "true" : "false");
        opsi[i].classList.toggle("is-aktif", ya);
        if (ya) {
          isian.setAttribute("aria-activedescendant", opsi[i].id);
          if (opsi[i].scrollIntoView) opsi[i].scrollIntoView({ block: "nearest" });
        }
      }
      if (aktif < 0) isian.removeAttribute("aria-activedescendant");
    }

    function pilih(entry) {
      isian.value = say(entry.item);
      hapus.hidden = false;
      tutupSaran();
      state.buka(entry.item.id);
    }

    function isiSaran() {
      var q = polos(isian.value.trim());
      saran.replaceChildren();
      var judul = el("p", "peta__saran-judul");
      if (!q) {
        hasil = terlihat();
        judul.textContent = say(TEXT.inView).replace("%n", hasil.length).replace("%t", jumlahTampil(markers));
      } else {
        hasil = markers
          .map(function (entry) { return { entry: entry, skor: cocok(entry.item, q) }; })
          .filter(function (x) { return x.skor > 0; })
          .sort(function (a, b) { return b.skor - a.skor; })
          .map(function (x) { return x.entry; });
        if (!hasil.length) judul.textContent = say(TEXT.noMatch).replace("%q", isian.value.trim());
      }
      if (judul.textContent) saran.appendChild(judul);

      hasil.forEach(function (entry, i) {
        var opsi = el("div", "peta__opsi");
        opsi.id = "peta-saran-" + entry.item.id;
        opsi.setAttribute("role", "option");
        opsi.setAttribute("aria-selected", "false");
        opsi.setAttribute("data-kind", entry.item.kind);
        var ikon = el("i", "peta__opsi-ikon");
        ikon.setAttribute("aria-hidden", "true");
        ikon.innerHTML = ikonKind(entry.item.kind);
        var teks = el("span", "peta__opsi-teks");
        teks.appendChild(el("span", "peta__opsi-nama", say(entry.item)));
        teks.appendChild(el("span", "peta__opsi-ket", say(KIND[entry.item.kind]) + " · " + say(entry.item.at)));
        opsi.appendChild(ikon);
        opsi.appendChild(teks);
        opsi.addEventListener("mousedown", function (event) { event.preventDefault(); });
        opsi.addEventListener("click", function () { pilih(entry); });
        opsi.addEventListener("mousemove", function () {
          if (aktif !== i) { aktif = i; tandaiAktif(); }
        });
        saran.appendChild(opsi);
      });

      aktif = q && hasil.length ? 0 : -1;
      saran.hidden = false;
      cari.classList.add("is-terbuka");
      isian.setAttribute("aria-expanded", "true");
      tandaiAktif();
    }

    isian.addEventListener("focus", function () {
      state.stopTour();
      isiSaran();
    });
    isian.addEventListener("input", function () {
      hapus.hidden = !isian.value;
      isiSaran();
    });
    isian.addEventListener("blur", function () {
      window.setTimeout(tutupSaran, 120);
    });
    isian.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (saran.hidden) isiSaran();
        if (!hasil.length) return;
        var arah = event.key === "ArrowDown" ? 1 : -1;
        aktif = (aktif + arah + hasil.length) % hasil.length;
        tandaiAktif();
      } else if (event.key === "Enter") {
        event.preventDefault();
        var entry = hasil[aktif >= 0 ? aktif : 0];
        if (entry) pilih(entry);
      } else if (event.key === "Escape") {
        if (!saran.hidden) {
          event.preventDefault();
          tutupSaran();
        } else if (isian.value) {
          isian.value = "";
          hapus.hidden = true;
        }
      }
    });
    hapus.addEventListener("click", function () {
      isian.value = "";
      hapus.hidden = true;
      isian.focus();
      isiSaran();
    });

    function label() {
      isian.placeholder = say(TEXT.search);
      isian.setAttribute("aria-label", say(TEXT.search));
      hapus.title = say(TEXT.clear);
      hapus.setAttribute("aria-label", say(TEXT.clear));
      kategori.setAttribute("aria-label", say(TEXT.kinds));
      tourTeks.textContent = say(TEXT.tour);
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__nama").textContent = say(KIND[key]);
      });
      if (lapisan) {
        lapisan.setAttribute("aria-label", say(TEXT.layers));
        Object.keys(pilihanLapisan).forEach(function (nama) {
          pilihanLapisan[nama].querySelector(".peta__lapisan-label").textContent = say(NAMA_DASAR[nama]);
        });
        markDasar(state.dasar());
      }
      if (!saran.hidden) isiSaran();
    }

    function kelompokkan() {
      var kepala = [];
      markers.forEach(function (entry) {
        var pin = entry.marker.getElement();
        entry.anggota = null;
        pin.classList.remove("is-gabung");
        pin.removeAttribute("data-jumlah");
        pin.title = say(entry.item);
        pin.setAttribute("aria-label", say(entry.item));
        pin.querySelector(".peta__pin-nama").textContent = say(entry.item);
        if (pin.classList.contains("is-off")) return;
        var titik = map.project([entry.item.lng, entry.item.lat]);
        if (!entry.popup.isOpen()) {
          for (var i = 0; i < kepala.length; i++) {
            if (Math.abs(kepala[i].x - titik.x) < 26 && Math.abs(kepala[i].y - titik.y) < 32) {
              kepala[i].anggota.push(entry);
              pin.classList.add("is-gabung");
              return;
            }
          }
        }
        kepala.push({ x: titik.x, y: titik.y, entry: entry, anggota: [entry] });
      });
      kepala.forEach(function (k) {
        if (k.anggota.length < 2) return;
        var pin = k.entry.marker.getElement();
        k.entry.anggota = k.anggota;
        pin.setAttribute("data-jumlah", k.anggota.length);
        pin.title = k.anggota.map(function (e) { return say(e.item); }).join(", ");
        pin.setAttribute("aria-label", say(TEXT.group).replace("%n", k.anggota.length) + " " + pin.title);
        pin.querySelector(".peta__pin-nama").textContent = say(TEXT.groupShort).replace("%n", k.anggota.length);
      });
    }

    function count() {
      kelompokkan();
      var view = map.getBounds();
      var seen = { app: 0, analysis: 0, satellite: 0, design: 0 };
      markers.forEach(function (entry) {
        if (mati(entry) || !view.contains([entry.item.lng, entry.item.lat])) return;
        seen[entry.item.kind]++;
      });
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__angka").textContent = seen[key];
        rows[key].classList.toggle("is-empty", seen[key] === 0);
      });
      frame.classList.toggle("is-dekat", map.getZoom() >= 9);
      if (!saran.hidden && !isian.value.trim()) isiSaran();
    }

    var pending = 0;
    function countSoon() {
      if (pending) return;
      pending = window.requestAnimationFrame(function () {
        pending = 0;
        count();
      });
    }

    function markDasar(dasar) {
      if (!lapisan) return;
      var berikut = dasar === "satelit" ? "peta" : "satelit";
      utamaGambar.innerHTML = GAMBAR_LAPISAN[berikut];
      utamaTeks.textContent = say(NAMA_DASAR[berikut]);
      utama.title = say(TEXT.layers) + ": " + utamaTeks.textContent;
      utama.setAttribute("aria-label", utama.title);
      Object.keys(pilihanLapisan).forEach(function (nama) {
        pilihanLapisan[nama].setAttribute("aria-pressed", nama === dasar ? "true" : "false");
      });
      frame.setAttribute("data-dasar", dasar);
    }

    label();
    map.on("move", countSoon);
    map.on("moveend", count);
    map.on("zoom", countSoon);

    return {
      label: label,
      count: count,
      markDasar: markDasar,
      markTour: function (running) {
        tour.setAttribute("aria-pressed", running ? "true" : "false");
        tourIkon.innerHTML = '<svg viewBox="0 0 24 24" focusable="false">' + (running ? IKON.henti : IKON.main) + "</svg>";
      },
      markFilter: function (kind) {
        Object.keys(rows).forEach(function (key) {
          rows[key].setAttribute("aria-pressed", kind === key ? "true" : "false");
        });
        atas.classList.toggle("is-filtered", Boolean(kind));
      }
    };
  }

  function build(container) {
    var bounds = new maplibregl.LngLatBounds();
    WORK.forEach(function (item) { bounds.extend([item.lng, item.lat]); });

    var frame = container.parentNode;
    var section = frame.parentNode;
    var current = {
      three: false, filter: null, tour: 0, tourAt: 0,
      dasar: TOKEN ? bacaLapisan() : "peta",
      gelap: temaGelap()
    };

    function pilihanGaya() {
      return {
        gelap: current.gelap,
        satelit: current.dasar === "satelit",
        medan: current.dasar === "medan",
        tiga: current.three
      };
    }

    var map = new maplibregl.Map({
      container: container,
      style: TOKEN ? mapboxStyle(pilihanGaya()) : FALLBACK_STYLE,
      bounds: bounds,
      fitBoundsOptions: { padding: 64, maxZoom: 6 },
      minZoom: 2.5,
      maxZoom: 18,
      maxPitch: 75,
      attributionControl: false,
      cooperativeGestures: sentuh(),
      scrollZoom: sentuh()
    });

    map.touchZoomRotate.disableRotation();

    function tepi() {
      var atas = 64;
      var cari = frame.querySelector(".peta__cari");
      if (cari) {
        var r = cari.getBoundingClientRect();
        var f = frame.getBoundingClientRect();
        if (r.top >= f.top && r.bottom <= f.bottom) atas = Math.max(atas, Math.round(r.bottom - f.top) + 56);
        atas = Math.min(atas, Math.max(64, Math.round(f.height / 2) - 64));
      }
      return { top: atas, right: 64, bottom: 64, left: 64 };
    }
    map.dragRotate.disable();

    map.on("styleimagemissing", function (event) {
      if (event && event.id && event.id.indexOf("hk-poi-") === 0) tambahIkon(map, event.id);
    });

    var tigaTombol;
    map.addControl(new maplibregl.FullscreenControl({ container: frame }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 96, unit: "metric" }), "bottom-right");
    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "bottom-right");
    map.addControl(new Kontrol(function () {
      var wrap = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
      var button = tombolKontrol("peta__rumah", "rumah");
      button.addEventListener("click", function () { state.home(); });
      wrap.appendChild(button);
      return wrap;
    }), "bottom-right");
    map.addControl(new Kontrol(function () {
      var wrap = el("div", "maplibregl-ctrl maplibregl-ctrl-group");
      tigaTombol = el("button", "peta__tiga");
      tigaTombol.type = "button";
      tigaTombol.setAttribute("aria-pressed", "false");
      tigaTombol.textContent = "3D";
      tigaTombol.addEventListener("click", function () { state.setThree(!current.three); });
      wrap.appendChild(tigaTombol);
      return wrap;
    }), "bottom-right");

    function terjemahkanKontrol() {
      var judul = [
        [".maplibregl-ctrl-zoom-in", TEXT.zoomIn],
        [".maplibregl-ctrl-zoom-out", TEXT.zoomOut],
        [".maplibregl-ctrl-compass", TEXT.north],
        [".peta__rumah", TEXT.home],
        [".peta__tiga", TEXT.three]
      ];
      judul.forEach(function (pasangan) {
        var node = frame.querySelector(pasangan[0]);
        if (!node) return;
        node.title = say(pasangan[1]);
        node.setAttribute("aria-label", say(pasangan[1]));
      });
      var layar = frame.querySelector(".maplibregl-ctrl-fullscreen, .maplibregl-ctrl-shrink");
      if (layar) {
        var penuh = layar.classList.contains("maplibregl-ctrl-shrink");
        layar.title = say(penuh ? TEXT.unfull : TEXT.full);
        layar.setAttribute("aria-label", layar.title);
      }
    }

    var markers = WORK.map(function (item, urutan) {
      var popup = new maplibregl.Popup({
        anchor: "bottom",
        offset: [0, -44],
        closeButton: false,
        focusAfterOpen: false,
        maxWidth: "320px",
        className: "peta__popup"
      });
      var marker = new maplibregl.Marker({ element: markerElement(item), anchor: "bottom" })
        .setLngLat([item.lng, item.lat])
        .setPopup(popup)
        .addTo(map);
      var entry = { item: item, marker: marker, popup: popup, anggota: null, klik: false };
      marker.getElement().style.setProperty("--tunda", (urutan * 70) + "ms");
      popup.setDOMContent(kartu(entry, umumkan));
      popup.on("open", function () {
        var lewatKlik = entry.klik;
        entry.klik = false;
        if (lewatKlik && entry.anggota) {
          popup.remove();
          perbesarKelompok(entry.anggota);
          return;
        }
        marker.getElement().classList.add("is-aktif");
        var foto = popup.getElement() && popup.getElement().querySelector(".peta__foto[data-src]");
        if (foto) {
          foto.src = foto.getAttribute("data-src");
          foto.removeAttribute("data-src");
        }
      });
      popup.on("close", function () {
        marker.getElement().classList.remove("is-aktif");
      });
      marker.getElement().addEventListener("pointerdown", function () { entry.klik = true; });
      marker.getElement().addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") entry.klik = true;
      });
      marker.getElement().addEventListener("click", function (event) {
        var lewatPapan = event.detail === 0;
        if (entry.anggota) return;
        window.setTimeout(function () {
          state.flyTo(entry, false);
          if (lewatPapan && popup.isOpen()) {
            var tutup = popup.getElement() && popup.getElement().querySelector(".peta__tutup");
            if (tutup) tutup.focus({ preventScroll: true });
          }
        }, 0);
      });
      return entry;
    });

    var ui;
    var sudahDipusatkan = false;

    function perbesarKelompok(anggota) {
      state.stopTour();
      var kotak = new maplibregl.LngLatBounds();
      anggota.forEach(function (entry) { kotak.extend([entry.item.lng, entry.item.lat]); });
      map.fitBounds(kotak, { padding: 120, maxZoom: 12.5, duration: ms(900) });
    }

    var kabar = document.createElement("p");
    kabar.className = "peta__kabar visually-hidden";
    kabar.setAttribute("aria-live", "polite");

    function umumkan(teks) {
      kabar.textContent = "";
      window.setTimeout(function () { kabar.textContent = teks; }, 60);
    }

    function cari(id) {
      for (var i = 0; i < markers.length; i++) {
        if (markers[i].item.id === id) return markers[i];
      }
      return null;
    }

    function terapkan() {
      if (TOKEN) {
        map.setStyle(mapboxStyle(pilihanGaya()), { diff: true });
      } else {
        tuneBasemap(map, current.gelap);
        applyRelief(map, current.three);
      }
      frame.classList.toggle("is-tiga", current.three);
      frame.classList.toggle("is-gelap", current.gelap);
    }

    function flyToWork(entry, openPopup) {
      map.flyTo({
        center: [entry.item.lng, entry.item.lat],
        offset: [0, Math.round(Math.min(160, frame.clientHeight * 0.3))],
        zoom: 15.2,
        pitch: current.three ? 62 : 0,
        bearing: current.three ? -22 : 0,
        speed: 0.9,
        curve: 1.5,
        duration: ms(2600)
      });
      if (openPopup && !entry.popup.isOpen()) entry.marker.togglePopup();
      tulisHash(entry.item.id);
    }

    function segarkanKartu() {
      markers.forEach(function (entry) {
        entry.popup.setDOMContent(kartu(entry, umumkan));
      });
    }

    var state = {
      dasar: function () { return current.dasar; },
      setDasar: function (dasar) {
        if (!TOKEN || dasar === current.dasar) return;
        current.dasar = dasar;
        tulisLapisan(dasar);
        ui.markDasar(dasar);
        terapkan();
        umumkan(say(TEXT.layerOn).replace("%l", say(NAMA_DASAR[dasar])));
      },
      setThree: function (three) {
        if (three === current.three) return;
        current.three = three;
        if (tigaTombol) tigaTombol.setAttribute("aria-pressed", three ? "true" : "false");
        terapkan();
        if (three) { map.dragRotate.enable(); } else { map.dragRotate.disable(); }
        window.requestAnimationFrame(function () {
          map.easeTo(sudutPandang(three, 900));
        });
      },
      filter: function (kind) {
        state.stopTour();
        current.filter = current.filter === kind ? null : kind;
        ui.markFilter(current.filter);
        var visible = new maplibregl.LngLatBounds();
        markers.forEach(function (entry) {
          var show = !current.filter || entry.item.kind === current.filter;
          entry.marker.getElement().classList.toggle("is-off", !show);
          if (!show && entry.popup.isOpen()) entry.popup.remove();
          if (show) visible.extend([entry.item.lng, entry.item.lat]);
        });
        map.fitBounds(current.filter ? visible : bounds, {
          padding: tepi(),
          maxZoom: current.filter ? 7 : 6,
          duration: ms(700)
        });
        ui.count();
        umumkan(current.filter
          ? say(TEXT.filterOn)
              .replace("%k", say(KIND[current.filter]))
              .replace("%n", jumlahTampil(markers))
              .replace("%t", markers.length)
          : say(TEXT.filterOff).replace("%t", markers.length));
      },
      buka: function (id) {
        var entry = cari(id);
        if (!entry) return false;
        sudahDipusatkan = true;
        state.stopTour();
        if (current.filter && entry.item.kind !== current.filter) state.filter(current.filter);
        flyToWork(entry, true);
        umumkan(say(TEXT.focus).replace("%w", say(entry.item)));
        return true;
      },
      toggleTour: function () {
        if (current.tour) { state.stopTour(); return; }
        current.tourAt = 0;
        function step() {
          var entry = markers[current.tourAt % markers.length];
          current.tourAt++;
          if (!mati(entry)) flyToWork(entry, true);
        }
        step();
        current.tour = window.setInterval(step, 7000);
        ui.markTour(true);
      },
      stopTour: function () {
        if (!current.tour) return;
        window.clearInterval(current.tour);
        current.tour = 0;
        ui.markTour(false);
      },
      flyTo: flyToWork,
      home: function () {
        state.stopTour();
        if (current.filter) {
          current.filter = null;
          ui.markFilter(null);
          markers.forEach(function (entry) {
            entry.marker.getElement().classList.remove("is-off");
          });
        }
        tutupKartu(markers);
        map.easeTo(sudutPandang(current.three, 500));
        map.fitBounds(bounds, { padding: tepi(), maxZoom: 6, duration: ms(750) });
        ui.count();
        tulisHash(null);
      },
      reset: function () {
        state.home();
      }
    };

    ui = buildUi(map, frame, markers, state);
    ui.markDasar(current.dasar);
    section.insertBefore(kabar, section.querySelector(".peta__ket"));
    frame.classList.toggle("is-gelap", current.gelap);
    terjemahkanKontrol();

    var booted = false;
    var sudahSiap = false;

    function siap() {
      if (sudahSiap) return;
      sudahSiap = true;
      if (!TOKEN) {
        tuneBasemap(map, current.gelap);
        applyRelief(map, current.three);
      }
      map.resize();
      if (!sudahDipusatkan) map.fitBounds(bounds, { padding: tepi(), maxZoom: 6, duration: 0 });
      frame.classList.add("is-ready");
      terjemahkanKontrol();

      window.requestAnimationFrame(function () {
        ui.count();
        var id = idDariHash();
        if (id) state.buka(id);
      });
    }

    map.on("load", siap);
    map.on("styledata", siap);
    map.on("idle", siap);
    window.setTimeout(siap, 4000);

    map.on("styledata", function () { booted = true; });

    window.addEventListener("hashchange", function () {
      var id = idDariHash();
      if (id) state.buka(id);
    });

    document.addEventListener("hk:lang", function () {
      ui.label();
      ui.count();
      terjemahkanKontrol();
      if (TOKEN) terapkan();
      segarkanKartu();
    });

    document.addEventListener("hk:tema", function (event) {
      var gelap = Boolean(event && event.detail && event.detail.tema === "dark");
      if (gelap === current.gelap) return;
      current.gelap = gelap;
      terapkan();
    });

    document.addEventListener("fullscreenchange", function () {
      window.setTimeout(terjemahkanKontrol, 0);
    });

    function tanganDiPeta() {
      state.stopTour();
    }

    if (!sentuh()) {
      container.addEventListener("wheel", function (event) {
        if (event.ctrlKey || event.metaKey) {
          map.scrollZoom.enable();
        } else {
          map.scrollZoom.disable();
        }
      }, { capture: true, passive: true });
    }

    container.addEventListener("pointerdown", tanganDiPeta, true);
    container.addEventListener("wheel", tanganDiPeta, { capture: true, passive: true });
    container.addEventListener("keydown", tanganDiPeta, true);
    frame.addEventListener("keydown", function (event) {
      if (event.key === "Escape") tutupKartu(markers);
    });
    map.on("dragstart", tanganDiPeta);

    map.on("rotateend", function () {
      if (!current.three && Math.abs(map.getBearing()) > 0.01) map.setBearing(0);
    });
    map.on("error", function (event) {
      var note = {
        message: (event && event.error && event.error.message) || String(event && event.type),
        source: (event && event.sourceId) || null,
        booted: booted
      };
      (window.HK_PETA_ERRORS = window.HK_PETA_ERRORS || []).push(note);
      if (booted) return;
      if (note.source) return;
      section.classList.add("is-failed");
    });

    window.HK_PETA_STATE = state;

    return map;
  }

  window.HK_PETA = {
    build: build,
    count: WORK.length,
    gaya: mapboxStyle,
    ikon: tambahIkon,
    cadangan: FALLBACK_STYLE
  };
})();
