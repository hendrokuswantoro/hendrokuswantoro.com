import Link from "next/link";
import type { Metadata } from "next";
import { KerangkaSitus } from "@/components/KerangkaSitus";

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  /* Halaman ini duduk di akar, di luar (situs), sebab Next memakainya untuk
     404 seluruh situs. Jadi perabotnya dipasang sendiri di sini. */
  return (
    <KerangkaSitus>
      <main id="main">
      <section className="section">
        <div className="wrap center" style={{ maxWidth: 640 }}>
          <span className="eyebrow">Error 404</span>
          <h1>This point is off the map.</h1>
          <p>The page you were looking for is not here. The link may have changed, or the address has a typo.</p>
          <p className="mt-24">
            <Link className="btn btn--primary" href="/">
              Go home
            </Link>{" "}
            <Link className="btn btn--ghost" href="/project/">
              See my work
            </Link>
          </p>
        </div>
        </section>
      </main>
    </KerangkaSitus>
  );
}
