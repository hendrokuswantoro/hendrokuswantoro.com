import type { Metadata } from "next";

/**
 * Halaman admin tidak boleh diindeks, dan tidak boleh ikut sitemap.
 *
 * Bukan karena alamatnya rahasia, ia tidak rahasia dan tidak pernah bisa
 * jadi rahasia. Yang menjaganya adalah autentikasi di server, bukan
 * ketidaktahuan mesin pencari. Ini soal yang lain: halaman yang seluruh isinya
 * datang dari API dan tidak bisa dibaca tanpa masuk hanya akan muncul di
 * hasil pencarian sebagai halaman kosong, dan halaman kosong di hasil
 * pencarian merusak kesan seluruh situsnya.
 */
export const metadata: Metadata = {
  title: "Admin",
  robots: { index: false, follow: false, nocache: true },
};

/**
 * `lang="id"` dipasang di sini, dan itu bukan basa basi.
 *
 * Seluruh permukaan admin berbahasa Indonesia, sedangkan <html> situs ini
 * bawaannya "en". Dua hal bergantung padanya: pembaca layar melafalkannya
 * dengan benar, dan `hyphens: auto` hanya bisa memenggal kata kalau peramban
 * tahu bahasanya. Tanpa itu, teks yang dirata kiri kanan akan merentangkan
 * spasi untuk menutup baris, dan pada kolom sempit hasilnya sungai putih yang
 * menembus paragraf.
 */
export default function LayoutAdmin({ children }: { children: React.ReactNode }) {
  return <div lang="id">{children}</div>;
}
