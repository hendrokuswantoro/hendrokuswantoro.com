"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { PARKIR } from "@/content/parkir-jogja";
import { gulirKe, slug } from "./gulir";
import { useLang } from "./LanguageProvider";
import { ParkirMap } from "./ParkirMap";

export function ParkirJogjaView() {
  const { say } = useLang();
  const [now, setNow] = useState<string>("");

  const heads = useMemo(() => {
    const taken = new Set<string>();
    return PARKIR.bagian.map((bagian) => {
      let id = slug(bagian.h2.en);
      while (taken.has(id)) id += "-2";
      taken.add(id);
      return { id, text: bagian.h2 };
    });
  }, []);

  useEffect(() => {
    let frame = 0;

    function draw() {
      frame = 0;
      const edge = window.innerHeight * 0.3;
      let seen = heads[0]?.id ?? "";
      heads.forEach((head) => {
        const node = document.getElementById(head.id);
        if (node && node.getBoundingClientRect().top <= edge) seen = head.id;
      });
      setNow(seen);
    }

    function onScroll() {
      if (frame) return;
      frame = window.requestAnimationFrame(draw);
    }

    draw();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [heads]);

  return (
    <main id="main">
      <div className="section">
        <div className="wrap">
          <article className="article">
            <Link className="back-link" href="/project/">
              {say(PARKIR.back)}
            </Link>

            <header className="article__head">
              <p className="post__meta">
                <span className="tag">{say(PARKIR.badge)}</span>
                {PARKIR.tags.map((tag) => (
                  <span className="tag" key={tag}>
                    {tag}
                  </span>
                ))}
              </p>
              <h1>{say(PARKIR.title)}</h1>
              <p>{say(PARKIR.lede)}</p>
              <div className="hero__actions">
                <a className="btn btn--primary" href="#coba" onClick={(event) => gulirKe(event, "coba")}>
                  {say(PARKIR.coba.tombol)}
                </a>
              </div>
            </header>

            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="article__gambar"
              src={PARKIR.image}
              srcSet="/assets/img/work/parking-400.webp?v=8c0a75ce2b 400w, /assets/img/work/parking-600.webp?v=d514756973 600w, /assets/img/work/parking.webp?v=12dc5e71f9 800w"
              sizes="(min-width: 1080px) 840px, 92vw"
              alt={say(PARKIR.alt)}
              width={800}
              height={450}
              loading="lazy"
              decoding="async"
            />

            <div className="stats" id="angka-parkir">
              {PARKIR.angka.map((angka) => (
                <div className="stat" key={angka.num.en}>
                  <span className="stat__num">{say(angka.num)}</span>
                  <span className="stat__label">{say(angka.label)}</span>
                </div>
              ))}
            </div>

            {PARKIR.bagian.map((bagian, indeks) => (
              <section key={bagian.h2.en}>
                <h2 id={heads[indeks].id}>{say(bagian.h2)}</h2>
                {bagian.p.map((teks) => (
                  <p key={teks.en}>{say(teks)}</p>
                ))}
              </section>
            ))}

            <aside className="rail" aria-label={say(PARKIR.rail.daftar)}>
              <nav className="rail__daftar">
                <p className="rail__title">{say(PARKIR.rail.daftar)}</p>
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
              <div className="rail__ajak">
                <p className="rail__title">{say(PARKIR.rail.judul)}</p>
                <p>{say(PARKIR.rail.isi)}</p>
                <a className="btn btn--primary" href="#coba" onClick={(event) => gulirKe(event, "coba")}>
                  {say(PARKIR.rail.tombol)}
                </a>
              </div>
              <div>
                <p className="rail__title">{say(PARKIR.rail.bacaJuga)}</p>
                <div className="rail__lain">
                  <Link href="/blog/kapan-peta-diam/">{say(PARKIR.rail.tulisan)}</Link>
                  <Link href="/project/">{say(PARKIR.rail.semua)}</Link>
                </div>
              </div>
            </aside>
          </article>
        </div>
      </div>

      <section className="section section--surface" id="coba">
        <div className="wrap">
          <div className="peta__intro peta__intro--satu">
            <span className="eyebrow">{say(PARKIR.coba.eyebrow)}</span>
            <h2>{say(PARKIR.coba.h2)}</h2>
            {PARKIR.coba.intro.map((teks) => (
              <p key={teks.en}>{say(teks)}</p>
            ))}
          </div>
          <ParkirMap />
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="panel reveal">
            <h2>{say(PARKIR.ajakTitle)}</h2>
            <p>{say(PARKIR.ajakBody)}</p>
            <div className="panel__actions">
              <Link className="btn btn--onbrand" href="/project/">
                {say(PARKIR.ajakProyek)}
              </Link>
              <Link className="btn btn--outline-light" href="/blog/">
                {say(PARKIR.ajakBlog)}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
