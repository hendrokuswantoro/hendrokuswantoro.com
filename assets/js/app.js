(function () {
  "use strict";

  var STORAGE_KEY = "hk-lang";
  var TEMA_KEY = "hk-tema";
  var doc = document;

  function each(list, fn) {
    Array.prototype.forEach.call(list, fn);
  }

  function readStore(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }

  function writeStore(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) {}
  }

  function kurangiGerak() {
    return Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function bahasaKini() {
    return doc.documentElement.getAttribute("lang") === "id" ? "id" : "en";
  }

  var ATRIBUT_TERJEMAHAN = [
    { ind: "data-ind-label", eng: "data-eng-label", sasaran: "aria-label" },
    { ind: "data-ind-alt", eng: "data-eng-alt", sasaran: "alt" },
    { ind: "data-ind-gagal", eng: "data-eng-gagal", sasaran: "data-gagal" }
  ];

  function cacheEnglish() {
    each(doc.querySelectorAll("[data-ind]"), function (el) {
      if (el.hasAttribute("data-eng")) return;
      if (el.tagName === "META") {
        el.setAttribute("data-eng", el.getAttribute("content") || "");
      } else {
        el.setAttribute("data-eng", el.innerHTML);
      }
    });
    ATRIBUT_TERJEMAHAN.forEach(function (a) {
      each(doc.querySelectorAll("[" + a.ind + "]"), function (el) {
        if (!el.hasAttribute(a.eng)) el.setAttribute(a.eng, el.getAttribute(a.sasaran) || "");
      });
    });
  }

  function applyLang(lang) {
    var useId = lang === "id";

    each(doc.querySelectorAll("[data-ind]"), function (el) {
      var value = useId ? el.getAttribute("data-ind") : el.getAttribute("data-eng");
      if (value === null) return;
      if (el.tagName === "META") { el.setAttribute("content", value); }
      else { el.innerHTML = value; }
    });

    ATRIBUT_TERJEMAHAN.forEach(function (a) {
      each(doc.querySelectorAll("[" + a.ind + "]"), function (el) {
        var value = el.getAttribute(useId ? a.ind : a.eng);
        if (value) el.setAttribute(a.sasaran, value);
      });
    });

    doc.documentElement.setAttribute("lang", useId ? "id" : "en");

    each(doc.querySelectorAll(".lang__btn"), function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-lang") === lang ? "true" : "false");
    });

    doc.dispatchEvent(new CustomEvent("hk:lang", { detail: { lang: lang } }));
  }

  function initLang() {
    cacheEnglish();
    var stored = readStore(STORAGE_KEY);
    var nav = (navigator.language || "en").toLowerCase();
    var lang = stored || (nav.indexOf("id") === 0 ? "id" : "en");
    applyLang(lang);

    each(doc.querySelectorAll(".lang__btn"), function (btn) {
      btn.addEventListener("click", function () {
        var next = btn.getAttribute("data-lang");
        applyLang(next);
        writeStore(STORAGE_KEY, next);
      });
    });
  }

  function applyTema(tema) {
    var gelap = tema === "dark";
    doc.documentElement.setAttribute("data-theme", gelap ? "dark" : "light");
    each(doc.querySelectorAll(".tema"), function (btn) {
      btn.setAttribute("aria-pressed", gelap ? "true" : "false");
    });
    var meta = doc.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", gelap ? "#17181a" : "#f6f6f6");
    doc.dispatchEvent(new CustomEvent("hk:tema", { detail: { tema: gelap ? "dark" : "light" } }));
  }

  function initTema() {
    applyTema(readStore(TEMA_KEY) === "dark" ? "dark" : "light");

    each(doc.querySelectorAll(".tema"), function (btn) {
      btn.addEventListener("click", function () {
        var berikut = doc.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        applyTema(berikut);
        writeStore(TEMA_KEY, berikut);
      });
    });
  }

  function initHeader() {
    var header = doc.querySelector(".header");
    if (!header) return;
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 4);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  var CATATAN = {
    en: "This text is © Hendro Kuswantoro. Write to kuswantoro.hendro01@gmail.com to reuse it.",
    id: "Tulisan ini © Hendro Kuswantoro. Hubungi kuswantoro.hendro01@gmail.com untuk memakainya ulang."
  };

  var catatanEl = null;
  var catatanWaktu = 0;

  function beriTahu() {
    if (!catatanEl) {
      catatanEl = doc.createElement("div");
      catatanEl.className = "salin-catatan";
      catatanEl.setAttribute("role", "status");
      doc.body.appendChild(catatanEl);
    }
    catatanEl.textContent = CATATAN[bahasaKini()];
    catatanEl.classList.add("is-in");

    window.clearTimeout(catatanWaktu);
    catatanWaktu = window.setTimeout(function () {
      catatanEl.classList.remove("is-in");
    }, 2600);
  }

  function bolehSalin(node) {
    if (!node || !node.closest) return false;
    return Boolean(node.closest("input, textarea, select, [contenteditable='true'], .boleh-salin"));
  }

  function initLindungi() {
    doc.addEventListener("copy", function (event) {
      if (bolehSalin(event.target)) return;
      event.preventDefault();
      if (event.clipboardData) {
        event.clipboardData.setData(
          "text/plain",
          CATATAN[bahasaKini()] + "\n" + window.location.href
        );
      }
      beriTahu();
    });

    doc.addEventListener("cut", function (event) {
      if (bolehSalin(event.target)) return;
      event.preventDefault();
      beriTahu();
    });

    doc.addEventListener("contextmenu", function (event) {
      if (bolehSalin(event.target)) return;
      event.preventDefault();
      beriTahu();
    });

    doc.addEventListener("dragstart", function (event) {
      if (bolehSalin(event.target)) return;
      event.preventDefault();
    });

    doc.addEventListener("keydown", function (event) {
      var perintah = event.ctrlKey || event.metaKey;
      if (perintah && (event.key === "p" || event.key === "P")) beriTahu();
      if (perintah && (event.key === "s" || event.key === "S")) {
        event.preventDefault();
        beriTahu();
      }
    });
  }

  var WIB = "Asia/Jakarta";

  function initJam() {
    var jamnya = doc.querySelectorAll("[data-jam]");
    var tanggalnya = doc.querySelectorAll("[data-tanggal]");
    if (!jamnya.length && !tanggalnya.length) return;

    function buang(el) {
      var induk = el.closest ? el.closest("[data-kini]") : null;
      (induk || el).remove();
    }

    var bentukJam;
    var bentukTanggal = {};
    try {
      bentukJam = new Intl.DateTimeFormat("en-GB", {
        timeZone: WIB, hour: "2-digit", minute: "2-digit", hour12: false
      });
      bentukTanggal.en = new Intl.DateTimeFormat("en-GB", {
        timeZone: WIB, weekday: "short", day: "numeric", month: "short", year: "numeric"
      });
      bentukTanggal.id = new Intl.DateTimeFormat("id-ID", {
        timeZone: WIB, weekday: "short", day: "numeric", month: "short", year: "numeric"
      });
    } catch (e) {
      each(jamnya, buang);
      each(tanggalnya, buang);
      return;
    }

    if (bentukTanggal.id.resolvedOptions().locale.indexOf("id") !== 0) {
      bentukTanggal.id = bentukTanggal.en;
    }

    function tulis() {
      var kini = new Date();
      var jam = bentukJam.format(kini);
      each(jamnya, function (el) {
        el.innerHTML = jam.replace(":", '<span class="jam__titik">:</span>');
      });

      var tanggal = bentukTanggal[bahasaKini()].format(kini);
      each(tanggalnya, function (el) {
        if (el.textContent !== tanggal) el.textContent = tanggal;
      });

      each(doc.querySelectorAll("[data-kini][hidden]"), function (el) {
        el.removeAttribute("hidden");
      });
    }

    tulis();
    window.setInterval(tulis, 1000);
    doc.addEventListener("hk:lang", tulis);
  }

  function initTumpuk() {
    each(doc.querySelectorAll(".reveal"), function (induk) {
      each(induk.children, function (anak, i) {
        anak.style.setProperty("--i", Math.min(i, 9));
      });
    });
  }

  function initKilau() {
    if (!window.matchMedia || kurangiGerak()) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    var menunggu = null;

    doc.addEventListener("mousemove", function (event) {
      if (menunggu) return;
      menunggu = window.requestAnimationFrame(function () {
        menunggu = null;
        var kartu = event.target.closest && event.target.closest(".card, .tile, .post, .stat");
        if (!kartu) return;
        var kotak = kartu.getBoundingClientRect();
        kartu.style.setProperty("--mx", (event.clientX - kotak.left) + "px");
        kartu.style.setProperty("--my", (event.clientY - kotak.top) + "px");
      });
    }, { passive: true });
  }

  function initReveal() {
    var items = doc.querySelectorAll(".reveal");
    if (!items.length) return;

    if (kurangiGerak() || !("IntersectionObserver" in window)) {
      each(items, function (el) { el.classList.add("is-in"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      each(entries, function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });

    each(items, function (el) { io.observe(el); });
  }

  function initFilters() {
    var buttons = doc.querySelectorAll("[data-filter]");
    var cards = doc.querySelectorAll("[data-category]");
    var empty = doc.querySelector("[data-empty]");
    if (!buttons.length || !cards.length) return;

    function run(key) {
      var shown = 0;
      each(cards, function (card) {
        var match = key === "all" || card.getAttribute("data-category").split(" ").indexOf(key) !== -1;
        card.classList.toggle("is-hidden", !match);
        if (match) shown++;
      });
      each(buttons, function (btn) {
        btn.setAttribute("aria-pressed", btn.getAttribute("data-filter") === key ? "true" : "false");
      });
      if (empty) empty.classList.toggle("is-hidden", shown > 0);
    }

    each(buttons, function (btn) {
      btn.addEventListener("click", function () { run(btn.getAttribute("data-filter")); });
    });

    run("all");
  }

  function loadOnce(kind, url) {
    return new Promise(function (resolve, reject) {
      var el;
      if (kind === "css") {
        el = doc.createElement("link");
        el.rel = "stylesheet";
        el.href = url;
      } else {
        el = doc.createElement("script");
        el.src = url;
        el.defer = true;
      }
      el.onload = function () { resolve(); };
      el.onerror = function () { reject(new Error(url)); };
      doc.head.appendChild(el);
    });
  }

  var pustakaPeta = null;

  function muatPustakaPeta() {
    if (!pustakaPeta) {
      pustakaPeta = Promise.all([
        loadOnce("css", "/assets/vendor/maplibre/6.9.0/maplibre-gl.css"),
        import("/assets/vendor/maplibre/6.9.0/maplibre-gl.mjs").then(function (mod) {
          window.maplibregl = mod;
          return mod;
        }),
        loadOnce("js", "/assets/js/konfigurasi.js").catch(function () { return null; })
      ]).then(function () { return loadOnce("js", "/assets/js/peta.js?v=269744b2e8"); });
    }
    return pustakaPeta;
  }

  function saatMendekat(wrap, mulai) {
    if (!("IntersectionObserver" in window)) { mulai(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.disconnect();
        mulai();
      });
    }, { rootMargin: "500px 0px" });
    io.observe(wrap);
  }

  function initMap() {
    var wrap = doc.querySelector("[data-peta]");
    if (!wrap) return;

    var canvas = wrap.querySelector("[data-peta-kanvas]");
    if (!canvas) return;

    var started = false;
    function start() {
      if (started) return;
      started = true;

      muatPustakaPeta()
        .then(function () {
          wrap.classList.add("is-live");
          window.HK_PETA_MAP = window.HK_PETA.build(canvas);
        })
        .catch(function () {
          wrap.classList.add("is-failed");
        });
    }

    each(doc.querySelectorAll("[data-peta-buka]"), function (tautan) {
      tautan.addEventListener("click", function (event) {
        var id = tautan.getAttribute("data-peta-buka");
        if (!id) return;
        event.preventDefault();
        start();

        function gulirKePeta() {
          wrap.scrollIntoView({ behavior: kurangiGerak() ? "auto" : "smooth", block: "start" });
        }

        if (window.HK_PETA_STATE) {
          window.HK_PETA_STATE.buka(id);
          window.requestAnimationFrame(gulirKePeta);
        } else {
          gulirKePeta();
          if (window.history && window.history.replaceState) {
            try {
              window.history.replaceState(null, "", "#peta-" + id);
            } catch (galat) {}
          }
        }
      });
    });

    saatMendekat(wrap, start);
  }

  function initParkir() {
    var wrap = doc.querySelector("[data-parkir]");
    if (!wrap) return;
    var canvas = wrap.querySelector("[data-parkir-kanvas]");
    if (!canvas) return;

    saatMendekat(wrap, function () {
      muatPustakaPeta()
        .then(function () { return loadOnce("js", "/assets/js/parkir-data.js?v=259bffdc68"); })
        .then(function () { return loadOnce("js", "/assets/js/parkir.js?v=4b508dc97a"); })
        .then(function () {
          wrap.classList.add("is-live");
          window.HK_PARKIR.build(canvas);
        })
        .catch(function () {
          wrap.classList.add("is-failed");
        });
    });
  }

  function initProgress() {
    var bar = doc.querySelector("[data-progres]");
    var article = doc.querySelector(".article");
    if (!bar || !article) return;

    var frame = 0;
    function draw() {
      frame = 0;
      var box = article.getBoundingClientRect();
      var start = window.scrollY + box.top;
      var span = box.height - window.innerHeight;
      if (span <= 0) { bar.style.transform = "scaleX(1)"; return; }
      var seen = (window.scrollY - start) / span;
      bar.style.transform = "scaleX(" + Math.min(1, Math.max(0, seen)) + ")";
    }
    function onScroll() {
      if (frame) return;
      frame = window.requestAnimationFrame(draw);
    }

    draw();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
  }

  function slug(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 60) || "bagian";
  }

  function initToc() {
    var rail = doc.querySelector(".rail__daftar");
    var article = doc.querySelector(".article");
    if (!rail || !article) return;

    var heads = article.querySelectorAll("h2");
    if (heads.length < 2) return;

    var list = rail.querySelector("ol");
    var taken = Object.create(null);
    var links = [];

    each(heads, function (head) {
      var english = head.getAttribute("data-eng") || head.innerHTML;
      var indo = head.getAttribute("data-ind") || english;

      if (!head.id) {
        var dasar = slug(english);
        var id = dasar;
        for (var n = 2; taken[id]; n++) id = dasar + "-" + n;
        taken[id] = true;
        head.id = id;
      }

      var item = doc.createElement("li");
      var link = doc.createElement("a");
      link.href = "#" + head.id;
      link.innerHTML = head.innerHTML;
      link.setAttribute("data-eng", english);
      link.setAttribute("data-ind", indo);
      item.appendChild(link);
      list.appendChild(item);
      links.push({ link: link, head: head });
    });

    rail.hidden = false;

    var frame = 0;
    function mark() {
      frame = 0;
      var edge = window.innerHeight * 0.3;
      var now = links[0];
      links.forEach(function (pair) {
        if (pair.head.getBoundingClientRect().top <= edge) now = pair;
      });
      links.forEach(function (pair) {
        pair.link.classList.toggle("is-now", pair === now);
      });
    }
    function onScroll() {
      if (frame) return;
      frame = window.requestAnimationFrame(mark);
    }

    mark();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
  }

  function gulirKe(tujuan, halus) {
    tujuan.scrollIntoView({ behavior: halus && !kurangiGerak() ? "smooth" : "auto", block: "start" });
    if (!tujuan.hasAttribute("tabindex") && !/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(tujuan.tagName)) {
      tujuan.setAttribute("tabindex", "-1");
    }
    tujuan.focus({ preventScroll: true });
  }

  function buangPagar() {
    if (!window.history || !window.history.replaceState) return;
    try {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    } catch (galat) {}
  }

  function initGulir() {
    doc.addEventListener("click", function (event) {
      if (event.defaultPrevented || event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      var tautan = event.target.closest ? event.target.closest('a[href^="#"]') : null;
      if (!tautan || tautan.hasAttribute("data-peta-buka")) return;
      var id = tautan.getAttribute("href").slice(1);
      if (!id || id.indexOf("peta-") === 0) return;
      var tujuan = doc.getElementById(id);
      if (!tujuan) return;
      event.preventDefault();
      gulirKe(tujuan, true);
    });

    var awal = decodeURIComponent(window.location.hash.slice(1));
    if (!awal || awal.indexOf("peta-") === 0) return;
    var tujuan = doc.getElementById(awal);
    if (tujuan) gulirKe(tujuan, false);
    buangPagar();
  }

  function initYear() {
    var year = String(new Date().getFullYear());
    each(doc.querySelectorAll("[data-year]"), function (el) { el.textContent = year; });
  }

  function boot() {
    initLang();
    initTema();
    initHeader();
    initTumpuk();
    initReveal();
    initJam();
    initKilau();
    initLindungi();
    initFilters();
    initMap();
    initParkir();
    initProgress();
    initToc();
    initGulir();
    initYear();

    doc.documentElement.setAttribute("data-siap", "1");
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
