from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import validate_webexcel_font_harness as harness

ROOT = Path(__file__).resolve().parents[1]


class WebExcelFontHarnessTests(unittest.TestCase):
    def test_complete_harness_passes(self) -> None:
        result = harness.validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["default_font"], "Aptos")
        self.assertIn("Carlito", result["forbidden_fonts"])

    def test_registry_connects_every_component(self) -> None:
        registry = json.loads(
            (ROOT / "harness" / "webexcel-fonts" / "registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(registry["schema"], "webexcel-font-harness/v1")
        for path in registry["components"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual(
            registry["artifacts"]["validation_report"]["default_path"],
            "Outputs/webexcel-font-validation.json",
        )

    def test_root_manifest_registers_font_domain(self) -> None:
        manifest = json.loads(
            (ROOT / "harness" / "manifest.v1.json").read_text(encoding="utf-8")
        )
        domain = manifest["domain_contracts"]["webexcel_font_compatibility"]
        self.assertEqual(domain["policy"], "configs/webexcel_fonts_v1.json")
        self.assertEqual(domain["default_font"], "Aptos")
        self.assertEqual(domain["validator"], "scripts/validate_webexcel_fonts.py")

    def test_hooks_enforce_font_contract(self) -> None:
        for relative in (".githooks/pre-commit", ".githooks/pre-push"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("validate_webexcel_font_harness.py", text)
            self.assertIn("validate_webexcel_fonts.py --scan-source", text)


if __name__ == "__main__":
    unittest.main()
