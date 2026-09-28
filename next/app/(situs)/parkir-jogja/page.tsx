import type { Metadata } from "next";
import { ParkirJogjaView } from "@/components/ParkirJogjaView";

export const metadata: Metadata = {
  title: "Yogyakarta Parking Map",
  description:
    "A case study: a Yogyakarta parking map that shows the zone and fee for any street, and knows when to stay quiet.",
  alternates: { canonical: "/parkir-jogja/" },
  openGraph: {
    type: "article",
    title: "Yogyakarta Parking Map, a case study",
    description: "A Yogyakarta parking map that shows the zone and fee for any street, and knows when to stay quiet.",
  },
};

export default function ParkirJogjaPage() {
  return <ParkirJogjaView />;
}
