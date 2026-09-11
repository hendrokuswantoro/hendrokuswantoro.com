import type { Metadata } from "next";
import { HomeView } from "@/components/HomeView";

export const metadata: Metadata = {
  title: "Hendro Kuswantoro",
  description:
    "I make maps and map apps in Yogyakarta. Location data turned into something you can open, read and use.",
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return <HomeView />;
}
