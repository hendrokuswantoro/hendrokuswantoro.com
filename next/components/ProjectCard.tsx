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
          /* Jalan pulang dari kartu ke peta, kebalikan dari tautan di dalam
             popup penanda. href-nya betulan alamat yang bisa disalin, bukan
             "#": yang tersalin dari bilah alamat sesudah ini membuka peta di
             titik yang sama. */
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
                  /* Gulirnya menyusul satu bingkai kemudian, dan urutannya
                     penting. Popup MapLibre memindahkan fokus ke dalam dirinya
                     begitu terbuka, focusAfterOpen, dan pemindahan fokus itu
                     ikut menggulir halaman. Kalau gulir kita berangkat lebih
                     dulu, ia kalah: terukur berhenti 196 piksel dari tempat
                     yang dimaksud. */
                  window.requestAnimationFrame(gulirKePeta);
                } else {
                  /* petanya baru dimuat, belum ada popup yang berebut gulir.
                     Alamatnya ditulis sekarang, dan WorkMap membacanya sendiri
                     begitu selesai. Bukan lewat location.hash: #peta-<id>
                     tidak menunjuk elemen mana pun, dan peramban menjawab
                     fragmen yang tidak ditemukan dengan menggulir ke awal
                     dokumen. */
                  gulirKePeta();
                  try {
                    window.history.replaceState(null, "", `#peta-${project.id}`);
                  } catch {
                    /* alamat file:// */
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
