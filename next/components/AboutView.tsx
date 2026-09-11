"use client";

import Link from "next/link";
import { ABOUT } from "@/content/about";
import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

export function AboutView() {
  const { say } = useLang();

  return (
    <main id="main">
      <section className="hero">
        <div className="wrap">
          <div className="hero__grid" style={{ gridTemplateColumns: "1fr", paddingBottom: 0 }}>
            <div>
              <span className="eyebrow">{say(ABOUT.eyebrow)}</span>
              <h1>{ABOUT.title}</h1>
              <p className="hero__lede">{say(ABOUT.lede)}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(ABOUT.skillsEyebrow)}</span>
            <h2>{say(ABOUT.skillsTitle)}</h2>
          </div>

          <div className="grid reveal">
            {ABOUT.skills.map((skill) => (
              <article className="card" key={skill.title.en}>
                <div className="card__body">
                  <h3>{say(skill.title)}</h3>
                  <p>{say(skill.body)}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section--surface">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(ABOUT.toolsEyebrow)}</span>
            <h2>{say(ABOUT.toolsTitle)}</h2>
          </div>

          <div className="grid reveal">
            {ABOUT.tools.map((group) => (
              <article className="card" key={group.title.en}>
                <div className="card__body">
                  <h3>{say(group.title)}</h3>
                  <ul className="tags">
                    {group.items.map((item) => (
                      <li className="tag" key={item}>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="panel reveal">
            <h2>{say(ABOUT.ctaTitle)}</h2>
            <div className="panel__actions">
              <Link className="btn btn--onbrand" href="/project/">
                {say(COMMON.seeProjects)}
              </Link>
              <Link className="btn btn--outline-light" href="/blog/">
                {say(COMMON.readBlog)}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
