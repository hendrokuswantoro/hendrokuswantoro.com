"use client";

import Link from "next/link";
import { BLOG, POSTS } from "@/content/posts";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

export function BlogIndexView() {
  const { say } = useLang();

  return (
    <main id="main">
      <section className="hero">
        <div className="wrap">
          <div className="hero__grid" style={{ gridTemplateColumns: "1fr", paddingBottom: 0 }}>
            <div>
              <span className="eyebrow">{say(BLOG.eyebrow)}</span>
              <h1>{say(BLOG.title)}</h1>
              <p className="hero__lede">{say(BLOG.lede)}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="post-list reveal">
            {POSTS.map((post) => (
              <Link className="post" href={`/blog/${post.slug}/`} key={post.slug}>
                <span className="post__meta">
                  <span className="tag">{say(post.tag)}</span>
                  <time dateTime={post.date}>{say(post.dateLabel)}</time>
                  <span>{say(post.readTime)}</span>
                </span>
                <h3>{say(post.title)}</h3>
                <p>{say(post.excerpt)}</p>
                <span className="post__more">{say(COMMON.readMore)}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
