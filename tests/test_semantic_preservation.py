from __future__ import annotations

import zipfile
from pathlib import Path

from triage.semantic_preservation import compare_semantics


CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'''
WB = '''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'''
RELS = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''


def _xlsx(path: Path, cells: str, shared_strings: list[str] | None = None) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("xl/workbook.xml", WB)
        z.writestr("xl/_rels/workbook.xml.rels", RELS)
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData><row r="1">{cells}</row></sheetData></worksheet>',
        )
        if shared_strings is not None:
            body = "".join(f"<si><t>{value}</t></si>" for value in shared_strings)
            z.writestr(
                "xl/sharedStrings.xml",
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f"{body}</sst>",
            )


def test_missing_payload_and_changed_string_are_reported(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _xlsx(
        candidate,
        '<c r="A1" t="inlineStr"><is><t>keep me</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>header</t></is></c>',
    )
    _xlsx(
        repaired,
        '<c r="B1" t="s"><v>0</v></c>',
        shared_strings=["Column1"],
    )

    report = compare_semantics(candidate, repaired)

    assert not report.pass_all
    assert report.counts() == {"lost_cell_payload": 1, "changed_string": 1}
    assert {(item.kind, item.cell) for item in report.findings} == {
        ("lost_cell_payload", "A1"),
        ("changed_string", "B1"),
    }


def test_inline_to_shared_string_and_numeric_reformat_are_preserved(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _xlsx(
        candidate,
        '<c r="A1" t="inlineStr"><is><t>same</t></is></c>'
        '<c r="B1"><v>11.8333333333</v></c>',
    )
    _xlsx(
        repaired,
        '<c r="A1" t="s"><v>0</v></c>'
        '<c r="B1"><v>11.833333333300001</v></c>',
        shared_strings=["same"],
    )

    report = compare_semantics(candidate, repaired)

    assert report.pass_all


def test_shared_formula_follower_is_not_treated_as_formula_loss(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    repaired = tmp_path / "repaired.xlsx"
    _xlsx(candidate, '<c r="A1"><f>1+1</f><v>2</v></c>')
    _xlsx(repaired, '<c r="A1"><f t="shared" si="0"/><v>2</v></c>')

    report = compare_semantics(candidate, repaired)

    assert report.pass_all
