from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from triage.prompt_kit_contract import validate_prompt_kit_contract

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="4">
    <font><sz val="11"/><name val="Aptos"/></font>
    <font><b/><sz val="11"/><name val="Aptos"/></font>
    <font><sz val="12"/><name val="Aptos"/></font>
    <font><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="4">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  </cellXfs>
</styleSheet>"""


def cell(ref: str, value: str = "", style: int = 0) -> str:
    style_attr = f' s="{style}"' if style else ""
    if value:
        return (
            f'<c r="{ref}"{style_attr} t="inlineStr"><is><t>'
            f'{escape(value)}</t></is></c>'
        )
    return f'<c r="{ref}"{style_attr}/>'


def worksheet(
    rows: list[str],
    dimension: str,
    hyperlinks: list[tuple[str, str]] | None = None,
) -> str:
    links = ""
    if hyperlinks:
        links = "<hyperlinks>" + "".join(
            f'<hyperlink ref="{ref}" location="{escape(location)}"/>'
            for ref, location in hyperlinks
        ) + "</hyperlinks>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="{dimension}"/><sheetData>{"".join(rows)}</sheetData>'
        f'{links}</worksheet>'
    )


def row(number: int, cells: list[str]) -> str:
    return f'<row r="{number}">{"".join(cells)}</row>'


def write_fixture(path: Path, *, broken: bool = False) -> None:
    sheets = [
        "Prompt_Library",
        "Prompt_Class_Legend",
        "P00_COPY_SAFE",
        "P01_COPY_SAFE",
    ]
    workbook_sheets = "".join(
        f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheets, start=1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{workbook_sheets}</sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, len(sheets) + 1)
        )
        + '<Relationship Id="rIdStyles" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        '</Relationships>'
    )

    color_header = "Color Meaning" if broken else "Color"
    p01_location = "P01_COPY_SAFE!A1" if broken else "P01_COPY_SAFE!A1:A2"
    body_style = 0 if broken else 2
    prompt_id_style = 3 if broken else 0
    library_rows = [
        row(
            1,
            [
                cell("B1", "Prompt ID"),
                cell("H1", "Use This When", 1),
                cell("M1", color_header),
                cell("N1", "Copy-Safe Sheet"),
            ],
        ),
        row(
            2,
            [
                cell("B2", "P00", prompt_id_style),
                cell("H2", "Set baseline behavior", body_style),
                cell("M2", "Green"),
                cell("N2", "P00_COPY_SAFE"),
            ],
        ),
        row(
            3,
            [
                cell("B3", "P01"),
                cell("H3", "Bootstrap the harness", body_style),
                cell("M3", "Amber"),
                cell("N3", "P01_COPY_SAFE"),
            ],
        ),
    ]
    library_links = [
        ("B2", "P00_COPY_SAFE!A1:A2"),
        ("N2", "P00_COPY_SAFE!A1:A2"),
        ("B3", p01_location),
        ("N3", p01_location),
    ]
    library = worksheet(library_rows, "B1:N3", library_links)

    legend_rows = [
        row(
            1,
            [
                cell("A1", "Color", 1),
                cell("B1", "Operational Meaning", 1),
            ],
        ),
        row(
            2,
            [
                cell("A2", "Green"),
                cell("B2", "Build or mutate owned repository scope"),
            ],
        ),
        row(
            3,
            [
                cell("A3", "Amber"),
                cell(
                    "B3",
                    "Plan or distribute bounded work" if not broken else "",
                ),
            ],
        ),
    ]
    legend = worksheet(legend_rows, "A1:B3")

    p00 = worksheet(
        [
            row(1, [cell("A1", "MISSION")]),
            row(2, [cell("A2", "Execute the bounded sprint.")]),
        ],
        "A1:A2",
    )
    if broken:
        p01 = worksheet(
            [
                row(1, [cell("A1", "MISSION")]),
                row(2, []),
                row(3, [cell("A3", "Bootstrap the harness.")]),
                row(4, [cell("A4", "", 2)]),
            ],
            "A1:A4",
        )
    else:
        p01 = worksheet(
            [
                row(1, [cell("A1", "MISSION")]),
                row(2, [cell("A2", "Bootstrap the harness.")]),
            ],
            "A1:A2",
        )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", STYLES)
        archive.writestr("xl/worksheets/sheet1.xml", library)
        archive.writestr("xl/worksheets/sheet2.xml", legend)
        archive.writestr("xl/worksheets/sheet3.xml", p00)
        archive.writestr("xl/worksheets/sheet4.xml", p01)


class PromptKitContractTests(unittest.TestCase):
    def test_healthy_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "healthy.xlsx"
            write_fixture(path)
            report = validate_prompt_kit_contract(
                path, prompt_ids=["P00", "P01"]
            )
            self.assertTrue(report.pass_all, report.render_text())
            self.assertTrue(
                all(check.status == "PASS" for check in report.checks)
            )
            self.assertEqual(
                [0, 0],
                [
                    surface["internal_blank_rows"]
                    for surface in report.copy_surfaces
                ],
            )
            self.assertEqual(
                [0, 0],
                [surface["trailing_rows"] for surface in report.copy_surfaces],
            )

    def test_broken_contract_reports_cross_surface_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.xlsx"
            write_fixture(path, broken=True)
            report = validate_prompt_kit_contract(
                path, prompt_ids=["P00", "P01"]
            )
            self.assertFalse(report.pass_all)
            by_name = {check.name: check for check in report.checks}
            expected_failures = {
                "visible fonts approved",
                "Prompt Library contract columns",
                "Prompt Library column H typography",
                "copy surfaces dense and bounded",
                "Prompt Library links select exact payload ranges",
                "Prompt Class Legend covers every library color",
            }
            self.assertTrue(
                expected_failures.issubset(
                    {
                        name
                        for name, check in by_name.items()
                        if check.status == "FAIL"
                    }
                )
            )

    def test_exact_range_link_tracks_compacted_payload_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.xlsx"
            write_fixture(path, broken=True)
            report = validate_prompt_kit_contract(
                path, prompt_ids=["P00", "P01"]
            )
            links = next(
                check
                for check in report.checks
                if check.name
                == "Prompt Library links select exact payload ranges"
            )
            self.assertEqual("FAIL", links.status)
            p01 = [
                finding
                for finding in links.findings
                if finding.get("prompt_id") == "P01"
            ]
            self.assertTrue(p01)
            self.assertTrue(
                all(
                    finding["expected"] == "P01_COPY_SAFE!A1:A3"
                    for finding in p01
                )
            )

    def test_default_contract_requires_all_21_prompt_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "partial.xlsx"
            write_fixture(path)
            report = validate_prompt_kit_contract(path)
            required = next(
                check
                for check in report.checks
                if check.name == "required sheets"
            )
            self.assertEqual("FAIL", required.status)
            self.assertIn({"sheet": "P20_COPY_SAFE"}, required.findings)


if __name__ == "__main__":
    unittest.main()
