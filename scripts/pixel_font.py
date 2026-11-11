#!/usr/bin/env python3
"""Original 5x7 pixel font for the Minecraft skin (D1).

The licence red line: refs/vanilla-26.3/textures/font/ascii.png is a Mojang asset
and must never ship, and this repository never extracted unifont.png. So every
glyph below is drawn here, pixel by pixel, as our own work - nothing is traced,
sampled or converted from any existing font file. The metrics (5px cell, 6px
advance, 7px cap height, 1px descender) are a plain bitmap grid, not a copy of
Minecraft's ascii.png layout.

Outputs:
  skin/fonts/skin-pixel-5x7.ttf   the font binary (our asset, CC0 dedication)
  skin/fonts/LICENSE.txt          the licence that ships with it
  skin/pixel-font.css             @font-face with the TTF inlined as base64
                                  (generated; appended to skin.css by the build)

Coverage: printable ASCII 0x20-0x7E only. CJK is intentionally absent: Chinese
text keeps the system font through the normal font stack, per the D1 scope.
"""

from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = Path(__file__).resolve().parent.parent
UPM = 64          # font units per em
PX = 8            # font units per pixel -> em is exactly 8 pixels tall
ADVANCE = 6 * PX  # 5px cell + 1px side bearing
ASCENT = 7 * PX
DESCENT = -1 * PX

# 5 columns x 7 rows per glyph, top row first. '1' = ink.
GLYPHS: dict[str, list[str]] = {
    " ": ["00000"] * 7,
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "%": ["11000", "11001", "00010", "00100", "01000", "10011", "00011"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "'": ["00100", "00100", "00000", "00000", "00000", "00000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "*": ["00000", "01010", "00100", "11111", "00100", "01010", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00100", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ";": ["00000", "00100", "00100", "00000", "00100", "00100", "01000"],
    "<": ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "[": ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    "\\": ["10000", "01000", "01000", "00100", "00010", "00010", "00001"],
    "]": ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    "^": ["00100", "01010", "10001", "00000", "00000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "`": ["01000", "00100", "00000", "00000", "00000", "00000", "00000"],
    "a": ["00000", "00000", "01110", "00001", "01111", "10001", "01111"],
    "b": ["10000", "10000", "11110", "10001", "10001", "10001", "11110"],
    "c": ["00000", "00000", "01111", "10000", "10000", "10000", "01111"],
    "d": ["00001", "00001", "01111", "10001", "10001", "10001", "01111"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "f": ["00110", "01001", "01000", "11110", "01000", "01000", "01000"],
    "g": ["00000", "01111", "10001", "10001", "01111", "00001", "01110"],
    "h": ["10000", "10000", "11110", "10001", "10001", "10001", "10001"],
    "i": ["00100", "00000", "01100", "00100", "00100", "00100", "01110"],
    "j": ["00010", "00000", "00110", "00010", "00010", "10010", "01100"],
    "k": ["10000", "10000", "10010", "10100", "11000", "10100", "10010"],
    "l": ["01100", "00100", "00100", "00100", "00100", "00100", "01110"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10101", "10101"],
    "n": ["00000", "00000", "11110", "10001", "10001", "10001", "10001"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "p": ["00000", "11110", "10001", "10001", "11110", "10000", "10000"],
    "q": ["00000", "01111", "10001", "10001", "01111", "00001", "00001"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "t": ["01000", "01000", "11110", "01000", "01000", "01001", "00110"],
    "u": ["00000", "00000", "10001", "10001", "10001", "10011", "01101"],
    "v": ["00000", "00000", "10001", "10001", "10001", "01010", "00100"],
    "w": ["00000", "00000", "10001", "10101", "10101", "10101", "01010"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    "y": ["00000", "10001", "10001", "10001", "01111", "00001", "01110"],
    "z": ["00000", "00000", "11111", "00010", "00100", "01000", "11111"],
    "{": ["00010", "00100", "00100", "01000", "00100", "00100", "00010"],
    "|": ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
    "}": ["01000", "00100", "00100", "00010", "00100", "00100", "01000"],
    "~": ["00000", "00000", "01001", "10110", "00000", "00000", "00000"],
}

FAMILY = "Skin Pixel 5x7"


def _glyph(rows: list[str]):
    pen = TTGlyphPen(None)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "1":
                pen.moveTo((x * PX, (7 - y) * PX))
                pen.lineTo(((x + 1) * PX, (7 - y) * PX))
                pen.lineTo(((x + 1) * PX, (6 - y) * PX))
                pen.lineTo((x * PX, (6 - y) * PX))
                pen.closePath()
    return pen.glyph()


def build_ttf() -> bytes:
    order = [".notdef"] + sorted(GLYPHS)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(ch): ch for ch in GLYPHS})
    fb.setupGlyf({name: (_glyph(GLYPHS[name]) if name in GLYPHS else TTGlyphPen(None).glyph()) for name in order})
    fb.setupHorizontalMetrics({name: (ADVANCE, 0) for name in order})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": "Regular",
        "uniqueFontIdentifier": "Skin Pixel 5x7; original artwork of the minecraft_skin project",
        "fullName": FAMILY,
        "psName": "SkinPixel5x7-Regular",
        "version": "Version 1.000",
        "description": "Original 5x7 pixel font drawn for the minecraft_skin DSH skin. CC0-1.0.",
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, usWinAscent=ASCENT, usWinDescent=-DESCENT,
                achVendID="NONE", fsType=0)
    fb.setupPost(isFixedPitch=1)
    buf = io.BytesIO()
    fb.save(buf)
    return buf.getvalue()


LICENCE = """skin-pixel-5x7.ttf - original pixel font of the minecraft_skin project
=========================================================================

Copyright: the authors of the minecraft_skin repository.
Licence:   CC0 1.0 Universal (public domain dedication).

Every glyph in this font was drawn by scripts/pixel_font.py from the bitmap table
in that file. No existing font file was copied, converted, traced or subset, and
no Mojang asset (for example refs/vanilla-26.3/textures/font/ascii.png, which
stays local reference only) contributed any pixel to it.

You may use, modify and redistribute this font for any purpose, including
commercially, without asking permission. Attribution is appreciated but not
required. The font is provided as-is, without warranty of any kind.

The 5x7 bitmap grid and 6px advance are ordinary bitmap-metrics conventions; the
glyph shapes themselves are this project's own design.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, default=ROOT / "skin" / "fonts")
    ap.add_argument("--css", type=Path, default=ROOT / "skin" / "pixel-font.css")
    args = ap.parse_args()
    args.fonts.mkdir(parents=True, exist_ok=True)
    ttf = build_ttf()
    (args.fonts / "skin-pixel-5x7.ttf").write_bytes(ttf)
    (args.fonts / "LICENSE.txt").write_text(LICENCE, encoding="utf-8", newline="\n")
    b64 = base64.b64encode(ttf).decode("ascii")
    css = (
        "/* Generated by scripts/pixel_font.py - do not edit by hand.\n"
        f" * {FAMILY}: {len(GLYPHS)} original 5x7 glyphs, printable ASCII only.\n"
        " * CJK is deliberately absent so Chinese text falls back to the system font. */\n"
        "@font-face {\n"
        f"  font-family: \"{FAMILY}\";\n"
        "  font-style: normal;\n"
        "  font-weight: 400;\n"
        "  font-display: swap;\n"
        f"  src: url(data:font/ttf;base64,{b64}) format(\"truetype\");\n"
        "}\n"
    )
    args.css.write_text(css, encoding="utf-8", newline="\n")
    print(f"{len(GLYPHS)} glyphs -> {args.fonts / 'skin-pixel-5x7.ttf'} ({len(ttf)} bytes)")
    print(f"@font-face -> {args.css} ({len(css)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
