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
  lede: {
    en: "I write down what I learn while working: how to read data, when a map may answer, and when it should stay quiet. In plain words.",
    id: "Saya tulis yang saya pelajari waktu kerja: cara membaca data, kapan peta boleh menjawab, dan kapan sebaiknya diam. Bahasa sederhana saja.",
  } as Copy,
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
      en: "The parking map I built refuses to answer outside Yogyakarta. It looks like a missing feature. It is actually the most important part.",
      id: "Peta parkir yang saya bikin menolak menjawab di luar Kota Yogyakarta. Kelihatannya seperti kekurangan, padahal itu justru bagian yang paling penting.",
    },
    lede: {
      en: "The parking map I built covers Yogyakarta city only. Outside it, the app shows no zone and no fee. That was on purpose.",
      id: "Peta parkir yang saya bikin hanya meliput Kota Yogyakarta. Di luar itu, aplikasinya tidak menampilkan zona dan tidak menampilkan tarif. Itu memang disengaja.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "The rule only lives in one city", id: "Aturannya cuma berlaku di satu kota" },
      },
      {
        kind: "p",
        text: {
          en: "The parking fee follows a Yogyakarta city rule. A city rule does not apply in Purworejo, not in Bandung, and certainly not in the middle of the sea. So if the map still shows a number there, it is not just a display bug. The map is making up a rule that does not exist.",
          id: "Tarif parkirnya mengikuti aturan Kota Yogyakarta. Aturan kota itu tidak berlaku di Purworejo, tidak di Bandung, apalagi di tengah laut. Jadi kalau petanya tetap menampilkan angka di sana, itu bukan sekadar salah tampil. Petanya sedang mengarang aturan yang tidak ada.",
        },
      },
      {
        kind: "p",
        text: {
          en: "The first version did exactly that. Any point far from a zoned street was treated as Zone III, one thousand rupiah, wherever the point was. It looked tidy. It was wrong.",
          id: "Versi pertama sistem ini melakukan persis itu. Tiap titik yang jauh dari jalan berzona dianggap Kawasan III, tarif seribu rupiah, di mana pun titiknya. Rapi dilihat, tapi salah.",
        },
      },
      { kind: "h2", text: { en: "What the app does now", id: "Yang dilakukan aplikasinya sekarang" } },
      {
        kind: "p",
        text: {
          en: "The app carries one boundary: how far its data reaches. The boundary is built from the road network that was actually loaded, then buffered a little. Inside it, you get a zone and a fee. Outside it, the zone is empty, the fee is empty, and the screen says the point is outside the covered area.",
          id: "Aplikasinya membawa satu batas: sejauh mana datanya menjangkau. Batas itu dibangun dari jaringan jalan yang benar-benar dimuat, lalu disangga sedikit. Di dalam batas, Anda dapat zona dan tarif. Di luar batas, zonanya kosong, tarifnya kosong, dan layarnya bilang titik itu di luar cakupan.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "Zero is a reading. Missing data is not. The two must never look the same.",
          id: "Nol itu hasil bacaan. Data yang tidak ada bukan. Keduanya tidak boleh kelihatan sama.",
        },
      },
      { kind: "h2", text: { en: "Why bother", id: "Kenapa repot-repot begini" } },
      {
        kind: "p",
        text: {
          en: "Answering nothing feels like an unfinished product. But a wrong number gets copied, argued over, and printed. A wrong number lives far longer than the small disappointment of an app that stays quiet.",
          id: "Menjawab tidak tahu memang terasa seperti produk yang belum jadi. Tapi angka yang salah itu disalin orang, dijadikan bahan debat, lalu dicetak. Angka salah hidup jauh lebih lama daripada rasa kecewa sesaat karena aplikasinya diam.",
        },
      },
      {
        kind: "p",
        text: {
          en: "People are also not as easily fooled as we assume. They quickly learn which app admits it does not know, and that is the app they trust when it does answer.",
          id: "Lagi pula pengguna tidak sebodoh yang sering dikira. Mereka cepat tahu aplikasi mana yang mau mengaku tidak tahu, dan justru aplikasi itu yang dipercaya waktu menjawab.",
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
      en: "A satellite sees heat, not flames. A small difference, with big consequences if a hotspot is read as a confirmed fire.",
      id: "Satelit melihat panas, bukan api. Beda tipis, tapi akibatnya besar kalau titik panas dibaca sebagai kebakaran yang sudah pasti.",
    },
    lede: {
      en: "Every dry season, hotspot maps go around. One red dot is often read as one fire. But what the satellite sees is not flames. It is heat.",
      id: "Tiap musim kemarau, peta titik panas beredar di mana-mana. Satu titik merah sering dibaca sebagai satu kebakaran. Padahal yang dilihat satelit bukan api, melainkan panas.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "What the satellite actually sees", id: "Yang sebenarnya dilihat satelit" },
      },
      {
        kind: "p",
        text: {
          en: "The sensor compares the temperature of one patch of ground with its surroundings. If that patch is much hotter, it gets flagged. The patch is not small, about 375 by 375 metres for the common sensor. So one dot is not one flame, it is one patch of ground that runs hot.",
          id: "Sensornya membandingkan suhu satu petak lahan dengan sekitarnya. Kalau petak itu jauh lebih panas, ia ditandai. Petaknya tidak kecil, sekitar 375 meter kali 375 meter untuk sensor yang biasa dipakai. Jadi satu titik bukan satu kobaran, melainkan satu petak lahan yang kepanasan.",
        },
      },
      {
        kind: "p",
        text: {
          en: "What makes it hot is not always a land fire either. A factory chimney, a furnace, a brick kiln, even a metal roof baking at noon can get flagged too.",
          id: "Yang bikin panas juga tidak selalu kebakaran lahan. Cerobong pabrik, tungku, tanur bata, bahkan atap seng yang terbakar matahari siang bisa ikut tertandai.",
        },
      },
      {
        kind: "h2",
        text: {
          en: "No dots does not mean nothing burns",
          id: "Tidak ada titik bukan berarti aman",
        },
      },
      {
        kind: "p",
        text: {
          en: "This is the side people miss more often. The satellite passes a few times a day, and clouds block its view. A fire burning under thick cloud, or one that dies down before the satellite passes, never shows up on the map.",
          id: "Ini sisi yang lebih sering terlewat. Satelit lewat beberapa kali sehari, dan awan menutup pandangannya. Api yang menyala di bawah awan tebal, atau yang padam sebelum satelit lewat, tidak pernah muncul di peta.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "A hotspot map answers one question only: where the satellite saw heat, at the hour it passed. The rest is interpretation.",
          id: "Peta titik panas menjawab satu pertanyaan saja: di mana satelit melihat panas, pada jam ia lewat. Selebihnya tafsiran.",
        },
      },
      { kind: "h2", text: { en: "How I use them", id: "Cara saya memakainya" } },
      {
        kind: "p",
        text: {
          en: "I group the dots first. Dots that sit close in both place and time become one event, so what you read is no longer thousands of loose dots but an event with a beginning, a direction and an end.",
          id: "Titik-titiknya saya kelompokkan dulu. Titik yang berdekatan tempat dan waktunya digabung jadi satu kejadian, supaya yang dibaca bukan lagi ribuan titik lepas, melainkan kejadian yang punya awal, arah, dan akhir.",
        },
      },
      {
        kind: "p",
        text: {
          en: "Then every map gets a note: which sensor, the date and hour, and the confidence level I used. That way a reader can judge for themselves instead of just trusting the red.",
          id: "Lalu tiap peta saya beri keterangan: sensornya apa, tanggal dan jamnya, dan tingkat keyakinan yang saya pakai. Dengan begitu pembaca bisa menilai sendiri, bukan sekadar percaya warna merahnya.",
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
      en: "That small text in the corner decides whether your map can be trusted. It only needs three things.",
      id: "Tulisan kecil di pojok peta itu yang menentukan peta Anda bisa dipercaya atau tidak. Isinya cuma tiga hal.",
    },
    lede: {
      en: "A good map is often judged by its colours. What decides whether it can actually be used is usually the small text in the bottom corner.",
      id: "Peta yang bagus sering dinilai dari warnanya. Padahal yang menentukan peta itu bisa dipakai atau tidak biasanya tulisan kecil di pojok bawah.",
    },
    blocks: [
      {
        kind: "h2",
        text: { en: "Three things that must be there", id: "Tiga hal yang harus ada" },
      },
      {
        kind: "p",
        text: {
          en: "First, where the data came from. The name of the agency or the file, not just the word internet. Second, when it was taken. A land cover map from last year and this year can differ a lot. Third, the coordinate system and the scale, so people know whether distances on the map may be measured at all.",
          id: "Pertama, datanya dari mana. Nama lembaga atau berkasnya, bukan sekadar tulisan sumber: internet. Kedua, kapan datanya diambil. Peta tutupan lahan tahun lalu dan tahun ini bisa beda jauh. Ketiga, sistem koordinat dan skalanya, supaya orang tahu jarak di peta itu boleh diukur atau tidak.",
        },
      },
      {
        kind: "p",
        text: {
          en: "If there is room, I add one more: who made the map and when. Not for show, but so there is someone to ask when something looks odd.",
          id: "Kalau muat, saya tambahkan satu lagi: siapa yang membuat petanya dan kapan dibuat. Bukan untuk gagah-gagahan, tapi supaya ada yang bisa ditanya kalau ada yang janggal.",
        },
      },
      {
        kind: "quote",
        text: {
          en: "A map with no source note is not a map. It is a picture that happens to be shaped like an island.",
          id: "Peta tanpa keterangan sumber itu bukan peta. Itu gambar yang kebetulan berbentuk pulau.",
        },
      },
      { kind: "h2", text: { en: "Why this matters", id: "Kenapa ini penting" } },
      {
        kind: "p",
        text: {
          en: "A printed map lives a long time. It goes on an office wall, gets photographed, gets sent to a group chat, then used again a year later by someone who was not in the meeting. The only thing left for them is that text in the corner.",
          id: "Peta cetak umurnya panjang. Ia ditempel di dinding kantor, difoto, dikirim ke grup, lalu dipakai lagi setahun kemudian oleh orang yang tidak ikut rapatnya. Yang tersisa untuk mereka cuma tulisan di pojok itu.",
        },
      },
      {
        kind: "p",
        text: {
          en: "So I write that part first, before thinking about colours. If the source is not clear yet, the map is not ready to be made.",
          id: "Jadi bagian itu saya tulis lebih dulu, sebelum memikirkan warna. Kalau sumbernya belum jelas, petanya memang belum siap dibuat.",
        },
      },
    ],
  },
];

export function postBySlug(slug: string): Post | undefined {
  return POSTS.find((post) => post.slug === slug);
}
