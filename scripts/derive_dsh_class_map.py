"""Compare two installed DSH client builds using their CSS-module exports.

Usage: python scripts/derive_dsh_class_map.py OLD_NODE_MODULES NEW_NODE_MODULES
The JSON report is written to stdout. Both inputs are the @deepseek-ai directory.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


OBJECT = re.compile(r"var\s+([\w$]+_module_css_default)\s*=\s*\{(.*?)\n\s*\};", re.S)
PAIR = re.compile(r'"([^"\n]+)"\s*:\s*"([^"\n]+)"')


def read_modules(root: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    result = {}
    for path in sorted(root.glob("dsh-*/lib/client*.js")):
        text = path.read_text(encoding="utf-8")
        for match in OBJECT.finditer(text):
            key = (path.parent.parent.name, path.name, match.group(1))
            if key in result:
                raise ValueError(f"duplicate CSS module export: {key}")
            result[key] = dict(PAIR.findall(match.group(2)))
    return result


def main() -> None:
    old, new = (read_modules(Path(path)) for path in sys.argv[1:3])
    candidates: dict[str, set[str]] = {}
    modules = {}
    for module in old.keys() & new.keys():
        before, after = old[module], new[module]
        entries = {before[k]: after[k] for k in before.keys() & after.keys() if before[k] != after[k]}
        if entries:
            modules["/".join(module)] = len(entries)
        for source, target in entries.items():
            candidates.setdefault(source, set()).add(target)
    conflicts = {k: sorted(v) for k, v in candidates.items() if len(v) != 1}
    mappings = {k: next(iter(v)) for k, v in candidates.items() if len(v) == 1}
    print(json.dumps({"classes": dict(sorted(mappings.items())), "conflicts": conflicts,
                      "modules": dict(sorted(modules.items())), "old_modules": len(old),
                      "new_modules": len(new)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
