from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scripts import validate_webexcel_fonts as fonts


STYLES_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="{count}">{font_nodes}</fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>
"""


def make_workbook(path: Path, font_names: list[str]) -> None:
    nodes = "".join(f'<font><name val="{name}"/><sz val="11"/></font>' for name in font_names)
    styles = STYLES_TEMPLATE.format(count=len(font_names), font_nodes=nodes)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/styles.xml", styles)
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )


class WebExcelFontCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = fonts.load_policy()

    def test_aptos_default_passes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "share-ready.xlsx"
            make_workbook(path, ["Aptos", "Aptos Display"])
            result = fonts.inspect_workbook(path, self.policy)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["default_font"], "Aptos")
        self.assertEqual(result["violation_count"], 0)

    def test_carlito_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "regression.xlsx"
            make_workbook(path, ["Carlito"])
            result = fonts.inspect_workbook(path, self.policy)
        rules = {item["rule_id"] for item in result["violations"]}
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("WEBFONT001", rules)
        self.assertIn("WEBFONT002", rules)
        self.assertIn("WEBFONT003", rules)

    def test_non_aptos_default_fails_even_when_not_carlito(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "calibri.xlsx"
            make_workbook(path, ["Calibri"])
            result = fonts.inspect_workbook(path, self.policy)
        rules = {item["rule_id"] for item in result["violations"]}
        self.assertEqual(result["status"], "FAIL")
        self.assertNotIn("WEBFONT001", rules)
        self.assertIn("WEBFONT002", rules)
        self.assertIn("WEBFONT003", rules)

    def test_macro_enabled_container_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "share-ready.xlsm"
            make_workbook(path, ["Aptos"])
            result = fonts.inspect_workbook(path, self.policy)
        self.assertEqual(result["status"], "PASS")

    def test_source_scan_rejects_carlito_in_producer_code(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "triage").mkdir()
            (root / "triage" / "generator.py").write_text(
                'DEFAULT_FONT = "Carlito"\n', encoding="utf-8"
            )
            policy = json.loads(json.dumps(self.policy))
            policy["source_scan"] = {
                "roots": ["triage"],
                "extensions": [".py"],
                "excluded_paths": [],
            }
            with mock.patch.object(fonts, "ROOT", root):
                result = fonts.inspect_sources(policy)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["violation_count"], 1)
        self.assertEqual(result["violations"][0]["rule_id"], "WEBFONT004")

    def test_combined_report_preserves_artifact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "share-ready.xlsx"
            make_workbook(path, ["Aptos"])
            result = fonts.build_report(policy=self.policy, workbooks=[path], scan_source=False)
        self.assertEqual(result["schema"], "webexcel-font-validation-result/v1")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["artifact_count"], 1)
        self.assertEqual(len(result["artifacts"][0]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
