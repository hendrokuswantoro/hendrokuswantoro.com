import type { Metadata } from "next";
import { AboutView } from "@/components/AboutView";

export const metadata: Metadata = {
  title: "About",
  description:
    "Hendro Kuswantoro, spatial data and systems architect in Yogyakarta. The skills and tools I use most.",
  alternates: { canonical: "/about/" },
  openGraph: { type: "profile" },
};

export default function AboutPage() {
  return <AboutView />;
}
