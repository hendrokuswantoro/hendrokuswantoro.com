import type { Copy } from "./i18n";

/* Studi kasus Parkir Jogja, salinan port Next dari parkir-jogja.html.
 *
 * Isinya ditaruh di sini, bukan di dalam komponennya, dengan alasan yang sama
 * seperti posts.ts dan projects.ts: tampilannya boleh berubah tanpa menyentuh
 * satu kalimat pun, dan tiap kalimat punya pasangan Indonesianya di baris yang
 * sama sehingga yang hilang terjemahannya langsung kelihatan.
 *
 * Tiap angka di bawah dibaca dari dokumen proyek parkirnya sendiri. Tidak ada
 * satu pun yang dikira kira, dan angka nol di bawah adalah nol yang sungguhan,
 * bukan tempat kosong yang belum diisi.
 */

export type Angka = { num: Copy; label: Copy };
export type Bagian = { h2: Copy; p: Copy[] };

export const PARKIR = {
  slug: "parkir-jogja",

  back: { en: "Back to projects", id: "Kembali ke proyek" } as Copy,
  badge: { en: "Case study", id: "Studi kasus" } as Copy,
  tags: ["FastAPI", "PostGIS", "MapLibre"],

  title: { en: "Yogyakarta Parking Map", id: "Peta Parkir Yogyakarta" } as Copy,
  lede: {
    en: "Pick a point on the map and the zone and the fee show up. The part that took longest to get right was not that. It was deciding when the map should refuse to answer.",
    id: "Pilih titik di peta, zona dan tarifnya muncul. Bagian yang paling lama saya pikirkan justru bukan itu, melainkan kapan peta ini harus menolak menjawab.",
  } as Copy,

  image: "/assets/img/work/parking.webp",
  alt: {
    en: "The parking map showing the zone and the fee for a street in Yogyakarta",
    id: "Peta parkir yang menampilkan zona dan tarif untuk sebuah ruas di Yogyakarta",
  } as Copy,

  angka: [
    {
      num: { en: "495", id: "495" },
      label: {
        en: "street segments stored for Zone I and II",
        id: "ruas Kawasan I dan II yang disimpan",
      },
    },
    {
      num: { en: "14,272", id: "14.272" },
      label: {
        en: "roads used to build the coverage boundary",
        id: "ruas jalan dipakai membangun batas cakupan",
      },
    },
    {
      num: { en: "594", id: "594" },
      label: {
        en: "fee combinations, three implementations agree",
        id: "kombinasi tarif, tiga penerapan sepakat",
      },
    },
    {
      num: { en: "0", id: "0" },
      label: {
        en: "places labelled legal or illegal",
        id: "tempat yang dilabeli legal atau ilegal",
      },
    },
  ] as Angka[],

  bagian: [
    {
      h2: { en: "The question it answers", id: "Pertanyaan yang dijawabnya" },
      p: [
        {
          en: "What is the parking fee on this street, and why that number. The fee follows a city regulation that splits Yogyakarta into Zone I, Zone II and Zone III. Zone I and Zone II have a list of streets. Zone III is whatever is left.",
          id: "Berapa tarif parkir di ruas ini, dan kenapa segitu. Tarifnya mengikuti Perwal 149/2020, yang membagi kota jadi Kawasan I, II, dan III. Kawasan I dan II punya daftar ruas; Kawasan III adalah sisanya.",
        },
        {
          en: "Because Zone III is the remainder, the system does not store a list for it. It stores 27 segments for Zone I and 468 for Zone II. Building a Zone III list would mean inventing a list the regulation itself does not have.",
          id: "Karena Kawasan III adalah sisa, sistem ini tidak menyimpan daftarnya. Yang tersimpan 27 ruas Kawasan I dan 468 ruas Kawasan II. Membuat daftar Kawasan III berarti mengarang daftar yang aturannya sendiri tidak punya.",
        },
      ],
    },
    {
      h2: { en: "What it refuses to answer", id: "Yang ia tolak jawab" },
      p: [
        {
          en: "The regulation binds inside Yogyakarta city and nowhere else. An early version answered Zone III for any point far from a Zone I or Zone II street. So it showed Zone III and a fee in other towns, and out at sea.",
          id: "Aturan itu mengikat di Kota Yogyakarta saja. Versi awal menjawab Kawasan III untuk titik mana pun yang jauh dari ruas Kawasan I dan II, jadi ia menampilkan Kawasan III dan Rp1.000 di Purworejo, di Bandung, bahkan di tengah laut.",
        },
        {
          en: "That is not a display bug. It is a claim that a city regulation applies somewhere it does not. Outside the coverage the zone comes back empty and the fee comes back empty, not as a number.",
          id: "Itu bukan sekadar salah tampilan. Itu mengarang bahwa aturan Kota Yogyakarta berlaku di tempat itu. Sekarang di luar cakupan, zonanya kosong dan tarifnya kosong, bukan angka.",
        },
        {
          en: "The coverage boundary is not the administrative boundary either, and the system says so plainly. It is a concave hull around the 14,272 road segments that were actually loaded, buffered by 250 metres, about 91 km2. The city itself is 32.5 km2, so the error leans the safe way. A point still inside the city will not be turned away.",
          id: "Batas cakupannya juga bukan batas administrasi kota, dan itu disebut terus terang. Yang dipakai selubung cekung dari 14.272 ruas jalan yang benar benar dimuat, disangga 250 meter, luasnya sekitar 91 km2. Kota Yogyakarta sendiri 32,5 km2, jadi kekeliruannya condong ke arah yang aman: tempat yang masih di dalam kota tidak akan tertolak.",
        },
      ],
    },
    {
      h2: { en: "What it never says", id: "Yang ia tidak pernah katakan" },
      p: [
        {
          en: "No place and no person is labelled legal or illegal. The data for that does not exist. The list of permitted points sits with the transport agency, and there is no data on no-parking signs. A label like that would have to be invented.",
          id: "Tidak ada tempat dan tidak ada orang yang dilabeli legal atau ilegal. Datanya memang tidak ada: daftar titik bersurat keputusan hanya dipegang Dinas Perhubungan, dan data rambu larangan parkir belum tersedia. Label semacam itu akan dikarang.",
        },
        {
          en: "There are only three states: matching, needs checking, and no assignment on record. Deciding legal status belongs to an officer, not to an algorithm, and least of all to one reading a phone position that can be twenty to thirty metres out in a tight corridor.",
          id: "Status yang dikenal cuma tiga: sesuai, perlu verifikasi, dan tanpa penugasan. Penetapan status hukum wewenang petugas, bukan algoritma, apalagi algoritma yang membaca posisi ponsel yang di koridor rapat bisa meleset dua puluh sampai tiga puluh meter.",
        },
        {
          en: "Five Malioboro side streets that are still proposals are drawn with a dashed line and carry a warning, so a proposal never looks like a decision.",
          id: "Lima sirip Malioboro yang belum ditetapkan digambar putus putus dan memunculkan peringatan, supaya usulan tidak terlihat seperti keputusan.",
        },
      ],
    },
    {
      h2: { en: "What it does not store", id: "Yang ia tidak simpan" },
      p: [
        {
          en: "The parking attendant table holds no national ID number, no name and no address. Only a pseudonym. That follows the Indonesian personal data protection law.",
          id: "Tabel juru parkir tidak memuat NIK, nama, maupun alamat. Hanya pseudonim. Ini mengikuti Undang-Undang Nomor 27 Tahun 2022.",
        },
        {
          en: "A complaint never asks who is filing it. What is kept is the place, the time, the category, the fee that was charged, and a free text note. That note is the one place an identity could slip in by accident, so the form warns against writing names and numbers in it.",
          id: "Aduan tidak pernah menanyakan identitas pelapor. Yang disimpan lokasi, waktu, kategori, tarif yang dipungut, dan keterangan bebas. Kolom keterangan itu satu satunya tempat identitas bisa masuk tanpa sengaja, jadi antarmukanya memperingatkan agar nama dan nomor tidak ditulis di sana.",
        },
        {
          en: "The rate limiter on complaints hashes the IP address with a random salt made fresh for each process. It lives in memory only, never reaches the database or a log file, and disappears when the process stops.",
          id: "Pembatas laju pengiriman aduan meringkas alamat IP dengan garam acak per proses, disimpan di memori saja, tidak pernah masuk basis data maupun berkas log, dan hilang saat prosesnya berhenti.",
        },
      ],
    },
    {
      h2: { en: "How it is built", id: "Cara ia dibangun" },
      p: [
        {
          en: "The fee is calculated in exactly one place. The interface does not do its own arithmetic. Three implementations have to agree, the GeoPackage mode, the PostGIS mode, and an embedded copy inside the standalone preview file, and all three were tested against 594 combinations.",
          id: "Perhitungan tarif hanya ada di satu tempat. Antarmukanya tidak menghitung sendiri. Ada tiga penerapan yang harus sepakat, yaitu mode GeoPackage, mode PostGIS, dan salinan tertanam di berkas pratinjau mandiri, dan ketiganya sudah diuji sepakat pada 594 kombinasi.",
        },
        {
          en: "The coverage check is written in plain Python rather than with a geometry library, so both storage modes run exactly the same code. Two modes that answer differently is a defect that only shows up in production.",
          id: "Pemeriksaan batas cakupan ditulis dengan Python biasa, bukan memakai shapely, supaya kedua mode penyimpanan menjalankan kode yang sama persis. Dua mode yang menjawab berbeda adalah cacat yang hanya muncul di produksi.",
        },
        {
          en: "The zone colours were checked against the basemap rather than picked by eye. Zone I reaches 6.64:1, Zone II 3.97:1, Zone III 4.94:1, against a 3.0:1 threshold for graphics.",
          id: "Warna kawasannya dihitung kontrasnya terhadap peta dasar, bukan dipilih karena enak dilihat. Kawasan I 6,64:1, Kawasan II 3,97:1, Kawasan III 4,94:1, sedangkan ambang WCAG untuk grafis 3,0:1.",
        },
      ],
    },
    {
      h2: { en: "What is still missing", id: "Yang belum ada" },
      p: [
        {
          en: "Three things hold up the next phase, and none of them is code. The list of permitted parking points, a pseudonymised register of attendants, and attendant positions, which will not exist until there is an operational partnership.",
          id: "Tiga hal menahan fase berikutnya, dan ketiganya bukan soal kode: daftar titik parkir bersurat keputusan, rekap juru parkir yang sudah dipseudonimkan, dan posisi juru parkir yang tidak akan ada sampai ada kemitraan operasional.",
        },
        {
          en: "The monitoring dashboard is already built and reads the real database views, so nothing more needs writing once the data arrives. While a table is empty the panel names which table is empty and who owns it, rather than showing a zero. A zero is a reading. Missing data is not.",
          id: "Kerangka dashboard pengawasannya sudah ada dan memanggil tampilan basis data yang sebenarnya, jadi begitu datanya masuk tidak ada lagi yang perlu ditulis. Selama datanya kosong, panelnya menyebutkan tabel mana yang kosong dan siapa pemiliknya, bukan menampilkan nol. Nol adalah bacaan; ketiadaan data bukan.",
        },
      ],
    },
  ] as Bagian[],

  ajakTitle: { en: "See the rest", id: "Lihat yang lain" } as Copy,
  ajakBody: {
    en: "Other projects, and writing about how I decide things like the above.",
    id: "Proyek lain, dan tulisan tentang cara saya memutuskan hal hal seperti di atas.",
  } as Copy,
  ajakProyek: { en: "See projects", id: "Lihat proyek" } as Copy,
  ajakBlog: { en: "Read the blog", id: "Baca blog" } as Copy,
};
