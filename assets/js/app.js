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
  var TEMA_KEY = "hk-tema";
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

  /* -------------------------------------------------------------------- tema */

  /* Tema dipilih pembaca, bukan sistem operasinya.
   *
   * Dulu palet gelap menempel pada @media (prefers-color-scheme: dark).
   * Akibatnya pembaca yang laptopnya gelap tidak pernah melihat palet terang
   * sama sekali, dan tidak punya cara memintanya. Sekarang bawaannya terang
   * dan gelap adalah pilihan, seperti aplikasi Uber.
   *
   * Yang mencegah kedipan bukan fungsi ini melainkan skrip sebaris di <head>:
   * app.js dimuat dengan defer, jadi kalau atribut data-theme baru dipasang
   * di sini, pembaca yang memilih gelap akan melihat satu bingkai putih lebih
   * dulu. Skrip sebaris itu diizinkan CSP lewat hash sha256, bukan lewat
   * 'unsafe-inline', supaya seluruh skrip lain tetap tertutup.
   */
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

  /* -------------------------------------------------------- perlindungan isi */

  /* Yang bisa dan tidak bisa dikerjakan bagian ini, disebut di muka supaya
   * tidak ada yang mengira ia lebih kuat daripada yang sebenarnya.
   *
   * BISA  : menghentikan penyalinan sambil lalu. Blok teks, Ctrl+C, klik
   *         kanan, seret teks keluar, dan cetak ke PDF.
   * TIDAK : menghentikan Lihat Sumber, JavaScript yang dimatikan, mode baca,
   *         curl, atau umpan RSS-nya sendiri. Teksnya memang ada di HTML,
   *         sebab di situlah mesin pencari dan pembaca layar membacanya.
   * TIDAK : menghentikan tangkapan layar. Tidak ada satu pun cara di web
   *         untuk itu, dan trik yang beredar, seperti mengaburkan halaman
   *         saat jendelanya kehilangan fokus, hanya merusak halaman bagi
   *         pembaca yang jujur sambil tidak menghalangi siapa pun yang
   *         menekan tombol Print Screen.
   *
   * Isi yang benar benar tidak boleh disalin adalah isi yang tidak
   * diterbitkan. Yang ini menaikkan ongkosnya, bukan menutup pintunya, dan
   * itu memang sejauh yang bisa dijanjikan.
   */

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
      /* role=status, bukan alert: ini keterangan, bukan bahaya, dan alert
         memotong apa pun yang sedang dibacakan pembaca layar. */
      catatanEl.setAttribute("role", "status");
      doc.body.appendChild(catatanEl);
    }
    catatanEl.textContent = doc.documentElement.getAttribute("lang") === "id"
      ? CATATAN.id : CATATAN.en;
    catatanEl.classList.add("is-in");

    window.clearTimeout(catatanWaktu);
    catatanWaktu = window.setTimeout(function () {
      catatanEl.classList.remove("is-in");
    }, 2600);
  }

  function bolehSalin(node) {
    /* Kolom isian dan elemen yang bisa disunting tetap normal. Tanpa ini,
       setiap formulir dan halaman admin jadi tidak bisa dipakai. */
    if (!node || !node.closest) return false;
    return Boolean(node.closest("input, textarea, select, [contenteditable='true'], .boleh-salin"));
  }

  function initLindungi() {
    doc.addEventListener("copy", function (event) {
      if (bolehSalin(event.target)) return;
      event.preventDefault();
      /* Papan tempel tidak dibiarkan berisi potongan yang kebetulan
         tersalin sebelum ini: ia diisi ulang dengan barisnya sendiri. */
      if (event.clipboardData) {
        event.clipboardData.setData(
          "text/plain",
          (doc.documentElement.getAttribute("lang") === "id" ? CATATAN.id : CATATAN.en) +
          "\n" + window.location.href
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

    /* Ctrl+P dan Cmd+P. Cetakannya sendiri sudah dijaga @media print, jadi
       ini hanya menjelaskan kenapa yang keluar bukan isinya. */
    doc.addEventListener("keydown", function (event) {
      var perintah = event.ctrlKey || event.metaKey;
      if (perintah && (event.key === "p" || event.key === "P")) beriTahu();
      if (perintah && (event.key === "s" || event.key === "S")) {
        event.preventDefault();
        beriTahu();
      }
    });
  }

  /* -------------------------------------------------------------- kehidupan */

  /* Tiga hal kecil yang membuat halaman terasa ada yang menghuni, dan satu
   * aturan yang mengikat ketiganya: tidak ada satu pun yang mengarang data.
   *
   * Jam Yogyakarta memang jam Yogyakarta, dihitung dari zona waktunya sendiri
   * lewat Intl, bukan dari jam perangkat pembaca yang bisa di mana saja.
   * Angka yang berdetak tetapi tidak berarti apa apa lebih buruk daripada
   * halaman yang diam.
   */

  var WIB = "Asia/Jakarta";

  function initJam() {
    var tempat = doc.querySelectorAll("[data-jam]");
    if (!tempat.length) return;

    var bentuk;
    try {
      bentuk = new Intl.DateTimeFormat("en-GB", {
        timeZone: WIB, hour: "2-digit", minute: "2-digit", hour12: false
      });
    } catch (e) {
      /* Intl tanpa basis data zona waktu. Lebih baik tidak menampilkan jam
         sama sekali daripada menampilkan jam yang salah dan meyakinkan. */
      each(tempat, function (el) { el.remove(); });
      return;
    }

    function tulis() {
      var jam = bentuk.format(new Date());
      each(tempat, function (el) {
        el.innerHTML = jam.replace(":", '<span class="jam__titik">:</span>');
      });
    }

    tulis();
    /* Sekali per detik, bukan per menit: yang berdenyut titik dua di
       antaranya, dan denyutnya harus sejalan dengan detik yang sebenarnya. */
    window.setInterval(tulis, 1000);
  }

  function initTumpuk() {
    /* Memberi tiap anak di dalam .reveal nomor urutnya, supaya CSS bisa
       menundanya berurutan. Dibatasi sepuluh: baris kesebelas yang menunggu
       hampir satu detik bukan lagi rapi, ia lambat. */
    each(doc.querySelectorAll(".reveal"), function (induk) {
      each(induk.children, function (anak, i) {
        anak.style.setProperty("--i", Math.min(i, 9));
      });
    });
  }

  function initKilau() {
    /* Kilau yang mengikuti kursor. Tidak dipasang sama sekali pada perangkat
       sentuh: di sana tidak ada kursor untuk diikuti, dan pendengar
       pointermove hanya jadi pekerjaan yang dibuang percuma. */
    if (!window.matchMedia) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    var menunggu = null;

    /* mousemove, bukan pointermove. Keduanya sama saja di peramban
       sungguhan, tetapi Chromium yang dijalankan Playwright lewat CDP tidak
       membangkitkan pointermove sama sekali, sehingga fiturnya tidak akan
       pernah bisa diuji. Fitur yang tidak bisa diuji akan rusak diam diam,
       dan itu harga yang lebih mahal daripada nama peristiwa yang lebih
       baru. Perangkat sentuh sudah disaring media query di atas. */
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

      /* MapLibre 6 ships as an ES module only. There is no UMD bundle to drop
         in with a script tag, so it is imported and its namespace is put on
         window for peta.js to read, exactly where the old global used to be.
         The import is same origin, which script-src 'self' already allows. */
      Promise.all([
        loadOnce("css", "/assets/vendor/maplibre/6.9.0/maplibre-gl.css"),
        import("/assets/vendor/maplibre/6.9.0/maplibre-gl.mjs").then(function (mod) {
          window.maplibregl = mod;
          return mod;
        }),
        /* optional, the map falls back to key free sources when it is absent */
        loadOnce("js", "/assets/js/konfigurasi.js").catch(function () { return null; })
      ])
        .then(function () { return loadOnce("js", "/assets/js/peta.js?v=25b6d2826c"); })
        .then(function () {
          wrap.classList.add("is-live");
          window.HK_PETA_MAP = window.HK_PETA.build(canvas);
        })
        .catch(function () {
          wrap.classList.add("is-failed");
        });
    }

    /* Tautan "Lihat di peta" di tiap kartu. Arahnya kebalikan dari tautan
       di dalam popup penanda, yang membawa pembaca dari peta ke kartu.

       Yang dikerjakan tiga hal berurutan: menyalakan peta kalau ia belum
       dimuat, menggulir ke petanya, lalu menyuruh petanya memusatkan karya
       itu. Alamatnya ikut berubah, ditulis peta.js, jadi yang tersalin dari
       bilah alamat sesudah ini membuka peta di titik yang sama.

       Yang TIDAK dipakai: menyetel window.location.hash. Alamat #peta-<id>
       tidak menunjuk elemen mana pun, dan peramban menjawab fragmen yang
       tidak ditemukan dengan menggulir ke awal dokumen. Gulirannya beradu
       dengan gulir halus yang baru saja diminta, dan petanya berhenti 196
       piksel dari tempat yang dimaksud. Terukur, dan itu sebabnya alamatnya
       ditulis dengan replaceState. */
    each(doc.querySelectorAll("[data-peta-buka]"), function (tautan) {
      tautan.addEventListener("click", function (event) {
        var id = tautan.getAttribute("data-peta-buka");
        if (!id) return;
        event.preventDefault();
        start();

        /* wrap adalah .peta, dan .peta punya scroll-margin-top setinggi
           header, jadi petanya tidak berhenti di balik header yang lengket */
        function gulirKePeta() {
          var halus = !(window.matchMedia
            && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
          wrap.scrollIntoView({ behavior: halus ? "smooth" : "auto", block: "start" });
        }

        if (window.HK_PETA_STATE) {
          /* petanya sudah berdiri, jadi ia disuruh langsung. Alamatnya
             ditulis peta.js sendiri begitu kameranya berangkat. */
          window.HK_PETA_STATE.buka(id);
          /* Gulirnya menyusul satu bingkai kemudian, dan urutannya penting.
             Popup MapLibre memindahkan fokus ke dalam dirinya begitu terbuka,
             focusAfterOpen, dan pemindahan fokus itu ikut menggulir halaman.
             Kalau gulir kita berangkat lebih dulu, ia diadu dengan gulir itu
             dan kalah: terukur berhenti di 197 piksel, 196 piksel dari tempat
             yang dimaksud. Satu bingkai kemudian ia menang, dan fokusnya
             tetap di dalam popup, tempat yang benar bagi pembaca papan
             ketik. */
          window.requestAnimationFrame(gulirKePeta);
        } else {
          /* petanya baru dimuat, jadi belum ada popup yang berebut gulir.
             Alamatnya ditulis sekarang, dan peta.js membacanya sendiri
             begitu selesai. */
          gulirKePeta();
          if (window.history && window.history.replaceState) {
            try {
              window.history.replaceState(null, "", "#peta-" + id);
            } catch (galat) { /* alamat file:// */ }
          }
        }
      });
    });

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
    initTema();
    initHeader();
    initTumpuk();
    initReveal();
    initJam();
    initKilau();
    initLindungi();
    initFilters();
    initMap();
    initProgress();
    initToc();
    initYear();

    /* A readiness flag, and the reason it exists.
       The browser tests used to wait for "networkidle" before touching the
       page. On every page but one that is the same thing as waiting for this
       line. On /project it is not: the map keeps asking for tiles for as long
       as it is on screen, so the network never falls idle for the 500 ms
       Playwright wants, and the wait ran to its timeout instead. It passed
       locally only because the Mapbox token is restricted by URL and every
       tile came back 403 in under a second. A page that is declared ready by
       the code that finishes setting it up cannot go wrong that way. */
    doc.documentElement.setAttribute("data-siap", "1");
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
