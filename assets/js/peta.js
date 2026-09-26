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

  var KELOMPOK_POI = ["match", ["get", "class"],
    "park_like", "#6f9a63",
    "medical", "#b2626a",
    "education", "#6b7fa8",
    ["food_and_drink", "food_and_drink_stores", "store_like", "commercial_services"], "#a8815f",
    "religion", "#8c7aa6",
    "#8c99a6"];

  function mapboxStyle() {
    var source = "https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN;
    var reguler = ["DIN Pro Regular", "Arial Unicode MS Regular"];
    var tebal = ["DIN Pro Medium", "Arial Unicode MS Regular"];
    var miring = ["DIN Pro Italic", "Arial Unicode MS Regular"];
    var nama = labelField();

    var TOL = ["motorway", "motorway_link", "trunk", "trunk_link"];
    var ARTERI = ["primary", "primary_link", "secondary", "secondary_link"];
    var SEDANG = ["tertiary", "tertiary_link"];
    var JALAN = ["street", "street_limited", "residential", "service", "track"];

    function isClass(list) {
      return ["in", ["get", "class"], ["literal", list]];
    }

    return {
      version: 8,
      glyphs: "https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=" + TOKEN,
      sources: {
        jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
        dem: DEM,
        provinsi: { type: "geojson", data: PROVINSI_ID }
      },
      layers: [
        { id: "latar", type: "background", paint: { "background-color": "#e8ecf1" } },
        { id: "bayangan", type: "hillshade", source: "dem",
          paint: { "hillshade-exaggeration": 0.32, "hillshade-shadow-color": "#96a4b0", "hillshade-highlight-color": "#ffffff" } },
        { id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
          filter: ["in", ["get", "class"], ["literal", ["park", "grass", "wood", "scrub", "agriculture", "national_park", "pitch", "cemetery"]]],
          paint: { "fill-color": "#dfe9dc", "fill-opacity": 0.85 } },
        { id: "air", type: "fill", source: "jalan", "source-layer": "water",
          paint: { "fill-color": "#c3d7e8" } },
        { id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
          paint: { "line-color": "#c3d7e8", "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 16, 2.4] } },

        { id: "batas-kabupaten", type: "line", source: "jalan", "source-layer": "admin", minzoom: 5,
          filter: ["all", ["==", ["get", "admin_level"], 2], ["!=", ["get", "maritime"], "true"]],
          paint: {
            "line-color": "#98a6b3",
            "line-dasharray": [1.4, 1.6],
            "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.5, 10, 1.2, 14, 1.8],
            "line-opacity": 0.8
          } },
        { id: "batas-provinsi", type: "line", source: "jalan", "source-layer": "admin",
          filter: ["all", ["==", ["get", "admin_level"], 1], ["!=", ["get", "maritime"], "true"]],
          paint: {
            "line-color": "#6d7e8e",
            "line-dasharray": [3, 1.6],
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.8, 8, 1.7, 14, 2.8]
          } },
        { id: "batas-negara", type: "line", source: "jalan", "source-layer": "admin",
          filter: ["==", ["get", "admin_level"], 0],
          paint: {
            "line-color": "#54626f",
            "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.8, 8, 2, 14, 3.4]
          } },

        { id: "jalan-kecil-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 12,
          filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#c2ccd9", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 12, 1.5, 18, 14] } },
        { id: "jalan-sedang-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
          filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#b5c2d1", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 10, 1.6, 14, 5, 18, 17] } },
        { id: "arteri-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
          filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#d8bd7e", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 7, 1.8, 12, 5.5, 18, 21] } },
        { id: "tol-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
          filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#dd9a2b", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 4, 2, 10, 6.4, 18, 25] } },

        { id: "jalan-kecil", type: "line", source: "jalan", "source-layer": "road", minzoom: 12,
          filter: isClass(JALAN), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 12, 0.6, 18, 11] } },
        { id: "jalan-sedang", type: "line", source: "jalan", "source-layer": "road", minzoom: 10,
          filter: isClass(SEDANG), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 10, 0.7, 14, 2.8, 18, 13] } },
        { id: "arteri", type: "line", source: "jalan", "source-layer": "road", minzoom: 7,
          filter: isClass(ARTERI), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#ffefcd", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 7, 0.8, 12, 3.4, 18, 17] } },
        { id: "tol", type: "line", source: "jalan", "source-layer": "road", minzoom: 4,
          filter: isClass(TOL), layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#ffd27f", "line-width": ["interpolate", ["exponential", 1.5], ["zoom"], 4, 1, 10, 4.4, 18, 20] } },

        { id: "apron", type: "fill", source: "jalan", "source-layer": "aeroway", minzoom: 11,
          filter: ["in", ["get", "type"], ["literal", ["apron", "helipad"]]],
          paint: { "fill-color": "#dfe4eb" } },
        { id: "landasan", type: "line", source: "jalan", "source-layer": "aeroway", minzoom: 10,
          filter: ["in", ["get", "type"], ["literal", ["runway", "taxiway"]]],
          paint: {
            "line-color": "#d3dae3",
            "line-width": ["interpolate", ["exponential", 1.5], ["zoom"],
              10, ["match", ["get", "type"], "runway", 1.6, 0.6],
              16, ["match", ["get", "type"], "runway", 14, 5]]
          } },
        { id: "rel", type: "line", source: "jalan", "source-layer": "road", minzoom: 11,
          filter: ["==", ["get", "class"], "major_rail"],
          paint: { "line-color": "#a6b2bf", "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.9, 18, 3.2] } },
        { id: "rel-palang", type: "line", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: ["==", ["get", "class"], "major_rail"],
          paint: {
            "line-color": "#ffffff", "line-dasharray": [2, 3],
            "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 18, 2]
          } },

        { id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
          filter: ["!=", ["get", "underground"], true],
          paint: { "fill-color": "#dde2e9", "fill-outline-color": "#c7cfd9" } },

        { id: "panah-searah", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 15,
          filter: ["all", ["==", ["get", "oneway"], "true"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
          layout: {
            "symbol-placement": "line",
            "symbol-spacing": 110,
            "text-field": "\u25b8",
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 15, 9, 18, 13],
            "text-allow-overlap": true,
            "text-ignore-placement": true,
            "text-rotation-alignment": "map",
            "text-keep-upright": false,
            "text-padding": 0
          },
          paint: { "text-color": "#9fadbb", "text-halo-color": "#ffffff", "text-halo-width": 1 } },

        { id: "titik-poi", type: "circle", source: "jalan", "source-layer": "poi_label", minzoom: 15.5,
          filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 16, 2, 17, 3]],
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 15, 2.2, 18, 3.8],
            "circle-color": KELOMPOK_POI,
            "circle-stroke-width": 1,
            "circle-stroke-color": "#ffffff"
          } },
        { id: "nama-poi", type: "symbol", source: "jalan", "source-layer": "poi_label", minzoom: 15.5,
          filter: ["<=", ["to-number", ["get", "filterrank"], 5], ["step", ["zoom"], 1, 16, 2, 17, 3]],
          layout: {
            "text-field": nama,
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 15.5, 10, 18, 12],
            "text-anchor": "top",
            "text-offset": [0, 0.6],
            "text-max-width": 9,
            "symbol-sort-key": ["to-number", ["get", "sizerank"], 30]
          },
          paint: { "text-color": "#5d6a77", "text-halo-color": "#ffffff", "text-halo-width": 1.4 } },

        { id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 3,
          filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay", "water", "landform"]]],
          layout: {
            "text-field": nama,
            "text-font": miring,
            "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10, 10, 13],
            "text-max-width": 8
          },
          paint: { "text-color": "#7593aa", "text-halo-color": "#ffffff", "text-halo-width": 1 } },

        { id: "nama-kelurahan", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 12,
          filter: ["==", ["get", "class"], "settlement_subdivision"],
          layout: {
            "text-field": nama,
            "text-font": reguler,
            "text-size": 11,
            "text-max-width": 8,
            "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
          },
          paint: { "text-color": "#68757f", "text-halo-color": "#ffffff", "text-halo-width": 1.2 } },

        { id: "nama-kota", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 3,
          filter: ["all",
            ["==", ["get", "class"], "settlement"],
            ["<=", ["to-number", ["get", "filterrank"], 5],
              ["step", ["zoom"], 2, 5, 3, 7, 4, 9, 5]]],
          layout: {
            "text-field": nama,
            "text-font": tebal,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 9, 13, 14, 17],
            "text-max-width": 8,
            "symbol-sort-key": ["to-number", ["get", "symbolrank"], 20]
          },
          paint: { "text-color": "#2f3b46", "text-halo-color": "#ffffff", "text-halo-width": 1.5 } },
        { id: "nama-jalan", type: "symbol", source: "jalan", "source-layer": "road", minzoom: 13,
          filter: ["all", ["has", "name"], isClass(TOL.concat(ARTERI, SEDANG, JALAN))],
          layout: {
            "symbol-placement": "line",
            "symbol-spacing": 250,
            "text-field": nama,
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 13, 11, 18, 13],
            "text-max-angle": 40,
            "text-padding": 2,
            "text-rotation-alignment": "map"
          },
          paint: { "text-color": "#46535f", "text-halo-color": "#ffffff", "text-halo-width": 1.6 } },

        { id: "nama-provinsi", type: "symbol", source: "jalan", "source-layer": "place_label", minzoom: 5, maxzoom: 11,
          filter: ["==", ["get", "class"], "state"],
          layout: {
            "text-field": nama,
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 8, 12],
            "text-transform": "uppercase",
            "text-letter-spacing": 0.12,
            "text-max-width": 9
          },
          paint: { "text-color": "#6d7e8e", "text-halo-color": "#ffffff", "text-halo-width": 1.3 } },
        { id: "nama-provinsi-id", type: "symbol", source: "provinsi", minzoom: 5, maxzoom: 10.5,
          layout: {
            "text-field": nama,
            "text-font": reguler,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 8, 12.5],
            "text-transform": "uppercase",
            "text-letter-spacing": 0.12,
            "text-max-width": 9
          },
          paint: { "text-color": "#67788a", "text-halo-color": "#ffffff", "text-halo-width": 1.6 } },
        { id: "nama-negara", type: "symbol", source: "jalan", "source-layer": "place_label", maxzoom: 5,
          filter: ["==", ["get", "class"], "country"],
          layout: {
            "text-field": nama,
            "text-font": tebal,
            "text-size": ["interpolate", ["linear"], ["zoom"], 2, 11, 6, 15],
            "text-transform": "uppercase",
            "text-letter-spacing": 0.1,
            "text-max-width": 8
          },
          paint: { "text-color": "#33404c", "text-halo-color": "#ffffff", "text-halo-width": 1.6 } }
      ]
    };
  }

  var LAYER_NAMA = [
    "nama-jalan", "nama-kelurahan", "nama-kota", "nama-provinsi", "nama-provinsi-id",
    "nama-negara", "nama-alam", "nama-poi"
  ];

  function retitleLabels(map) {
    var field = labelField();
    LAYER_NAMA.forEach(function (id) {
      try {
        if (map.getLayer(id)) map.setLayoutProperty(id, "text-field", field);
      } catch (e) {  }
    });
  }

  var FALLBACK_STYLE = "https://tiles.openfreemap.org/styles/positron";

  function currentStyle() {
    return TOKEN ? mapboxStyle() : FALLBACK_STYLE;
  }

  var KIND = {
    app: { colour: "#276ef1", en: "Map app", ind: "Aplikasi peta" },
    analysis: { colour: "#0b0b0b", en: "Map analysis", ind: "Analisis peta" },
    satellite: { colour: "#e11900", en: "Satellite data", ind: "Data satelit" },
    design: { colour: "#05944f", en: "Map design", ind: "Desain peta" }
  };

  var WORK = [
    { id: "parking", kind: "app", lng: 110.3656, lat: -7.7925,
      en: "Yogyakarta Parking Map", ind: "Peta Parkir Yogyakarta" },
    { id: "landcover", kind: "design", lng: 110.4050, lat: -7.7550,
      en: "Yogyakarta Land Cover Map", ind: "Peta Tutupan Lahan Yogyakarta" },
    { id: "fire", kind: "satellite", lng: 113.2000, lat: -1.6000,
      en: "Kalimantan Fire Maps", ind: "Peta Kebakaran Kalimantan" },
    { id: "fish", kind: "analysis", lng: 108.2200, lat: 3.7000,
      en: "Fish Landing Sites, Natuna", ind: "Lokasi Pendaratan Ikan, Natuna" },
    { id: "pickup", kind: "analysis", lng: 106.8200, lat: -6.2100,
      en: "Pickup Points from GPS Pings, Jakarta", ind: "Titik Jemput dari Ping GPS, Jakarta" },
    { id: "reach", kind: "analysis", lng: 136.0800, lat: -1.1800,
      en: "Service Reach, Biak Numfor", ind: "Jangkauan Layanan, Biak Numfor" },
    { id: "mimika", kind: "satellite", lng: 137.0000, lat: -4.3500,
      en: "Mining and Forest Loss, Mimika", ind: "Tambang dan Hutan Hilang, Mimika" }
  ];

  var AWALAN_HASH = "#peta-";

  function idDariHash() {
    var hash = window.location.hash || "";
    if (hash.indexOf(AWALAN_HASH) !== 0) return null;
    var id = hash.slice(AWALAN_HASH.length);
    for (var i = 0; i < WORK.length; i++) {
      if (WORK[i].id === id) return id;
    }
    return null;
  }

  function tulisHash(id) {
    if (!window.history || !window.history.replaceState) return;
    if (id && window.location.hash === AWALAN_HASH + id) return;
    if (!id && !window.location.hash) return;
    var alamat = id ? AWALAN_HASH + id : window.location.pathname + window.location.search;
    try {
      window.history.replaceState(null, "", alamat);
    } catch (e) {  }
  }

  var TEXT = {
    view: { en: "View", ind: "Tampilan" },
    tour: { en: "Tour", ind: "Jelajah" },
    legend: { en: "Legend", ind: "Legenda" },
    open: { en: "See the project", ind: "Lihat proyek" },
    reset: { en: "Reset view", ind: "Kembalikan tampilan" },
    home: { en: "Back to the starting view", ind: "Kembali ke posisi semula" },
    panel: { en: "Map options", ind: "Pilihan peta" },
    hide: { en: "Hide", ind: "Sembunyikan" },
    show: { en: "Show", ind: "Tampilkan" },
    inView: { en: "in view", ind: "terlihat" },
    of: { en: "of", ind: "dari" },
    none: { en: "Nothing in view", ind: "Tidak ada yang terlihat" },
    more: { en: "and %n more", ind: "dan %n lainnya" },
    filterOn: { en: "%k. %n of %t works shown.", ind: "%k. %n dari %t karya ditampilkan." },
    filterOff: { en: "Filter off. All %t works shown.", ind: "Saringan mati. Semua %t karya ditampilkan." },
    focus: { en: "%w, centred on the map.", ind: "%w, dipusatkan di peta." }
  };

  function sentuh() {
    return Boolean(window.matchMedia
      && window.matchMedia("(hover: none) and (pointer: coarse)").matches);
  }

  function reducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function ms(duration) {
    return reducedMotion() ? 0 : duration;
  }

  function isId() {
    return document.documentElement.getAttribute("lang") === "id";
  }

  function say(entry) {
    return isId() ? entry.ind : entry.en;
  }


  function tuneBasemap(map) {
    var tweaks = [
      ["water", "fill-color", "#dbe3ea"],
      ["water_shadow", "fill-color", "#dbe3ea"],
      ["landcover_wood", "fill-color", "#eceee9"],
      ["landcover_grass", "fill-color", "#eef0ec"],
      ["landuse_residential", "fill-color", "#f2f2f2"],
      ["building", "fill-color", "#e9e9e9"],
      ["background", "background-color", "#f7f7f7"]
    ];
    tweaks.forEach(function (item) {
      try {
        if (map.getLayer(item[0])) map.setPaintProperty(item[0], item[1], item[2]);
      } catch (e) {  }
    });
  }


  function applyRelief(map, three) {
    function run() {
      try {
        if (!map.getSource("dem")) map.addSource("dem", DEM);

        if (three) {
          map.setTerrain({ source: "dem", exaggeration: 1.3 });

          if (map.getSource("jalan") && !map.getLayer("gedung3d")) {
            map.addLayer({
              id: "gedung3d",
              type: "fill-extrusion",
              source: "jalan",
              "source-layer": "building",
              minzoom: 13.5,
              filter: ["all",
                ["==", ["get", "extrude"], "true"],
                ["!=", ["get", "underground"], "true"]],
              paint: {
                "fill-extrusion-color": ["interpolate", ["linear"], ["get", "height"],
                  0, "#e9edf2", 3, "#dbe1e9", 6, "#cdd5e0", 14, "#b9c3d1", 40, "#a5b0c0"],
                "fill-extrusion-height": ["coalesce", ["get", "height"], 6],
                "fill-extrusion-base": ["coalesce", ["get", "min_height"], 0],
                "fill-extrusion-opacity": 0.92,
                "fill-extrusion-vertical-gradient": true
              }
            }, map.getLayer("panah-searah") ? "panah-searah" : undefined);
          }
          if (map.getLayer("gedung")) map.setLayoutProperty("gedung", "visibility", "none");
        } else {
          map.setTerrain(null);
          if (map.getLayer("gedung3d")) map.removeLayer("gedung3d");
          if (map.getLayer("gedung")) map.setLayoutProperty("gedung", "visibility", "visible");
        }
        return true;
      } catch (e) {
        return false;
      }
    }

    if (run()) return;
    map.once("styledata", run);
    map.once("idle", run);
  }


  function HomeControl(onClick) {
    this._click = onClick;
  }

  HomeControl.prototype.onAdd = function () {
    var wrap = document.createElement("div");
    wrap.className = "maplibregl-ctrl maplibregl-ctrl-group";

    var button = document.createElement("button");
    button.type = "button";
    button.className = "peta__rumah";
    button.title = say(TEXT.home);
    button.setAttribute("aria-label", say(TEXT.home));
    button.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"></path>' +
      '<path d="M9 21v-7h6v7"></path></svg>';
    button.addEventListener("click", this._click);

    document.addEventListener("hk:lang", function () {
      button.title = say(TEXT.home);
      button.setAttribute("aria-label", say(TEXT.home));
    });

    wrap.appendChild(button);
    this._wrap = wrap;
    return wrap;
  };

  HomeControl.prototype.onRemove = function () {
    if (this._wrap && this._wrap.parentNode) this._wrap.parentNode.removeChild(this._wrap);
  };


  function markerElement(item) {
    var el = document.createElement("button");
    el.type = "button";
    el.className = "peta__pin";
    el.setAttribute("data-work", item.id);
    el.setAttribute("data-kind", item.kind);
    el.title = say(item);
    el.setAttribute("aria-label", say(item));
    return el;
  }

  function popupHtml(item) {
    return (
      '<span class="peta__kind peta__kind--' + item.kind + '">' + say(KIND[item.kind]) + "</span>" +
      "<strong>" + say(item) + "</strong>" +
      '<a href="#karya-' + item.id + '">' + say(TEXT.open) + "</a>"
    );
  }


  function chip(text, pressed) {
    var el = document.createElement("button");
    el.type = "button";
    el.className = "peta__chip";
    el.textContent = text;
    el.setAttribute("aria-pressed", pressed ? "true" : "false");
    return el;
  }

  var PANEL_KEY = "hk-peta-panel";

  function readPanelState() {
    try { return window.localStorage.getItem(PANEL_KEY) === "tutup"; } catch (e) { return false; }
  }

  function writePanelState(collapsed) {
    try { window.localStorage.setItem(PANEL_KEY, collapsed ? "tutup" : "buka"); } catch (e) {  }
  }

  function buildPanel(map, markers, bounds, state) {
    var box = document.createElement("div");
    box.className = "peta__legenda";

    var header = document.createElement("div");
    header.className = "peta__kepala";
    var heading = document.createElement("span");
    heading.className = "peta__kepala-judul";
    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "peta__lipat";
    toggle.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg>';
    header.appendChild(heading);
    header.appendChild(toggle);
    box.appendChild(header);

    var collapsed = readPanelState();

    function paintToggle() {
      box.classList.toggle("is-collapsed", collapsed);
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      var word = say(collapsed ? TEXT.show : TEXT.hide) + " " + say(TEXT.panel).toLowerCase();
      toggle.title = word;
      toggle.setAttribute("aria-label", word);
    }

    toggle.addEventListener("click", function () {
      collapsed = !collapsed;
      writePanelState(collapsed);
      paintToggle();
      window.setTimeout(function () { map.resize(); }, 220);
    });

    var groups = {};
    function group(key) {
      var wrap = document.createElement("div");
      wrap.className = "peta__grup";
      var title = document.createElement("p");
      title.className = "peta__legenda-judul";
      wrap.appendChild(title);
      box.appendChild(wrap);
      groups[key] = { wrap: wrap, title: title };
      return wrap;
    }

    var viewWrap = group("view");
    var viewRow = document.createElement("div");
    viewRow.className = "peta__chips";
    viewWrap.appendChild(viewRow);
    var flat = chip("2D", true);
    var relief = chip("3D", false);
    var tour = chip("", false);
    flat.addEventListener("click", function () { state.setThree(false); });
    relief.addEventListener("click", function () { state.setThree(true); });
    tour.addEventListener("click", function () { state.toggleTour(); });
    viewRow.appendChild(flat);
    viewRow.appendChild(relief);
    viewRow.appendChild(tour);

    var legendWrap = group("legend");

    var summary = document.createElement("p");
    summary.className = "peta__ringkas";
    legendWrap.appendChild(summary);
    var rows = {};
    Object.keys(KIND).forEach(function (key) {
      var row = document.createElement("button");
      row.type = "button";
      row.className = "peta__baris";
      row.setAttribute("data-kind", key);
      row.setAttribute("aria-pressed", "false");
      row.innerHTML = '<i></i><span class="peta__nama"></span><span class="peta__angka">0</span>';
      row.addEventListener("click", function () { state.filter(key); });
      legendWrap.appendChild(row);
      rows[key] = row;
    });

    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "peta__reset";
    reset.addEventListener("click", function () { state.reset(); });
    legendWrap.appendChild(reset);

    function label() {
      heading.textContent = say(TEXT.panel);
      paintToggle();
      tour.textContent = say(TEXT.tour);
      groups.view.title.textContent = say(TEXT.view);
      groups.legend.title.textContent = say(TEXT.legend);
      reset.textContent = say(TEXT.reset);
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__nama").textContent = say(KIND[key]);
      });
    }

    function count() {
      var view = map.getBounds();
      var seen = { app: 0, analysis: 0, satellite: 0, design: 0 };
      var names = [];
      var total = 0;

      markers.forEach(function (entry) {
        if (entry.marker.getElement().classList.contains("is-off")) return;
        total++;
        if (!view.contains([entry.item.lng, entry.item.lat])) return;
        seen[entry.item.kind]++;
        names.push(say(entry.item));
      });

      var shown = names.length;
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__angka").textContent = seen[key];
        rows[key].classList.toggle("is-empty", seen[key] === 0);
      });

      if (shown === 0) {
        summary.textContent = say(TEXT.none);
      } else {
        var head = shown + " " + say(TEXT.of) + " " + total + " " + say(TEXT.inView);
        var list = names.slice(0, 2).join(", ");
        if (names.length > 2) {
          list += ", " + say(TEXT.more).replace("%n", names.length - 2);
        }
        summary.textContent = head + ". " + list + ".";
      }
    }

    var pending = 0;
    function countSoon() {
      if (pending) return;
      pending = window.requestAnimationFrame(function () {
        pending = 0;
        count();
      });
    }

    label();
    map.on("move", countSoon);
    map.on("moveend", count);
    map.on("zoom", countSoon);
    document.addEventListener("hk:lang", function () {
      label();
      count();
      if (TOKEN) retitleLabels(map);
      markers.forEach(function (entry) {
        entry.marker.getElement().title = say(entry.item);
        entry.marker.getElement().setAttribute("aria-label", say(entry.item));
        entry.popup.setHTML(popupHtml(entry.item));
      });
    });

    return {
      node: box,
      count: count,
      markTour: function (running) {
        tour.setAttribute("aria-pressed", running ? "true" : "false");
      },
      markView: function (three) {
        flat.setAttribute("aria-pressed", three ? "false" : "true");
        relief.setAttribute("aria-pressed", three ? "true" : "false");
      },
      markFilter: function (kind) {
        Object.keys(rows).forEach(function (key) {
          rows[key].setAttribute("aria-pressed", kind === key ? "true" : "false");
        });
        box.classList.toggle("is-filtered", Boolean(kind));
      }
    };
  }


  function build(container) {
    var bounds = new maplibregl.LngLatBounds();
    WORK.forEach(function (item) { bounds.extend([item.lng, item.lat]); });

    var map = new maplibregl.Map({
      container: container,
      style: currentStyle(),
      bounds: bounds,
      fitBoundsOptions: { padding: 56, maxZoom: 6 },
      minZoom: 2.5,
      maxZoom: 17,
      maxPitch: 75,
      attributionControl: false,
      cooperativeGestures: sentuh(),
      scrollZoom: sentuh()
    });


    map.touchZoomRotate.disableRotation();
    map.dragRotate.disable();

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
    map.addControl(new HomeControl(function () { state.home(); }), "top-right");
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

    var markers = WORK.map(function (item) {
      var popup = new maplibregl.Popup({ offset: 18, closeButton: false, className: "peta__popup" })
        .setHTML(popupHtml(item));
      var marker = new maplibregl.Marker({ element: markerElement(item) })
        .setLngLat([item.lng, item.lat])
        .setPopup(popup)
        .addTo(map);
      var entry = { item: item, marker: marker, popup: popup };
      marker.getElement().addEventListener("click", function () {
        window.setTimeout(function () { state.flyTo(entry, false); }, 0);
      });
      return entry;
    });

    var current = { three: false, filter: null, tour: 0, tourAt: 0 };
    var panel;
    var sudahDipusatkan = false;

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

    function dressStyle() {
      if (!TOKEN) tuneBasemap(map);
      applyRelief(map, current.three);
    }

    function flyToWork(entry, openPopup) {
      map.flyTo({
        center: [entry.item.lng, entry.item.lat],
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

    var state = {
      setThree: function (three) {
        if (three === current.three) return;
        current.three = three;
        panel.markView(three);
        applyRelief(map, three);
        if (three) { map.dragRotate.enable(); } else { map.dragRotate.disable(); }
        window.requestAnimationFrame(function () {
          map.easeTo({
            pitch: three ? 58 : 0,
            bearing: three ? -18 : 0,
            duration: ms(900)
          });
        });
      },
      filter: function (kind) {
        state.stopTour();
        current.filter = current.filter === kind ? null : kind;
        panel.markFilter(current.filter);
        var visible = new maplibregl.LngLatBounds();
        markers.forEach(function (entry) {
          var show = !current.filter || entry.item.kind === current.filter;
          entry.marker.getElement().classList.toggle("is-off", !show);
          if (show) visible.extend([entry.item.lng, entry.item.lat]);
        });
        map.fitBounds(current.filter ? visible : bounds, {
          padding: 56,
          maxZoom: current.filter ? 7 : 6,
          duration: ms(700)
        });
        panel.count();
        var tampil = markers.filter(function (entry) {
          return !entry.marker.getElement().classList.contains("is-off");
        }).length;
        umumkan(current.filter
          ? say(TEXT.filterOn)
              .replace("%k", say(KIND[current.filter]))
              .replace("%n", tampil)
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
          if (!entry.marker.getElement().classList.contains("is-off")) flyToWork(entry, true);
        }
        step();
        current.tour = window.setInterval(step, 7000);
        panel.markTour(true);
      },
      stopTour: function () {
        if (!current.tour) return;
        window.clearInterval(current.tour);
        current.tour = 0;
        panel.markTour(false);
      },
      flyTo: flyToWork,
      home: function () {
        state.stopTour();
        if (current.filter) {
          current.filter = null;
          panel.markFilter(null);
          markers.forEach(function (entry) {
            entry.marker.getElement().classList.remove("is-off");
          });
        }
        markers.forEach(function (entry) {
          if (entry.popup.isOpen()) entry.popup.remove();
        });
        map.easeTo({
          pitch: current.three ? 58 : 0,
          bearing: current.three ? -18 : 0,
          duration: ms(500)
        });
        map.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: ms(750) });
        panel.count();
        tulisHash(null);
      },
      reset: function () {
        state.home();
      }
    };

    panel = buildPanel(map, markers, bounds, state);
    var section = container.parentNode.parentNode;
    section.insertBefore(panel.node, section.querySelector(".peta__ket"));
    section.insertBefore(kabar, section.querySelector(".peta__ket"));

    var booted = false;

    var sudahSiap = false;

    function siap() {
      if (sudahSiap) return;
      sudahSiap = true;
      dressStyle();
      map.resize();
      if (!sudahDipusatkan) map.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
      container.parentNode.classList.add("is-ready");

      window.requestAnimationFrame(function () {
        panel.count();
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

  window.HK_PETA = { build: build, count: WORK.length };
})();
