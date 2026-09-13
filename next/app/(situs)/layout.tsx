import { KerangkaSitus } from "@/components/KerangkaSitus";

/**
 * Tata letak untuk halaman yang dibaca pengunjung.
 *
 * (situs) adalah route group: tanda kurung membuatnya tidak muncul di alamat
 * sama sekali, jadi /about tetap /about. Gunanya satu, yaitu memberi halaman
 * publik sebuah tata letak yang tidak ikut dipakai /admin.
 */
export default function LayoutSitus({ children }: { children: React.ReactNode }) {
  return <KerangkaSitus>{children}</KerangkaSitus>;
}
