"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { POSTS, type Post } from "@/content/posts";
import { COMMON } from "@/content/nav";
import { gulirKe, slug } from "./gulir";
import { useLang } from "./LanguageProvider";

export function PostView({ post }: { post: Post }) {
  const { say } = useLang();
  const bar = useRef<HTMLDivElement>(null);
  const article = useRef<HTMLElement | null>(null);
  const [now, setNow] = useState<string>("");

  const heads = useMemo(() => {
    const taken = new Set<string>();
    return post.blocks
      .filter((block) => block.kind === "h2")
      .map((block) => {
        let id = slug(block.text.en);
        while (taken.has(id)) id += "-2";
        taken.add(id);
        return { id, text: block.text };
      });
  }, [post]);

  const others = POSTS.filter((other) => other.slug !== post.slug);
  const ids = useMemo(() => heads.map((head) => head.id), [heads]);

  useEffect(() => {
    let frame = 0;

    function draw() {
      frame = 0;
      if (!bar.current || !article.current) return;
      const box = article.current.getBoundingClientRect();
      const span = box.height - window.innerHeight;
      if (span <= 0) {
        bar.current.style.transform = "scaleX(1)";
      } else {
        const done = Math.min(1, Math.max(0, -box.top / span));
        bar.current.style.transform = `scaleX(${done})`;
      }

      const edge = window.innerHeight * 0.3;
      let seen = ids[0] ?? "";
      ids.forEach((id) => {
        const head = document.getElementById(id);
        if (head && head.getBoundingClientRect().top <= edge) seen = id;
      });
      setNow(seen);
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
  }, [ids]);

  let seenHeads = 0;

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
              if (block.kind === "h2") {
                const head = heads[seenHeads];
                seenHeads += 1;
                return (
                  <h2 key={key} id={head.id}>
                    {say(block.text)}
                  </h2>
                );
              }
              if (block.kind === "quote") {
                return (
                  <blockquote key={key}>
                    <p>{say(block.text)}</p>
                  </blockquote>
                );
              }
              if (block.kind === "ul" || block.kind === "ol") {
                const Daftar = block.kind;
                return (
                  <Daftar key={key} className="tulisan__daftar">
                    {block.items.map((butir, nomor) => (
                      <li key={`${key}-${nomor}`}>{say(butir)}</li>
                    ))}
                  </Daftar>
                );
              }
              if (block.kind === "gambar") {
                return (
                  <figure key={key} className="tulisan__media">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={block.src}
                      alt={say(block.text)}
                      width={block.width}
                      height={block.height}
                      loading="lazy"
                      decoding="async"
                    />
                    {block.text.en ? <figcaption>{say(block.text)}</figcaption> : null}
                  </figure>
                );
              }
              if (block.kind === "video") {
                return (
                  <figure key={key} className="tulisan__media">
                    <video src={block.src} controls preload="metadata" playsInline />
                    {block.text.en ? <figcaption>{say(block.text)}</figcaption> : null}
                  </figure>
                );
              }
              return <p key={key}>{say(block.text)}</p>;
            })}

            <p className="mt-32">
              <Link className="btn btn--ghost" href="/blog/">
                {say(COMMON.otherPosts)}
              </Link>
            </p>

            <aside className="rail" aria-label={say(COMMON.onThisPage)}>
              {heads.length > 1 ? (
                <nav className="rail__daftar">
                  <p className="rail__title">{say(COMMON.onThisPage)}</p>
                  <ol>
                    {heads.map((head) => (
                      <li key={head.id}>
                        <a
                          className={head.id === now ? "is-now" : undefined}
                          href={`#${head.id}`}
                          onClick={(event) => gulirKe(event, head.id)}
                        >
                          {say(head.text)}
                        </a>
                      </li>
                    ))}
                  </ol>
                </nav>
              ) : null}
              <div>
                <p className="rail__title">{say(COMMON.morePosts)}</p>
                <div className="rail__lain">
                  {others.map((other) => (
                    <Link href={`/blog/${other.slug}/`} key={other.slug}>
                      {say(other.title)}
                    </Link>
                  ))}
                </div>
              </div>
            </aside>
          </article>
        </div>
      </section>
    </main>
  );
}
