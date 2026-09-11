import type { NextConfig } from "next";

/**
 * The site has no server side behaviour, so it is exported as plain files.
 * `next build` writes them to `out/`, which is what Cloudflare Pages serves.
 *
 * `trailingSlash` keeps the exported URLs as folders (/about/ rather than
 * /about.html), so every route resolves to its own index.html on any host.
 */
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
