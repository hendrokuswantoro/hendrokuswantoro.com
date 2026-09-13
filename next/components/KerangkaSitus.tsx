import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { LanguageProvider } from "@/components/LanguageProvider";
import { RevealObserver } from "@/components/RevealObserver";
import { TabBar } from "@/components/TabBar";

/**
 * Kepala, kaki, bilah tab, dan saklar bahasa, yaitu seluruh perabot yang
 * dimiliki halaman yang dibaca pengunjung.
 *
 * Dipisah dari tata letak akar supaya /admin tidak ikut memakainya. Sebelum
 * ini semuanya duduk di app/layout.tsx, jadi halaman admin punya dua <header>
 * sekaligus: kepala situs di atas kepala adminnya sendiri, lengkap dengan
 * tautan Beranda dan saklar bahasa yang tidak berarti apa apa di sana.
 * Ketahuan saat uji peramban menolak memilih satu dari dua <header>, bukan
 * saat membaca kodenya.
 */
export function KerangkaSitus({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <Header />
      {children}
      <Footer />
      <TabBar />
      <RevealObserver />
    </LanguageProvider>
  );
}
