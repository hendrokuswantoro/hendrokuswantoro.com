"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { HOME, type Tile } from "@/content/home";
import { COMMON } from "@/content/nav";
import { PROJECTS } from "@/content/projects";
import { useLang } from "./LanguageProvider";
import { HeroCard } from "./HeroCard";
import { ProjectCard } from "./ProjectCard";
import { ChartIcon, DatabaseIcon, GlobeIcon, MapIcon, SatelliteIcon, SurveyIcon } from "./Icons";

const TOOLS = ["PostGIS", "Python", "QGIS", "MapLibre", "FastAPI", "GDAL", "GeoPandas", "Rasterio", "PostgreSQL", "Docker", "Xarray", "GeoServer"];

const TILE_ICONS: Record<Tile["icon"], ReactNode> = {
  globe: <GlobeIcon />,
  chart: <ChartIcon />,
  satellite: <SatelliteIcon />,
  map: <MapIcon />,
  database: <DatabaseIcon />,
  survey: <SurveyIcon />,
};

export function HomeView() {
  const { say } = useLang();
  const featured = PROJECTS.filter((project) => project.featured);

  return (
    <main id="main">
      <section className="hero">
        <div className="wrap">
          <div className="hero__grid">
            <div>
              <span className="eyebrow">{say(HOME.eyebrow)}</span>
              <h1>{say(HOME.title)}</h1>

              <div className="hero__actions">
                <Link className="btn btn--primary" href="/project/">
                  {say(HOME.seeWork)}
                </Link>
                <Link className="btn btn--ghost" href="/blog/">
                  {say(COMMON.readBlog)}
                </Link>
              </div>

            </div>

            <HeroCard />
          </div>
        </div>
      </section>


      {/* decorative, every name appears elsewhere as a real tag */}
      <div className="pita-alat" aria-hidden="true">
        <div className="pita-alat__jalur">
          {[...TOOLS, ...TOOLS].map((tool, index) => (
            <span key={`${tool}-${index}`}>{tool}</span>
          ))}
        </div>
      </div>

      <section className="section section--surface">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(HOME.doEyebrow)}</span>
            <h2>{say(HOME.doTitle)}</h2>
          </div>

          <ul className="tiles reveal">
            {HOME.tiles.map((tile) => (
              <li key={tile.icon}>
                <Link className="tile" href="/project/">
                  <span className="tile__icon">{TILE_ICONS[tile.icon]}</span>
                  <span className="tile__label">{say(tile.label)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(HOME.workEyebrow)}</span>
            <h2>{say(HOME.workTitle)}</h2>
          </div>

          <div className="grid">
            {featured.map((project, index) => (
              <ProjectCard key={project.id} project={project} priority={index === 0} />
            ))}
          </div>

          <p className="mt-32">
            <Link className="btn btn--ghost" href="/project/">
              {say(HOME.seeAll)}
            </Link>
          </p>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(HOME.mapEyebrow)}</span>
            <h2>{say(HOME.mapTitle)}</h2>
            <p>{say(HOME.mapBody)}</p>
          </div>
          <p>
            <Link className="btn btn--primary" href="/project/">
              {say(HOME.mapOpen)}
            </Link>
          </p>
        </div>
      </section>

      <section className="section section--surface">
        <div className="wrap">
          <div className="section-head">
            <span className="eyebrow">{say(HOME.howEyebrow)}</span>
            <h2>{say(HOME.howTitle)}</h2>
          </div>

          <div className="grid reveal">
            {HOME.steps.map((step) => (
              <article className="card" key={step.number}>
                <div className="card__body">
                  <span className="stat__num">{step.number}</span>
                  <h3>{say(step.title)}</h3>
                  <p>{say(step.body)}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="panel reveal">
            <h2>{say(HOME.ctaTitle)}</h2>
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
