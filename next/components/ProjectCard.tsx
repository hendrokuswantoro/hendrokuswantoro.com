"use client";

import type { Project } from "@/content/projects";
import { useLang } from "./LanguageProvider";
import { ProjectCover } from "./ProjectCover";

export function ProjectCard({ project, withMeta = false }: { project: Project; withMeta?: boolean }) {
  const { say } = useLang();

  return (
    <article className="card reveal">
      <div className="card__cover">
        <ProjectCover kind={project.cover} />
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
