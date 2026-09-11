/*!
 * Work map. MapLibre GL JS.
 *
 * The module is fetched only when the map section is about to enter the
 * screen, then the map builds itself. No button, nothing to press.
 *
 * Three basemaps, two of which need no key at all, and a 2D or 3D view with
 * real terrain. The points are label positions, not study area boundaries:
 * each marks roughly where the work was done, close enough to find on a map
 * of Indonesia and never presented as a survey coordinate.
 */
(function () {
  "use strict";

  var TOKEN = (window.HK_KONFIG && window.HK_KONFIG.mapboxToken) || "";

  /* Elevation for the relief. Mapbox ships a proper DEM, and without a token
     the free terrarium tiles stand in. */
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

  /* One basemap, drawn here rather than pulled from a Mapbox style URL.
     Mapbox styles address their sources with mapbox:// URLs that MapLibre
     cannot resolve, and the raster version of the same style carries no
     building heights, which is why the 3D buildings never appeared. Reading
     the vector tiles directly fixes both. */
  function mapboxStyle() {
    var source = "https://api.mapbox.com/v4/mapbox.mapbox-streets-v8/{z}/{x}/{y}.vector.pbf?access_token=" + TOKEN;
    var font = ["DIN Pro Regular", "Arial Unicode MS Regular"];

    return {
      version: 8,
      glyphs: "https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=" + TOKEN,
      sources: {
        jalan: { type: "vector", tiles: [source], minzoom: 0, maxzoom: 16, attribution: MAPBOX_ATTRIBUTION },
        dem: DEM
      },
      layers: [
        { id: "latar", type: "background", paint: { "background-color": "#eef1f5" } },
        { id: "bayangan", type: "hillshade", source: "dem",
          paint: { "hillshade-exaggeration": 0.35, "hillshade-shadow-color": "#93a1ad", "hillshade-highlight-color": "#ffffff" } },
        { id: "hijau", type: "fill", source: "jalan", "source-layer": "landuse",
          filter: ["in", ["get", "class"], ["literal", ["park", "grass", "wood", "scrub", "agriculture", "national_park", "pitch"]]],
          paint: { "fill-color": "#e0e9dd", "fill-opacity": 0.85 } },
        { id: "air", type: "fill", source: "jalan", "source-layer": "water",
          paint: { "fill-color": "#c7d9e8" } },
        { id: "sungai", type: "line", source: "jalan", "source-layer": "waterway",
          paint: { "line-color": "#c7d9e8", "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 16, 2.4] } },
        { id: "jalan-tepi", type: "line", source: "jalan", "source-layer": "road", minzoom: 6,
          filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary", "secondary", "tertiary", "street", "street_limited"]]],
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": "#d3dae1",
            "line-width": ["interpolate", ["exponential", 1.4], ["zoom"], 6, 1.2, 12, 4, 18, 22]
          } },
        { id: "jalan-isi", type: "line", source: "jalan", "source-layer": "road", minzoom: 6,
          filter: ["in", ["get", "class"], ["literal", ["motorway", "trunk", "primary", "secondary", "tertiary", "street", "street_limited"]]],
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["match", ["get", "class"], "motorway", "#ffffff", "trunk", "#ffffff", "#fbfcfd"],
            "line-width": ["interpolate", ["exponential", 1.4], ["zoom"], 6, 0.5, 12, 2.4, 18, 17]
          } },
        { id: "gedung", type: "fill", source: "jalan", "source-layer": "building", minzoom: 14,
          filter: ["!=", ["get", "underground"], true],
          paint: { "fill-color": "#dfe4ea", "fill-outline-color": "#ccd3db" } },
        { id: "batas", type: "line", source: "jalan", "source-layer": "admin",
          filter: ["<=", ["get", "admin_level"], 2],
          paint: {
            "line-color": "#a7b1bc",
            "line-dasharray": [2.5, 1.5],
            "line-width": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 10, 1.4]
          } },
        { id: "nama-tempat", type: "symbol", source: "jalan", "source-layer": "place_label",
          filter: ["in", ["get", "class"], ["literal", ["country", "state", "settlement", "settlement_subdivision"]]],
          layout: {
            "text-field": ["get", "name_en"],
            "text-font": font,
            "text-size": ["interpolate", ["linear"], ["zoom"], 3, 10, 8, 13, 14, 16],
            "text-max-width": 8
          },
          paint: { "text-color": "#41505e", "text-halo-color": "#ffffff", "text-halo-width": 1.4 } },
        { id: "nama-alam", type: "symbol", source: "jalan", "source-layer": "natural_label", minzoom: 4,
          filter: ["in", ["get", "class"], ["literal", ["sea", "ocean", "bay"]]],
          layout: {
            "text-field": ["get", "name_en"],
            "text-font": font,
            "text-size": ["interpolate", ["linear"], ["zoom"], 4, 10, 10, 13],
            "text-max-width": 8
          },
          paint: { "text-color": "#7d94a8", "text-halo-color": "#ffffff", "text-halo-width": 1 } }
      ]
    };
  }

  var FALLBACK_STYLE = "https://tiles.openfreemap.org/styles/positron";

  function currentStyle() {
    return TOKEN ? mapboxStyle() : FALLBACK_STYLE;
  }

  /* one colour per kind of work, all four readable on every basemap */
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
    more: { en: "and %n more", ind: "dan %n lainnya" }
  };

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

  /* ----------------------------------------------------------- basemap tone */

  /* Positron is already quiet. These nudges pull it the rest of the way
     towards the site palette. Every change is guarded, a missing layer must
     never break the map. */
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
      } catch (e) { /* style changed upstream, leave that layer alone */ }
    });
  }

  /* ------------------------------------------------------------ 2D and 3D */

  /* Terrain rides on its own source, so it survives a basemap change: the
     source is added again after every style load. Buildings are only raised
     where the style actually carries them, which is the vector basemap. */
  function applyRelief(map, three) {
    /* Trying and retrying beats asking first. isStyleLoaded() stays false for
       as long as tiles keep arriving, so waiting on it meant the relief was
       never applied on a slow connection. */
    function run() {
      try {
        if (!map.getSource("dem")) map.addSource("dem", DEM);

        if (three) {
          map.setTerrain({ source: "dem", exaggeration: 1.3 });

          /* Mapbox Streets carries a height on every building, so the
             extrusion is real rather than a flat guess. The 2D footprints
             step aside to stop the two fighting over the same pixels. */
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
                  0, "#e3e7ec", 20, "#d7dce3", 60, "#c9d0d9", 140, "#b9c2cd"],
                "fill-extrusion-height": ["coalesce", ["get", "height"], 6],
                "fill-extrusion-base": ["coalesce", ["get", "min_height"], 0],
                "fill-extrusion-opacity": 0.92,
                "fill-extrusion-vertical-gradient": true
              }
            });
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

  /* ------------------------------------------------------- home control */

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

  /* ---------------------------------------------------------------- markers */

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

  /* ------------------------------------------------------------------ panel */

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
    try { window.localStorage.setItem(PANEL_KEY, collapsed ? "tutup" : "buka"); } catch (e) { /* private mode */ }
  }

  function buildPanel(map, markers, bounds, state) {
    var box = document.createElement("div");
    box.className = "peta__legenda";

    /* the panel can be folded away, and it remembers that between visits */
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

    /* 2D or 3D, and the guided tour */
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

    /* legend */
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

    /* the numbers answer one question only: what is on screen right now, and
       they are recomputed while the map is still moving, not after it stops */
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

  /* ------------------------------------------------------------------ build */

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
      cooperativeGestures: true
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), "top-right");
    map.addControl(new HomeControl(function () { state.home(); }), "top-right");
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");
    /* every style ships its own credit line, adding ours would repeat it */
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

    function dressStyle() {
      if (!TOKEN) tuneBasemap(map);
      applyRelief(map, current.three);
    }

    /* close enough to read the streets, tilted enough to see the buildings */
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
      /* a click on the marker has already opened its popup, only the tour
         needs to open one itself */
      if (openPopup && !entry.popup.isOpen()) entry.marker.togglePopup();
    }

    var state = {
      setThree: function (three) {
        if (three === current.three) return;
        current.three = three;
        panel.markView(three);
        applyRelief(map, three);
        /* switching terrain on rebuilds the camera transform, which cancels
           any move started in the same tick. The tilt waits one frame. */
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
      },
      /* one work at a time, close in, until someone touches the map */
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
      },
      reset: function () {
        state.home();
      }
    };

    panel = buildPanel(map, markers, bounds, state);
    var section = container.parentNode.parentNode;
    section.insertBefore(panel.node, section.querySelector(".peta__ket"));

    map.on("load", function () {
      dressStyle();
      map.resize();
      map.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
      map.once("idle", panel.count);
      container.parentNode.classList.add("is-ready");
    });

    /* Only a map that never starts counts as a failure. A single tile that
       404s, or a style layer the renderer skips, must not replace a working
       map with an error message. */
    var booted = false;
    var section = container.parentNode.parentNode;

    map.on("load", function () { booted = true; });

    /* the tour is a suggestion, not a ride: any hand on the map stops it */
    ["dragstart", "wheel", "touchstart"].forEach(function (kind) {
      map.on(kind, function () { state.stopTour(); });
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
    /* no blanket timeout here: a slow connection is not a failure, and a
       reader on a weak signal should get the map late rather than a notice
       saying it broke */

    /* exposed for the browser console, handy when checking the map by hand */
    window.HK_PETA_STATE = state;

    return map;
  }

  window.HK_PETA = { build: build, count: WORK.length };
})();
