/*!
 * Work map. MapLibre GL JS over OpenFreeMap vector tiles.
 *
 * The module is fetched only when the map section is about to enter the
 * screen, then the map builds itself. No button, nothing to press.
 *
 * The points are label positions, not study area boundaries. Each one marks
 * roughly where the work was done, close enough to find on a map of
 * Indonesia and never presented as a survey coordinate.
 */
(function () {
  "use strict";

  var STYLE = "https://tiles.openfreemap.org/styles/positron";

  /* one colour per kind of work, all four readable on the pale basemap */
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
    legend: { en: "Legend", ind: "Legenda" },
    all: { en: "All work", ind: "Semua karya" },
    inView: { en: "in view", ind: "terlihat" },
    open: { en: "See the project", ind: "Lihat proyek" },
    reset: { en: "Reset view", ind: "Kembalikan tampilan" }
  };

  function isId() {
    return document.documentElement.getAttribute("lang") === "id";
  }

  function say(entry) {
    return isId() ? entry.ind : entry.en;
  }

  /* ----------------------------------------------------------- basemap tone */

  /* Positron is already quiet. These few nudges pull it the rest of the way
     towards the site palette: paper white land, cool grey water, hairline
     roads. Every change is guarded, a missing layer must never break the map. */
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

  /* ----------------------------------------------------------------- legend */

  function buildLegend(map, markers, bounds) {
    var box = document.createElement("div");
    box.className = "peta__legenda";

    var head = document.createElement("p");
    head.className = "peta__legenda-judul";
    box.appendChild(head);

    var rows = {};
    Object.keys(KIND).forEach(function (key) {
      var row = document.createElement("button");
      row.type = "button";
      row.className = "peta__baris";
      row.setAttribute("data-kind", key);
      row.innerHTML = "<i></i><span class=\"peta__nama\"></span><span class=\"peta__angka\">0</span>";
      box.appendChild(row);
      rows[key] = row;
    });

    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "peta__reset";
    box.appendChild(reset);

    var active = null;

    function label() {
      head.textContent = say(TEXT.legend);
      reset.textContent = say(TEXT.reset);
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__nama").textContent = say(KIND[key]);
      });
    }

    /* the numbers answer one question only: what is on screen right now */
    function count() {
      var view = map.getBounds();
      var seen = { app: 0, analysis: 0, satellite: 0, design: 0 };
      markers.forEach(function (entry) {
        if (entry.marker.getElement().classList.contains("is-off")) return;
        if (view.contains(entry.item)) seen[entry.item.kind]++;
      });
      Object.keys(rows).forEach(function (key) {
        rows[key].querySelector(".peta__angka").textContent = seen[key];
        rows[key].classList.toggle("is-empty", seen[key] === 0);
      });
    }

    function filter(kind) {
      active = active === kind ? null : kind;
      var visible = new maplibregl.LngLatBounds();
      markers.forEach(function (entry) {
        var show = !active || entry.item.kind === active;
        entry.marker.getElement().classList.toggle("is-off", !show);
        if (show) visible.extend([entry.item.lng, entry.item.lat]);
      });
      Object.keys(rows).forEach(function (key) {
        rows[key].setAttribute("aria-pressed", active === key ? "true" : "false");
      });
      box.classList.toggle("is-filtered", Boolean(active));
      map.fitBounds(active ? visible : bounds, { padding: 56, maxZoom: active ? 7 : 6, duration: 700 });
    }

    Object.keys(rows).forEach(function (key) {
      rows[key].setAttribute("aria-pressed", "false");
      rows[key].addEventListener("click", function () { filter(key); });
    });
    reset.addEventListener("click", function () {
      if (active) { filter(active); return; }
      map.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 700 });
    });

    label();
    map.on("moveend", count);
    map.on("zoomend", count);
    document.addEventListener("hk:lang", function () {
      label();
      markers.forEach(function (entry) {
        entry.marker.getElement().title = say(entry.item);
        entry.marker.getElement().setAttribute("aria-label", say(entry.item));
        entry.popup.setHTML(popupHtml(entry.item));
      });
    });

    return { node: box, count: count };
  }

  /* ------------------------------------------------------------------ build */

  function build(container) {
    var bounds = new maplibregl.LngLatBounds();
    WORK.forEach(function (item) { bounds.extend([item.lng, item.lat]); });

    var map = new maplibregl.Map({
      container: container,
      style: STYLE,
      bounds: bounds,
      fitBoundsOptions: { padding: 56, maxZoom: 6 },
      minZoom: 2.5,
      maxZoom: 16,
      attributionControl: false,
      cooperativeGestures: true
    });

    /* compass turns with the map, scale bar keeps the distances honest */
    map.addControl(
      new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }),
      "top-right"
    );
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");
    map.addControl(new maplibregl.FullscreenControl(), "top-right");
    /* the style ships its own credit line, adding ours would repeat it */
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

    var legend = buildLegend(map, markers, bounds);
    var section = container.parentNode.parentNode;
    section.insertBefore(legend.node, section.querySelector(".peta__ket"));

    map.on("load", function () {
      tuneBasemap(map);
      map.resize();
      map.fitBounds(bounds, { padding: 56, maxZoom: 6, duration: 0 });
      map.once("idle", legend.count);
      container.parentNode.classList.add("is-ready");
    });

    map.on("error", function () {
      container.parentNode.classList.add("is-failed");
    });

    return map;
  }

  window.HK_PETA = { build: build, count: WORK.length };
})();
