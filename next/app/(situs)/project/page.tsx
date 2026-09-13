import type { Metadata } from "next";
import { ProjectView } from "@/components/ProjectView";

export const metadata: Metadata = {
  title: "Project",
  description: "Six map projects: map apps, map analysis, satellite data and print maps.",
  alternates: { canonical: "/project/" },
};

export default function ProjectPage() {
  return <ProjectView />;
}
