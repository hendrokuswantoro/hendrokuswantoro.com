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

  /* free, no key, OpenStreetMap data rendered as quiet vector tiles */
  var STYLE_PETA = "https://tiles.openfreemap.org/styles/positron";

  /* terrain for the 3D view, free elevation tiles in terrarium encoding */
  var DEM = {
    type: "raster-dem",
    tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
    encoding: "terrarium",
    tileSize: 256,
    maxzoom: 14,
    attribution: "Elevation: Mapzen, AWS Open Data"
  };

  function rasterStyle(tiles, attribution, maxzoom) {
    return {
      version: 8,
      sources: { dasar: { type: "raster", tiles: [tiles], tileSize: 256, maxzoom: maxzoom || 19, attribution: attribution } },
      layers: [
        { id: "latar", type: "background", paint: { "background-color": "#e9ebee" } },
        { id: "dasar", type: "raster", source: "dasar" }
      ]
    };
  }

  var ESRI_IMAGERY =
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

  function mapboxRaster(style) {
    return (
      "https://api.mapbox.com/styles/v1/mapbox/" + style +
      "/tiles/256/{z}/{x}/{y}@2x?access_token=" + TOKEN
    );
  }

  /* the satellite view prefers Mapbox when a token is present, otherwise it
     falls back to Esri imagery, which needs no key */
  var BASEMAPS = [
    { id: "peta", en: "Map", ind: "Peta", style: STYLE_PETA, vector: true },
    {
      id: "satelit", en: "Satellite", ind: "Satelit",
      style: TOKEN
        ? rasterStyle(mapboxRaster("satellite-streets-v12"), "&copy; Mapbox &copy; OpenStreetMap &copy; Maxar")
        : rasterStyle(ESRI_IMAGERY, "Imagery: Esri, Maxar, Earthstar Geographics", 18)
    }
  ];

  if (TOKEN) {
    BASEMAPS.push({
      id: "mapbox", en: "Mapbox", ind: "Mapbox",
      style: rasterStyle(mapboxRaster("streets-v12"), "&copy; Mapbox &copy; OpenStreetMap")
    });
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
    basemap: { en: "Basemap", ind: "Peta dasar" },
    view: { en: "View", ind: "Tampilan" },
    legend: { en: "Legend", ind: "Legenda" },
    open: { en: "See the project", ind: "Lihat proyek" },
    reset: { en: "Reset view", ind: "Kembalikan tampilan" },
    home: { en: "Back to the starting view", ind: "Kembali ke posisi semula" },
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
    if (!map.getSource("dem")) {
      try { map.addSource("dem", DEM); } catch (e) { return; }
    }

    if (three) {
      map.setTerrain({ source: "dem", exaggeration: 1.35 });
      if (!map.getLayer("langit")) {
        try {
          map.addLayer({
            id: "langit",
            type: "sky",
            paint: {
              "sky-type": "atmosphere",
              "sky-atmosphere-sun-intensity": 6,
              "sky-atmosphere-color": "#cfdae6"
            }
          });
        } catch (e) { /* older style spec, the map simply has no sky */ }
      }
      if (map.getLayer("building") && !map.getLayer("gedung3d")) {
        try {
          map.addLayer({
            id: "gedung3d",
            type: "fill-extrusion",
            source: map.getLayer("building").source,
            "source-layer": "building",
            minzoom: 13,
            paint: {
              "fill-extrusion-color": "#d6d9dd",
              "fill-extrusion-height": ["coalesce", ["get", "render_height"], 8],
              "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
              "fill-extrusion-opacity": 0.85
            }
          });
        } catch (e) { /* no building heights in this style */ }
      }
    } else {
      map.setTerrain(null);
      if (map.getLayer("gedung3d")) map.removeLayer("gedung3d");
      if (map.getLayer("langit")) map.removeLayer("langit");
    }
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

  function buildPanel(map, markers, bounds, state) {
    var box = document.createElement("div");
    box.className = "peta__legenda";

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

    /* basemap */
    var baseWrap = group("basemap");
    var baseRow = document.createElement("div");
    baseRow.className = "peta__chips";
    baseWrap.appendChild(baseRow);
    var baseChips = BASEMAPS.map(function (base, index) {
      var el = chip(say(base), index === 0);
      el.addEventListener("click", function () { state.setBasemap(base.id); });
      baseRow.appendChild(el);
      return { id: base.id, el: el, base: base };
    });

    /* 2D or 3D */
    var viewWrap = group("view");
    var viewRow = document.createElement("div");
    viewRow.className = "peta__chips";
    viewWrap.appendChild(viewRow);
    var flat = chip("2D", true);
    var relief = chip("3D", false);
    flat.addEventListener("click", function () { state.setThree(false); });
    relief.addEventListener("click", function () { state.setThree(true); });
    viewRow.appendChild(flat);
    viewRow.appendChild(relief);

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
      groups.basemap.title.textContent = say(TEXT.basemap);
      groups.view.title.textContent = say(TEXT.view);
      groups.legend.title.textContent = say(TEXT.legend);
      reset.textContent = say(TEXT.reset);
      baseChips.forEach(function (entry) { entry.el.textContent = say(entry.base); });
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
      markBasemap: function (id) {
        baseChips.forEach(function (entry) {
          entry.el.setAttribute("aria-pressed", entry.id === id ? "true" : "false");
        });
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
      style: BASEMAPS[0].style,
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
      return { item: item, marker: marker, popup: popup };
    });

    var current = { basemap: BASEMAPS[0].id, three: false, filter: null };
    var panel;

    function dressStyle() {
      if (current.basemap === "peta") tuneBasemap(map);
      applyRelief(map, current.three);
    }

    var state = {
      setBasemap: function (id) {
        if (id === current.basemap) return;
        var base = BASEMAPS.filter(function (item) { return item.id === id; })[0];
        if (!base) return;
        current.basemap = id;
        panel.markBasemap(id);
        map.setStyle(base.style);
        map.once("styledata", function () { dressStyle(); });
      },
      setThree: function (three) {
        if (three === current.three) return;
        current.three = three;
        panel.markView(three);
        applyRelief(map, three);
        map.easeTo({ pitch: three ? 58 : 0, bearing: three ? -18 : 0, duration: ms(900) });
      },
      filter: function (kind) {
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
      reset: function () {
        state.home();
      },
      /* back to the view the map opened with: every marker shown, the whole
         country in frame, north up unless the 3D view is on */
      home: function () {
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

    map.on("error", function () {
      container.parentNode.parentNode.classList.add("is-failed");
    });

    return map;
  }

  window.HK_PETA = { build: build, count: WORK.length, basemaps: BASEMAPS.length };
})();
