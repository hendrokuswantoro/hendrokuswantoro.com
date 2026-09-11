"""Generate the PWA and Apple touch icons from the brand mark.

Run from the project root:
    python tools/build_icons.py

Outputs assets/img/icon-192.png, icon-512.png and apple-touch-icon.png.
The SVG favicon stays the source of truth for browsers that support it.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

INK = (0, 0, 0)
ACCENT = (39, 110, 241)
WHITE = (255, 255, 255)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "img"
BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")

SIZES = {"icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180}


def load(size):
    try:
        return ImageFont.truetype(str(BOLD), size)
    except OSError:
        return ImageFont.load_default(size)


def build(size, radius_ratio=0.24):
    scale = 4
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * radius_ratio), fill=INK)
    draw.text((big * 0.5, big * 0.53), "H", font=load(int(big * 0.56)), fill=WHITE, anchor="mm")
    r = big * 0.075
    cx, cy = big * 0.78, big * 0.24
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    return img.resize((size, size), Image.LANCZOS)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, size in SIZES.items():
        icon = build(size)
        target = OUT_DIR / name
        icon.convert("RGB").save(target, "PNG", optimize=True) if name.startswith("apple") else icon.save(target, "PNG", optimize=True)
        print("wrote", target, icon.size)


if __name__ == "__main__":
    main()
