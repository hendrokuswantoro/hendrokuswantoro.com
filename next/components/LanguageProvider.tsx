"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { isLang, STORAGE_KEY, type Copy, type Lang } from "@/content/i18n";

type LanguageValue = {
  lang: Lang;
  setLang: (next: Lang) => void;
  say: (copy: Copy) => string;
};

const LanguageContext = createContext<LanguageValue>({
  lang: "en",
  setLang: () => undefined,
  say: (copy) => copy.en,
});

/**
 * The exported HTML is English, so English is also the first render. The
 * stored or browser language is applied in an effect, which keeps server and
 * client markup identical and avoids a hydration mismatch.
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = window.localStorage.getItem(STORAGE_KEY);
    } catch {
      stored = null;
    }
    if (isLang(stored)) {
      setLangState(stored);
      return;
    }
    const browser = (navigator.language || "en").toLowerCase();
    if (browser.startsWith("id")) setLangState("id");
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* private mode, the choice simply does not persist */
    }
  }, []);

  const value = useMemo<LanguageValue>(
    () => ({ lang, setLang, say: (copy: Copy) => copy[lang] }),
    [lang, setLang],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLang(): LanguageValue {
  return useContext(LanguageContext);
}
