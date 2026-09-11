"use client";

import type { Project } from "@/content/projects";
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
    <article className="card reveal">
      <div className="card__cover">
        {/* plain img on purpose: the export is static and the files are already
            sized and compressed by tools/build_work_images.py */}
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
        <h3>{say(project.title)}</h3>
        <p>{say(project.body)}</p>
        <ul className="tags">
          {project.tags.map((tag) => (
            <li className="tag" key={tag}>
              {tag}
            </li>
          ))}
        </ul>
        {withMeta ? <p className="card__meta">{say(project.meta)}</p> : null}
      </div>
    </article>
  );
}
