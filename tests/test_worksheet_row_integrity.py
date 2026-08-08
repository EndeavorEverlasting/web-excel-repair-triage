from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from triage.worksheet_row_integrity import (
    DuplicateRowConflict,
    repair_duplicate_rows,
    scan_worksheet_row_integrity,
)


def _xlsx(path: Path, sheet_xml: str) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _sheet(rows: str) -> str:
    return (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{rows}</sheetData></worksheet>'
    )


def test_duplicate_row_and_nonmonotonic_order_are_detected(tmp_path: Path) -> None:
    workbook = tmp_path / "candidate.xlsx"
    _xlsx(
        workbook,
        _sheet(
            '<row r="1"><c r="A1"><v>1</v></c></row>'
            '<row r="2"><c r="A2"><v>2</v></c></row>'
            '<row r="1"><c r="Q1"><v>3</v></c></row>'
        ),
    )

    report = scan_worksheet_row_integrity(workbook)

    assert not report.pass_all
    assert [(item.row, item.occurrences) for item in report.duplicate_rows] == [(1, 2)]
    assert [(item.previous_row, item.next_row) for item in report.order_violations] == [(2, 1)]
    assert report.duplicate_rows[0].cell_refs_by_occurrence == (("A1",), ("Q1",))


def test_safe_repair_merges_disjoint_duplicate_rows(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _xlsx(
        candidate,
        _sheet(
            '<row r="1"><c r="A1"><v>1</v></c></row>'
            '<row r="2"><c r="A2"><v>2</v></c></row>'
            '<row r="1"><c r="Q1"><v>3</v></c><c r="R1"><v>4</v></c></row>'
        ),
    )

    result = repair_duplicate_rows(candidate, repaired)
    post = scan_worksheet_row_integrity(repaired)

    assert result["merged_rows"] == 1
    assert post.pass_all
    with zipfile.ZipFile(repaired) as z:
        xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert xml.count('<row r="1">') == 1
    assert 'r="A1"' in xml and 'r="Q1"' in xml and 'r="R1"' in xml


def test_overlapping_duplicate_cells_stop_instead_of_guessing(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _xlsx(
        candidate,
        _sheet(
            '<row r="1"><c r="A1"><v>1</v></c></row>'
            '<row r="1"><c r="A1"><v>9</v></c></row>'
        ),
    )

    with pytest.raises(DuplicateRowConflict, match="overlapping duplicate cell refs"):
        repair_duplicate_rows(candidate, repaired)
    assert not repaired.exists()
