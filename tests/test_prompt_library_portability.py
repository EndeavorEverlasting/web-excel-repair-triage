from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from triage.prompt_library_portability import (
    LINK_COLUMNS,
    select_sparse_navigation_cadence,
    validate_prompt_library_workbook,
)

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def inline_cell(reference: str, value: str) -> str:
    return (
        f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    )


def worksheet_xml(
    rows: dict[int, dict[str, str]], hyperlinks: dict[str, str]
) -> str:
    row_xml = []
    for number in sorted(rows):
        cells = "".join(
            inline_cell(f"{column}{number}", value)
            for column, value in sorted(rows[number].items())
        )
        row_xml.append(f'<row r="{number}">{cells}</row>')
    links = "".join(
        f'<hyperlink ref="{reference}" location="{escape(location)}"/>'
        for reference, location in sorted(hyperlinks.items())
    )
    hyperlink_xml = f"<hyperlinks>{links}</hyperlinks>" if links else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{MAIN_NS}" xmlns:r="{REL_NS}">'
        f'<sheetData>{"".join(row_xml)}</sheetData>{hyperlink_xml}</worksheet>'
    )


def build_fixture(
    path: Path,
    *,
    prompt_count: int = 10,
    remove_link: str | None = None,
    drift_link: str | None = None,
    wrong_end_prompt: str | None = None,
    dense_navigation_row: int | None = None,
) -> None:
    library_rows: dict[int, dict[str, str]] = {
        1: {
            "A": "Top",
            "B": "Seq",
            "C": "Prompt ID",
            "O": "Copy-Safe Sheet",
            "P": "Bottom",
        }
    }
    library_links: dict[str, str] = {}
    sheet_names = ["Prompt_Library"]
    sheet_parts = ["worksheets/sheet1.xml"]

    cadence = None
    try:
        cadence = select_sparse_navigation_cadence(prompt_count)
    except ValueError:
        pass

    for ordinal in range(1, prompt_count + 1):
        row = ordinal + 1
        prompt_id = f"P{ordinal - 1:02d}"
        sheet_name = f"{prompt_id}_COPY_SAFE"
        sheet_names.append(sheet_name)
        sheet_parts.append(f"worksheets/sheet{ordinal + 1}.xml")
        library_rows[row] = {column: f"{prompt_id}-{column}" for column in LINK_COLUMNS}
        library_rows[row]["C"] = prompt_id
        library_rows[row]["O"] = sheet_name
        target_end = 4 if wrong_end_prompt == prompt_id else 3
        target = f"'{sheet_name}'!A1:A{target_end}"
        for column in LINK_COLUMNS:
            reference = f"{column}{row}"
            library_links[reference] = target
        if drift_link == prompt_id:
            library_links[f"N{row}"] = f"'{sheet_name}'!A1:A2"
        if cadence and (ordinal - 1) % cadence == 0:
            library_links[f"A{row}"] = "Prompt_Library!A1"
            library_links[f"P{row}"] = f"Prompt_Library!P{prompt_count + 1}"

    if remove_link:
        library_links.pop(remove_link, None)
    if dense_navigation_row:
        library_links[f"A{dense_navigation_row}"] = "Prompt_Library!A1"
        library_links[f"P{dense_navigation_row}"] = (
            f"Prompt_Library!P{prompt_count + 1}"
        )

    workbook_sheets = []
    workbook_relationships = []
    overrides = []
    for index, (name, target) in enumerate(zip(sheet_names, sheet_parts), start=1):
        workbook_sheets.append(
            f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        )
        workbook_relationships.append(
            f'<Relationship Id="rId{index}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="{target}"/>'
        )
        overrides.append(
            f'<Override PartName="/xl/{target}" '
            f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{MAIN_NS}" xmlns:r="{REL_NS}">'
        f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG_REL_NS}">'
        f'{"".join(workbook_relationships)}</Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f'{"".join(overrides)}</Types>'
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            worksheet_xml(library_rows, library_links),
        )
        for ordinal in range(1, prompt_count + 1):
            prompt_rows = {
                1: {"A": f"P{ordinal - 1:02d}"},
                2: {"A": "Prompt body"},
                3: {"A": "Closeout"},
            }
            archive.writestr(
                f"xl/worksheets/sheet{ordinal + 1}.xml",
                worksheet_xml(prompt_rows, {}),
            )


class PromptLibraryPortabilityTests(unittest.TestCase):
    def test_cadence_selects_largest_allowed_divisor_and_fails_closed(self) -> None:
        self.assertEqual(select_sparse_navigation_cadence(60), 10)
        self.assertEqual(select_sparse_navigation_cadence(30), 10)
        self.assertEqual(select_sparse_navigation_cadence(14), 2)
        with self.assertRaises(ValueError):
            select_sparse_navigation_cadence(13)

    def test_valid_workbook_enforces_b_to_o_and_sparse_a_p(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "valid.xlsx"
            build_fixture(path)
            report = validate_prompt_library_workbook(path)
        self.assertTrue(report.valid, report.to_dict())
        self.assertEqual(report.prompt_count, 10)
        self.assertEqual(report.cadence, 10)
        self.assertEqual(report.findings, [])

    def test_missing_row_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing-link.xlsx"
            build_fixture(path, remove_link="H2")
            report = validate_prompt_library_workbook(path)
        self.assertFalse(report.valid)
        self.assertIn("PROMPT_ROW_LINK_MISSING", {item.code for item in report.findings})

    def test_mixed_target_and_inexact_copy_range_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "drift.xlsx"
            build_fixture(path, drift_link="P00", wrong_end_prompt="P01")
            report = validate_prompt_library_workbook(path)
        codes = {item.code for item in report.findings}
        self.assertIn("PROMPT_ROW_LINK_DRIFT", codes)
        self.assertIn("PROMPT_COPY_RANGE_NOT_EXACT", codes)

    def test_dense_navigation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dense.xlsx"
            build_fixture(path, dense_navigation_row=3)
            report = validate_prompt_library_workbook(path)
        self.assertFalse(report.valid)
        self.assertIn(
            "SPARSE_NAVIGATION_DENSITY_DRIFT",
            {item.code for item in report.findings},
        )

    def test_prompt_count_without_allowed_cadence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "thirteen.xlsx"
            build_fixture(path, prompt_count=13)
            report = validate_prompt_library_workbook(path)
        self.assertFalse(report.valid)
        self.assertIsNone(report.cadence)
        self.assertIn("SPARSE_CADENCE_UNAVAILABLE", {item.code for item in report.findings})


if __name__ == "__main__":
    unittest.main()
