"""Bundle the files that should actually be served into one zip.

    python tools/build_dist.py

The result, dist-hendrokuswantoro.zip, is what you drag into the Cloudflare
Pages "Upload assets" box. It leaves out the README, the tools folder, the
git metadata and the Next.js port, since none of those belong on a web
server.
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist-hendrokuswantoro.zip"

FILES = [
    "index.html",
    "about.html",
    "project.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "feed.xml",
    "site.webmanifest",
    "_headers",
    "CNAME",
]

DIRS = ["assets", "blog"]


def main() -> None:
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in FILES:
            bundle.write(ROOT / name, name)
        for folder in DIRS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file():
                    bundle.write(path, path.relative_to(ROOT).as_posix())

    with zipfile.ZipFile(OUT) as bundle:
        count = len(bundle.namelist())
    print(f"wrote {OUT.name}: {count} files, {round(OUT.stat().st_size / 1024)} KB")


if __name__ == "__main__":
    main()
