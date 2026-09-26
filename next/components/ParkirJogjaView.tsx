"use client";

import Link from "next/link";
import { PARKIR } from "@/content/parkir-jogja";
import { useLang } from "./LanguageProvider";

export function ParkirJogjaView() {
  const { say } = useLang();

  return (
    <main id="main">
      <section className="section">
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
            </header>

            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="article__gambar"
              src={PARKIR.image}
              srcSet="/assets/img/work/parking-400.webp?v=52d7f76f31 400w, /assets/img/work/parking-600.webp?v=6232295625 600w, /assets/img/work/parking.webp?v=8e000f92a9 800w"
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

            {PARKIR.bagian.map((bagian) => (
              <section key={bagian.h2.en}>
                <h2>{say(bagian.h2)}</h2>
                {bagian.p.map((teks) => (
                  <p key={teks.en}>{say(teks)}</p>
                ))}
              </section>
            ))}
          </article>
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
