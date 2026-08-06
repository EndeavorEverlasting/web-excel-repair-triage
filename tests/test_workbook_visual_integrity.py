from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_workbook_visual_integrity as visual

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  {worksheet_overrides}
</Types>
"""
ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""


def _cell_xml(address: str, value: object, style_id: int, formula: str | None = None) -> str:
    style = f' s="{style_id}"' if style_id else ""
    if formula is not None:
        return f'<c r="{address}"{style}><f>{formula}</f><v>{value}</v></c>'
    if isinstance(value, str):
        escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'<c r="{address}"{style} t="inlineStr"><is><t>{escaped}</t></is></c>'
    return f'<c r="{address}"{style}><v>{value}</v></c>'


def build_workbook(path: Path, sheets: list[tuple[str, dict[str, tuple[object, int, str | None]]]], fills: list[str]) -> None:
    worksheet_overrides = "\n  ".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, len(sheets) + 1)
    )
    workbook_sheets = "".join(
        f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>'
        for index, (name, _) in enumerate(sheets, start=1)
    )
    workbook = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{workbook_sheets}</sheets></workbook>'''
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">""" + "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(sheets) + 1)
    ) + '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    fill_nodes = '<fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>' + "".join(
        f'<fill><patternFill patternType="solid"><fgColor rgb="{fill}"/><bgColor indexed="64"/></patternFill></fill>'
        for fill in fills
    )
    xfs = '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>' + "".join(
        f'<xf numFmtId="0" fontId="0" fillId="{index + 2}" borderId="0" xfId="0" applyFill="1"/>'
        for index in range(len(fills))
    )
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Aptos"/><family val="2"/></font></fonts>
  <fills count="{len(fills) + 2}">{fill_nodes}</fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="{len(fills) + 1}">{xfs}</cellXfs>
</styleSheet>'''
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES.format(worksheet_overrides=worksheet_overrides))
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        for index, (_, cells) in enumerate(sheets, start=1):
            rows: dict[int, list[str]] = {}
            for address, (value, style_id, formula) in cells.items():
                row = int("".join(char for char in address if char.isdigit()))
                rows.setdefault(row, []).append(_cell_xml(address, value, style_id, formula))
            row_xml = "".join(f'<row r="{row}">{"".join(sorted(items))}</row>' for row, items in sorted(rows.items()))
            sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{row_xml}</sheetData></worksheet>'''
            archive.writestr(f"xl/worksheets/sheet{index}.xml", sheet_xml)


def write_profile(path: Path, rules: list[dict], required_sheets: list[str] | None = None) -> None:
    payload = {
        "schema": "workbook-visual-profile/v1",
        "profile_id": "fixture/v1",
        "artifact_family": "fixture",
        "scope": "fixture semantic workbook",
        "filename_patterns": ["fixture\\.xlsx"],
        "required_sheets": required_sheets or ["Main"],
        "artifact_specific_roles": {
            "documentation": "FFE7E6E6",
            "cleanup_disposal": "FFF0F1F2",
            "go_live_support": "FFD9EAF7"
        },
        "exceptions": [],
        "rules": rules,
        "generator_binding": {
            "required": True,
            "manifest_fields": [
                "visual_profile_id", "visual_policy_sha256", "visual_validation_result",
                "artifact_sha256", "font_validation_result", "operator_excel_for_web_status"
            ]
        },
        "proof_ceiling": "fixture proof"
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class WorkbookVisualIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workbook = self.root / "fixture.xlsx"
        self.profile = self.root / "profile.json"
        self.fills = ["FFD9E1F2", "FFE2F0D9", "FFFCE4D6", "FFFFF2CC"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_semantic_rows_and_paired_ranges_pass(self) -> None:
        main = {"A2": ("Configuration 8h", 1, None), "B2": (8, 1, None), "A3": ("Inventory 8h", 2, None), "B3": (8, 2, None)}
        summary = {"A2": ("Configuration", 1, None), "B2": (8, 1, None), "D2": ("Configuration", 1, None), "A3": ("Inventory", 2, None), "B3": (8, 2, None), "D3": ("Inventory", 2, None)}
        build_workbook(self.workbook, [("Main", main), ("Summary", summary)], self.fills)
        write_profile(self.profile, [
            {"id": "T1", "type": "semantic_rows", "sheet": "Main", "rows": [2, 3], "label_column": "A", "style_columns": ["A", "B"], "match_mode": "prefix", "mappings": [{"token": "Configuration", "role": "configuration"}, {"token": "Inventory", "role": "inventory_management"}]},
            {"id": "T2", "type": "paired_range_fill", "sheet": "Summary", "left_range": "A2:B3", "right_range": "D2:D3", "compare": "row_fill"}
        ], ["Main", "Summary"])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertEqual(report["status"], "PASS")

    def test_semantic_color_mismatch_fails(self) -> None:
        build_workbook(self.workbook, [("Main", {"A2": ("Configuration 8h", 2, None), "B2": (8, 2, None)})], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "semantic_rows", "sheet": "Main", "rows": [2, 2], "label_column": "A", "style_columns": ["A", "B"], "match_mode": "prefix", "mappings": [{"token": "Configuration", "role": "configuration"}]}])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertIn("WVI003", {item["rule_id"] for item in report["violations"]})

    def test_same_key_style_divergence_catches_one_wrong_row(self) -> None:
        main = {"A2": (1, 3, None), "B2": ("first", 3, None), "A3": (1, 2, None), "B3": ("second", 2, None)}
        build_workbook(self.workbook, [("Main", main)], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "same_key_style", "sheet": "Main", "rows": [2, 3], "key_column": "A", "style_columns": ["A", "B"], "attributes": ["fill"], "contiguous": True}])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertIn("WVI004", {item["rule_id"] for item in report["violations"]})

    def test_range_boundary_bleed_fails(self) -> None:
        main = {"A2": ("inside", 3, None), "B2": (1, 3, None), "A3": ("outside", 3, None), "B3": (1, 3, None)}
        build_workbook(self.workbook, [("Main", main)], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "range_fill", "sheet": "Main", "range": "A2:B2", "expected_fill": "FFFCE4D6"}, {"id": "T2", "type": "boundary", "sheet": "Main", "range": "A2:B2", "expected_fill": "FFFCE4D6", "edges": ["bottom"]}])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertIn("WVI005", {item["rule_id"] for item in report["violations"]})

    def test_paired_range_mismatch_fails(self) -> None:
        summary = {"A2": ("Configuration", 1, None), "B2": (8, 1, None), "D2": ("Configuration", 2, None)}
        build_workbook(self.workbook, [("Main", {}), ("Summary", summary)], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "paired_range_fill", "sheet": "Summary", "left_range": "A2:B2", "right_range": "D2:D2", "compare": "row_fill"}], ["Main", "Summary"])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertIn("WVI006", {item["rule_id"] for item in report["violations"]})

    def test_style_only_baseline_rejects_value_and_formula_drift(self) -> None:
        baseline = self.root / "baseline.xlsx"
        build_workbook(baseline, [("Main", {"A2": (1, 1, None), "B2": (2, 1, "A2+1")})], self.fills)
        build_workbook(self.workbook, [("Main", {"A2": (9, 1, None), "B2": (3, 1, "A2+2")})], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "style_only_baseline", "preserve": ["sheet_order", "cell_values", "formulas", "merged_ranges"]}])
        report = visual.validate_workbook(self.workbook, self.profile, baseline)
        reasons = {item.get("reason") for item in report["violations"] if item["rule_id"] == "WVI007"}
        self.assertIn("cell_value_changed", reasons)
        self.assertIn("formula_changed", reasons)

    def test_report_does_not_echo_private_cell_text(self) -> None:
        secret = "PRIVATE PERSON-SPECIFIC NOTE"
        build_workbook(self.workbook, [("Main", {"A2": (secret, 2, None)})], self.fills)
        write_profile(self.profile, [{"id": "T1", "type": "range_fill", "sheet": "Main", "range": "A2:A2", "expected_fill": "FFD9E1F2"}])
        report = visual.validate_workbook(self.workbook, self.profile)
        self.assertNotIn(secret, json.dumps(report))


if __name__ == "__main__":
    unittest.main()
