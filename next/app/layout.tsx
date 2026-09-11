import type { Metadata, Viewport } from "next";
import { Inter, Outfit } from "next/font/google";
import { SITE } from "@/content/nav";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { LanguageProvider } from "@/components/LanguageProvider";
import { RevealObserver } from "@/components/RevealObserver";
import { TabBar } from "@/components/TabBar";
import "./globals.css";

/**
 * The fonts are self hosted by next/font, so the exported site makes no
 * request to Google at runtime. The CSS variables match the family names the
 * stylesheet already asks for.
 */
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-inter",
});

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["600", "700"],
  display: "swap",
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: "Hendro Kuswantoro - Maps and map apps",
    template: "%s - Hendro Kuswantoro",
  },
  description: "I make maps and map apps in Yogyakarta.",
  authors: [{ name: SITE.name, url: SITE.url }],
  manifest: "/site.webmanifest",
  icons: {
    icon: [{ url: "/assets/img/favicon.svg", type: "image/svg+xml" }],
    apple: [{ url: "/assets/img/apple-touch-icon.png" }],
  },
  openGraph: {
    type: "website",
    siteName: SITE.name,
    locale: "en_US",
    alternateLocale: "id_ID",
    images: ["/assets/img/og-cover.png"],
  },
  twitter: { card: "summary_large_image", images: ["/assets/img/og-cover.png"] },
};

export const viewport: Viewport = {
  themeColor: "#00aa13",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body>
        <LanguageProvider>
          <Header />
          {children}
          <Footer />
          <TabBar />
          <RevealObserver />
        </LanguageProvider>
      </body>
    </html>
  );
}
