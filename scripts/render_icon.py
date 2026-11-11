"""Render the project's 16x16 SVG icon to a nearest-neighbour PNG."""

from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageColor, ImageDraw


root = Path(__file__).resolve().parent.parent
svg = ElementTree.parse(root / "icon.svg").getroot()
if svg.get("viewBox") != "0 0 16 16":
    raise SystemExit("Unexpected icon viewBox")
image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
for rect in svg:
    if rect.tag != "{http://www.w3.org/2000/svg}rect":
        raise SystemExit(f"Unexpected icon element: {rect.tag}")
    x, y = int(rect.get("x", "0")), int(rect.get("y", "0"))
    width, height = int(rect.get("width")), int(rect.get("height"))
    draw.rectangle((x, y, x + width - 1, y + height - 1), fill=ImageColor.getcolor(rect.get("fill"), "RGBA"))
output = root / "assets" / "icon.png"
output.parent.mkdir(parents=True, exist_ok=True)
image.resize((256, 256), Image.Resampling.NEAREST).save(output, optimize=True)
print(output)
