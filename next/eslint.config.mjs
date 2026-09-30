import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const aturan = [
  { ignores: [".next/**", "out/**", "node_modules/**", "next-env.d.ts", "public/assets/vendor/**"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    files: ["app/admin/page.tsx", "components/admin/MasukView.tsx"],
    rules: { "@next/next/no-html-link-for-pages": "off" },
  },
  {
    files: [
      "components/ParkirJogjaView.tsx",
      "components/PostView.tsx",
      "components/ProjectCard.tsx",
      "components/admin/PanelBerkas.tsx",
    ],
    rules: { "@next/next/no-img-element": "off" },
  },
];

export default aturan;
