"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { COMMON, NAV } from "@/content/nav";
import { useLang } from "./LanguageProvider";
import { DocIcon, GridIcon, HomeIcon, UserIcon } from "./Icons";

const ICONS: Record<string, ReactNode> = {
  "/": <HomeIcon />,
  "/about/": <UserIcon />,
  "/project/": <GridIcon />,
  "/blog/": <DocIcon />,
};

export function TabBar() {
  const { say } = useLang();
  const pathname = usePathname();

  return (
    <nav className="tabbar" aria-label={say(COMMON.mobileNav)}>
      {NAV.map((item) => {
        const current = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            className="tabbar__link"
            href={item.href}
            aria-current={current ? "page" : undefined}
          >
            {ICONS[item.href]}
            <span>{say(item.label)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
