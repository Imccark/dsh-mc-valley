"""Generate the Minecraft-flavoured UI sprites used by the DSH skin.

Everything here is drawn from scratch: no Mojang texture bytes are copied.
Colours are the ones measured from the reference screenshots in ``参考图/``:

    dirt   #573925   wood #8F5C2F   green #6FA33A
    parchment #ECE1D4   stone #D9D3C7

Run:  python scripts/mc_textures.py [--out skin/sprites]
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "skin" / "sprites"

NINE = 32          # nine-slice sprite edge
SLICE = 6          # border-image-slice used by the CSS
TILE = 16          # repeating tile edge

# --- palette ---------------------------------------------------------------

OUTLINE = (30, 20, 12, 255)

WOOD = dict(
    base=(157, 102, 48),
    light=(218, 170, 100),
    dark=(99, 60, 29),
    groove=(119, 73, 34),
    outline=(48, 29, 15),
)
WOOD_HOVER = dict(
    base=(175, 118, 58),
    light=(238, 193, 120),
    dark=(116, 72, 34),
    groove=(133, 84, 39),
    outline=(48, 29, 15),
)
WOOD_ACTIVE = dict(
    base=(114, 72, 36),
    light=(132, 85, 44),
    dark=(84, 51, 26),
    groove=(58, 34, 17),
    outline=(30, 18, 9),
)

GREEN = dict(
    base=(102, 154, 26),
    light=(168, 216, 86),
    dark=(57, 96, 19),
    groove=(45, 74, 26),
    outline=(18, 44, 8),
)
GREEN_HOVER = dict(
    base=(126, 181, 67),
    light=(186, 230, 124),
    dark=(78, 122, 44),
    groove=(52, 84, 30),
    outline=(20, 50, 9),
)
GREEN_ACTIVE = dict(
    base=(90, 136, 46),
    light=(120, 170, 74),
    dark=(56, 88, 31),
    groove=(38, 62, 22),
    outline=(14, 36, 6),
)

# R04: the green *plate* behind text. The bright grass greens above are right for
# frames, rails and selection, but cream 14px text on the 0.21-0.32 luminance
# dither measured only 2.79:1 (and 2.15:1 on hover). These three palettes keep the
# same grass hue one step deeper so the worst texture pixel stays >= 4.5:1 for
# #fffdf2; the hover/pressed feedback comes from the brighter frame sprite
# (green_hover.png / green_active.png) instead of from a lighter fill.
GREEN_PLATE = dict(
    base=(57, 89, 14),
    light=(76, 110, 26),
    dark=(40, 64, 11),
    groove=(33, 54, 11),
    outline=(14, 32, 6),
)
GREEN_PLATE_HOVER = dict(
    base=(61, 92, 17),
    light=(80, 114, 29),
    dark=(45, 72, 14),
    groove=(36, 59, 13),
    outline=(16, 36, 6),
)
GREEN_PLATE_ACTIVE = dict(
    base=(46, 72, 10),
    light=(62, 92, 22),
    dark=(32, 52, 9),
    groove=(27, 45, 9),
    outline=(10, 26, 4),
)

# R05: running/information blue. The host paints running work with
# --dsw-alias-state-business-primary; the skin keeps that hue (blue) instead of
# reusing grass green, which is reserved for primary actions, selection and
# success. Measured against #f7ead1 paper: #2a5d8f = 5.35:1 for text and rails.
BLUE = dict(
    base=(62, 124, 177),
    light=(132, 178, 216),
    dark=(38, 84, 124),
    groove=(30, 66, 98),
    outline=(14, 40, 62),
)

STONE = dict(
    base=(211, 208, 202),
    light=(247, 245, 239),
    dark=(143, 138, 131),
    groove=(111, 106, 100),
    outline=(43, 39, 33),
)
STONE_DARK = dict(
    base=(92, 88, 82),
    light=(126, 121, 113),
    dark=(63, 59, 55),
    groove=(46, 43, 40),
    outline=(18, 17, 15),
)
GUIDE_STONE = dict(
    base=(166, 153, 132),
    light=(231, 216, 190),
    dark=(103, 88, 67),
    groove=(111, 95, 73),
    outline=(67, 53, 37),
)
GUIDE_STONE_HOVER = dict(
    base=(181, 168, 145),
    light=(251, 237, 210),
    dark=(121, 104, 80),
    groove=(125, 109, 83),
    outline=(73, 59, 42),
)
TAB_OAK = dict(
    base=(224, 180, 106),
    light=(255, 224, 166),
    dark=(157, 111, 54),
    groove=(180, 135, 73),
    outline=(69, 44, 23),
)
BIRCH = dict(
    base=(232, 221, 186),
    light=(253, 245, 217),
    dark=(166, 145, 98),
    groove=(188, 168, 120),
    outline=(105, 88, 55),
)

PARCH = dict(
    base=(251, 238, 219),
    light=(255, 246, 234),
    dark=(241, 220, 196),
    groove=(216, 191, 163),
    outline=(74, 64, 56),
)

TOOLTIP = dict(
    base=(17, 3, 21),
    light=(52, 12, 72),
    dark=(8, 0, 12),
    groove=(96, 22, 132),
    outline=(150, 60, 200),
)


# --- helpers ---------------------------------------------------------------


def canvas(size: int, color=(0, 0, 0, 0)) -> Image.Image:
    return Image.new("RGBA", (size, size), color)


def rgba(color):
    return tuple(color) if len(color) == 4 else (color[0], color[1], color[2], 255)


def px(img: Image.Image, x: int, y: int, color) -> None:
    img.putpixel((x, y), rgba(color))


def hline(img, x0, x1, y, color):
    for x in range(x0, x1 + 1):
        px(img, x, y, color)


def vline(img, x, y0, y1, color):
    for y in range(y0, y1 + 1):
        px(img, x, y, color)


def speckle(img, box, colors, seed, weights=None, density=0.35):
    """Scatter `colors` over `box` so textures never read as flat colour."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            if rng.random() < density:
                px(img, x, y, rng.choices(colors, weights=weights or None, k=1)[0])


def shade(color, delta):
    r, g, b = color[0], color[1], color[2]
    a = color[3] if len(color) == 4 else 255
    return (
        max(0, min(255, r + delta)),
        max(0, min(255, g + delta)),
        max(0, min(255, b + delta)),
        a,
    )


def plank_fill(img, pal, seed, box=(0, 0, NINE, NINE)):
    """Wood planks: 5px boards with a 1px groove, plus a continuous vertical
    seam. Both periods (5 and 10) divide the tiled centre slice, so
    ``border-image-repeat: repeat`` never halves a board."""
    x0, y0, x1, y1 = box
    rng = random.Random(seed)
    for y in range(y0, y1):
        row = (y - y0) % 10
        board = ((y - y0) // 10) % 2
        if row == 9:
            for x in range(x0, x1):
                px(img, x, y, shade(pal["groove"], rng.choice((0, 4))))
            continue
        tone = pal["base"] if board == 0 else shade(pal["base"], 12)
        seam_at = 10 * board
        for x in range(x0, x1):
            c = shade(tone, rng.choice((0, 0, 0, 4, -4, 8)))
            if (x - x0) % 20 == seam_at:
                c = shade(pal["dark"], rng.choice((-6, 0)))
            px(img, x, y, c)


def noise_fill(img, pal, seed, box=(0, 0, NINE, NINE), colors=None, density=0.3):
    colors = colors or [pal["light"], pal["dark"], shade(pal["base"], 5)]
    speckle(img, box, colors, seed, weights=[3, 3, 6], density=density)


def mottle(img, pal, seed, box=(0, 0, TILE, TILE), density=0.22, spread=9):
    """Low-contrast grain: a base tone with isolated +/- specks, the way MC
    textures read light rather than as a checkerboard."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    base = pal["base"]
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = base
            if rng.random() < density:
                c = shade(base, rng.randint(-spread, spread))
            elif rng.random() < density / 3:
                c = shade(base, -spread - 6)
            px(img, x, y, c)


def bevel_frame(img, pal, size=NINE, inset=0, chamfer=4):
    """Trace each bevel layer around the stepped corner, including its diagonal.

    Clearing a triangle after drawing straight edges left the corner contour
    disconnected. Nested pixel silhouettes keep outline and highlights joined.
    """
    def inside(x, y, layer):
        lo, hi = inset + layer, size - 1 - inset - layer
        cut = max(0, chamfer - layer)
        return (lo <= x <= hi and lo <= y <= hi
                and x + y >= 2 * lo + cut
                and (hi - x) + (y - lo) >= cut
                and (x - lo) + (hi - y) >= cut
                and (hi - x) + (hi - y) >= cut)

    lo, hi = inset, size - 1 - inset
    for y in range(lo, hi + 1):
        for x in range(lo, hi + 1):
            if not inside(x, y, 0):
                px(img, x, y, (0, 0, 0, 0))
                continue
            for layer in range(3):
                if inside(x, y, layer + 1):
                    continue
                lit = min(x - lo, y - lo) <= min(hi - x, hi - y)
                if layer == 0:
                    color = pal["outline"]
                elif layer == 1:
                    color = pal["light"] if lit else pal["dark"]
                else:
                    color = shade(pal["base"], 16 if lit else -24)
                px(img, x, y, color)
                break


def inner_shade(img, pal, size=NINE, inset=SLICE - 1):
    """Darken the pixel row that touches the content so the fill reads inset."""
    lo, hi = inset, size - 1 - inset
    hline(img, lo, hi, lo, pal["groove"])
    vline(img, lo, lo, hi, pal["groove"])


# --- sprites ---------------------------------------------------------------


def sprite_nav_frame(pal, pressed=False):
    """Six solid bevel layers: a thick cut-corner sign, not a noisy thin rim.

    CSS stretches the straight edges without repeating their texture; all
    relief fits inside the six-pixel slice and follows the corner silhouette.
    """
    img = canvas(NINE, rgba(pal["base"]))

    def inside(x, y, layer):
        hi, cut = NINE - 1 - layer, max(0, 5 - layer)
        return (layer <= x <= hi and layer <= y <= hi
                and min(x + y - 2 * layer, hi - x + y - layer,
                        x - layer + hi - y, 2 * hi - x - y) >= cut)

    lights = (pal["outline"], shade(pal["light"], 12), pal["light"],
              shade(pal["base"], 24), shade(pal["base"], 10), shade(pal["base"], -6))
    shadows = (pal["outline"], shade(pal["dark"], -24), pal["dark"],
               shade(pal["base"], -30), shade(pal["base"], -20), shade(pal["base"], -10))
    for y in range(NINE):
        for x in range(NINE):
            if not inside(x, y, 0):
                px(img, x, y, (0, 0, 0, 0))
                continue
            for layer in range(SLICE):
                if inside(x, y, layer + 1):
                    continue
                lit = min(x, y) <= min(NINE - 1 - x, NINE - 1 - y)
                colors = lights if lit != pressed else shadows
                px(img, x, y, colors[layer])
                break
    return img


def sprite_button_green(pal, seed=7):
    img = canvas(NINE)
    mottle(img, pal, seed, (1, 1, NINE - 1, NINE - 1), density=0.24, spread=8)
    # a few grass blades along the top edge only, like a grass-block face
    rng = random.Random(seed + 1)
    for y in range(3, 7):
        x = rng.randrange(3, NINE - 5)
        hline(img, x, x + rng.choice((2, 3)), y, shade(pal["base"], 16))
    bevel_frame(img, pal)
    return img


def sprite_stone_frame(pal=STONE, seed=11):
    """Stone nine-slice frame.

    The four corners keep the same continuous stepped silhouette as the edges.
    Earlier builds stamped a 4px square rivet into each corner; it collided with
    the outline and the inner groove, so frames read as two overlapping lines.
    Corners now stay smooth on every frame material.
    """
    img = canvas(NINE)
    mottle(img, pal, seed, (1, 1, NINE - 1, NINE - 1), density=0.16, spread=6)
    flat = pal["base"]
    for y in range(SLICE, NINE - SLICE):
        for x in range(SLICE, NINE - SLICE):
            px(img, x, y, flat)
    bevel_frame(img, pal)
    # inner edge: one groove pixel between frame and content
    lo, hi = SLICE - 1, NINE - SLICE
    hline(img, lo, hi, lo, pal["groove"])
    vline(img, lo, lo, hi, pal["groove"])
    hline(img, lo, hi, hi, shade(pal["base"], -14))
    vline(img, hi, lo, hi, shade(pal["base"], -14))
    return img


def sprite_inset(pal=PARCH, seed=21):
    """A pressed-in field: inverted bevel (dark top/left, light bottom/right)."""
    img = canvas(NINE)
    mottle(img, pal, seed, (2, 2, NINE - 2, NINE - 2), density=0.14, spread=5)
    hline(img, 0, NINE - 1, 0, pal["outline"])
    hline(img, 0, NINE - 1, NINE - 1, pal["outline"])
    vline(img, 0, 0, NINE - 1, pal["outline"])
    vline(img, NINE - 1, 0, NINE - 1, pal["outline"])
    hline(img, 1, NINE - 2, 1, pal["dark"])
    vline(img, 1, 1, NINE - 2, pal["dark"])
    hline(img, 1, NINE - 2, NINE - 2, pal["light"])
    vline(img, NINE - 2, 1, NINE - 2, pal["light"])
    for cx, cy in ((0, 0), (NINE - 1, 0), (0, NINE - 1), (NINE - 1, NINE - 1)):
        px(img, cx, cy, (0, 0, 0, 0))
    return img


def sprite_tooltip(seed=31):
    img = canvas(NINE)
    mottle(img, TOOLTIP, seed, (2, 2, NINE - 2, NINE - 2), density=0.12, spread=10)
    hline(img, 0, NINE - 1, 0, TOOLTIP["outline"])
    hline(img, 0, NINE - 1, NINE - 1, TOOLTIP["outline"])
    vline(img, 0, 0, NINE - 1, TOOLTIP["outline"])
    vline(img, NINE - 1, 0, NINE - 1, TOOLTIP["outline"])
    hline(img, 1, NINE - 2, 1, TOOLTIP["groove"])
    vline(img, 1, 1, NINE - 2, TOOLTIP["groove"])
    return img


def sprite_plank_tile(pal, seed=61, size=64):
    """Warm oak with staggered horizontal grain in broad pixel clusters."""
    img = canvas(size)
    for y in range(size):
        board = y // 8
        tone = shade(pal["base"], (0, 8, -5, 4)[board % 4])
        if y % 8 == 7:
            tone = shade(tone, -14)
        elif y % 8 == 0:
            tone = shade(tone, 12)
        # Two-pixel-high strips, offset per band, read as grain instead of dust.
        strips = random.Random(seed + y // 2 * 37)
        grain = [strips.choice((-14, -8, -3, 0, 3, 8, 14)) for _ in range(size // 4)]
        offset = (board * 11 + y // 2 * 3) % size
        for x in range(size):
            c = shade(tone, grain[((x + offset) % size) // 4])
            px(img, x, y, c)
    return img


def sprite_birch_tile(seed=119, size=64):
    """Nearly plain reading field; the carved border carries the detail."""
    img = canvas(size)
    for y in range(size):
        board = y // 16
        tone = shade((242, 233, 207), (0, 1, -1, 0)[board % 4])
        if y % 16 == 15:
            tone = shade(tone, -2)
        elif y % 16 == 0:
            tone = shade(tone, 1)
        strips = random.Random(seed + y // 2 * 37)
        grain = [strips.choice((-2, -1, 0, 0, 1, 2)) for _ in range(size // 4)]
        for x in range(size):
            px(img, x, y, shade(tone, grain[((x + board * 11) % size) // 4]))
    return img


def sprite_birch_medallion():
    """Small square relief, shared by the corners and edge-center plaques."""
    img = canvas(16)
    for y in range(16):
        for x in range(16):
            if (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
                continue
            edge = min(x, y, 15 - x, 15 - y)
            light = min(x, y) <= min(15 - x, 15 - y)
            if edge == 0:
                color = (126, 108, 64)
            elif edge == 1:
                color = (255, 247, 219) if light else (169, 147, 95)
            else:
                color = (225, 211, 168)
            px(img, x, y, color)
    dark, light = (164, 143, 89), (255, 246, 214)
    hline(img, 3, 12, 3, dark); vline(img, 3, 3, 12, dark)
    hline(img, 3, 12, 12, light); vline(img, 12, 3, 12, light)
    hline(img, 5, 10, 5, light); vline(img, 5, 5, 10, light)
    hline(img, 5, 10, 10, dark); vline(img, 10, 5, 10, dark)
    hline(img, 7, 10, 7, dark); vline(img, 7, 7, 9, dark)
    return img


def sprite_birch_carved_frame(seed=137):
    """A 16-source-pixel carved rim; the center is not used by border-image."""
    size = 64
    img = canvas(size, rgba(BIRCH["base"]))
    mottle(img, BIRCH, seed, (3, 3, size - 3, size - 3), density=.4, spread=8)
    # Outer bevel and inner recessed molding are independent continuous edges.
    for lo, hi, dark, light in (
        (5, 58, (239, 226, 186), (176, 155, 104)),
        (12, 51, (159, 137, 83), (255, 245, 211)),
        (13, 50, (191, 172, 120), (247, 235, 199)),
        (15, 48, (218, 203, 158), (244, 232, 198)),
    ):
        hline(img, lo, hi, lo, dark); vline(img, lo, lo, hi, dark)
        hline(img, lo, hi, hi, light); vline(img, hi, lo, hi, light)
    stamp = sprite_birch_medallion().resize((14, 14), Image.Resampling.NEAREST)
    for x, y in ((2, 2), (48, 2), (2, 48), (48, 48)):
        img.alpha_composite(stamp, (x, y))
    bevel_frame(img, BIRCH, size=size, chamfer=6)
    # Keep the open center transparent, even when viewed as a standalone asset.
    for y in range(16, 48):
        for x in range(16, 48):
            px(img, x, y, (0, 0, 0, 0))
    return img


def sprite_nav_grass_tile(pal, seed=81, size=32):
    """Coarse moss/grass patches for the large sidebar action only."""
    img = canvas(size)
    rng = random.Random(seed)
    for y in range(0, size, 4):
        for x in range(0, size, 4):
            color = shade(pal["base"], rng.choice((-20, -12, -5, 0, 6, 13, 20)))
            for dy in range(4):
                for dx in range(4):
                    px(img, x + dx, y + dy, color)
            if rng.random() < .45:
                for dy in range(2):
                    for dx in range(2):
                        px(img, x + dx, y + dy, shade(color, 8))
    return img


def sprite_green_tile(pal, seed=62, size=TILE):
    img = canvas(size)
    rng = random.Random(seed + 1)
    for y in range(0, size, 2):
        for x in range(0, size, 2):
            color = shade(pal["base"], rng.choice((-13, -7, -3, 0, 4, 8, 14)))
            for dy in range(2):
                for dx in range(2):
                    px(img, x + dx, y + dy, color)
    return img


def sprite_dirt(seed=51, size=32):
    """Readable soil clusters, rather than isolated one-pixel noise."""
    img = canvas(size)
    rng = random.Random(seed)
    for y in range(0, size, 4):
        for x in range(0, size, 4):
            tone = rng.choice((-15, -9, -4, 0, 4, 9, 14))
            for dy in range(4):
                for dx in range(4):
                    px(img, x + dx, y + dy, shade((87, 57, 37, 255), tone))
    return img


def sprite_titlebar_terrain(seed=163, width=512, height=40):
    """Half turf/soil, using the sidebar's 8px displayed material clusters."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (width, height))
    cuts = []
    for x in range(0, width, 4):
        phase = 2 * math.pi * x / width
        depth = height / 2 + 4 * math.sin(3 * phase) + 2.5 * math.sin(7 * phase + .4) + 2 * math.sin(13 * phase)
        cuts.append(max(10, min(30, int(depth / 2) * 2 + (2 if rng.random() < .12 else 0))))
    # The sidebar displays these 32px sources at 64px. Bake the same nearest-
    # neighbor scale into the titlebar rather than adding finer random noise.
    turf = sprite_nav_grass_tile(GREEN, 81).resize((64, 64), Image.Resampling.NEAREST)
    soil = sprite_dirt(51).resize((64, 64), Image.Resampling.NEAREST)
    for y in range(height):
        for x in range(width):
            cut = cuts[x // 4]
            color = turf.getpixel((x % 64, y % 64)) if y < cut else soil.getpixel((x % 64, y % 64))
            if y < 2:
                color = shade(color, 9)
            elif cut - 2 <= y < cut:
                color = shade(color, -18)
            px(img, x, y, color)
    return img


def sprite_stone_tile(pal=STONE, seed=55, size=32):
    """Quiet mineral clusters, without the grass-blade streaks of sprite_tile."""
    img = canvas(size)
    rng = random.Random(seed)
    for y in range(0, size, 4):
        for x in range(0, size, 4):
            tone = rng.choice((-5, -3, 0, 0, 2, 4))
            for dy in range(4):
                for dx in range(4):
                    px(img, x + dx, y + dy, shade(pal["base"], tone))
    return img


def sprite_cobble_overlay(seed=151, size=32):
    """Seamless irregular stones, with translucent seams for legible buttons.

    A wrapped nearest-cell field avoids a brick grid and makes the tile repeat
    without a hard seam. Low alpha keeps the existing light face underneath.
    """
    rng = random.Random(seed)
    cells = [(x * 8 + 4 + rng.randrange(-2, 3),
              y * 8 + 4 + rng.randrange(-2, 3)) for y in range(4) for x in range(4)]
    owners = []
    for y in range(size):
        row = []
        for x in range(size):
            def distance(cell):
                dx, dy = abs(x - cell[0]), abs(y - cell[1])
                return min(dx, size - dx) ** 2 + min(dy, size - dy) ** 2
            row.append(min(range(len(cells)), key=lambda i: distance(cells[i])))
        owners.append(row)
    fills = [rng.choice(((72, 70, 65, 10), (72, 70, 65, 6),
                         (255, 253, 245, 12), (255, 253, 245, 7))) for _ in cells]
    img = canvas(size)
    for y in range(size):
        for x in range(size):
            owner = owners[y][x]
            if owners[y][(x - 1) % size] != owner or owners[(y - 1) % size][x] != owner:
                color = (78, 76, 70, 26)
            elif owners[y][(x + 1) % size] != owner or owners[(y + 1) % size][x] != owner:
                color = (255, 253, 245, 24)
            else:
                color = fills[owner]
            px(img, x, y, color)
    return img


def sprite_tile(pal, seed, size=TILE, blades=0):
    img = canvas(size)
    mottle(img, pal, seed, (0, 0, size, size), density=0.2, spread=7)
    rng = random.Random(seed + 5)
    for _ in range(blades):
        x = rng.randrange(0, size)
        y = rng.randrange(0, size)
        hline(img, x, min(size - 1, x + 1), y, shade(pal["light"], 12))
    return img


def sprite_scroll_thumb(seed=41):
    img = canvas(TILE)
    pal = STONE
    mottle(img, pal, seed, (0, 0, TILE, TILE), density=0.2, spread=7)
    hline(img, 0, TILE - 1, 0, pal["light"])
    vline(img, 0, 0, TILE - 1, pal["light"])
    hline(img, 0, TILE - 1, TILE - 1, pal["dark"])
    vline(img, TILE - 1, 0, TILE - 1, pal["dark"])
    return img


# --- big art ---------------------------------------------------------------

PANO_W, PANO_H, PANO_SCALE = 240, 150, 4


def _patch(img, x0, y0, w, h, color):
    for y in range(max(0, y0), min(PANO_H, y0 + h)):
        for x in range(max(0, x0), min(PANO_W, x0 + w)):
            px(img, x, y, color)


def _dither(img, x0, x1, y, colors, seed):
    """1px checker between two palette bands, the signature MC transition."""
    rng = random.Random(seed)
    for x in range(x0, x1):
        if (x + y) % 2 == 0:
            px(img, x, y, rng.choice(colors))
        else:
            px(img, x, y, rng.choice(colors[::-1]))


def grass_bank(img, seed):
    """A shallow turf-covered bank that rises into the right foreground.

    The contour enters through the bottom edge, so there is no rectangular
    left wall. Short terraces, hanging turf and quiet soil clusters keep the
    near bank part of the landscape rather than a separate brown panel.
    """
    rng = random.Random(seed)
    terraces = ((148, 150), (156, 148), (166, 146), (176, 142),
                (188, 140), (198, 137), (212, 134), (226, 132), (240, 131))
    edge = {}
    for (x0, y0), (x1, _) in zip(terraces, terraces[1:]):
        for x in range(x0, x1):
            edge[x] = y0

    # Fill soil below the stepped contour; broad clusters replace loose dots.
    soil = ((126, 89, 56), (132, 94, 60), (138, 99, 64), (144, 104, 67))
    clusters = {(x, y): rng.choice(soil)
                for y in range(130, PANO_H, 2)
                for x in range(148, PANO_W, 3)}
    for x, top in edge.items():
        for y in range(top, PANO_H):
            color = clusters[(148 + (x - 148) // 3 * 3, 130 + (y - 130) // 2 * 2)]
            # A little contact shade under the grass, fading into the earth.
            px(img, x, y, shade(color, -10 if y - top < 3 else 0))

    # Grass top and irregular two-pixel tufts overhang the soil face.
    for (x0, top), (x1, _) in zip(terraces, terraces[1:]):
        _patch(img, x0, top - 3, x1 - x0, 2, (126, 178, 76))
        _patch(img, x0, top - 1, x1 - x0, 1, (145, 192, 92))
        for x in range(x0, x1, 2):
            drop = rng.choice((1, 1, 2, 2, 3))
            color = rng.choice(((88, 138, 48), (98, 150, 54), (105, 157, 58)))
            _patch(img, x, top, min(2, x1 - x), drop, color)

    # Sparse blades on the slope, away from the hero and input area.
    for x in (164, 183, 207, 231):
        y = edge[x] - 6
        _patch(img, x, y, 1, 3, (83, 138, 46))
        _patch(img, x + 1, y + 1, 1, 2, (97, 152, 53))


def build_panorama(seed=99):
    """Procedural Minecraft-style daytime vista, redrawn: square sun above the
    ridge line, blue-grey far peaks + rolling green hills, a lake with a soft
    reflection, then a blocky grass plain with rooted oaks, flowers, tall
    grass, a shallow turf-covered bank and one creeper on the near ledge."""
    img = Image.new("RGBA", (PANO_W, PANO_H), (0, 0, 0, 255))
    _patch(img, 0, 0, PANO_W, PANO_H, (226, 234, 246))   # safety under-layer
    bands = [
        (0, (110, 158, 232)),
        (14, (124, 170, 238)),
        (28, (144, 184, 242)),
        (42, (172, 203, 246)),
        (54, (204, 222, 249)),
        (60, (226, 234, 246)),
    ]
    for i, (y0, c) in enumerate(bands):
        y1 = bands[i + 1][0] if i + 1 < len(bands) else 64
        _patch(img, 0, y0, PANO_W, y1 - y0, c)
        if y1 < 64:
            _dither(img, 0, PANO_W, y1 - 1, (c, bands[i + 1][1]), seed + i)

    # --- blocky clouds ------------------------------------------------------
    clouds = [
        (14, 12, 30, 6), (26, 10, 10, 3), (104, 14, 24, 5), (172, 18, 34, 7),
        (62, 28, 16, 4), (200, 30, 22, 4), (88, 20, 12, 3), (146, 32, 12, 3),
    ]
    for cx, cy, cw, ch in clouds:
        _patch(img, cx, cy, cw, ch, (252, 254, 255))
        _patch(img, cx, cy + ch, cw // 3, 1, (233, 242, 250))
        _patch(img, cx + cw - cw // 3, cy + ch, cw // 3, 1, (238, 246, 252))

    # --- sun stands above the ridge, square with a pale ring -----------------
    _patch(img, 108, 38, 16, 16, (255, 245, 192))
    _patch(img, 110, 40, 12, 12, (255, 251, 222))
    _patch(img, 107, 37, 18, 1, (255, 252, 236))
    _patch(img, 107, 37, 1, 18, (255, 252, 236))
    _patch(img, 107, 54, 18, 1, (255, 252, 236))
    _patch(img, 124, 37, 1, 18, (255, 252, 236))

    # --- far ridge: cool blue-grey peaks, snow caps --------------------------
    far_top = [58, 54, 50, 47, 52, 57, 53, 48, 45, 50, 55, 59, 55, 51, 47, 51,
               56, 60, 56, 52, 48, 54, 58]
    step = PANO_W // len(far_top)
    for i, top in enumerate(far_top):
        x0 = i * step
        _patch(img, x0, top, step, 92 - top, (162, 182, 205))
        _dither(img, x0, x0 + step, top, ((162, 182, 205), (141, 164, 192)), seed + 20 + i)
        if top <= 52:
            _patch(img, x0, top, step, 2, (241, 246, 251))
            _patch(img, x0 + step // 4, top + 2, step // 2, 1, (241, 246, 251))

    # --- rolling green hills with a few sunlit facets ------------------------
    hill_top = [78, 76, 72, 74, 78, 74, 70, 72, 76, 79, 76, 72, 69, 73, 77, 80,
                77, 73, 76, 79]
    step = PANO_W // len(hill_top)
    for i, top in enumerate(hill_top):
        x0 = i * step
        _patch(img, x0, top, step, 94 - top, (124, 154, 78))
        _patch(img, x0, top, step, 2, (146, 176, 98))
        for gx in range(x0, x0 + step, 2):
            if (gx // 4 + i) % 3 == 0:
                _dither(img, gx, gx + 2, top + 3, ((124, 154, 78), (110, 140, 68)), seed + 40 + i)

    # --- tree line behind the lake ------------------------------------------
    for tx, ty in ((18, 80), (60, 78), (104, 80), (150, 79), (196, 80), (226, 78)):
        _patch(img, tx, ty, 9, 5, (70, 116, 46))
        _patch(img, tx + 2, ty - 2, 5, 2, (80, 130, 54))
        _patch(img, tx + 4, ty + 5, 2, 4, (86, 58, 34))

    # --- lake: gentle shore, flecks, soft reflection -------------------------
    lake_y0, lake_y1 = 94, 124
    _patch(img, 0, lake_y0, PANO_W, lake_y1 - lake_y0, (74, 106, 186))
    _patch(img, 0, lake_y0 - 1, PANO_W, 1, (214, 198, 148))          # beach line
    for y in range(lake_y0 + 1, lake_y1):
        # depth bands
        t = y - lake_y0
        _patch(img, 0, y, PANO_W, 1, (74 + min(26, t), 106 + min(22, t), 186 + min(28, t)))
    fleck = random.Random(seed + 500)
    for y in range(lake_y0 + 2, lake_y1 - 2, 3):
        x = fleck.randrange(6, PANO_W - 30)
        hline(img, x, x + fleck.randint(2, 5), y, (134, 164, 220))
        if fleck.random() < 0.5:
            hline(img, x + 3, x + 7, y + 1, (108, 138, 204))
    for y in range(lake_y0, lake_y1, 4):                              # sun reflect
        _patch(img, 113, y, 3, 1, (226, 239, 250, 110))

    # --- foreground: blocky grass plain, stepped top edge --------------------
    rng_g = random.Random(seed + 77)
    ground = {}
    height = 104
    for x in range(PANO_W):
        if rng_g.random() < 0.12:
            height += rng_g.choice((-2, 2))
        height = max(100, min(112, height))
        ground[x] = height

    greens = [(116, 174, 72), (104, 162, 64), (126, 182, 80), (98, 156, 62)]
    tone_i, tone_j = 1, 2
    for bx in range(0, PANO_W, 8):                                      # 8px blocks
        if rng_g.random() < 0.3:
            tone_i = max(0, min(len(greens) - 1, tone_i + rng_g.choice((-1, 1))))
        span = min(8, PANO_W - bx)
        gx = ground[bx]
        _patch(img, bx, gx, span, PANO_H - gx, greens[tone_i])
        for x in range(bx, bx + span):
            px(img, x, gx, (140, 196, 96))                               # lit edge
        for _ in range(3):                                               # darker flecks
            sx = bx + rng_g.randint(0, span - 1)
            _patch(img, sx, gx + rng_g.randint(3, 12), 1, 2, (88, 144, 54))
    # stride stones for depth
    for sx in (36, 118, 210):
        for y in range(ground[sx] + 6, ground[sx] + 26, 3):
            _patch(img, sx, y, 3, 1, (92, 148, 58))

    # --- grass over the right part of the lake (bay) -------------------------
    for bx in range(200, PANO_W, 8):
        if bx != 200 and rng_g.random() < 0.3:
            tone_j = max(0, min(len(greens) - 1, tone_j + rng_g.choice((-1, 1))))
        span = min(8, PANO_W - bx)
        gy = max(ground[bx], 102)
        _patch(img, bx, gy, span, PANO_H - gy, greens[tone_j])
        for x in range(bx, bx + span):
            px(img, x, gy, (140, 196, 96))

    # --- grass-covered terraces enter from the bottom-right -----------------
    grass_bank(img, seed + 280)

    # --- oak trees, rooted on the ground ------------------------------------
    oaks = ((40, "far"), (248 - 40, None))
    for tx, side in ((40, "far"), (210, "near"), (188, "near")):
        rng_t = random.Random(tx * 13)
        if side == "far":
            base_y = 94
            canopy_y, trunk_h = 74, 12
        else:
            base_y = ground[min(tx, PANO_W - 1)] + 2
            canopy_y = base_y - 17
            trunk_h = 17
        _patch(img, tx - 2, canopy_y, 13, 10, (70, 120, 44))
        _patch(img, tx, canopy_y - 3, 9, 3, (78, 130, 52))
        _patch(img, tx + 2, canopy_y + 3, 9, 6, (62, 108, 38))
        for _ in range(30):
            lx = min(PANO_W - 1, max(0, tx - 2 + rng_t.randint(0, 12)))
            ly = min(PANO_H - 1, canopy_y + rng_t.randint(0, 8))
            px(img, lx, ly, (94, 150, 62) if rng_t.random() < 0.5 else (58, 104, 34))
        _patch(img, tx + 4, base_y - trunk_h, 3, trunk_h + 1, (92, 62, 36))
        px(img, tx + 4, base_y - trunk_h, (112, 76, 46))
        _patch(img, tx + 4, base_y - trunk_h, 1, trunk_h, (104, 70, 40))

    # --- flowers + tall grass ------------------------------------------------
    for fi in range(34):
        rr = random.Random(seed * 5 + fi)
        fx = rr.randrange(4, PANO_W - 4)
        gy = ground[fx]
        fy = gy + rr.randint(1, 7)
        kind = fi % 3
        if kind == 0:
            px(img, fx, fy, (244, 214, 70)); px(img, fx, fy + 1, (66, 118, 40))
        elif kind == 1:
            px(img, fx, fy, (226, 74, 74)); px(img, fx, fy + 1, (66, 118, 40))
        else:
            vline(img, fx, fy - 2, fy, (70, 126, 44))
            vline(img, fx + 1, fy - 1, fy, (62, 114, 40))

    # --- creeper on the near ledge ------------------------------------------
    cx0, cy0 = 216, ground[216] - 12
    for y in range(cy0, cy0 + 13):
        for x in range(cx0, min(PANO_W, cx0 + 8)):
            base = (120, 178, 66) if (x + y) % 5 else (106, 162, 58)
            px(img, x, min(PANO_H - 1, y), base)
    px(img, cx0, cy0, (96, 148, 52)); px(img, cx0 + 7, cy0, (96, 148, 52))
    _patch(img, cx0 + 1, cy0 + 2, 2, 2, (24, 38, 22))
    _patch(img, cx0 + 5, cy0 + 2, 2, 2, (24, 38, 22))
    _patch(img, cx0 + 3, cy0 + 4, 2, 3, (24, 38, 22))
    _patch(img, cx0 + 2, cy0 + 5, 1, 3, (24, 38, 22))
    _patch(img, cx0 + 5, cy0 + 5, 1, 3, (24, 38, 22))
    px(img, cx0 + 6, cy0 + 12, (88, 144, 54)); px(img, cx0 + 1, cy0 + 12, (88, 144, 54))

    return img.resize((PANO_W * PANO_SCALE, PANO_H * PANO_SCALE), Image.Resampling.NEAREST)


def sprite_parch_large(seed=71, size=64):
    """Quiet, seamless paper with broad pixel clusters and no dark scratches."""
    img = canvas(size)
    rng = random.Random(seed)
    base = PARCH["base"]
    # Wrap the coarse field so opposite edges join without a visible seam.
    grid = [[rng.randint(-4, 3) for _ in range(8)] for _ in range(8)]
    cell = size // 8
    for y in range(size):
        for x in range(size):
            gx, gy = x // cell, y // cell
            fx, fy = (x % cell) / cell, (y % cell) / cell
            top = grid[gy][gx] * (1 - fx) + grid[gy][(gx + 1) % 8] * fx
            bottom = grid[(gy + 1) % 8][gx] * (1 - fx) + grid[(gy + 1) % 8][(gx + 1) % 8] * fx
            tone = round(top * (1 - fy) + bottom * fy)
            px(img, x, y, shade(base, tone + rng.choice((0, 0, 0, 1, -1))))
    return img


def sprite_sandstone_tile() -> Image.Image:
    """Draw original low-contrast sandstone grain and broken sediment ledges.

    No reference pixels are sampled. Expand a 32px grid to whole 4px clusters
    so the UI can render this tile directly at 128px without interpolation.
    """
    rng = random.Random(239)
    img = Image.new("RGB", (32, 32), (225, 211, 164))
    grain = [(230, 217, 173), (220, 205, 156), (234, 221, 181), (215, 199, 149)]
    for _ in range(125):
        x, y = rng.randrange(32), rng.randrange(32)
        w, h = rng.choice((2, 3, 4)), rng.choice((1, 2))
        color = rng.choice(grain)
        for dy in range(h):
            for dx in range(w):
                img.putpixel(((x + dx) % 32, (y + dy) % 32), color)
    for base_y, offset in ((8, 0), (23, 4)):
        for x in range(32):
            y = base_y + ((x + offset) // 7 % 3)
            if (x + offset) % 11 < 8:
                img.putpixel((x, y), (207, 189, 137))
                img.putpixel((x, y + 1), (236, 223, 181))
    return img.resize((128, 128), Image.Resampling.NEAREST)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sprites = {
        "plank": sprite_nav_frame(WOOD),
        "plank_hover": sprite_nav_frame(WOOD_HOVER),
        "plank_active": sprite_nav_frame(WOOD_ACTIVE, pressed=True),
        "plank_tile": sprite_plank_tile(WOOD, 61),
        "plank_tile_hover": sprite_plank_tile(WOOD_HOVER, 61),
        "plank_tile_active": sprite_plank_tile(WOOD_ACTIVE, 61),
        "parch_large": sprite_parch_large(71),
        "sandstone_tile": sprite_sandstone_tile(),
        "stone_tile": sprite_stone_tile(STONE, 55),
        "stone_dark_tile": sprite_stone_tile(STONE_DARK, 56),
        "cobble_overlay": sprite_cobble_overlay(),
        "dirt_tile": sprite_dirt(51),
        "panorama": build_panorama(99),
        "green": sprite_button_green(GREEN, 7),
        "green_hover": sprite_button_green(GREEN_HOVER, 8),
        "green_active": sprite_button_green(GREEN_ACTIVE, 9),
        "blue_tile": sprite_green_tile(BLUE, 71),
        "green_tile": sprite_green_tile(GREEN_PLATE, 64),
        "green_tile_hover": sprite_green_tile(GREEN_PLATE_HOVER, 65),
        "green_tile_active": sprite_green_tile(GREEN_PLATE_ACTIVE, 66),
        "nav_grass": sprite_nav_frame(GREEN),
        "nav_grass_hover": sprite_nav_frame(GREEN_HOVER),
        "nav_grass_active": sprite_nav_frame(GREEN_ACTIVE, pressed=True),
        "nav_grass_tile": sprite_nav_grass_tile(GREEN_PLATE, 81),
        "nav_grass_tile_hover": sprite_nav_grass_tile(GREEN_PLATE_HOVER, 81),
        "nav_grass_tile_active": sprite_nav_grass_tile(GREEN_PLATE_ACTIVE, 81),
        "stone": sprite_stone_frame(STONE, 11),
        "stone_dark": sprite_stone_frame(STONE_DARK, 12),
        "stone_plain": sprite_stone_frame(STONE, 13),
        "guide_frame": sprite_nav_frame(GUIDE_STONE),
        "guide_frame_hover": sprite_nav_frame(GUIDE_STONE_HOVER),
        "tab_oak": sprite_nav_frame(TAB_OAK),
        "tab_oak_tile": sprite_plank_tile(TAB_OAK, 108),
        "birch_frame": sprite_nav_frame(BIRCH),
        "birch_tile": sprite_birch_tile(),
        "birch_carved_frame": sprite_birch_carved_frame(),
        "birch_medallion": sprite_birch_medallion(),
        "inset": sprite_inset(PARCH, 21),
        "inset_plain": sprite_inset(STONE, 22),
        "tooltip": sprite_tooltip(31),
        "dirt": sprite_dirt(51),
        "grass": sprite_green_tile(GREEN, 52),
        "titlebar_terrain": sprite_titlebar_terrain(),
        "parchment": sprite_tile(PARCH, 53),
        "scrollbar_track": sprite_tile(dict(WOOD, base=(58, 42, 28), light=(74, 54, 36), dark=(38, 27, 18)), 54),
        "scrollbar_thumb": sprite_scroll_thumb(41),
    }

    for name, img in sprites.items():
        img.save(out / f"{name}.png", optimize=True)
    print(f"wrote {len(sprites)} sprites to {out}")


if __name__ == "__main__":
    main()
