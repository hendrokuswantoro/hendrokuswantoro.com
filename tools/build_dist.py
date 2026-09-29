import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist-hendrokuswantoro.zip"

FILES = [
    "index.html",
    "about.html",
    "project.html",
    "parkir-jogja.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "feed.xml",
    "site.webmanifest",
    "_headers",
    "CNAME",
    ".well-known/security.txt",
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
        unggahan = ROOT / "content" / "unggahan"
        if unggahan.is_dir():
            for path in sorted(unggahan.iterdir()):
                if path.is_file() and not path.name.startswith("."):
                    bundle.write(path, f"unggahan/{path.name}")

    with zipfile.ZipFile(OUT) as bundle:
        count = len(bundle.namelist())
    print(f"wrote {OUT.name}: {count} files, {round(OUT.stat().st_size / 1024)} KB")


if __name__ == "__main__":
    main()
