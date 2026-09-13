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

export default function LayoutAdmin({ children }: { children: React.ReactNode }) {
  return children;
}
