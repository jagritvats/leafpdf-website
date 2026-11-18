"""Render the website's icons and its Open Graph image from the Leaf icon.

    python tools/make_brand.py [--shot PATH_TO_SCREENSHOT]

Writes into site/:
  favicon.ico (16, 32, 48), icons/icon-{32,192,512}.png (the rounded green square on transparency),
  icons/icon-maskable-512.png and icons/apple-touch-icon.png (full-bleed green, the leaf inside the safe zone),
  img/og-1200x630.png (link previews).

The icon is the same drawing as the app's (leaf/icons.py and packaging/msix/make_assets.py in the Leaf
repository): a white leaf with a green stem line on a green rounded square, #43c463 to #1f8a3b. site/favicon.svg
is the same drawing written by hand.

--shot defaults to ../leaf/marketing/out/screens/light/03-edit-text-1920x1080.png. Needs PySide6. Run it on
Windows (or anywhere the fonts below are installed): the Open Graph image uses Sitka and Segoe UI Variable.
"""
from __future__ import annotations

import argparse
import io
import os
import sys

from PySide6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetricsF, QGuiApplication, QImage, QLinearGradient, QPainter,
                           QPainterPath, QPen)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
TOP, BOTTOM, STEM = "#43c463", "#1f8a3b", "#2a9a48"

app = QGuiApplication.instance() or QGuiApplication(sys.argv)


def leaf_path() -> QPainterPath:
    path = QPainterPath(QPointF(4.5, 19.5))
    path.cubicTo(3, 10, 9, 3.5, 20, 4)
    path.cubicTo(20.5, 15, 14, 21, 4.5, 19.5)
    return path


def draw_icon(p: QPainter, x: float, y: float, size: float, square: bool = True) -> None:
    """The Leaf icon in the size x size square at (x, y); square=False draws only the leaf (for a green plate)."""
    p.save()
    p.translate(x, y)
    p.scale(size / 24, size / 24)
    p.setPen(Qt.PenStyle.NoPen)
    if square:
        g = QLinearGradient(0, 0, 0, 24)
        g.setColorAt(0, QColor(TOP))
        g.setColorAt(1, QColor(BOTTOM))
        p.setBrush(g)
        p.drawRoundedRect(QRectF(1, 1, 22, 22), 5.5, 5.5)
    p.translate(12, 12)
    p.scale(0.82, 0.82)
    p.translate(-12, -12.5)
    p.setBrush(QColor(255, 255, 255, 240))
    p.drawPath(leaf_path())
    p.setPen(QPen(QColor(STEM), 1.3 if size >= 32 else 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(5, 19), QPointF(14.5, 9.5))
    p.restore()


def icon(n: int, plated: bool = False, frac: float = 1.0) -> QImage:
    img = QImage(n, n, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if plated:
        g = QLinearGradient(0, 0, 0, n)
        g.setColorAt(0, QColor(TOP))
        g.setColorAt(1, QColor(BOTTOM))
        p.fillRect(QRectF(0, 0, n, n), g)
    s = n * frac
    draw_icon(p, (n - s) / 2, (n - s) / 2, s, square=not plated)
    p.end()
    return img


def png_bytes(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def write_ico(path: str, sizes: tuple[int, ...]) -> None:
    """A .ico with PNG-compressed entries (supported since Windows Vista and by every browser)."""
    blobs = [png_bytes(icon(n)) for n in sizes]
    header = (0).to_bytes(2, "little") + (1).to_bytes(2, "little") + len(sizes).to_bytes(2, "little")
    offset = 6 + 16 * len(sizes)
    entries = b""
    for n, blob in zip(sizes, blobs):
        entries += bytes([n % 256, n % 256, 0, 0]) + (1).to_bytes(2, "little") + (32).to_bytes(2, "little")
        entries += len(blob).to_bytes(4, "little") + offset.to_bytes(4, "little")
        offset += len(blob)
    with open(path, "wb") as f:
        f.write(header + entries + b"".join(blobs))


def font(family: str, px: float, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont(family)
    f.setPixelSize(round(px))
    f.setWeight(weight)
    return f


def og_image(shot_path: str) -> QImage:
    W, H = 1200, 630
    paper, ink, muted, edit = QColor("#f6f8f4"), QColor("#14231a"), QColor("#46574b"), QColor("#1b7c35")
    img = QImage(W, H, QImage.Format.Format_RGB32)
    p = QPainter(img)
    p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
                     | QPainter.RenderHint.SmoothPixmapTransform)
    p.fillRect(QRectF(0, 0, W, H), paper)

    # Right: a green plate with the app window on it, bleeding off the right and bottom edges.
    plate_x = 700
    g = QLinearGradient(plate_x, 0, W, H)
    g.setColorAt(0, QColor(TOP))
    g.setColorAt(1, QColor(BOTTOM))
    p.fillRect(QRectF(plate_x, 0, W - plate_x, H), g)
    p.setOpacity(0.16)
    draw_icon(p, plate_x + 150, -40, 520, square=False)
    p.setOpacity(1.0)
    shot = QImage(shot_path)
    if shot.isNull():
        sys.exit(f"missing {shot_path}")
    sw = 860
    sh = sw * shot.height() / shot.width()
    sx, sy = 620, 150
    for i in range(18, 0, -1):  # soft shadow
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(10, 40, 20, 5))
        p.drawRoundedRect(QRectF(sx - i, sy - i + 10, sw + 2 * i, sh + 2 * i), 14 + i, 14 + i)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(sx, sy, sw, sh), 12, 12)
    p.save()
    p.setClipPath(clip)
    p.drawImage(QRectF(sx, sy, sw, sh), shot)
    p.restore()
    p.setPen(QPen(QColor(0, 0, 0, 40), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(sx + 0.5, sy + 0.5, sw - 1, sh - 1), 12, 12)

    # Left: the mark, the name, the headline inside an edit-text outline with a caret, the subline.
    x = 72
    draw_icon(p, x - 4, 64, 60)
    p.setPen(ink)
    p.setFont(font("Segoe UI Variable Display", 38, QFont.Weight.DemiBold))
    p.drawText(QPointF(x + 70, 108), "Leaf")

    head = font("Sitka Display", 60, QFont.Weight.Normal)
    fm = QFontMetricsF(head)
    lines = ["Edit PDFs.", "Keep them yours."]
    top = 200
    lh = 72
    widest = max(fm.horizontalAdvance(t) for t in lines)
    box = QRectF(x - 16, top - 12, widest + 44, lh * len(lines) + 22)
    p.fillRect(box, QColor(255, 255, 255))
    p.setPen(QPen(edit, 2))
    p.drawRect(box)
    p.setFont(head)
    p.setPen(ink)
    for i, t in enumerate(lines):
        p.drawText(QPointF(x, top + fm.ascent() + i * lh), t)
    caret_x = x + fm.horizontalAdvance(lines[-1]) + 6
    caret_top = top + (len(lines) - 1) * lh + 6
    p.fillRect(QRectF(caret_x, caret_top, 3, fm.ascent() + 6), ink)

    p.setFont(font("Segoe UI Variable Text", 23))
    p.setPen(muted)
    sub = ["A native PDF editor for Windows and Linux.", "Works offline, so nothing leaves your computer."]
    for i, t in enumerate(sub):
        p.drawText(QPointF(x - 2, 410 + i * 34), t)
    p.setFont(font("Segoe UI Variable Text", 22, QFont.Weight.DemiBold))
    p.setPen(edit)
    p.drawText(QPointF(x - 2, 566), "leafpdf.org")
    p.end()
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shot", default=os.path.join(ROOT, "..", "leaf", "marketing", "out", "screens", "light",
                                                   "03-edit-text-1920x1080.png"))
    args = ap.parse_args()
    icons = os.path.join(SITE, "icons")
    os.makedirs(icons, exist_ok=True)
    os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
    for n in (32, 192, 512):
        icon(n).save(os.path.join(icons, f"icon-{n}.png"))
    icon(512, plated=True, frac=0.62).save(os.path.join(icons, "icon-maskable-512.png"))
    icon(180, plated=True, frac=0.66).save(os.path.join(icons, "apple-touch-icon.png"))
    write_ico(os.path.join(SITE, "favicon.ico"), (16, 32, 48))
    og = og_image(args.shot)
    og.save(os.path.join(SITE, "img", "og-1200x630.png"))
    # Re-encode through Pillow if available: a palette-free optimized PNG is a good deal smaller.
    try:
        from PIL import Image

        path = os.path.join(SITE, "img", "og-1200x630.png")
        Image.open(io.BytesIO(png_bytes(og))).convert("RGB").save(path, "PNG", optimize=True)
    except ImportError:
        pass
    print("icons, favicon.ico and img/og-1200x630.png written")


if __name__ == "__main__":
    main()
