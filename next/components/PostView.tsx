"use client";

import Link from "next/link";
import type { Post } from "@/content/posts";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

export function PostView({ post }: { post: Post }) {
  const { say } = useLang();

  return (
    <main id="main">
      <section className="section">
        <div className="wrap">
          <article className="article">
            <Link className="back-link" href="/blog/">
              {say(COMMON.backToBlog)}
            </Link>

            <header className="article__head">
              <p className="post__meta">
                <span className="tag">{say(post.tag)}</span>
                <time dateTime={post.date}>{say(post.dateLabel)}</time>
                <span>{say(post.readTime)}</span>
              </p>
              <h1>{say(post.title)}</h1>
              <p>{say(post.lede)}</p>
            </header>

            {post.blocks.map((block, index) => {
              const key = `${block.kind}-${index}`;
              if (block.kind === "h2") return <h2 key={key}>{say(block.text)}</h2>;
              if (block.kind === "quote") {
                return (
                  <blockquote key={key}>
                    <p>{say(block.text)}</p>
                  </blockquote>
                );
              }
              return <p key={key}>{say(block.text)}</p>;
            })}

            <p className="mt-32">
              <Link className="btn btn--ghost" href="/blog/">
                {say(COMMON.otherPosts)}
              </Link>
            </p>
          </article>
        </div>
      </section>
    </main>
  );
}
