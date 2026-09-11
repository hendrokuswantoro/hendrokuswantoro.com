import type { MetadataRoute } from "next";
import { POSTS } from "@/content/posts";
import { SITE } from "@/content/nav";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  const pages = ["/", "/about/", "/project/", "/blog/"].map((path) => ({
    url: `${SITE.url}${path}`,
    changeFrequency: "monthly" as const,
    priority: path === "/" ? 1 : 0.8,
  }));

  const posts = POSTS.map((post) => ({
    url: `${SITE.url}/blog/${post.slug}/`,
    lastModified: new Date(post.date),
    changeFrequency: "yearly" as const,
    priority: 0.7,
  }));

  return [...pages, ...posts];
}
