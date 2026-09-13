"""Turn the full size portfolio maps into card images for the website.

    python tools/build_work_images.py

The originals live outside this repository, in D:/Projects/Portfolio Kerja,
and run from 0.4 MB to 4.7 MB each, far too heavy for a browser. This script
fits each one inside a 16 by 9 frame, keeping the whole sheet visible, and
writes a WebP around 60 KB.

Nothing is cropped. A map sheet with its legend cut off is a different
document, so the frame is padded instead.

Three widths, not one. The card holds roughly 329 px on the project page and
445 px on the home page, both measured in the browser rather than guessed, so
a single 800 px file is between 1,8 and 2,4 times wider than a screen at
device pixel ratio 1 can show. The extra pixels are thrown away after being
paid for. With 400 and 600 px alongside it, the browser takes 800 only when
the screen really is dense enough to use it, and `sizes` in the markup is
what tells it the slot width before layout exists. The 800 px file keeps its
plain name so `src` still works where `srcset` is not understood.
"""

from pathlib import Path
from PIL import Image

SOURCE = Path("D:/Projects/Portfolio Kerja")
OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "work"

WIDTH, HEIGHT = 800, 450
WIDTHS = (400, 600, 800)
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


def build(name: str, relative: str) -> int:
    source = SOURCE / relative
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        canvas.paste(image, ((WIDTH - image.width) // 2, (HEIGHT - image.height) // 2))

    total = 0
    for width in WIDTHS:
        # The widest one keeps the plain name: it is what src points at.
        akhiran = "" if width == WIDTH else f"-{width}"
        target = OUT / f"{name}{akhiran}.webp"
        frame = canvas if width == WIDTH else canvas.resize(
            (width, round(width * HEIGHT / WIDTH)), Image.LANCZOS
        )
        frame.save(target, "WEBP", quality=QUALITY, method=6)
        kb = target.stat().st_size / 1024
        total += target.stat().st_size
        print(f"  {target.name:22} {width:4}w {kb:6.1f} KB")
    return total


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, relative in WORK.items():
        print(f"{name}  from  {(SOURCE / relative).name}")
        total += build(name, relative)
    print(f"\n{len(WORK)} karya x {len(WIDTHS)} lebar = "
          f"{len(WORK) * len(WIDTHS)} berkas, {total / 1024:.0f} KB di cakram")


if __name__ == "__main__":
    main()
