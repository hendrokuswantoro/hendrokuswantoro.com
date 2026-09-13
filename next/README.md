# hendrokuswantoro.com, Next.js port

Versi Next.js 15 + TypeScript dari situs yang ada di folder induk. Isinya
sama persis, hanya cara membangunnya yang berbeda.

> **Dibangun, belum diterbitkan.** Sejak Node 24.19.0 terpasang pada
> 12 September 2026, `npm ci`, `npm run typecheck`, dan `npm run build` semuanya
> jalan dan lolos: 12 halaman diekspor ke `out/`. Yang belum, ia belum pernah
> jadi versi yang dilihat pengunjung. Versi HTML biasa di folder induk yang
> hidup, dan ia yang punya 437 uji.
>
> `npm ci`, bukan `npm install`: `package-lock.json` sudah ikut repositori,
> dan `ci` memasang persis versi yang tertulis di sana.

> **Jangan menyunting `app/globals.css`.** Berkas itu dibangkitkan dari
> `assets/css/style.css` oleh `python tools/gaya_next.py`. Dua salinan sistem
> desain adalah dua tempat yang harus diubah tiap kali satu warna bergeser,
> dan yang kedua selalu tertinggal. Sudah terjadi.

## Menjalankan

```bash
cd "D:/Projects/personal web/next"
npm install
npm run dev        # http://localhost:3000
```

Perintah lain:

```bash
npm run typecheck  # tsc --noEmit
npm run lint
npm run build      # menghasilkan folder out/
```

## Kenapa static export

`next.config.ts` memakai `output: "export"`, sebab situs ini tidak punya
perilaku sisi server sama sekali. Hasil `npm run build` adalah folder `out/`
berisi berkas statis, persis seperti versi HTML biasa, jadi Cloudflare Pages
cukup menyajikannya tanpa runtime Node.

`trailingSlash: true` membuat setiap rute menjadi folder sendiri, misalnya
`/about/index.html`. Karena itu tautannya `/about/`, bukan `/about.html`
seperti versi HTML biasa. Kalau nanti berpindah ke versi ini, pasang
pengalihan dari alamat lama ke alamat baru supaya tautan yang sudah beredar
tidak mati.

## Susunan

```
app/layout.tsx          font, metadata, provider bahasa, header, footer, tab bar
app/page.tsx            Home
app/about/page.tsx      About
app/project/page.tsx    Project
app/blog/page.tsx       daftar tulisan
app/blog/[slug]/        satu halaman per tulisan, dibangun dari content/posts.ts
app/not-found.tsx       404
app/sitemap.ts          sitemap.xml dibangkitkan saat build
app/robots.ts           robots.txt dibangkitkan saat build
app/globals.css         salinan assets/css/style.css, dua nama font diganti variabel
components/             komponen tampilan, semuanya memakai kelas CSS yang sama
content/                seluruh teks, satu berkas per halaman
public/                 gambar, manifest, dan _headers
```

## Dwibahasa

Tidak ada lagi atribut `data-ind`. Tiap teks sekarang bertipe
`Copy = { en: string; id: string }` di dalam `content/`, dan komponen
memanggil `say(copy)` dari `useLang()`. Terjemahan yang hilang menjadi galat
TypeScript, bukan teks Inggris yang lolos diam-diam.

Render pertama selalu Inggris supaya HTML hasil ekspor cocok dengan hasil
hidrasi. Pilihan bahasa dari `localStorage` atau dari bahasa peramban
diterapkan di dalam `useEffect` sesudah itu.

## Menambah tulisan blog

Cukup satu tempat: tambahkan satu objek di awal larik `POSTS` pada
`content/posts.ts`. Halaman, sitemap, dan daftar di `/blog/` ikut menyesuaikan
sendiri, karena `generateStaticParams` membacanya dari larik itu.

Isi tulisan disusun dari blok: `{ kind: "p" }`, `{ kind: "h2" }`, dan
`{ kind: "quote" }`.

## Font

`next/font/google` mengunduh Inter dan Outfit saat build lalu menyajikannya
dari domain sendiri, jadi tidak ada permintaan ke Google saat halaman dibuka.
Nama variabelnya `--font-inter` dan `--font-outfit`, dan `app/globals.css`
sudah menunjuk ke keduanya.

## Menerbitkan ke Cloudflare Pages

| Pengaturan | Nilai |
| --- | --- |
| Framework preset | Next.js (Static HTML Export) |
| Build command | `npm run build` |
| Build output directory | `out` |
| Root directory | `next` |
| Node version | 20 atau lebih baru, lewat variabel `NODE_VERSION` |

Atau dari komputer sendiri, sesudah Node.js terpasang:

```bash
npm run build
npx wrangler pages deploy out --project-name hendrokuswantoro
```
