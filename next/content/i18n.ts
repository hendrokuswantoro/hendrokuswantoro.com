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
