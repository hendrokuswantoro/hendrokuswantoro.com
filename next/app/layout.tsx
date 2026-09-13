import type { Metadata, Viewport } from "next";
import { Poppins } from "next/font/google";
import { SITE } from "@/content/nav";
import "./globals.css";

/** Sama persis dengan skrip sebaris di versi HTML biasa, sampai ke bitanya,
 *  supaya satu hash CSP di `_headers` berlaku untuk keduanya. */
const SKRIP_TEMA =
  'try{var t=localStorage.getItem("hk-tema");' +
  'if(t==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}';

/**
 * Poppins is self hosted by next/font, so the exported site makes no request
 * to Google at runtime. It stands in for the Gojek lettering, which is not
 * publicly licensed.
 */
const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-poppins",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: "Hendro Kuswantoro",
    template: "%s",
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
  themeColor: "#f6f6f6",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={poppins.variable}>
      <head>
        {/* Tema dipasang sebelum bingkai pertama. React baru menyala sesudah
            hidrasi, jadi tanpa ini pembaca yang memilih gelap melihat satu
            bingkai putih lebih dulu. Isinya dijaga sama persis dengan yang di
            versi HTML biasa, termasuk hash CSP-nya. */}
        <script
          dangerouslySetInnerHTML={{
            __html: SKRIP_TEMA,
          }}
        />
      </head>
      {/* Kepala, kaki, dan bilah tab tidak ada di sini. Keduanya milik
          halaman yang dibaca pengunjung, dan tinggal di app/(situs)/layout.tsx.
          Halaman admin memakai tata letak akar ini saja, jadi ia tidak lagi
          punya dua <header> bertumpuk. */}
      <body>{children}</body>
    </html>
  );
}
