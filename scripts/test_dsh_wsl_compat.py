"""Regression checks for the two verified DSH 0.2.2-rc.1 CSS builds."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from build_plugin import HOST_CLASSES, add_host_compat, read_skin_css
from derive_dsh_class_map import read_modules


class DshWebCompatibility(unittest.TestCase):
    def test_exact_classes_keep_desktop_and_linux_branches(self) -> None:
        result = add_host_compat('[class~="wtg9ga_newSession"] { color: red; }')
        self.assertEqual(
            result,
            ':is([class~="wtg9ga_newSession"],[class~="hHd-Xa_newSession"]) { color: red; }',
        )

    def test_partial_module_selector_includes_only_exported_targets(self) -> None:
        result = add_host_compat('[class*="q_sidebarCol"] { background: red; }')
        self.assertIn('[class*="q_sidebarCol"]', result)
        self.assertIn('[class~="pI_x6G_sidebarCol"]', result)
        self.assertNotIn('[class*="pI_x6G_"]', result)

    def test_generic_and_unknown_selectors_do_not_expand(self) -> None:
        css = '[class*="_selector"] [class~="unknown_component"] { color: red; }'
        self.assertEqual(add_host_compat(css), css)

    def test_source_contains_original_and_linux_main_surface_selectors(self) -> None:
        css = add_host_compat(read_skin_css())
        for token in (
            'class~="pI_x6G_frame"', 'class~="pI_x6G_sidebarCol"',
            'class~="hHd-Xa_newSession"', 'class~="uV2eYG_card"',
            'class*="q_frame"', 'class~="wtg9ga_newSession"',
        ):
            self.assertIn(token, css)

    @unittest.skipUnless(os.environ.get("DSH_LINUX_NODE_MODULES"), "requires installed Linux DSH modules")
    def test_targets_exist_in_installed_linux_build(self) -> None:
        root = Path(os.environ["DSH_LINUX_NODE_MODULES"])
        exports = read_modules(root)
        available = {value for module in exports.values() for value in module.values()}
        mapping = json.loads(HOST_CLASSES.read_text(encoding="utf-8"))["classes"]
        missing = set(mapping.values()) - available
        self.assertFalse(missing, f"mapped classes absent from installed DSH: {sorted(missing)[:20]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
