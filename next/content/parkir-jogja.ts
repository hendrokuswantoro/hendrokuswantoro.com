import type { Copy } from "./i18n";


type Angka = { num: Copy; label: Copy };
type Bagian = { h2: Copy; p: Copy[] };

export const PARKIR = {
  slug: "parkir-jogja",

  back: { en: "Back to projects", id: "Kembali ke proyek" } as Copy,
  badge: { en: "Case study", id: "Studi kasus" } as Copy,
  tags: ["FastAPI", "PostGIS", "MapLibre"],

  title: { en: "Yogyakarta Parking Map", id: "Peta Parkir Yogyakarta" } as Copy,
  lede: {
    en: "Drop a pin on any street in Yogyakarta and see its parking zone and fee in seconds. Just as important, the map knows when to stay quiet.",
    id: "Taruh pin di jalan mana pun di Kota Yogyakarta, zona dan tarif parkirnya langsung terlihat. Sama pentingnya, peta ini tahu kapan harus diam.",
  } as Copy,

  image: "/assets/img/work/parking.webp?v=12dc5e71f9",
  alt: {
    en: "The parking map showing the zone and the fee for a street in Yogyakarta",
    id: "Peta parkir yang menampilkan zona dan tarif untuk sebuah ruas di Yogyakarta",
  } as Copy,

  angka: [
    {
      num: { en: "495", id: "495" },
      label: {
        en: "Zone I and II street segments mapped",
        id: "ruas Kawasan I dan II terpetakan",
      },
    },
    {
      num: { en: "14,272", id: "14.272" },
      label: {
        en: "roads that shape the coverage area",
        id: "ruas jalan membentuk area cakupan",
      },
    },
    {
      num: { en: "594", id: "594" },
      label: {
        en: "fee combinations, three engines agree",
        id: "kombinasi tarif, tiga mesin hitung sepakat",
      },
    },
    {
      num: { en: "0", id: "0" },
      label: {
        en: "places labelled legal or illegal",
        id: "tempat dilabeli legal atau ilegal",
      },
    },
  ] as Angka[],

  bagian: [
    {
      h2: { en: "The problem it solves", id: "Masalah yang diselesaikan" },
      p: [
        {
          en: "Parking fees in Yogyakarta depend on the zone. Mayoral Regulation 149/2020 divides the city into Zone I, Zone II and Zone III, and each zone has its own rate. The catch is that none of these zones can be seen from the street.",
          id: "Tarif parkir di Kota Yogyakarta bergantung pada kawasannya. Perwal 149/2020 membagi kota menjadi Kawasan I, II, dan III, dan tiap kawasan punya tarif sendiri. Masalahnya, batas kawasan itu tidak terlihat dari jalan.",
        },
        {
          en: "This map makes them visible. It holds all 27 Zone I segments and 468 Zone II segments named in the regulation. Zone III is every other street in the city, so it is never stored as a list. Writing that list would mean inventing something the regulation never wrote.",
          id: "Peta ini membuatnya terlihat. Seluruh 27 ruas Kawasan I dan 468 ruas Kawasan II yang disebut peraturan itu tersimpan di dalamnya. Kawasan III adalah semua jalan lain di dalam kota, jadi tidak disimpan sebagai daftar. Membuat daftarnya sama dengan mengarang sesuatu yang tidak pernah ditulis peraturannya.",
        },
      ],
    },
    {
      h2: { en: "Knowing when to say no", id: "Tahu kapan harus menolak" },
      p: [
        {
          en: "The regulation only applies inside Yogyakarta city. An early version missed this. Any point far from a Zone I or II street was treated as Zone III, so the map quoted a fee in Bandung, in Purworejo, even out at sea.",
          id: "Peraturan ini hanya berlaku di Kota Yogyakarta. Versi awal peta ini melewatkan hal itu. Titik mana pun yang jauh dari ruas Kawasan I atau II dianggap Kawasan III, sehingga peta memberi tarif di Bandung, di Purworejo, bahkan di tengah laut.",
        },
        {
          en: "That was more than a display bug. The map was claiming a city rule applied where it does not. Now, outside the coverage area, it shows no zone and no fee.",
          id: "Itu lebih dari sekadar salah tampilan. Peta mengklaim aturan kota berlaku di tempat yang bukan wilayahnya. Sekarang, di luar area cakupan, peta tidak menampilkan zona maupun tarif.",
        },
        {
          en: "The coverage area is not the official city boundary, and the map says so openly. It is drawn around the 14,272 road segments in the data with a 250 metre margin, about 91 km² in total. The city itself is 32.5 km², so any error falls on the safe side. No place inside the city is ever turned away.",
          id: "Area cakupannya juga bukan batas resmi kota, dan itu disampaikan terus terang. Area ini dibentuk dari 14.272 ruas jalan dalam data, ditambah jarak aman 250 meter, luasnya sekitar 91 km². Luas kota sendiri 32,5 km², jadi selisihnya selalu berpihak pada pengguna. Tidak ada tempat di dalam kota yang tertolak.",
        },
      ],
    },
    {
      h2: { en: "No labels it cannot back up", id: "Tanpa label yang tidak berdasar" },
      p: [
        {
          en: "The map never labels a place or a person as legal or illegal. The data to support that does not exist. Only the city transport agency holds the list of licensed parking spots, and there is no data on no-parking signs. Any such label would be a guess.",
          id: "Peta ini tidak pernah melabeli tempat atau orang sebagai legal maupun ilegal. Data untuk mendukungnya memang tidak ada. Daftar titik parkir berizin hanya dipegang Dinas Perhubungan, dan data rambu larangan parkir belum tersedia. Label semacam itu hanya tebakan.",
        },
        {
          en: "Instead it uses three neutral states: matching, needs checking, and no assignment on record. Legal status is for an officer to decide, not an algorithm, least of all one reading a phone position that can drift twenty to thirty metres in a narrow street.",
          id: "Sebagai gantinya, peta memakai tiga status netral: sesuai, perlu dicek, dan belum ada penugasan. Status hukum ditentukan petugas, bukan algoritma, apalagi algoritma yang membaca lokasi ponsel yang bisa meleset dua puluh sampai tiga puluh meter di jalan sempit.",
        },
        {
          en: "Five Malioboro side streets are still only proposals. They are drawn as dashed lines with a warning, so a proposal never looks like a decision.",
          id: "Lima sirip Malioboro masih berupa usulan. Ruasnya digambar putus putus dan disertai peringatan, supaya usulan tidak terlihat seperti keputusan.",
        },
      ],
    },
    {
      h2: { en: "Privacy by design", id: "Privasi sejak rancangan" },
      p: [
        {
          en: "The parking attendant table stores no ID number, name or address. Only a pseudonym is kept, in line with Indonesia's Personal Data Protection Law of 2022.",
          id: "Tabel juru parkir tidak menyimpan NIK, nama, atau alamat. Yang tersimpan hanya nama samaran, sesuai Undang-Undang Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.",
        },
        {
          en: "Complaints are anonymous. The form records the place, the time, the category, the fee charged and a short note. That note is the only place a name could slip in, so the form reminds people not to write names or phone numbers there.",
          id: "Aduan bersifat anonim. Formulirnya mencatat lokasi, waktu, kategori, tarif yang ditarik, dan catatan singkat. Catatan itu satu satunya tempat nama bisa ikut masuk, jadi formulirnya mengingatkan agar nama dan nomor telepon tidak ditulis di sana.",
        },
        {
          en: "Spam protection hashes each IP address with a random salt that changes every time the server restarts. It lives in memory only and never reaches the database or the logs.",
          id: "Perlindungan dari spam meringkas alamat IP dengan kunci acak yang berganti setiap server dinyalakan ulang. Datanya hanya ada di memori, tidak pernah masuk basis data maupun log.",
        },
      ],
    },
    {
      h2: { en: "Built to be trusted", id: "Dibangun agar bisa dipercaya" },
      p: [
        {
          en: "The fee is calculated in one place only. Three versions must agree on every result: the GeoPackage mode, the PostGIS mode and the standalone preview file. All three were tested against 594 combinations and matched every time.",
          id: "Tarif hanya dihitung di satu tempat. Tiga versi harus selalu memberi hasil yang sama: mode GeoPackage, mode PostGIS, dan berkas pratinjau mandiri. Ketiganya diuji pada 594 kombinasi dan hasilnya selalu sama.",
        },
        {
          en: "The coverage check is written in plain Python, without a geometry library, so both storage modes run exactly the same code. Two modes that disagree would be a bug that only shows up in production.",
          id: "Pemeriksaan area cakupan ditulis dengan Python biasa tanpa pustaka geometri, supaya kedua mode penyimpanan menjalankan kode yang persis sama. Dua mode yang memberi jawaban berbeda adalah bug yang baru muncul di produksi.",
        },
        {
          en: "Zone colours were chosen by measuring contrast against the base map, not by eye. Zone I reaches 6.64:1, Zone II 3.97:1 and Zone III 4.94:1, all above the WCAG threshold of 3:1 for graphics.",
          id: "Warna kawasan dipilih dengan mengukur kontrasnya terhadap peta dasar, bukan sekadar enak dilihat. Kawasan I mencapai 6,64:1, Kawasan II 3,97:1, dan Kawasan III 4,94:1, semuanya di atas ambang WCAG 3:1 untuk grafis.",
        },
      ],
    },
  ] as Bagian[],

  coba: {
    eyebrow: { en: "Live demo", id: "Demo langsung" } as Copy,
    h2: { en: "Check parking fees on the map", id: "Cek tarif parkir di peta" } as Copy,
    intro: [
      {
        en: "Search for a street, tap the map or drag it. The pin shows the zone and the fee right away.",
        id: "Cari nama jalan, ketuk peta, atau geser petanya. Pin langsung menunjukkan kawasan dan tarifnya.",
      },
    ] as Copy[],
    label: { en: "Parking fee map", id: "Peta tarif parkir" } as Copy,
    gagal: {
      en: "The map could not load. The fee panel still works for central Yogyakarta.",
      id: "Petanya gagal dimuat. Panel tarif tetap bekerja untuk pusat Yogyakarta.",
    } as Copy,
    ket: {
      en: "Move the map until the pin sits on your parking spot. Fees follow Yogyakarta city regulation 10/2023 and zones follow mayoral regulation 149/2020. This map is a guide, not a ruling. The fee board on site is what counts.",
      id: "Geser peta sampai pin tepat di tempat parkir. Tarif mengikuti Perda Kota Yogyakarta No. 10 Tahun 2023, kawasan mengikuti Perwal 149/2020. Peta ini panduan, bukan keputusan. Yang berlaku tetap papan tarif di lokasi.",
    } as Copy,
    tombol: { en: "See the live map", id: "Lihat peta langsung" } as Copy,
  },

  rail: {
    daftar: { en: "On this page", id: "Di halaman ini" } as Copy,
    judul: { en: "Interactive map", id: "Peta interaktif" } as Copy,
    isi: {
      en: "Drop a pin on any street in Yogyakarta. The zone and the fee appear instantly.",
      id: "Taruh pin di jalan mana pun di Kota Yogyakarta. Zona dan tarifnya langsung muncul.",
    } as Copy,
    tombol: { en: "Open the parking map", id: "Buka peta parkir" } as Copy,
    bacaJuga: { en: "Read next", id: "Baca juga" } as Copy,
    tulisan: { en: "When a map should say I do not know", id: "Kapan peta sebaiknya bilang tidak tahu" } as Copy,
    semua: { en: "All projects", id: "Semua proyek" } as Copy,
  },

  ajakTitle: { en: "See the rest", id: "Lihat yang lain" } as Copy,
  ajakBody: {
    en: "Other projects, and writing about how I decide things like the above.",
    id: "Proyek lain, dan tulisan tentang cara saya memutuskan hal hal seperti di atas.",
  } as Copy,
  ajakProyek: { en: "See projects", id: "Lihat proyek" } as Copy,
  ajakBlog: { en: "Read the blog", id: "Baca blog" } as Copy,
};
