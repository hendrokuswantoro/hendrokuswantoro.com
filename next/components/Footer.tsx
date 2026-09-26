"use client";

import { useEffect, useState } from "react";
import { COMMON } from "@/content/nav";
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
        <div className="footer__bottom">
          <p>
            &copy; {year} {say(COMMON.rights)}
          </p>
        </div>
      </div>
    </footer>
  );
}
