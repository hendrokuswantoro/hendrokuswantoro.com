import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { LanguageProvider } from "@/components/LanguageProvider";
import { RevealObserver } from "@/components/RevealObserver";
import { TabBar } from "@/components/TabBar";

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
