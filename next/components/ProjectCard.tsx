"use client";

import Link from "next/link";

import type { Project } from "@/content/projects";
import { PROJECT_PAGE } from "@/content/projects";
import { useLang } from "./LanguageProvider";

export function ProjectCard({
  project,
  withMeta = false,
  priority = false,
}: {
  project: Project;
  withMeta?: boolean;
  priority?: boolean;
}) {
  const { say } = useLang();

  return (
    <article className="card reveal" id={`karya-${project.id}`}>
      <div className="card__cover">
        {}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={project.image}
          alt={say(project.alt)}
          width={800}
          height={450}
          loading={priority ? "eager" : "lazy"}
          decoding="async"
        />
        <span className="card__badge">{say(project.badge)}</span>
      </div>
      <div className="card__body">
        <h2>{say(project.title)}</h2>
        <p>{say(project.body)}</p>
        <ul className="tags">
          {project.tags.map((tag) => (
            <li className="tag" key={tag}>
              {tag}
            </li>
          ))}
        </ul>
        {withMeta ? <p className="card__meta">{say(project.meta)}</p> : null}
        {withMeta ? (
          <p className="card__aksi">
            {project.studiKasus ? (
              <Link href={project.studiKasus}>{say(PROJECT_PAGE.readCaseStudy)}</Link>
            ) : null}
            <a
              className="card__peta"
              href={`#peta-${project.id}`}
              onClick={(event) => {
                event.preventDefault();
                const gulirKePeta = () => {
                  const halus = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
                  document
                    .querySelector(".peta")
                    ?.scrollIntoView({ behavior: halus ? "smooth" : "auto", block: "start" });
                };
                const peta = (window as unknown as {
                  HK_PETA_STATE?: { buka: (id: string) => boolean };
                }).HK_PETA_STATE;

                if (peta) {
                  peta.buka(project.id);
                  window.requestAnimationFrame(gulirKePeta);
                } else {
                  gulirKePeta();
                  try {
                    window.history.replaceState(null, "", `#peta-${project.id}`);
                  } catch {
                  }
                }
              }}
            >
              {say(PROJECT_PAGE.showOnMap)}
            </a>
          </p>
        ) : null}
      </div>
    </article>
  );
}
