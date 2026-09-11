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

    doc.documentElement.setAttribute("lang", useId ? "id" : "en");

    each(doc.querySelectorAll(".lang__btn"), function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-lang") === lang ? "true" : "false");
    });
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
    initYear();
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
