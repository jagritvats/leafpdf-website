"""Print the <picture> markup for one of the scenes in make_images.py, ready to paste into the HTML.

    python tools/picture_html.py edit-text "Alt text" ["sizes"] [--eager]

The dark source carries data-theme-src="dark": site.js rewrites its media query when a visitor picks a theme by
hand, so the screenshots follow the toggle as well as the system setting.
"""
from __future__ import annotations

import argparse
import html
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from make_images import SCENES  # noqa: E402

DEFAULT_SIZES = "(min-width: 75rem) 40rem, (min-width: 48rem) 70vw, calc(100vw - 2rem)"
FULL_SIZE = {"hero": (1920, 1080), "focus": (1920, 1080)}


def crop_size(name: str) -> tuple[int, int]:
    box = SCENES[name][1]
    if box is None:
        return FULL_SIZE.get(name, (1920, 1080))
    return box[2] - box[0], box[3] - box[1]


def picture(name: str, alt: str, sizes: str = DEFAULT_SIZES, eager: bool = False, indent: str = "") -> str:
    _stem, _box, widths, fallback = SCENES[name]
    w, h = crop_size(name)

    def srcset(theme: str) -> str:
        return ", ".join(f"/img/v1/{name}-{theme}-{x}.webp {x}w" for x in widths)

    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    lines = [
        "<picture>",
        f'  <source type="image/webp" media="(prefers-color-scheme: dark)" data-theme-src="dark" srcset="{srcset("dark")}" sizes="{sizes}">',
        f'  <source type="image/webp" srcset="{srcset("light")}" sizes="{sizes}">',
        f'  <img src="/img/v1/{name}-light-{fallback}.jpg" width="{w}" height="{h}" alt="{html.escape(alt)}" {load} decoding="async">',
        "</picture>",
    ]
    return "\n".join(indent + line for line in lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", choices=sorted(SCENES))
    ap.add_argument("alt")
    ap.add_argument("sizes", nargs="?", default=DEFAULT_SIZES)
    ap.add_argument("--eager", action="store_true", help="above the fold: no lazy loading, high fetch priority")
    a = ap.parse_args()
    print(picture(a.name, a.alt, a.sizes, a.eager))
