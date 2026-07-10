from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from triage.workbook_package_hygiene import validate_workbook_package


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/tables/table1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="COPY_SAFE" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

SHEET_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdTable1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" Target="../tables/table1.xml"/>
</Relationships>"""

GOOD_SHEET = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="A1:B2"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>Prompt</t></is></c><c r="B1" t="inlineStr"><is><t>Class</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>EXECUTE THE REPO SPRINT.</t></is></c><c r="B2" t="inlineStr"><is><t>BUILD</t></is></c></row>
  </sheetData>
  <tableParts count="1"><tablePart r:id="rIdTable1"/></tableParts>
</worksheet>"""

GOOD_TABLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" id="1" name="CopySafe" displayName="CopySafe" ref="A1:B2" headerRowCount="1">
  <autoFilter ref="A1:B2"/>
  <tableColumns count="2"><tableColumn id="1" name="Prompt"/><tableColumn id="2" name="Class"/></tableColumns>
  <tableStyleInfo name="TableStyleMedium2" showFirstColumn="0" showLastColumn="0" showRowStripes="1" showColumnStripes="0"/>
</table>"""

BROKEN_SHEET = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>PASTE THIS DIRECTLY INTO THE AGENT CHAT.&#10;EXECUTE THE REPO SPRINT.</t></is></c></row>
  </sheetData>
  <mergeCells count="2"><mergeCell ref="A1:B1"/><mergeCell ref="A1:C1"/></mergeCells>
  <tableParts count="1"><tablePart r:id="rIdTable1"/></tableParts>
</worksheet>"""

BROKEN_TABLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<table xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" id="1" name="CopySafe" displayName="CopySafe" ref="A1:B2" headerRowCount="1">
  <autoFilter ref="A1:C2"/>
  <tableColumns count="1"><tableColumn id="1" name="Wrong"/></tableColumns>
</table>"""


def write_fixture(path: Path, *, broken: bool = False) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("xl/workbook.xml", WORKBOOK)
        z.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        z.writestr("xl/worksheets/sheet1.xml", BROKEN_SHEET if broken else GOOD_SHEET)
        z.writestr("xl/worksheets/_rels/sheet1.xml.rels", SHEET_RELS)
        z.writestr("xl/tables/table1.xml", BROKEN_TABLE if broken else GOOD_TABLE)


class WorkbookPackageHygieneTests(unittest.TestCase):
    def test_healthy_fixture_passes_package_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "healthy.xlsx"
            write_fixture(path)
            report = validate_workbook_package(
                str(path),
                expected_freeze_sheets=["COPY_SAFE"],
            )
            self.assertTrue(report.package_valid, report.render_text())
            self.assertFalse(report.failures)

    def test_broken_fixture_reports_table_merge_freeze_and_copy_surface_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.xlsx"
            write_fixture(path, broken=True)
            report = validate_workbook_package(
                str(path),
                expected_freeze_sheets=["COPY_SAFE"],
                copy_surface_sheets=["COPY_SAFE"],
            )
            by_name = {check.name: check for check in report.checks}
            self.assertFalse(report.package_valid)
            self.assertEqual("FAIL", by_name["table refs and filters"].status)
            self.assertEqual("FAIL", by_name["table column counts"].status)
            self.assertEqual("FAIL", by_name["visible headers match table XML"].status)
            self.assertEqual("FAIL", by_name["merge ranges non-overlapping"].status)
            self.assertEqual("FAIL", by_name["freeze panes"].status)
            self.assertEqual("WARN", by_name["copy-surface package shape"].status)
            findings = by_name["copy-surface package shape"].findings
            issues = {item["issue"] for item in findings}
            self.assertIn("multiline_cells_risk_wrapper_quotes", issues)
            self.assertIn("guidance_contaminates_payload", issues)
            self.assertEqual("manual_test_required", report.clipboard_acceptance)

    def test_missing_file_is_a_failure(self) -> None:
        report = validate_workbook_package("definitely-missing.xlsx")
        self.assertFalse(report.package_valid)
        self.assertEqual("file exists", report.failures[0].name)


if __name__ == "__main__":
    unittest.main()
