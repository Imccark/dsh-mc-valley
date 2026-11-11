#!/usr/bin/env python3
"""Original 16x16 pixel file-type icons for the Minecraft skin.

Every pixel is drawn by this script from shapes defined below - no Mojang asset is
copied or sampled. The rules follow the skin's existing pixel language:

  * 1px dark outline around every silhouette
  * 1px light bevel inside the top+left edge, 1px dark bevel inside bottom+right
  * flat fills, no gradients, transparent background
  * palette reuses the colours already used by skin/skin.css

R06/C10: the first pass drew every type as a pale page and relied on 1px glyphs,
which is unreadable at 16px. The set now separates the *silhouette* first and the
label second: a document with a coloured bottom band (red PDF, blue Word, green
Excel, amber HTML), a charcoal command block for code, a film strip for video, a
framed painting for images, a bound book for Markdown and a slide with bars for
PowerPoint. Each band is 3px tall so it survives 16px and stays legible at 24/32.

The host (dsh-web-frontend) ships one 24x24 stroke SVG per file type:
  _markdown_1wejo_28, _code_1wejo_8, _html_1wejo_20, _image_1wejo_24,
  _pdf_1wejo_36, _word_1wejo_48, _excel_1wejo_12, _ppt_1wejo_40,
  _video_1wejo_44, _folder_1wejo_16, _other_1wejo_32.
The skin paints a background sprite on the same <svg> element and hides its
children, so the host keeps its accessible <title> and we never touch the
folder (open/closed boxes) or the unknown-type icon.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "skin" / "sprites"

SIZE = 16

# Colours already used by the skin (see skin/skin.css); no new hues.
PALETTE = {
    "k": (32, 26, 18),      # outline / ink
    "c": (58, 50, 42),      # charcoal (command block, film)
    "C": (92, 82, 70),      # charcoal light
    "p": (253, 243, 220),   # paper light
    "P": (230, 213, 176),   # paper shade
    "w": (138, 98, 56),     # wood mid
    "W": (92, 61, 34),      # wood dark
    "g": (102, 154, 26),    # grass green
    "G": (63, 97, 16),      # deep green
    "r": (160, 46, 37),     # redstone
    "R": (125, 31, 24),     # redstone dark
    "a": (230, 183, 74),    # amber
    "A": (154, 116, 32),    # amber dark
    "b": (78, 140, 192),    # information blue (same family as R05 running blue)
    "B": (44, 88, 128),     # information blue dark
    "s": (201, 191, 168),   # stone light
    "S": (154, 143, 120),   # stone dark
    "l": (223, 233, 242),   # pale sky (mountain backdrop)
}


class Canvas:
    def __init__(self) -> None:
        self.im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        self.px = self.im.load()

    def dot(self, x: int, y: int, key: str) -> None:
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.px[x, y] = (*PALETTE[key], 255)

    def rect(self, x0: int, y0: int, x1: int, y1: int, key: str, fill: bool = True) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if fill or x in (x0, x1) or y in (y0, y1):
                    self.dot(x, y, key)

    def frame(self, x0: int, y0: int, x1: int, y1: int, key: str) -> None:
        self.rect(x0, y0, x1, y1, key, fill=False)

    def hline(self, x0: int, x1: int, y: int, key: str) -> None:
        for x in range(x0, x1 + 1):
            self.dot(x, y, key)

    def vline(self, x: int, y0: int, y1: int, key: str) -> None:
        for y in range(y0, y1 + 1):
            self.dot(x, y, key)

    def bevel(self, x0: int, y0: int, x1: int, y1: int, light: str, dark: str) -> None:
        self.hline(x0, x1, y0, light)
        self.vline(x0, y0, y1, light)
        self.hline(x0, x1, y1, dark)
        self.vline(x1, y0, y1, dark)

    def stroke(self) -> None:
        """Outline every opaque pixel with the ink colour, outside the shape."""
        src = self.im.load()
        out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        dst = out.load()
        solid = {(x, y) for y in range(SIZE) for x in range(SIZE) if src[x, y][3] > 0}
        for (x, y) in list(solid):
            dst[x, y] = src[x, y]
        for (x, y) in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < SIZE and 0 <= ny < SIZE and (nx, ny) not in solid:
                    dst[nx, ny] = (*PALETTE["k"], 255)
        self.im = out
        self.px = out.load()


def _page(c: Canvas, x0: int = 3, y0: int = 2, x1: int = 12, y1: int = 13) -> None:
    """Shared document silhouette: paper face, bevel, folded top-right corner."""
    c.rect(x0, y0, x1, y1, "p")
    c.bevel(x0, y0, x1, y1, "p", "P")
    c.rect(x1 - 2, y0, x1, y0 + 2, "P")
    c.hline(x1 - 2, x1 - 1, y0 + 2, "S")
    c.vline(x1 - 2, y0, y0 + 1, "S")


def _band(c: Canvas, x0: int, x1: int, top: int, bottom: int, key: str, dark: str) -> None:
    """Coloured type band with a 1px darker rule under it."""
    c.rect(x0, top, x1, bottom, key)
    c.hline(x0, x1, bottom, dark)


def markdown() -> Canvas:
    """Bound book with a green ribbon - 'book and quill' without the clutter."""
    c = Canvas()
    c.rect(3, 3, 12, 12, "w")
    c.bevel(3, 3, 12, 12, "P", "W")
    c.rect(5, 4, 11, 11, "p")
    c.vline(4, 4, 11, "W")
    for y in (6, 8, 10):
        c.hline(6, 10, y, "P")
    c.rect(8, 3, 10, 7, "g")
    c.rect(8, 7, 10, 7, "G")
    c.dot(9, 5, "p")
    return c


def code() -> Canvas:
    """Command block: charcoal cube with a chunky light prompt."""
    c = Canvas()
    c.rect(2, 3, 13, 12, "c")
    c.hline(2, 13, 3, "C")
    c.hline(2, 13, 4, "C")
    c.hline(2, 13, 12, "k")
    c.vline(13, 3, 12, "k")
    # '>' two pixels thick
    for (x, y) in ((5, 5), (6, 6), (6, 7), (5, 8)):
        c.dot(x, y, "p")
        c.dot(x + 1, y, "p")
    # '_' under the caret
    c.hline(9, 11, 9, "p")
    c.hline(9, 11, 10, "p")
    c.dot(9, 5, "g")
    c.dot(10, 5, "g")
    return c


def html() -> Canvas:
    """Page with an amber band carrying a dark < > pair."""
    c = Canvas()
    _page(c)
    _band(c, 3, 12, 10, 12, "a", "A")
    for (x, y) in ((5, 10), (4, 11), (5, 12)):
        c.dot(x, y, "k")
    for (x, y) in ((9, 10), (10, 11), (9, 12)):
        c.dot(x, y, "k")
    c.dot(7, 11, "k")
    c.hline(4, 9, 6, "w")
    c.hline(4, 9, 8, "P")
    return c


def image() -> Canvas:
    """Painting frame: pale sky, stone mountain and an amber sun."""
    c = Canvas()
    c.rect(2, 3, 13, 13, "w")
    c.bevel(2, 3, 13, 13, "a", "W")
    c.rect(4, 5, 11, 11, "l")
    c.rect(8, 6, 10, 7, "a")
    for (x, y) in ((5, 10), (6, 9), (7, 10), (6, 10), (7, 9)):
        c.dot(x, y, "S")
    c.hline(5, 10, 11, "S")
    return c


def pdf() -> Canvas:
    """Document with a redstone band and a white label block."""
    c = Canvas()
    _page(c)
    c.hline(4, 8, 5, "w")
    c.hline(4, 9, 7, "P")
    c.hline(4, 9, 8, "P")
    _band(c, 3, 12, 10, 12, "r", "R")
    c.hline(5, 10, 11, "p")
    c.dot(4, 11, "p")
    c.dot(11, 11, "p")
    return c


def word() -> Canvas:
    """Document with a blue band and a white label block."""
    c = Canvas()
    _page(c)
    c.hline(4, 9, 5, "w")
    c.hline(4, 9, 7, "P")
    _band(c, 3, 12, 10, 12, "b", "B")
    c.hline(5, 10, 11, "p")
    c.dot(4, 11, "p")
    c.dot(11, 11, "p")
    return c


def excel() -> Canvas:
    """Document with a green band carrying a two-column ledger grid."""
    c = Canvas()
    _page(c)
    c.hline(4, 9, 5, "w")
    c.hline(4, 9, 7, "P")
    _band(c, 3, 12, 10, 12, "g", "G")
    for x in (6, 9):
        c.vline(x, 10, 12, "p")
    c.hline(4, 11, 11, "p")
    return c


def ppt() -> Canvas:
    """Slide frame on a stand, with three rising bars."""
    c = Canvas()
    c.rect(2, 3, 13, 11, "A")
    c.bevel(2, 3, 13, 11, "a", "A")
    c.rect(3, 4, 12, 9, "p")
    c.rect(4, 7, 5, 9, "g")
    c.rect(7, 6, 8, 9, "G")
    c.rect(10, 5, 11, 9, "g")
    c.hline(3, 12, 9, "S")
    c.vline(7, 12, 13, "A")
    c.vline(8, 12, 13, "A")
    return c


def video() -> Canvas:
    """Film strip: charcoal frame, sprocket holes and a light play mark."""
    c = Canvas()
    c.rect(2, 4, 13, 12, "c")
    c.hline(2, 13, 4, "C")
    c.hline(2, 13, 12, "k")
    for x in (3, 5, 8, 10, 12):
        c.dot(x, 5, "p")
        c.dot(x, 6, "C")
        c.dot(x, 11, "p")
        c.dot(x, 10, "C")
    for (x, y) in ((6, 7), (6, 8), (6, 9), (7, 8)):
        c.dot(x, y, "p")
    c.dot(8, 8, "C")
    return c


ICONS = {
    "markdown": markdown,
    "code": code,
    "html": html,
    "image": image,
    "pdf": pdf,
    "word": word,
    "excel": excel,
    "ppt": ppt,
    "video": video,
}


def render(kind: str) -> Image.Image:
    canvas = ICONS[kind]()
    canvas.stroke()
    return canvas.im


def contact_sheet(sizes: tuple[int, ...] = (16, 24, 32), gap: int = 12, pad: int = 10) -> Image.Image:
    kinds = list(ICONS)
    col_w = max(sizes) + gap
    w = pad * 2 + col_w * len(sizes)
    h = pad * 2 + col_w * len(kinds)
    sheet = Image.new("RGBA", (w, h), (242, 233, 207, 255))
    for row, kind in enumerate(kinds):
        icon = render(kind)
        x = pad
        for size in sizes:
            big = icon.resize((size, size), Image.NEAREST)
            sheet.alpha_composite(big, (x, pad + row * col_w + (max(sizes) - size) // 2))
            x += col_w
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sheet", type=Path, default=ROOT / "skin" / "build" / "file-icons-contact.png")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for kind in ICONS:
        render(kind).save(args.out / f"file-{kind}.png")
    sheet = contact_sheet()
    args.sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.sheet)
    print(f"{len(ICONS)} icons -> {args.out}")
    print(f"contact sheet -> {args.sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
