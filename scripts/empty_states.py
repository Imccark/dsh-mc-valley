#!/usr/bin/env python3
"""Original pixel-art empty-state scenes for the Minecraft skin (C12).

Three 110x100 scenes share one palette, one upper-left light and one pixel
density with skin/sprites/valley_day.png: moss/olive greens, warm cream, stone,
dirt and sky. Every pixel is drawn here with flat fills and 1px ink outlines -
no Mojang asset is copied and no photo/3D render is involved. Background is
transparent so the scenes sit on any panel colour the host uses.

  empty-campfire.png  -> olCj9W_emptyIllustration (automation list empty)
  empty-chest.png     -> m2i3Fa_empty               (plugin market empty)
  empty-signpost.png  -> GAkraW_emptyState          (workspace empty)
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "skin" / "sprites"
W, H = 110, 100

P = {
    "ink": (32, 26, 18),
    "grass": (102, 154, 26),
    "grass_d": (78, 122, 18),
    "grass_l": (130, 181, 58),
    "dirt": (138, 98, 56),
    "dirt_d": (92, 61, 34),
    "stone": (201, 191, 168),
    "stone_d": (154, 143, 120),
    "stone_l": (222, 214, 194),
    "cream": (242, 233, 207),
    "paper": (253, 243, 220),
    "wood": (168, 118, 66),
    "wood_d": (110, 74, 40),
    "char": (42, 32, 24),
    "ember": (240, 177, 60),
    "ember_d": (176, 96, 32),
    "flower_r": (196, 74, 62),
    "flower_w": (250, 246, 232),
    "flower_y": (232, 196, 78),
    "shadow": (0, 0, 0, 40),
}


class Scene:
    def __init__(self, seed: int) -> None:
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.rnd = random.Random(seed)

    def rect(self, x0, y0, x1, y1, key):
        color = key if isinstance(key, tuple) else P[key]
        self.d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=color)

    def dither(self, x0, y0, x1, y1, key, density=5):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if self.rnd.randrange(density) == 0:
                    self.d.point((x, y), fill=P[key])

    def mound(self, cx, cy, rx, ry, key="grass", shade="grass_d", light="grass_l"):
        """Flat pixel mound: solid fill, dark bottom band, light top band.

        C12: the first pass sprinkled random single pixels over the mound, which
        read as dirt/noise at 110x100. The bands alone give the form, so the
        dither is gone and every remaining pixel belongs to a shape.
        """
        self.d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=P[key])
        # bottom shade
        self.d.ellipse([cx - rx, cy - ry + ry * 0.55, cx + rx, cy + ry], fill=P[shade])
        # top light
        self.d.ellipse([cx - rx * 0.82, cy - ry, cx + rx * 0.55, cy - ry * 0.15], fill=P[light])

    def stone(self, x, y, w, h):
        self.d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=2, fill=P["stone"])
        self.d.line([x + 1, y + h - 2, x + w - 2, y + h - 2], fill=P["stone_d"])
        self.d.line([x + 1, y + 1, x + w - 3, y + 1], fill=P["stone_l"])

    def outline(self, color="ink"):
        src = self.im.load()
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dst = out.load()
        solid = {(x, y) for y in range(H) for x in range(W) if src[x, y][3] > 120}
        for (x, y) in solid:
            dst[x, y] = src[x, y]
        ink = (*P[color], 255)
        for (x, y) in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in solid:
                    if dst[nx, ny][3] == 0:
                        dst[nx, ny] = ink
        self.im = out
        self.d = ImageDraw.Draw(out)


def shadow(scene: Scene, cx: int, cy: int, rx: int, ry: int) -> None:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=P["shadow"])
    scene.im.alpha_composite(layer)
    scene.d = ImageDraw.Draw(scene.im)


def campfire() -> Image.Image:
    """A doused fire pit: stone ring, charred logs, one standing dead torch."""
    s = Scene(11)
    shadow(s, 55, 92, 38, 6)
    s.mound(55, 89, 40, 9)
    # standing dead torch behind the pit
    s.rect(51, 32, 59, 80, "wood_d")
    s.d.line([52, 34, 52, 78], fill=P["wood"])
    s.rect(49, 24, 61, 36, "char")
    for (x, y) in ((52, 27), (57, 30), (55, 25)):
        s.d.point((x, y), fill=(70, 54, 40))
    # ash bed and crossed logs
    s.d.ellipse([30, 76, 80, 94], fill=P["char"])
    s.d.polygon([(32, 88), (74, 76), (76, 82), (34, 94)], fill=P["wood_d"])
    s.d.line([34, 87, 74, 76], fill=P["wood"])
    s.d.polygon([(34, 74), (72, 90), (70, 96), (32, 80)], fill=P["char"])
    s.d.line([36, 76, 70, 90], fill=(70, 54, 40))
    # a few embers stay grouped in one small cluster instead of random dots
    s.rect(46, 84, 50, 86, "ember")
    s.rect(58, 86, 61, 88, "ember")
    s.rect(64, 82, 66, 83, "ember_d")
    # stone ring
    ring = [(10, 82, 11, 8), (22, 76, 11, 8), (37, 72, 11, 8), (55, 71, 11, 8),
            (71, 74, 11, 8), (84, 80, 11, 8), (64, 91, 11, 8), (30, 92, 11, 8)]
    for (x, y, w, h) in ring:
        s.stone(x, y, w, h)
    # green sprout beside the dead torch
    s.d.line([62, 84, 62, 74], fill=P["grass_d"])
    for (x, y) in ((60, 78), (59, 77), (64, 76), (65, 75)):
        s.d.point((x, y), fill=P["grass"])
    s.d.point((61, 72), fill=P["grass_l"])
    s.outline()
    return s.im

def chest() -> Image.Image:
    """An open chest with nothing inside, tall grass around it."""
    s = Scene(23)
    shadow(s, 55, 92, 30, 5)
    s.mound(55, 90, 34, 8)
    # tall grass tufts
    for (x, top) in ((24, 46), (28, 54), (33, 62), (80, 50), (85, 58), (76, 64)):
        s.d.line([x, 88, x, top], fill=P["grass_d"])
        s.d.point((x, top), fill=P["grass"])
        s.d.point((x - 1, top + 3), fill=P["grass_l"])
    # body
    s.rect(28, 52, 84, 90, "wood")
    s.rect(28, 52, 84, 60, "wood_d")
    s.rect(32, 60, 80, 88, P["char"])
    s.rect(35, 62, 77, 86, (52, 40, 30))
    # open lid hinged at the back rim
    s.d.polygon([(26, 28), (86, 24), (88, 52), (28, 56)], fill=P["wood"])
    s.d.polygon([(28, 30), (86, 26), (87, 36), (29, 40)], fill=P["cream"])
    s.d.line([29, 40, 87, 36], fill=P["dirt_d"])
    s.d.line([30, 47, 88, 43], fill=P["wood_d"])
    # iron corners and lock plate
    for (x, y) in ((28, 52), (76, 52), (28, 80), (76, 80)):
        s.rect(x, y, x + 8, y + 10, "stone_d")
        s.rect(x + 1, y + 1, x + 7, y + 3, "stone")
    s.rect(50, 60, 64, 74, "stone_d")
    s.rect(52, 62, 62, 67, "stone")
    s.d.point((56, 70), fill=P["ink"])
    s.d.point((57, 71), fill=P["ink"])
    for y in (64, 70, 76, 82):
        s.d.line([30, y, 82, y], fill=P["wood_d"])
    for (x, y) in ((40, 66), (70, 76), (60, 82)):
        s.d.point((x, y), fill=P["stone_l"])
    s.outline()
    return s.im

def signpost() -> Image.Image:
    """A blank signpost on a flowered mound."""
    s = Scene(37)
    shadow(s, 55, 94, 32, 5)
    s.mound(55, 90, 38, 9)
    # post
    s.rect(49, 30, 61, 90, "wood")
    s.d.line([51, 32, 51, 88], fill=P["cream"])
    s.d.line([59, 32, 59, 88], fill=P["wood_d"])
    # two blank planks
    s.d.polygon([(18, 30), (90, 26), (92, 44), (20, 48)], fill=P["paper"])
    s.d.polygon([(18, 30), (90, 26), (90, 34), (19, 38)], fill=P["cream"])
    s.d.line([20, 47, 91, 43], fill=P["dirt_d"])
    s.d.polygon([(24, 52), (84, 49), (85, 65), (25, 68)], fill=P["paper"])
    s.d.line([25, 67, 84, 64], fill=P["dirt_d"])
    for (x, y) in ((26, 33), (84, 30), (30, 58), (79, 55)):
        s.d.point((x, y), fill=P["ink"])
    for (x, y, k) in ((26, 82, "flower_r"), (34, 88, "flower_w"), (74, 84, "flower_y"), (82, 90, "flower_w")):
        s.d.point((x, y), fill=P[k])
        s.d.point((x, y + 1), fill=P["grass_d"])
    # three deliberate grass tufts instead of a random dotted line
    for x in (24, 46, 86):
        s.rect(x, 90, x + 1, 92, "grass_d")
    s.outline()
    return s.im

def trim(im: Image.Image) -> Image.Image:
    """Crop to the drawn pixels, then put the subject back on a 110-wide canvas
    with its ground line near the bottom, so all three scenes share one density
    and one baseline inside the host's 110x100 slot."""
    box = im.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    subject = im.crop((max(0, x0 - 2), max(0, y0 - 2), min(W, x1 + 2), min(H, y1 + 2)))
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - subject.width) // 2
    y = 96 - subject.height
    canvas.alpha_composite(subject, (x, max(0, y)))
    return canvas

SCENES = {"campfire": campfire, "chest": chest, "signpost": signpost}


def contact_sheet() -> Image.Image:
    cols = 3
    pad = 8
    sheet = Image.new("RGBA", (cols * W + pad * (cols + 1), H + pad * 2), (242, 233, 207, 255))
    for i, name in enumerate(SCENES):
        sheet.alpha_composite(SCENES[name](), (pad + i * (W + pad), pad))
    return sheet


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--sheet", type=Path, default=ROOT / "skin" / "build" / "empty-states-contact.png")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, fn in SCENES.items():
        trim(fn()).save(args.out / f"empty-{name}.png")
    args.sheet.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet().save(args.sheet)
    print(f"{len(SCENES)} scenes -> {args.out}")
    print(f"contact sheet -> {args.sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
