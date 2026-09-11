"use client";

import { COMMON } from "@/content/nav";
import { useLang } from "./LanguageProvider";

export function LanguageSwitch() {
  const { lang, setLang, say } = useLang();

  return (
    <div className="lang" role="group" aria-label={say(COMMON.language)}>
      <button
        className="lang__btn"
        type="button"
        aria-pressed={lang === "en"}
        onClick={() => setLang("en")}
      >
        EN
      </button>
      <button
        className="lang__btn"
        type="button"
        aria-pressed={lang === "id"}
        onClick={() => setLang("id")}
      >
        ID
      </button>
    </div>
  );
}
