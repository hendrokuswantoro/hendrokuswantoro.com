/**
 * Two languages, one shape. Every string in `content/` is a { en, id } pair,
 * so a missing translation is a type error rather than a silent fallback.
 */
export type Lang = "en" | "id";

export type Copy = {
  en: string;
  id: string;
};

export const STORAGE_KEY = "hk-lang";

export function t(lang: Lang, copy: Copy): string {
  return copy[lang];
}

export function isLang(value: unknown): value is Lang {
  return value === "en" || value === "id";
}
