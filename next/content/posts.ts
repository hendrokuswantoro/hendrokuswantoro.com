import type { Copy } from "./i18n";

export type Block =
  | { kind: "p"; text: Copy }
  | { kind: "h2"; text: Copy }
  | { kind: "quote"; text: Copy };

export type Post = {
  slug: string;
  date: string;
  dateLabel: Copy;
  readTime: Copy;
  tag: Copy;
  title: Copy;
  excerpt: Copy;
  lede: Copy;
  blocks: Block[];
};

export const BLOG = {
  eyebrow: { en: "Blog", id: "Blog" } as Copy,
  title: { en: "Short notes about maps.", id: "Catatan pendek soal peta." } as Copy,
};

export const POSTS: Post[] = [
  {
    slug: "kapan-peta-diam",
    date: "2026-09-02",
    dateLabel: { en: "2 Sep 2026", id: "2 Sep 2026" },
    readTime: { en: "3 min read", id: "3 menit baca" },
    tag: { en: "How I work", id: "Cara kerja" },
    title: {
      en: "When a map should say I do not know",
      id: "Kapan peta sebaiknya bilang tidak tahu",
    },
    excerpt: {
      en: "My parking map does not answer outside Yogyakarta. That looks like a gap. It is the best part.",
      id: "Peta parkir saya tidak menjawab di luar Kota Yogyakarta. Kelihatannya kurang, padahal itu bagian terbaiknya.",
    },
    lede: {
      en: "My parking map covers Yogyakarta city only. Outside it there is no zone and no fee. That is on purpose.",
      id: "Peta parkir saya hanya meliput Kota Yogyakarta. Di luar itu tidak ada zona dan tidak ada tarif. Itu disengaja.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "The rule only lives in one city", id: "Aturannya cuma berlaku di satu kota" },
      },
      {
        kind: "p",
        text: {
          en: "The fee follows a Yogyakarta city rule. That rule does not apply in Purworejo, in Bandung, or out at sea. A map that still shows a number there is making up a rule.",
          id: "Tarifnya mengikuti aturan Kota Yogyakarta. Aturan itu tidak berlaku di Purworejo, di Bandung, apalagi di tengah laut. Peta yang tetap menampilkan angka di sana sedang mengarang aturan.",
        },
      },
      {
        kind: "p",
        text: {
          en: "The first version did that. Every point far from a zoned street became Zone III, one thousand rupiah, anywhere in the world. It looked tidy. It was wrong.",
          id: "Versi pertama begitu. Tiap titik yang jauh dari jalan berzona jadi Kawasan III, seribu rupiah, di mana pun. Rapi dilihat, tapi salah.",
        },
      },
      { kind: "h2", text: { en: "What the app does now", id: "Yang dilakukan aplikasinya sekarang" } },
      {
        kind: "p",
        text: {
          en: "Now the app carries a boundary, drawn from the roads it really has. Inside it you get a zone and a fee. Outside it both stay empty, and the screen says the point is out of range.",
          id: "Sekarang aplikasinya punya batas, dibuat dari jalan yang benar benar dimuat. Di dalam batas ada zona dan tarif. Di luar batas keduanya kosong, dan layarnya bilang titik itu di luar jangkauan.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "Zero is a reading. Missing data is not. The two must never look the same.",
          id: "Nol itu hasil bacaan. Data yang tidak ada bukan. Keduanya tidak boleh kelihatan sama.",
        },
      },
      { kind: "h2", text: { en: "Why bother", id: "Kenapa harus begitu" } },
      {
        kind: "p",
        text: {
          en: "Saying nothing feels weak. But a wrong number gets copied, argued over, and printed. It lives much longer than a moment of disappointment.",
          id: "Menjawab tidak tahu memang terasa lemah. Tapi angka salah itu disalin, dijadikan bahan debat, lalu dicetak. Umurnya jauh lebih panjang daripada kecewa sesaat.",
        },
      },
      {
        kind: "p",
        text: {
          en: "People notice which app admits it does not know. That is the app they believe when it answers.",
          id: "Orang tahu aplikasi mana yang mau mengaku tidak tahu. Aplikasi itu yang dipercaya waktu menjawab.",
        },
      },
    ],
  },
  {
    slug: "titik-panas-bukan-kebakaran",
    date: "2026-08-24",
    dateLabel: { en: "24 Aug 2026", id: "24 Agu 2026" },
    readTime: { en: "4 min read", id: "4 menit baca" },
    tag: { en: "Satellite data", id: "Data satelit" },
    title: { en: "A hotspot is not a fire", id: "Titik panas bukan berarti kebakaran" },
    excerpt: {
      en: "A satellite sees heat, not flames. Small difference, big effect.",
      id: "Satelit melihat panas, bukan api. Beda tipis, akibatnya besar.",
    },
    lede: {
      en: "Every dry season the hotspot maps come around. One red dot is read as one fire. But a satellite sees heat, not flames.",
      id: "Tiap kemarau peta titik panas beredar. Satu titik merah dibaca sebagai satu kebakaran. Padahal satelit melihat panas, bukan api.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "What the satellite sees", id: "Yang dilihat satelit" },
      },
      {
        kind: "p",
        text: {
          en: "The sensor compares one patch of ground with the ground around it. If the patch is much hotter, it gets flagged. The patch is about 375 metres across. So one dot is a hot patch of land, not one flame.",
          id: "Sensornya membandingkan satu petak lahan dengan sekitarnya. Kalau petak itu jauh lebih panas, ia ditandai. Petaknya sekitar 375 meter. Jadi satu titik itu petak lahan yang panas, bukan satu kobaran.",
        },
      },
      {
        kind: "p",
        text: {
          en: "Heat is not always a land fire. A factory chimney, a furnace, a brick kiln, even a metal roof at noon can be flagged.",
          id: "Panas juga tidak selalu kebakaran lahan. Cerobong pabrik, tungku, tanur bata, bahkan atap seng waktu siang bisa ikut ditandai.",
        },
      },
      {
        kind: "h2",
        text: {
          en: "No dots does not mean safe",
          id: "Tidak ada titik bukan berarti aman",
        },
      },
      {
        kind: "p",
        text: {
          en: "This side is missed more often. The satellite passes a few times a day and clouds block the view. A fire under thick cloud never shows up.",
          id: "Sisi ini lebih sering terlewat. Satelit lewat beberapa kali sehari dan awan menutup pandangannya. Api di bawah awan tebal tidak pernah muncul.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "A hotspot map answers one question. Where the satellite saw heat, at the hour it passed.",
          id: "Peta titik panas menjawab satu pertanyaan. Di mana satelit melihat panas, pada jam ia lewat.",
        },
      },
      { kind: "h2", text: { en: "How I use them", id: "Cara saya memakainya" } },
      {
        kind: "p",
        text: {
          en: "I group the dots first. Dots close in place and time become one event, with a start, a direction and an end.",
          id: "Saya kelompokkan dulu titiknya. Titik yang berdekatan tempat dan waktunya jadi satu kejadian, punya awal, arah, dan akhir.",
        },
      },
      {
        kind: "p",
        text: {
          en: "Then every map says which sensor, which date and hour, and how sure the reading is. A reader can judge it, not just trust the red.",
          id: "Lalu tiap peta menyebut sensornya apa, tanggal dan jamnya, dan seberapa yakin bacaannya. Pembaca bisa menilai sendiri, bukan cuma percaya warna merahnya.",
        },
      },
    ],
  },
  {
    slug: "sumber-di-pojok-peta",
    date: "2026-08-12",
    dateLabel: { en: "12 Aug 2026", id: "12 Agu 2026" },
    readTime: { en: "3 min read", id: "3 menit baca" },
    tag: { en: "Map design", id: "Desain peta" },
    title: {
      en: "Why the source always goes in the corner",
      id: "Kenapa sumber selalu saya tulis di pojok peta",
    },
    excerpt: {
      en: "The small text in the corner decides if your map can be trusted. It holds three things.",
      id: "Tulisan kecil di pojok peta menentukan peta Anda bisa dipercaya atau tidak. Isinya tiga hal.",
    },
    lede: {
      en: "A map is often judged by its colours. What decides if it can be used is the small text in the corner.",
      id: "Peta sering dinilai dari warnanya. Padahal yang menentukan peta itu bisa dipakai atau tidak adalah tulisan kecil di pojok.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "Three things that must be there", id: "Tiga hal yang harus ada" },
      },
      {
        kind: "p",
        text: {
          en: "Where the data came from, named by agency or by file, not the word internet. When it was taken, because land cover last year and this year can differ a lot. The coordinate system and the scale, so people know if distances may be measured.",
          id: "Datanya dari mana, sebut nama lembaga atau berkasnya, bukan kata internet. Kapan diambil, sebab tutupan lahan tahun lalu dan tahun ini bisa beda jauh. Sistem koordinat dan skalanya, supaya orang tahu jaraknya boleh diukur atau tidak.",
        },
      },
      {
        kind: "p",
        text: {
          en: "If there is room I add one more, who made the map and when. So there is someone to ask when something looks odd.",
          id: "Kalau muat saya tambah satu lagi, siapa yang membuat peta dan kapan. Supaya ada yang bisa ditanya kalau ada yang janggal.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "A map with no source note is not a map. It is a picture shaped like an island.",
          id: "Peta tanpa keterangan sumber itu bukan peta. Itu gambar berbentuk pulau.",
        },
      },
      { kind: "h2", text: { en: "Why it matters", id: "Kenapa ini penting" } },
      {
        kind: "p",
        text: {
          en: "A printed map lives long. It goes on a wall, gets photographed, gets sent to a group, then used a year later by someone who was not in the meeting. All they have is that corner.",
          id: "Peta cetak umurnya panjang. Ditempel di dinding, difoto, dikirim ke grup, lalu dipakai setahun kemudian oleh orang yang tidak ikut rapat. Yang tersisa cuma pojok itu.",
        },
      },
      {
        kind: "p",
        text: {
          en: "So I write that part first, before the colours. If the source is not clear, the map is not ready.",
          id: "Jadi bagian itu saya tulis lebih dulu, sebelum warna. Kalau sumbernya belum jelas, petanya belum siap.",
        },
      },
    ],
  },
];

export function postBySlug(slug: string): Post | undefined {
  return POSTS.find((post) => post.slug === slug);
}
