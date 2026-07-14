from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from triage.copy_surface_bounds import inspect_copy_surface_bounds


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WORKBOOK = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="P07_COPY_SAFE" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

BOUNDED_SHEET = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="A1:A2"/>
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>EXECUTE.</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>Repo: xyz</t></is></c></row>
  </sheetData>
</worksheet>"""

BLOATED_SHEET = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="A1:A160"/>
  <sheetData>
    <row r="1"><c r="A1" t="inlineStr"><is><t>EXECUTE.</t></is></c></row>
    <row r="2"><c r="A2" t="inlineStr"><is><t>Repo: xyz</t></is></c></row>
    <row r="160"><c r="A160" s="7"/></row>
  </sheetData>
</worksheet>"""


def write_fixture(path: Path, worksheet: str) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


class CopySurfaceBoundsTests(unittest.TestCase):
    def test_bounded_surface_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bounded.xlsx"
            write_fixture(path, BOUNDED_SHEET)
            report = inspect_copy_surface_bounds(
                str(path), sheets=["P07_COPY_SAFE"], max_trailing_rows=0
            )
            self.assertTrue(report.pass_all)
            self.assertEqual("PASS", report.surfaces[0].status)
            self.assertEqual(0, report.surfaces[0].trailing_rows)

    def test_styled_blank_rows_fail_strict_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bloated.xlsx"
            write_fixture(path, BLOATED_SHEET)
            report = inspect_copy_surface_bounds(
                str(path), sheets=["P07_COPY_SAFE"], max_trailing_rows=0
            )
            self.assertFalse(report.pass_all)
            surface = report.surfaces[0]
            self.assertEqual("FAIL", surface.status)
            self.assertEqual(2, surface.last_payload_row)
            self.assertEqual(160, surface.package_end_row)
            self.assertEqual(158, surface.trailing_rows)

    def test_missing_sheet_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bounded.xlsx"
            write_fixture(path, BOUNDED_SHEET)
            report = inspect_copy_surface_bounds(str(path), sheets=["P14_COPY_SAFE"])
            self.assertFalse(report.pass_all)
            self.assertEqual(["P14_COPY_SAFE"], report.missing_sheets)

    def test_negative_allowance_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "zero or greater"):
            inspect_copy_surface_bounds("unused.xlsx", sheets=["P00_COPY_SAFE"], max_trailing_rows=-1)


if __name__ == "__main__":
    unittest.main()
