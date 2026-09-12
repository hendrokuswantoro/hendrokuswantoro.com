/*!
 * hendrokuswantoro.com - site behaviour
 * No dependencies. Progressive enhancement only: every page is fully
 * readable (in English) with JavaScript disabled.
 *
 * Bilingual model: the English copy lives in the HTML so crawlers see real
 * text; the Indonesian copy rides along in a data-ind attribute next to it.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "hk-lang";
  var doc = document;

  function each(list, fn) {
    Array.prototype.forEach.call(list, fn);
  }

  function readStore(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }

  function writeStore(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* private mode */ }
  }

  /* ---------------------------------------------------------------- language */

  function cacheEnglish() {
    each(doc.querySelectorAll("[data-ind]"), function (el) {
      if (el.hasAttribute("data-eng")) return;
      if (el.tagName === "META") {
        el.setAttribute("data-eng", el.getAttribute("content") || "");
      } else {
        el.setAttribute("data-eng", el.innerHTML);
      }
    });
    each(doc.querySelectorAll("[data-ind-label]"), function (el) {
      if (!el.hasAttribute("data-eng-label")) {
        el.setAttribute("data-eng-label", el.getAttribute("aria-label") || "");
      }
    });
    each(doc.querySelectorAll("[data-ind-alt]"), function (el) {
      if (!el.hasAttribute("data-eng-alt")) {
        el.setAttribute("data-eng-alt", el.getAttribute("alt") || "");
      }
    });
    each(doc.querySelectorAll("[data-ind-gagal]"), function (el) {
      if (!el.hasAttribute("data-eng-gagal")) {
        el.setAttribute("data-eng-gagal", el.getAttribute("data-gagal") || "");
      }
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

    each(doc.querySelectorAll("[data-ind-label]"), function (el) {
      var value = useId ? el.getAttribute("data-ind-label") : el.getAttribute("data-eng-label");
      if (value) el.setAttribute("aria-label", value);
    });

    each(doc.querySelectorAll("[data-ind-alt]"), function (el) {
      var value = useId ? el.getAttribute("data-ind-alt") : el.getAttribute("data-eng-alt");
      if (value) el.setAttribute("alt", value);
    });

    each(doc.querySelectorAll("[data-ind-gagal]"), function (el) {
      var value = useId ? el.getAttribute("data-ind-gagal") : el.getAttribute("data-eng-gagal");
      if (value) el.setAttribute("data-gagal", value);
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

  /* ------------------------------------------------------------------ header */

  function initHeader() {
    var header = doc.querySelector(".header");
    if (!header) return;
    var onScroll = function () {
      header.classList.toggle("is-stuck", window.scrollY > 4);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ------------------------------------------------------------------ reveal */

  function initReveal() {
    var items = doc.querySelectorAll(".reveal");
    if (!items.length) return;

    var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !("IntersectionObserver" in window)) {
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

  /* ----------------------------------------------------------------- filters */

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

  /* --------------------------------------------------------------- work map */

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

  function initMap() {
    var wrap = doc.querySelector("[data-peta]");
    if (!wrap) return;

    var canvas = wrap.querySelector("[data-peta-kanvas]");
    if (!canvas) return;

    var started = false;
    function start() {
      if (started) return;
      started = true;

      Promise.all([
        loadOnce("css", "/assets/vendor/maplibre/maplibre-gl.css"),
        loadOnce("js", "/assets/vendor/maplibre/maplibre-gl.js"),
        /* optional, the map falls back to key free sources when it is absent */
        loadOnce("js", "/assets/js/konfigurasi.js").catch(function () { return null; })
      ])
        .then(function () { return loadOnce("js", "/assets/js/peta.js?v=33"); })
        .then(function () {
          wrap.classList.add("is-live");
          window.HK_PETA_MAP = window.HK_PETA.build(canvas);
        })
        .catch(function () {
          wrap.classList.add("is-failed");
        });
    }

    /* the library is heavier than the rest of the site, so it waits until the
       section is about to be looked at, then loads without being asked */
    if (!("IntersectionObserver" in window)) { start(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.disconnect();
        start();
      });
    }, { rootMargin: "500px 0px" });
    io.observe(wrap);
  }

  /* ------------------------------------------------------- reading progress */

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

  /* ------------------------------------------------------ article contents */

  /* Builds the rail from the headings already in the article, so a post only
     has to be written once. Every link carries both languages the same way
     the rest of the page does, which means the language switch retitles the
     contents list without this code listening for anything. */

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
        var id = slug(english);
        while (taken[id]) id += "-2";
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

      /* the heading becomes linkable itself, quietly */
      var mark = doc.createElement("a");
      mark.className = "anchor";
      mark.href = "#" + head.id;
      mark.setAttribute("aria-hidden", "true");
      mark.setAttribute("tabindex", "-1");
      head.appendChild(mark);
    });

    rail.hidden = false;

    /* the entry you are reading is marked, recomputed on a frame so the
       scroll handler stays cheap */
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

  /* -------------------------------------------------------------- copyright */

  function initYear() {
    var year = String(new Date().getFullYear());
    each(doc.querySelectorAll("[data-year]"), function (el) { el.textContent = year; });
  }

  /* -------------------------------------------------------------------- boot */

  function boot() {
    initLang();
    initHeader();
    initReveal();
    initFilters();
    initMap();
    initProgress();
    initToc();
    initYear();
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
