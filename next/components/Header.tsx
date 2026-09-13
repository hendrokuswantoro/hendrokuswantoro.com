"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { COMMON, NAV } from "@/content/nav";
import { useLang } from "./LanguageProvider";
import { LanguageSwitch } from "./LanguageSwitch";
import { ThemeSwitch } from "./ThemeSwitch";
import { BrandMark } from "./Icons";

function isCurrent(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

export function Header() {
  const { say } = useLang();
  const pathname = usePathname();
  const [stuck, setStuck] = useState(false);

  useEffect(() => {
    const onScroll = () => setStuck(window.scrollY > 4);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <a className="skip-link" href="#main">
        {say(COMMON.skip)}
      </a>

      <header className={stuck ? "header is-stuck" : "header"}>
        <div className="wrap">
          <Link className="brand" href="/" aria-label={say(COMMON.brandAria)}>
            <BrandMark />
            <span className="brand__name">
              hendro<span>kuswantoro</span>
            </span>
          </Link>

          <nav className="nav" aria-label={say(COMMON.mainNav)}>
            <ul className="nav__list">
              {NAV.map((item) => (
                <li key={item.href}>
                  <Link
                    className="nav__link"
                    href={item.href}
                    aria-current={isCurrent(pathname, item.href) ? "page" : undefined}
                  >
                    {say(item.label)}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="header__actions">
            <LanguageSwitch />
            <ThemeSwitch />
          </div>
        </div>
      </header>
    </>
  );
}
