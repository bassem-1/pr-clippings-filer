#!/usr/bin/env python3
"""Turn any picture into the Mac app icon (AppIcon.icns), used automatically by build.sh.

    python3 make_icon.py path/to/picture.png|jpg

The picture's plain white/light background is removed, and the artwork is placed on a rounded, softly
pink tile that matches the app. Needs Pillow (pip install pillow) and macOS's iconutil.
"""
import sys, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
TILE = 824            # Apple's icon grid: ~824px tile inside a 1024px canvas
RADIUS = 185
TOP, BOTTOM = (255, 228, 239), (255, 182, 211)   # pink gradient (app theme)


def remove_background(img, tol=28):
    """Flood-fill the light background from the borders and make it transparent."""
    img = img.convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w + 2, h + 2), 0)
    rgb = Image.new("RGB", (w + 2, h + 2), (255, 255, 255))
    rgb.paste(img.convert("RGB"), (1, 1))
    ImageDraw.floodfill(rgb, (0, 0), (255, 0, 255), thresh=tol)       # magenta marks background
    px = rgb.load()
    m = mask.load()
    for y in range(h + 2):
        for x in range(w + 2):
            if px[x, y] == (255, 0, 255):
                m[x, y] = 255
    bg = mask.crop((1, 1, w + 1, h + 1)).filter(ImageFilter.GaussianBlur(1.2))
    alpha = Image.eval(bg, lambda v: 255 - v)
    img.putalpha(alpha)
    return img.crop(img.getbbox())


def build_icon(src: Path, out: Path):
    art = remove_background(Image.open(src))
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    off = (SIZE - TILE) // 2

    # Soft drop shadow + gradient rounded tile.
    shadow = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((off, off + 14, off + TILE, off + TILE + 14), RADIUS, fill=90)
    canvas.paste((80, 20, 50, 255), (0, 0), shadow.filter(ImageFilter.GaussianBlur(18)))
    grad = Image.new("RGBA", (TILE, TILE))
    gd = ImageDraw.Draw(grad)
    for y in range(TILE):
        t = y / (TILE - 1)
        gd.line([(0, y), (TILE, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)) + (255,))
    tile_mask = Image.new("L", (TILE, TILE), 0)
    ImageDraw.Draw(tile_mask).rounded_rectangle((0, 0, TILE - 1, TILE - 1), RADIUS, fill=255)
    canvas.paste(grad, (off, off), tile_mask)

    # Artwork, centred inside the tile with some breathing room.
    box = int(TILE * 0.84)
    scale = box / max(art.size)
    art = art.resize((round(art.width * scale), round(art.height * scale)), Image.LANCZOS)
    canvas.alpha_composite(art, ((SIZE - art.width) // 2, (SIZE - art.height) // 2))

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        for s in (16, 32, 128, 256, 512):
            canvas.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
            canvas.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True)
    canvas.save(out.with_suffix(".png"))   # preview


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(__file__).resolve().parent / "AppIcon.icns"
    build_icon(Path(sys.argv[1]).expanduser(), out)
    print(f"Wrote {out} (preview: {out.with_suffix('.png').name}). Run ./build.sh to apply it.")
