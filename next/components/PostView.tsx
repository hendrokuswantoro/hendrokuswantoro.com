"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import type { Post } from "@/content/posts";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

export function PostView({ post }: { post: Post }) {
  const { say } = useLang();
  const bar = useRef<HTMLDivElement>(null);
  const article = useRef<HTMLElement | null>(null);

  /* the bar tracks how much of the article has gone past the top of the
     screen, not how far the whole page has scrolled */
  useEffect(() => {
    let frame = 0;

    function draw() {
      frame = 0;
      if (!bar.current || !article.current) return;
      const box = article.current.getBoundingClientRect();
      const span = box.height - window.innerHeight;
      if (span <= 0) {
        bar.current.style.transform = "scaleX(1)";
        return;
      }
      const done = Math.min(1, Math.max(0, -box.top / span));
      bar.current.style.transform = `scaleX(${done})`;
    }

    function onScroll() {
      if (frame) return;
      frame = window.requestAnimationFrame(draw);
    }

    draw();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <main id="main">
      <div className="progres" ref={bar} />
      <section className="section">
        <div className="wrap">
          <article className="article" ref={article}>
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
