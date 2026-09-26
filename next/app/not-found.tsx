import Link from "next/link";
import type { Metadata } from "next";
import { KerangkaSitus } from "@/components/KerangkaSitus";

export const metadata: Metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <KerangkaSitus>
      <main id="main">
      <section className="section">
        <div className="wrap wrap--narrow center">
          <span className="eyebrow">Error 404</span>
          <h1>This point is off the map.</h1>
          <p>The page you were looking for is not here. The link may have changed, or the address has a typo.</p>
          <div className="hero__actions hero__actions--tengah">
            <Link className="btn btn--primary" href="/">
              Go home
            </Link>
            <Link className="btn btn--ghost" href="/project/">
              See my work
            </Link>
          </div>
        </div>
        </section>
      </main>
    </KerangkaSitus>
  );
}
