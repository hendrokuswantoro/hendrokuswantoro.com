/*!
 * Work map. MapLibre GL JS with OpenStreetMap raster tiles.
 *
 * Loaded only when the visitor asks for it, because the library alone is
 * heavier than the rest of the site put together.
 *
 * The points are label positions, not study area boundaries. Each one marks
 * roughly where the work was done, close enough to find on a map of
 * Indonesia and never presented as a survey coordinate.
 */
(function () {
  "use strict";

  /* OpenFreeMap serves OpenStreetMap data as vector tiles, free and without
     an API key. Its Positron style is grey and quiet, which lets the markers
     carry the page. CARTO was tried first and now stamps API KEY REQUIRED
     across every tile, so it cannot be used without an account. */
  var STYLE = "https://tiles.openfreemap.org/styles/positron";
  var ATTRIBUTION =
    '&copy; <a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> ' +
    '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';

  var WORK = [
    { id: "parking", lng: 110.3656, lat: -7.7925,
      en: "Yogyakarta Parking Map", ind: "Peta Parkir Yogyakarta",
      kindEn: "Map app", kindInd: "Aplikasi peta" },
    { id: "landcover", lng: 110.4050, lat: -7.7550,
      en: "Yogyakarta Land Cover Map", ind: "Peta Tutupan Lahan Yogyakarta",
      kindEn: "Map design", kindInd: "Desain peta" },
    { id: "fire", lng: 113.2000, lat: -1.6000,
      en: "Kalimantan Fire Maps", ind: "Peta Kebakaran Kalimantan",
      kindEn: "Satellite data", kindInd: "Data satelit" },
    { id: "fish", lng: 108.2200, lat: 3.7000,
      en: "Fish Landing Sites, Natuna", ind: "Lokasi Pendaratan Ikan, Natuna",
      kindEn: "Map analysis", kindInd: "Analisis peta" },
    { id: "pickup", lng: 106.8200, lat: -6.2100,
      en: "Pickup Points from GPS Pings, Jakarta", ind: "Titik Jemput dari Ping GPS, Jakarta",
      kindEn: "Map analysis", kindInd: "Analisis peta" },
    { id: "reach", lng: 136.0800, lat: -1.1800,
      en: "Service Reach, Biak Numfor", ind: "Jangkauan Layanan, Biak Numfor",
      kindEn: "Service reach", kindInd: "Jangkauan layanan" },
    { id: "mimika", lng: 137.0000, lat: -4.3500,
      en: "Mining and Forest Loss, Mimika", ind: "Tambang dan Hutan Hilang, Mimika",
      kindEn: "Satellite data", kindInd: "Data satelit" }
  ];

  function lang() {
    return document.documentElement.getAttribute("lang") === "id" ? "id" : "en";
  }

  function markerElement(item) {
    var el = document.createElement("button");
    el.type = "button";
    el.className = "peta__pin";
    el.setAttribute("data-work", item.id);
    return el;
  }

  function popupHtml(item) {
    var id = lang() === "id";
    var title = id ? item.ind : item.en;
    var kind = id ? item.kindInd : item.kindEn;
    var more = id ? "Lihat proyek" : "See the project";
    return (
      '<span class="peta__kind">' + kind + "</span>" +
      "<strong>" + title + "</strong>" +
      '<a href="#karya-' + item.id + '">' + more + "</a>"
    );
  }

  function build(container, onReady) {
    var bounds = new maplibregl.LngLatBounds();
    WORK.forEach(function (item) { bounds.extend([item.lng, item.lat]); });

    var map = new maplibregl.Map({
      container: container,
      style: STYLE,
      bounds: bounds,
      fitBoundsOptions: { padding: 44, maxZoom: 6 },
      minZoom: 2.5,
      maxZoom: 16,
      attributionControl: false,
      cooperativeGestures: true
    });

    map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: ATTRIBUTION }),
      "bottom-right"
    );
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    var popups = [];
    WORK.forEach(function (item) {
      var popup = new maplibregl.Popup({ offset: 16, closeButton: false, className: "peta__popup" })
        .setHTML(popupHtml(item));
      new maplibregl.Marker({ element: markerElement(item) })
        .setLngLat([item.lng, item.lat])
        .setPopup(popup)
        .addTo(map);
      popups.push({ item: item, popup: popup });
    });

    document.addEventListener("hk:lang", function () {
      popups.forEach(function (entry) {
        entry.popup.setHTML(popupHtml(entry.item));
      });
    });

    map.on("load", function () {
      map.resize();
      map.fitBounds(bounds, { padding: 44, maxZoom: 6, duration: 0 });
      if (onReady) onReady();
    });

    return map;
  }

  window.HK_PETA = { build: build, count: WORK.length };
})();
