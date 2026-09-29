import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

const aturan = [
  { ignores: [".next/**", "out/**", "node_modules/**", "next-env.d.ts", "public/assets/vendor/**"] },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];

export default aturan;
