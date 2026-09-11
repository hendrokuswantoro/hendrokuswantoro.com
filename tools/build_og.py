"""Generate the social preview image (Open Graph / Twitter card).

Run from the project root:
    python tools/build_og.py

Output: assets/img/og-cover.png at 1200x630, the size every major platform
crops from. Re-run it whenever the name or tagline changes.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
GREEN_DEEP = (0, 92, 10)
GREEN = (0, 115, 13)
GREEN_LIGHT = (155, 224, 166)
WHITE = (255, 255, 255)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img" / "og-cover.png"

FONT_DIR = Path("C:/Windows/Fonts")
BOLD = FONT_DIR / "segoeuib.ttf"
REGULAR = FONT_DIR / "segoeui.ttf"


def load(path, size):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default(size)


def main():
    img = Image.new("RGB", (W, H), GREEN_DEEP)
    draw = ImageDraw.Draw(img, "RGBA")

    # vertical green wash, dark at the top
    for y in range(H):
        t = y / (H - 1)
        colour = tuple(int(GREEN_DEEP[i] + (GREEN[i] - GREEN_DEEP[i]) * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=colour)

    # map grid
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 18), width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 18), width=1)

    # route line and survey points
    draw.line([(-20, 600), (240, 556), (470, 602), (720, 516), (980, 556), (1220, 492)],
              fill=(0, 170, 19, 255), width=10, joint="curve")
    for cx, cy, r in ((240, 556, 12), (720, 516, 16), (1180, 500, 10)):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN_LIGHT)
    draw.ellipse([720 - 34, 516 - 34, 720 + 34, 516 + 34], outline=(255, 255, 255, 120), width=3)

    # logo mark
    draw.rounded_rectangle([80, 74, 158, 152], radius=24, fill=WHITE)
    draw.text((119, 113), "H", font=load(BOLD, 52), fill=GREEN, anchor="mm")

    draw.text((180, 113), "hendrokuswantoro.com", font=load(REGULAR, 26), fill=(255, 255, 255, 220), anchor="lm")

    draw.text((80, 250), "Hendro Kuswantoro", font=load(BOLD, 84), fill=WHITE)
    draw.text((80, 350), "Geospatial Engineer", font=load(BOLD, 44), fill=GREEN_LIGHT)
    draw.text((80, 420), "Maps, map apps, and satellite data.",
              font=load(REGULAR, 30), fill=(255, 255, 255, 225))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    main()
