from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from triage.worksheet_cell_integrity import validate_worksheet_cell_integrity

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
  <sheets><sheet name="Prompt_Class_Legend" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""


def worksheet(*, dimension: str, duplicate: bool = False) -> str:
    duplicate_cell = '<c r="J4" s="47" t="inlineStr"><is><t>Color</t></is></c>' if duplicate else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="{dimension}"/>
  <sheetData>
    <row r="4"><c r="J4" s="6"/>{duplicate_cell}</row>
    <row r="100"><c r="Z100" s="7"/></row>
  </sheetData>
</worksheet>"""


def write_fixture(path: Path, *, dimension: str = "A1:Z100", duplicate: bool = False) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet(dimension=dimension, duplicate=duplicate))


class WorksheetCellIntegrityTests(unittest.TestCase):
    def test_unique_coordinates_and_covering_dimension_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "healthy.xlsx"
            write_fixture(path)
            report = validate_worksheet_cell_integrity(str(path))
            self.assertTrue(report.passed, report.render_text())
            self.assertEqual(1, report.checked_sheets)

    def test_v19_shaped_duplicate_cell_records_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.xlsx"
            write_fixture(path, duplicate=True)
            report = validate_worksheet_cell_integrity(str(path))
            self.assertFalse(report.passed)
            finding = next(item for item in report.findings if item.issue == "duplicate_cell_references")
            self.assertEqual({"J4": 2}, finding.details["coordinates"])
            self.assertEqual(1, finding.details["extra_cell_records"])

    def test_dimension_that_excludes_existing_cells_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stale-dimension.xlsx"
            write_fixture(path, dimension="A1:K23")
            report = validate_worksheet_cell_integrity(str(path))
            self.assertFalse(report.passed)
            finding = next(item for item in report.findings if item.issue == "dimension_excludes_explicit_cells")
            self.assertEqual("A1:K23", finding.details["dimension"])
            self.assertEqual((26, 100), tuple(finding.details["actual_end"]))

    def test_missing_file_fails(self) -> None:
        report = validate_worksheet_cell_integrity("missing.xlsx")
        self.assertFalse(report.passed)
        self.assertEqual("file_missing", report.findings[0].issue)


if __name__ == "__main__":
    unittest.main()
