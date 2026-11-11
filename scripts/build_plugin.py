"""Build the Minecraft skin bundle's client module.

Inlines PNG/SVG ``url(sprites/*)`` assets in ``skin/skin.css`` and the alias-token
overrides in ``skin/tokens.mc.json`` into the bundle's ``client.js``.

Run:  python scripts/build_plugin.py
"""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIN = ROOT / "skin"
PLUGIN = ROOT
SPRITE_REF = re.compile(r"url\(sprites/([A-Za-z0-9_-]+\.(?:png|svg))\)")
DATA_IMAGE = re.compile(r"url\(data:image/[a-z+]+;base64,[A-Za-z0-9+/=]+\)")
HOST_CLASSES = SKIN / "host-classes.dsh-0.2.2-rc.1-linux.json"
CLASS_SELECTOR = re.compile(r'\[class([~*])="([^"]+)"\]')


def inline_sprites(css: str) -> str:
    missing = []
    cache: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in cache:
            path = SKIN / "sprites" / name
            if not path.is_file():
                missing.append(name)
                return match.group(0)
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
            cache[name] = f"url(data:{mime};base64,{data})"
        return cache[name]

    out = SPRITE_REF.sub(replace, css)
    if missing:
        raise SystemExit(f"missing sprites: {', '.join(sorted(set(missing)))}")
    return dedupe_images(out)


def dedupe_images(css: str) -> str:
    """Hoist every repeated inline image into one :root custom property.

    The same texture is referenced dozens of times (a sprite used by ten panels
    would otherwise carry its base64 payload ten times). Each unique payload is
    declared once on :root and referenced through var(), which keeps the pixels
    byte-identical while removing the repeated copies from the shipped bundle.
    """
    counts: dict[str, int] = {}
    for match in DATA_IMAGE.findall(css):
        counts[match] = counts.get(match, 0) + 1
    repeated = {uri: n for uri, n in counts.items() if n > 1}
    if not repeated:
        return css
    names = {uri: f"--mc-img-{i}" for i, uri in enumerate(repeated)}
    for uri, name in names.items():
        css = css.replace(uri, f"var({name})")
    header = ":root{" + ";".join(f"{name}:{uri}" for uri, name in names.items()) + "}\n"
    return header + css


IMPORT_REF = re.compile(r'@import\s+"([^"]+)"\s*;')


def read_skin_css(path: Path | None = None) -> str:
    """Resolve the import-only entry into one stylesheet, preserving bytes.

    skin/skin.css is the single entry and holds only @import lines; the rules
    live in skin/src/. Parts are joined with a newline, which is exactly how the
    pre-split file was concatenated, so the shipped CSS is byte-identical.
    """
    entry = path or (SKIN / "skin.css")
    text = entry.read_text(encoding="utf-8")
    imports = IMPORT_REF.findall(text)
    if not imports:
        return text
    remainder = re.sub(r"/\*.*?\*/", "", IMPORT_REF.sub("", text), flags=re.S).strip()
    if remainder:
        raise SystemExit(f"{entry} mixes @import with rules; keep the entry import-only")
    return "\n".join(read_skin_css((entry.parent / name).resolve()) for name in imports)


def add_host_compat(css: str) -> str:
    """Preserve desktop selectors and add verified Linux Web class exports.

    The two DSH builds use different CSS-module hashes even at the same version.
    :is() preserves the original selector specificity and declaration order.
    Native/generic substring selectors remain untouched; for module-specific
    fragments the additional branches match only exported class tokens.
    """
    classes = json.loads(HOST_CLASSES.read_text(encoding="utf-8"))["classes"]

    def replace(match: re.Match[str]) -> str:
        operator, source = match.groups()
        if operator == "~":
            targets = [classes[source]] if source in classes else []
        elif source.startswith("_"):
            # Generic semantic suffixes (e.g. _selector or _image) already
            # match in both builds; do not widen their scope to unrelated UI.
            targets = []
        else:
            targets = sorted({target for old, target in classes.items() if source in old})
        if not targets:
            return match.group(0)
        return ":is(" + ",".join([match.group(0), *(f'[class~="{target}"]' for target in targets)]) + ")"

    return CLASS_SELECTOR.sub(replace, css)


def render_client() -> str:
    css = inline_sprites(add_host_compat(read_skin_css()))
    pixel_css = SKIN / "pixel-font.css"
    if pixel_css.is_file():
        css = css + "\n" + pixel_css.read_text(encoding="utf-8")

    raw = json.loads((SKIN / "tokens.mc.json").read_text(encoding="utf-8"))
    tokens = {name: {"light": value, "dark": value} for name, value in raw["tokens"].items()}

    template = (PLUGIN / "client.template.js").read_text(encoding="utf-8")
    if "__CSS__" not in template or "__TOKENS__" not in template:
        raise SystemExit("client.template.js lost its __CSS__ / __TOKENS__ placeholders")

    # Split the placeholders so a stray "__" in content cannot be re-substituted.
    head, rest = template.split("__CSS__", 1)
    mid, tail = rest.split("__TOKENS__", 1)
    return head + json.dumps(css, ensure_ascii=False) + mid + json.dumps(tokens, ensure_ascii=False) + tail


def build(check: bool = False) -> None:
    client = render_client()
    target = PLUGIN / "client.js"
    if check:
        if not target.is_file() or target.read_text(encoding="utf-8") != client:
            raise SystemExit("client.js is stale; run scripts/build_plugin.py")
        print("client.js is up to date")
        return
    target.write_text(client, encoding="utf-8", newline="\n")
    print(f"client.js  {len(client.encode('utf-8')):,} bytes")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify the bundle without writing files")
    args = ap.parse_args()
    build(check=args.check)


if __name__ == "__main__":
    main()
