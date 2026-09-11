"""Turn the full size portfolio maps into card images for the website.

    python tools/build_work_images.py

The originals live outside this repository, in D:/Projects/Portfolio Kerja,
and run from 0.4 MB to 4.7 MB each, far too heavy for a browser. This script
fits each one inside a 16 by 9 frame, keeping the whole sheet visible, and
writes a WebP around 60 KB.

Nothing is cropped. A map sheet with its legend cut off is a different
document, so the frame is padded instead.
"""

from pathlib import Path
from PIL import Image

SOURCE = Path("D:/Projects/Portfolio Kerja")
OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "work"

WIDTH, HEIGHT = 800, 450
BACKGROUND = (229, 232, 234)  # --line, so the sheet edge stays visible
QUALITY = 82

WORK = {
    "parking": "sistem parkir yogyakarta/Aapppublik.png",
    "fire": "fig2_progression_2026_light.png",
    "fish": "Fish Landing Suitability Natuna.png",
    "reach": "Map_1_Service_Accessibility_Biak_Numfor.jpg",
    "landcover": "Peta_Tutupan_Lahan_Yogyakarta_HK.png",
    "mimika": "PTP-L-01Y-mimika.png",
    "pickup": "map_sheet_pickup_points.png",
}


def build(name: str, relative: str) -> None:
    source = SOURCE / relative
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        canvas.paste(image, ((WIDTH - image.width) // 2, (HEIGHT - image.height) // 2))

    target = OUT / f"{name}.webp"
    canvas.save(target, "WEBP", quality=QUALITY, method=6)
    print(f"{target.name:16} {target.stat().st_size / 1024:6.1f} KB  from {source.name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, relative in WORK.items():
        build(name, relative)


if __name__ == "__main__":
    main()
