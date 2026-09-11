import type { Copy } from "./i18n";

export type NavItem = {
  href: string;
  label: Copy;
};

export const NAV: NavItem[] = [
  { href: "/", label: { en: "Home", id: "Beranda" } },
  { href: "/about/", label: { en: "About", id: "Tentang" } },
  { href: "/project/", label: { en: "Project", id: "Proyek" } },
  { href: "/blog/", label: { en: "Blog", id: "Blog" } },
];

export const SITE = {
  url: "https://www.hendrokuswantoro.com",
  name: "Hendro Kuswantoro",
  role: "Spatial Data and Systems Architect",
  locality: "Yogyakarta",
  country: "ID",
};

export const COMMON = {
  skip: { en: "Skip to content", id: "Lompat ke isi" } as Copy,
  brandAria: { en: "Hendro Kuswantoro, home", id: "Hendro Kuswantoro, beranda" } as Copy,
  mainNav: { en: "Main", id: "Menu utama" } as Copy,
  mobileNav: { en: "Mobile", id: "Menu ponsel" } as Copy,
  language: { en: "Language", id: "Bahasa" } as Copy,
  rights: {
    en: "Hendro Kuswantoro. All rights reserved.",
    id: "Hendro Kuswantoro. Hak cipta dilindungi.",
  } as Copy,
  seeProjects: { en: "See projects", id: "Lihat proyek" } as Copy,
  readBlog: { en: "Read the blog", id: "Baca blog" } as Copy,
  aboutMe: { en: "About me", id: "Tentang saya" } as Copy,
  backToBlog: { en: "Back to the blog", id: "Kembali ke blog" } as Copy,
  otherPosts: { en: "See other posts", id: "Lihat tulisan lain" } as Copy,
  readMore: { en: "Read more", id: "Baca selengkapnya" } as Copy,
};
