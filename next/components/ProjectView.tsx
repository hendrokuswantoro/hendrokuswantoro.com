"use client";

import Link from "next/link";
import { useState } from "react";
import { COMMON } from "@/content/nav";
import { FILTERS, PROJECTS, PROJECT_PAGE, type Category } from "@/content/projects";
import { useLang } from "./LanguageProvider";
import { ProjectCard } from "./ProjectCard";
import { WorkMap } from "./WorkMap";

type FilterKey = Category | "all";

export function ProjectView() {
  const { say } = useLang();
  const [active, setActive] = useState<FilterKey>("all");

  const shown = PROJECTS.filter(
    (project) => active === "all" || project.categories.includes(active),
  );

  return (
    <main id="main">
      <section className="hero">
        <div className="wrap">
          <div className="hero__grid" style={{ gridTemplateColumns: "1fr", paddingBottom: 0 }}>
            <div>
              <h1>{say(PROJECT_PAGE.title)}</h1>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="peta__intro">
            <span className="eyebrow">{say(PROJECT_PAGE.mapEyebrow)}</span>
            <h2>{say(PROJECT_PAGE.mapTitle)}</h2>
            <p>{say(PROJECT_PAGE.mapIntro)}</p>
          </div>

          <WorkMap />

          <div className="filters" role="group" aria-label={say(PROJECT_PAGE.filterAria)}>
            {FILTERS.map((filter) => (
              <button
                key={filter.key}
                className="filter"
                type="button"
                aria-pressed={active === filter.key}
                onClick={() => setActive(filter.key)}
              >
                {say(filter.label)}
              </button>
            ))}
          </div>

          <div className="grid">
            {shown.map((project) => (
              <ProjectCard key={project.id} project={project} withMeta />
            ))}
          </div>

          {shown.length === 0 ? <p className="empty">{say(PROJECT_PAGE.empty)}</p> : null}
        </div>
      </section>

      <section className="section section--surface">
        <div className="wrap">
          <div className="panel reveal">
            <h2>{say(PROJECT_PAGE.ctaTitle)}</h2>
            <div className="panel__actions">
              <Link className="btn btn--onbrand" href="/blog/">
                {say(COMMON.readBlog)}
              </Link>
              <Link className="btn btn--outline-light" href="/about/">
                {say(COMMON.aboutMe)}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
