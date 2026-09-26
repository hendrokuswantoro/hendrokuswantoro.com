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

Every card carries the site's name in its lower right corner, added
26 September 2026. A web page cannot stop a screenshot: the operating system
takes it, outside anything the page can see. What the page can do is make
sure a captured image still says where it came from. The mark is drawn on
the 800 px frame before the smaller widths are cut from it, so all three
carry it at the same place.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SOURCE = Path("D:/Projects/Portfolio Kerja")
OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "work"

WIDTH, HEIGHT = 800, 450
WIDTHS = (400, 600, 800)
BACKGROUND = (229, 232, 234)  # --line, so the sheet edge stays visible
QUALITY = 82

TANDA = "hendrokuswantoro.com"
# The site's own Poppins, read straight from the woff2 the site serves.
# FreeType opens woff2, so no second copy of the font is needed.
HURUF = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "poppins-v24-600-latin.woff2"

WORK = {
    "parking": "sistem parkir yogyakarta/Aapppublik.png",
    "fire": "fig2_progression_2026_light.png",
    "fish": "Fish Landing Suitability Natuna.png",
    "reach": "Map_1_Service_Accessibility_Biak_Numfor.jpg",
    "landcover": "Peta_Tutupan_Lahan_Yogyakarta_HK.png",
    "mimika": "PTP-L-01Y-mimika.png",
    "pickup": "map_sheet_pickup_points.png",
}


def tandai(canvas: Image.Image) -> Image.Image:
    """Draw the site name on a dark pill in the lower right corner.

    Dark with white text, not white alone: the cards hold light map sheets
    and dark app screenshots, and the pill has to read on both. At 400 px the
    text shrinks to about 9 px, still legible, and the pill covers less than
    one percent of the frame, so it never hides a legend.
    """
    huruf = ImageFont.truetype(str(HURUF), 17)
    kiri, atas, kanan, bawah = huruf.getbbox(TANDA)
    lebar, tinggi = kanan - kiri, bawah - atas
    px, py, tepi = 11, 7, 12
    x1, y1 = WIDTH - tepi, HEIGHT - tepi
    x0, y0 = x1 - lebar - 2 * px, y1 - tinggi - 2 * py

    lapis = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gambar = ImageDraw.Draw(lapis)
    gambar.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=(0, 0, 0, 150))
    gambar.text((x0 + px - kiri, y0 + py - atas), TANDA, font=huruf, fill=(255, 255, 255, 235))
    return Image.alpha_composite(canvas.convert("RGBA"), lapis).convert("RGB")


def build(name: str, relative: str) -> int:
    source = SOURCE / relative
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((WIDTH, HEIGHT), Image.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        canvas.paste(image, ((WIDTH - image.width) // 2, (HEIGHT - image.height) // 2))
    canvas = tandai(canvas)

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
