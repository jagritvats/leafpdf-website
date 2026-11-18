"""Turn Leaf's marketing screenshots into the website's images.

    python tools/make_images.py [--src PATH_TO_SCREENS] [--sheet]

--src defaults to ../leaf/marketing/out/screens (the app repository checked out next to this one); it holds
dark/ and light/ folders with NN-scene-1920x1080.png files. Each scene below is cropped to the part of the window
that shows the feature, then written to site/img/v1/ as WebP at several widths (for srcset) plus one JPEG
fallback. The folder name is the cache version: the images are served as immutable, so if they change, write
them to a new folder (v2, ...) and update the HTML.

--sheet also writes out/contact-sheet-{dark,light}.png to check the crops by eye.

Needs Pillow with WebP support.
"""
from __future__ import annotations

import argparse
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "site", "img", "v1")

# name -> (source file stem, crop box in 1920x1080 source pixels or None for the whole frame,
#          WebP widths, JPEG fallback width)
SCENES = {
    "hero": ("01-hero-annotate", None, (640, 960, 1280, 1600, 1920), 1280),
    "edit-text": ("03-edit-text", (470, 270, 1770, 1000), (480, 720, 1040, 1300), 720),
    "redact": ("05-redact", (200, 95, 1920, 1045), (480, 720, 1040, 1440), 720),
    "forms": ("02-forms", (968, 104, 1612, 820), (480, 644), 644),
    "signature": ("06-digital-signature", (0, 95, 1920, 960), (480, 720, 1040, 1440), 720),
    "ocr": ("07-ocr", (330, 98, 1530, 800), (480, 720, 1040, 1200), 720),
    "organize": ("04-organize-pages", (0, 95, 1920, 1010), (480, 720, 1040, 1440), 720),
    "focus": ("12-focus-mode", None, (480, 720, 1040, 1440), 720),
    "start": ("11-start-screen", (340, 210, 1580, 920), (480, 720, 1040, 1240), 720),
}
THEMES = ("light", "dark")
WEBP_QUALITY = 78
JPEG_QUALITY = 80


def load(src: str, theme: str, stem: str) -> Image.Image:
    path = os.path.join(src, theme, f"{stem}-1920x1080.png")
    if not os.path.exists(path):
        sys.exit(f"missing {path}")
    return Image.open(path).convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=os.path.join(ROOT, "..", "leaf", "marketing", "out", "screens"))
    ap.add_argument("--sheet", action="store_true", help="also write contact sheets to out/")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    total = 0
    crops: dict[str, list[Image.Image]] = {t: [] for t in THEMES}
    for name, (stem, box, widths, fallback) in SCENES.items():
        for theme in THEMES:
            img = load(args.src, theme, stem)
            if box:
                img = img.crop(box)
            crops[theme].append(img)
            for w in widths:
                h = round(img.height * w / img.width)
                out = img if w == img.width else img.resize((w, h), Image.LANCZOS)
                path = os.path.join(OUT, f"{name}-{theme}-{w}.webp")
                out.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
                total += os.path.getsize(path)
            h = round(img.height * fallback / img.width)
            jpg = img.resize((fallback, h), Image.LANCZOS)
            path = os.path.join(OUT, f"{name}-{theme}-{fallback}.jpg")
            jpg.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
            total += os.path.getsize(path)
        print(f"{name:10} {img.width}x{img.height}  widths {widths}  fallback {fallback}")
    print(f"wrote {total / 1024:.0f} KB to {os.path.relpath(OUT, ROOT)}")

    if args.sheet:
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        for theme, imgs in crops.items():
            thumbs = [i.resize((480, round(i.height * 480 / i.width))) for i in imgs]
            cols = 3
            rows = (len(thumbs) + cols - 1) // cols
            cell_h = max(t.height for t in thumbs) + 10
            sheet = Image.new("RGB", (cols * 490, rows * cell_h), "#888")
            for k, t in enumerate(thumbs):
                sheet.paste(t, ((k % cols) * 490, (k // cols) * cell_h))
            sheet.save(os.path.join(ROOT, "out", f"contact-sheet-{theme}.png"))


if __name__ == "__main__":
    main()
