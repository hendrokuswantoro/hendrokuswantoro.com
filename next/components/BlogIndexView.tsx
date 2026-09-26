"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { BLOG, POSTS } from "@/content/posts";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

function Langganan() {
  const { say } = useLang();
  const isian = useRef<HTMLInputElement>(null);
  const [alamat, setAlamat] = useState("/feed.xml");
  const [kabar, setKabar] = useState<"ok" | "gagal" | null>(null);

  useEffect(() => {
    setAlamat(new URL("/feed.xml", window.location.href).href);
  }, []);

  const pilihSendiri = () => {
    isian.current?.focus();
    isian.current?.select();
    setKabar("gagal");
  };

  const salin = () => {
    if (!navigator.clipboard?.writeText) {
      pilihSendiri();
      return;
    }
    navigator.clipboard.writeText(alamat).then(() => setKabar("ok"), pilihSendiri);
  };

  return (
    <div className="langganan reveal" id="rss">
      <div className="langganan__teks">
        <h2>
          <svg className="langganan__ikon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d="M5 17a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM3 10.5a10.5 10.5 0 0 1 10.5 10.5h-3A7.5 7.5 0 0 0 3 13.5zM3 4a17 17 0 0 1 17 17h-3A14 14 0 0 0 3 7z" />
          </svg>
          <span>{say(BLOG.rssTitle)}</span>
        </h2>
        <p>{say(BLOG.rssText)}</p>
      </div>
      <div className="langganan__alamat">
        <input
          ref={isian}
          className="langganan__isian"
          type="text"
          value={alamat}
          readOnly
          spellCheck={false}
          aria-label={say(BLOG.rssLabel)}
          onFocus={(e) => e.currentTarget.select()}
        />
        <button className="btn btn--primary" type="button" onClick={salin}>
          {say(BLOG.rssCopy)}
        </button>
        <p className="langganan__kabar" role="status">
          {kabar === "ok" ? say(BLOG.rssOk) : kabar === "gagal" ? say(BLOG.rssFail) : ""}
        </p>
      </div>
    </div>
  );
}

export function BlogIndexView() {
  const { say } = useLang();

  return (
    <main id="main">
      <section className="hero">
        <div className="wrap">
          <div className="hero__grid hero__grid--solo">
            <div>
              <span className="eyebrow">{say(BLOG.eyebrow)}</span>
              <h1>{say(BLOG.title)}</h1>
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
                <h2>{say(post.title)}</h2>
                <p>{say(post.excerpt)}</p>
                <span className="post__more">{say(COMMON.readMore)}</span>
              </Link>
            ))}
          </div>
          <Langganan />
        </div>
      </section>
    </main>
  );
}
