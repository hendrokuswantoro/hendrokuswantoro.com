import type { MouseEvent } from "react";

export function slug(text: string): string {
  return (
    text
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 60) || "bagian"
  );
}

export function gulirKe(event: MouseEvent<HTMLAnchorElement>, id: string) {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const tujuan = document.getElementById(id);
  if (!tujuan) return;
  event.preventDefault();
  const kurangi = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  tujuan.scrollIntoView({ behavior: kurangi ? "auto" : "smooth", block: "start" });
}
