"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { COMMON, NAV } from "@/content/nav";
import { BrandMark } from "./Icons";
import { useLang } from "./LanguageProvider";

const BUILD_YEAR = 2026;

export function Footer() {
  const { say } = useLang();
  const [year, setYear] = useState(BUILD_YEAR);

  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  return (
    <footer className="footer">
      <div className="wrap">
        <div className="footer__atas">
          <div className="footer__merek">
            <Link className="brand" href="/" aria-label={say(COMMON.brandAria)}>
              <BrandMark size={40} />
              <span className="brand__name">
                hendro<span>kuswantoro</span>
              </span>
            </Link>
            <p>{say(COMMON.footerTagline)}</p>
          </div>
          <nav className="footer__nav" aria-label={say(COMMON.footerNav)}>
            {NAV.map((item) => (
              <Link key={item.href} href={item.href}>
                {say(item.label)}
              </Link>
            ))}
            <a href="/feed.xml">RSS</a>
          </nav>
        </div>
        <div className="footer__bottom">
          <p>
            &copy; {year} {say(COMMON.rights)}
          </p>
          <a className="footer__naik" href="#main">
            {say(COMMON.backToTop)}
          </a>
        </div>
      </div>
    </footer>
  );
}
