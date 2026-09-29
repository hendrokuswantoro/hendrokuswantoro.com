import shutil
from pathlib import Path
from PIL import Image

SOURCE = Path("D:/Projects/Portfolio Kerja")
OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "work"
OUT_NEXT = Path(__file__).resolve().parent.parent / "next" / "public" / "assets" / "img" / "work"

WIDTH, HEIGHT = 800, 450
WIDTHS = (400, 600, 800)
BACKGROUND = (229, 232, 234)
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
    salinan = sorted(OUT_NEXT.glob("*.webp"))
    for berkas in salinan:
        shutil.copyfile(OUT / berkas.name, berkas)
    print(f"{len(salinan)} salinan diperbarui di {OUT_NEXT.relative_to(OUT.parents[2])}")
    print(f"\n{len(WORK)} karya x {len(WIDTHS)} lebar = "
          f"{len(WORK) * len(WIDTHS)} berkas, {total / 1024:.0f} KB di cakram")


if __name__ == "__main__":
    main()
