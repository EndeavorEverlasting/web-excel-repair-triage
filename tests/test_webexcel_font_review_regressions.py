from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scripts import validate_webexcel_font_harness as harness
from scripts import validate_webexcel_fonts as fonts

STYLES = '''<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><name val="Aptos Display"/></font>
    <font><name val="Aptos"/></font>
  </fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf fontId="1" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0"/></cellStyles>
  {extra}
</styleSheet>'''


def workbook(path: Path, *, extra_styles: str = "", parts: dict[str, str] | None = None) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/styles.xml", STYLES.format(extra=extra_styles))
        archive.writestr("[Content_Types].xml", "<Types/>")
        for name, text in (parts or {}).items():
            archive.writestr(name, text)


class FontReviewRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = fonts.load_policy()

    def test_default_font_uses_normal_style_font_id(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "normal-style.xlsx"
            workbook(path)
            result = fonts.inspect_workbook(path, self.policy)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["default_font"], "Aptos")

    def test_differential_and_rich_text_fonts_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "explicit-fonts.xlsx"
            workbook(
                path,
                extra_styles='<dxfs count="1"><dxf><font><name val="Calibri"/></font></dxf></dxfs>',
                parts={
                    "xl/sharedStrings.xml": (
                        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                        '<si><r><rPr><rFont val="Carlito"/></rPr><t>x</t></r></si></sst>'
                    )
                },
            )
            result = fonts.inspect_workbook(path, self.policy)
        rules = {item["rule_id"] for item in result["violations"]}
        self.assertIn("WEBFONT001", rules)
        self.assertIn("WEBFONT003", rules)

    def test_plain_cell_text_named_carlito_is_not_a_font(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "plain-text.xlsx"
            workbook(
                path,
                parts={
                    "xl/sharedStrings.xml": (
                        '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                        '<si><t>Carlito</t></si></sst>'
                    )
                },
            )
            result = fonts.inspect_workbook(path, self.policy)
        self.assertEqual(result["status"], "PASS")

    def test_report_output_inside_repo_must_be_under_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.object(fonts, "ROOT", root), mock.patch.object(
                fonts, "OUTPUT_ROOT", root / "Outputs"
            ):
                with self.assertRaises(fonts.FontValidationError):
                    fonts._validate_output_path(root / "Candidates" / "report.json")
                allowed = fonts._validate_output_path(root / "Outputs" / "report.json")
        self.assertEqual(allowed.name, "report.json")

    def test_harness_report_output_inside_repo_must_be_under_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.object(harness, "ROOT", root), mock.patch.object(
                harness, "OUTPUT_ROOT", root / "Outputs"
            ):
                with self.assertRaises(harness.HarnessError):
                    harness._validate_output_path(root / "Active" / "report.json")


if __name__ == "__main__":
    unittest.main()
