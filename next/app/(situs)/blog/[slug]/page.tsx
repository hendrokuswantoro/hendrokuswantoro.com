import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { POSTS, postBySlug } from "@/content/posts";
import { SITE } from "@/content/nav";
import { PostView } from "@/components/PostView";

type Params = { slug: string };

export function generateStaticParams(): Params[] {
  return POSTS.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = postBySlug(slug);
  if (!post) return {};

  return {
    title: post.title.en,
    description: post.excerpt.en,
    alternates: { canonical: `/blog/${post.slug}/` },
    openGraph: {
      type: "article",
      title: post.title.en,
      description: post.excerpt.en,
      publishedTime: post.date,
      url: `${SITE.url}/blog/${post.slug}/`,
    },
  };
}

export default async function PostPage({ params }: { params: Promise<Params> }) {
  const { slug } = await params;
  const post = postBySlug(slug);
  if (!post) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title.en,
    datePublished: post.date,
    author: { "@type": "Person", name: SITE.name, url: SITE.url },
    mainEntityOfPage: `${SITE.url}/blog/${post.slug}/`,
    image: `${SITE.url}/assets/img/og-cover.png`,
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <PostView post={post} />
    </>
  );
}
