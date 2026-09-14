import type { Metadata } from "next";
import { ParkirJogjaView } from "@/components/ParkirJogjaView";

export const metadata: Metadata = {
  title: "Yogyakarta Parking Map",
  description:
    "A case study: the parking map that refuses to answer outside the city, and why refusing is part of the design.",
  alternates: { canonical: "/parkir-jogja/" },
  openGraph: {
    type: "article",
    title: "Yogyakarta Parking Map, a case study",
    description: "The parking map that refuses to answer outside the city.",
  },
};

export default function ParkirJogjaPage() {
  return <ParkirJogjaView />;
}
