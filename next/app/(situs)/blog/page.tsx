import type { Metadata } from "next";
import { BlogIndexView } from "@/components/BlogIndexView";

export const metadata: Metadata = {
  title: "Blog",
  description: "Short notes about maps, data and how to read them.",
  alternates: { canonical: "/blog/" },
};

export default function BlogPage() {
  return <BlogIndexView />;
}
