#!/usr/bin/env python3
"""Night / nether colour variants (D4) - recoloured copies of our own sprites.

The base textures in skin/sprites/ are already this project's own artwork
(mc_textures.py), so recolouring them keeps the whole asset chain original. The
target ramps are measured from vanilla block textures that stay local reference
only, and the source file + sampled hexes are recorded below and in
skin/variants.reference.md.

  refs/vanilla-26.3/textures/block/deepslate.png   #515151 #3d3d43 #646464 #2f2f37 #797979
  refs/vanilla-26.3/textures/block/netherrack.png  #652828 #723232 #501b1b #511515 #572121
  refs/vanilla-26.3/textures/block/obsidian.png    #06030b #100c1c #271e3d #3b2754
  refs/vanilla-26.3/textures/gui/signs/crimson.png #793753 #6a344b #613245 #4c2537

Mapping: luminance of the source pixel -> position on a 5-stop ramp, so the
existing dither and 1px bevel survive; alpha is preserved untouched.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "skin" / "sprites"

# ramp: darkest -> lightest
RAMPS = {
    # night: deepslate greys for stone, cold ink-blue paper, dark oak planks
    "night": {
        "stone": ["#1d1d22", "#2f2f37", "#3d3d43", "#515151", "#797979"],
        "parch": ["#c3cada", "#ced5e2", "#dbe1ec", "#e6ebf3", "#f2f5fa"],
        "plank": ["#1b1712", "#2a231c", "#3a2f25", "#4a3b2d", "#5b4a37"],
        "slot": ["#0f0f13", "#1c1c22", "#28282f", "#34343d", "#41414c"],
    },
    # nether: netherrack reds for paper, crimson plum for planks, dark basalt stone
    "nether": {
        "stone": ["#241417", "#331b1e", "#412326", "#502a2d", "#5f3336"],
        "parch": ["#d6c0ba", "#e0cdc7", "#ecdad4", "#f3e5e0", "#fbf2ee"],
        "plank": ["#26121b", "#351a26", "#432132", "#4c2537", "#5a2e40"],
        "slot": ["#180c0f", "#251318", "#31191f", "#3d2027", "#4a272f"],
    },
}

BASES = {"stone": "stone.png", "parch": "parch_large.png", "plank": "plank_tile.png", "slot": "slot.png"}

# D4: the recoloured parchment kept the base cloud noise and the wide ramps
# amplified it, so the night surface read as grey clouds and the nether surface as
# pink paper. The paper tiles are now drawn as calm materials instead: 32px
# deepslate panels for night and 3px crimson grain for the nether. Both stay light
# enough for the unchanged dark body text.
PAPER_PALETTE = {
    "night": {
        "cell": ["#d7dce6", "#dbe0e9", "#dfe4ec"],
        "seam": "#c6ccd8",
        "light": "#e8ecf2",
    },
    "nether": {
        "cell": ["#eddcd6", "#efdfda", "#f1e3de"],
        "seam": "#dfc9c2",
        "light": "#f7ece8",
    },
}
PAPER_SIZE = 128


def paper_tile(variant: str) -> Image.Image:
    """Deterministic material tile: block panels (night) or grain bands (nether)."""
    pal = PAPER_PALETTE[variant]
    im = Image.new("RGBA", (PAPER_SIZE, PAPER_SIZE), (0, 0, 0, 0))
    px = im.load()
    cells = pal["cell"]
    for y in range(PAPER_SIZE):
        for x in range(PAPER_SIZE):
            if variant == "night":
                # 32px deepslate panels with a 1px seam and a light top edge
                cx, cy = x // 32, y // 32
                pick = cells[(cx * 3 + cy * 5) % len(cells)]
                if x % 32 == 0 or y % 32 == 0:
                    pick = pal["seam"]
                elif y % 32 == 1 or x % 32 == 1:
                    pick = pal["light"]
            else:
                # 3px crimson grain bands with an occasional darker line
                band = y // 3
                pick = cells[band % len(cells)]
                if y % 3 == 0:
                    pick = pal["seam"]
                elif (x + band * 7) % 37 == 0:
                    pick = pal["light"]
            r, g, b = hex2rgb(pick)
            px[x, y] = (r, g, b, 255)
    return im


def hex2rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def recolour(src: Image.Image, ramp: list[str]) -> Image.Image:
    stops = [hex2rgb(c) for c in ramp]
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, dp = src.load(), out.load()
    w, h = src.size
    # normalise luminance against the source's own range so the ramp is used fully
    lums = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if a > 8:
                lums.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
    lo, hi = (min(lums), max(lums)) if lums else (0, 255)
    span = max(1.0, hi - lo)
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if a <= 8:
                continue
            t = ((0.2126 * r + 0.7152 * g + 0.0722 * b) - lo) / span
            pos = t * (len(stops) - 1)
            i = min(len(stops) - 2, int(pos))
            f = pos - i
            c = tuple(round(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3))
            dp[x, y] = (*c, a)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=SPRITES)
    args = ap.parse_args()
    written = 0
    for variant, ramps in RAMPS.items():
        for base, filename in BASES.items():
            src_path = SPRITES / filename
            if not src_path.is_file():
                continue
            src = Image.open(src_path).convert("RGBA")
            dst = args.out / f"{base}_{variant}.png"
            if base == "parch":
                paper_tile(variant).save(dst)
            else:
                recolour(src, ramps[base]).save(dst)
            written += 1
    print(f"{written} variant sprites -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
