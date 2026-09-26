import type { Metadata, Viewport } from "next";
import { Poppins } from "next/font/google";
import { SITE } from "@/content/nav";
import "./globals.css";

const SKRIP_TEMA =
  'try{var t=localStorage.getItem("hk-tema");' +
  'if(t==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}';

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
        <script
          dangerouslySetInnerHTML={{
            __html: SKRIP_TEMA,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
