from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from triage.prompt_kit_contract import (
    EXPECTED_COPY_SHEETS,
    LIBRARY_HEADERS,
    PROMPT_IDS,
    validate_prompt_kit_contract,
)

# ─────────────────── OOXML skeleton parts ───────────────────

CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

ROOT_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

STYLES_APTOS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="Aptos"/></font>
    <font><b/><sz val="11"/><name val="Aptos"/></font>
    <font><sz val="12"/><name val="Aptos"/></font>
  </fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf/></cellStyleXfs>
  <cellXfs count="3">
    <xf fontId="0"/>
    <xf fontId="1"/>
    <xf fontId="2"/>
  </cellXfs>
</styleSheet>"""


def _make_workbook_xml(sheet_entries: list[tuple[str, int, str]]) -> str:
    """Build workbook.xml. sheet_entries = [(name, sheet_id, rId)]."""
    sheets_xml = "\n".join(
        f'    <sheet name="{name}" sheetId="{sid}" r:id="{rid}"/>'
        for name, sid, rid in sheet_entries
    )
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
{sheets_xml}
  </sheets>
</workbook>"""


def _make_workbook_rels(sheet_entries: list[tuple[str, str]]) -> str:
    """Build workbook.xml.rels. sheet_entries = [(rId, target)]."""
    rels_xml = "\n".join(
        f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{target}"/>'
        for rid, target in sheet_entries
    )
    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels_xml}
</Relationships>"""


def _make_sheet_xml(
    rows: dict[int, dict[str, str]],
    *,
    font_map: dict[str, int] | None = None,
) -> str:
    """Build a minimal worksheet XML.

    rows: {row_num: {"A": "val", "B": "val", ...}}
    font_map: {cell_ref: style_index} e.g. {"H1": 1, "H2": 2}
    """
    cells_xml_parts: list[str] = []
    for row_num in sorted(rows.keys()):
        row_cells = rows[row_num]
        cells = []
        for col, val in sorted(row_cells.items()):
            ref = f"{col}{row_num}"
            style_attr = ""
            if font_map and ref in font_map:
                style_attr = f' s="{font_map[ref]}"'
            cells.append(f'      <c r="{ref}" t="inlineStr"{style_attr}><is><t>{val}</t></is></c>')
        cells_xml_parts.append(f'    <row r="{row_num}">\n' + "\n".join(cells) + "\n    </row>")
    cells_xml = "\n".join(cells_xml_parts)

    return f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetData>
{cells_xml}
  </sheetData>
</worksheet>"""


def _make_library_header_row() -> dict[str, str]:
    """Row 1 of Prompt_Library with correct headers."""
    row: dict[str, str] = {}
    for i, header in enumerate(LIBRARY_HEADERS):
        col = chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26)
        row[col] = header
    return row


def _make_library_data_row(
    seq: int,
    prompt_id: str,
    color: str,
    copy_sheet: str,
    *,
    description: str = "Use this when needed.",
) -> dict[str, str]:
    """Build one data row for the Prompt_Library."""
    return {
        "A": f"{seq:02d}",
        "B": prompt_id,
        "C": "BUILD",
        "D": "SPRINT / BUILD",
        "E": "Execute bounded work",
        "F": "YES",
        "G": f"{prompt_id} Executor",
        "H": description,
        "I": "Inspect first.",
        "J": "Output.",
        "K": "Next.",
        "L": "Gate.",
        "M": color,
        "N": copy_sheet,
    }


def _make_legend_xml(header_row: int, entries: dict[str, tuple[str, str]]) -> str:
    """Build Prompt_Class_Legend worksheet XML.

    entries = {"Slate": ("SETUP", "Install baseline"), ...}
    """
    rows: dict[int, dict[str, str]] = {}
    rows[header_row] = {
        "A": "Prompt Type",
        "B": "Prompt Class",
        "D": "When to Use",
        "H": "Color",
    }
    for i, (color, (ptype, when)) in enumerate(entries.items()):
        row_num = header_row + 1 + i
        rows[row_num] = {"A": ptype, "B": ptype, "D": when, "H": color}
    return _make_sheet_xml(rows)


def _build_passing_fixture(tmp: Path, *, compact: bool = True) -> Path:
    """Build a complete passing V19 fixture and return its path."""
    path = tmp / "passing.xlsx"

    sheet_entries_wb: list[tuple[str, int, str]] = []
    sheet_entries_rels: list[tuple[str, str]] = []
    sheet_xmls: dict[str, str] = {}

    # Prompt_Library
    lib_rows: dict[int, dict[str, str]] = {1: _make_library_header_row()}
    copy_sheet_map: dict[str, int] = {}

    colors = [
        "Slate", "Gray", "Sky", "Amber", "Blue",
        "Green", "Rose", "Purple", "Peach", "Teal",
        "Gray", "Lavender", "Cyan", "Indigo", "Blue-Green",
        "Gold", "Sand", "Orange", "Emerald", "Slate", "Amber",
    ]

    for i, pid in enumerate(PROMPT_IDS):
        sheet_name = f"{pid}_COPY_SAFE"
        copy_sheet_map[sheet_name] = i + 4  # after START_HERE, Prompt_Library, Prompt_Class_Legend
        seq = i
        copy_ref = f"{pid}_COPY_SAFE"
        color = colors[i % len(colors)]

        # Build copy-safe payload (3 rows, no blanks)
        payload_rows: dict[int, dict[str, str]] = {
            1: {"A": f"EXECUTE {pid}"},
            2: {"A": "Second line."},
            3: {"A": "Third line."},
        }
        sheet_xmls[sheet_name] = _make_sheet_xml(payload_rows)
        lib_rows[i + 2] = _make_library_data_row(seq, pid, color, copy_ref)

    # Library font map: H1 bold (style 1), H2-H22 regular 12pt (style 2)
    lib_font_map: dict[str, int] = {"H1": 1}
    for i in range(21):
        lib_font_map[f"H{i + 2}"] = 2
    sheet_xmls["Prompt_Library"] = _make_sheet_xml(lib_rows, font_map=lib_font_map)

    # Prompt_Class_Legend
    legend_entries: dict[str, tuple[str, str]] = {}
    for i, pid in enumerate(PROMPT_IDS):
        color = colors[i % len(colors)]
        ptype = pid
        legend_entries[color] = (ptype, f"When using {pid}")
    sheet_xmls["Prompt_Class_Legend"] = _make_legend_xml(1, legend_entries)

    # START_HERE
    sheet_xmls["START_HERE"] = _make_sheet_xml({1: {"A": "Welcome"}})

    # Assemble sheet entries
    all_sheets = [("START_HERE", 1, "rId1"), ("Prompt_Library", 2, "rId2"), ("Prompt_Class_Legend", 3, "rId3")]
    all_rels = [("rId1", "worksheets/sheet_start.xml"), ("rId2", "worksheets/sheet_lib.xml"), ("rId3", "worksheets/sheet_legend.xml")]

    for i, pid in enumerate(PROMPT_IDS):
        sn = f"{pid}_COPY_SAFE"
        sid = i + 4
        rid = f"rId{i + 4}"
        all_sheets.append((sn, sid, rid))
        all_rels.append((rid, f"worksheets/sheet_{pid.lower()}.xml"))

    wb_xml = _make_workbook_xml(all_sheets)
    wb_rels = _make_workbook_rels(all_rels)

    # Write ZIP
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("xl/workbook.xml", wb_xml)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/styles.xml", STYLES_APTOS)

        # Write sheet parts (skip Prompt_Library; written below with hyperlinks)
        part_map = {
            "START_HERE": "xl/worksheets/sheet_start.xml",
            "Prompt_Class_Legend": "xl/worksheets/sheet_legend.xml",
        }
        for pid in PROMPT_IDS:
            part_map[f"{pid}_COPY_SAFE"] = f"xl/worksheets/sheet_{pid.lower()}.xml"

        for sheet_name, part_path in part_map.items():
            z.writestr(part_path, sheet_xmls[sheet_name])

        # Build and write hyperlink rels for Prompt_Library
        lib_rels_entries: list[str] = []
        lib_hyperlinks: list[str] = []
        for i, pid in enumerate(PROMPT_IDS):
            row_num = i + 2
            rid = f"rIdHL{i}"
            target_sheet = f"{pid}_COPY_SAFE"
            endpoint = f"{target_sheet}!A1:A3"
            lib_rels_entries.append(
                f'  <Relationship Id="{rid}" '
                f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                f'Target="{endpoint}" TargetMode="External"/>'
            )
            lib_hyperlinks.append(
                f'  <hyperlink ref="N{row_num}" r:id="{rid}"/>'
            )
            lib_hyperlinks.append(
                f'  <hyperlink ref="B{row_num}" r:id="{rid}"/>'
            )

        lib_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            + "\n".join(lib_rels_entries)
            + "\n</Relationships>"
        )
        z.writestr("xl/worksheets/_rels/sheet_lib.xml.rels", lib_rels_xml)

        # Rewrite Prompt_Library with hyperlinks
        base_lib = sheet_xmls["Prompt_Library"]
        # Insert hyperlinks before </worksheet>
        hl_block = "  <hyperlinks>\n" + "\n".join(lib_hyperlinks) + "\n  </hyperlinks>\n"
        lib_with_hl = base_lib.replace("  </sheetData>\n</worksheet>", f"  </sheetData>\n{hl_block}</worksheet>")
        z.writestr("xl/worksheets/sheet_lib.xml", lib_with_hl)

    return path


# ─────────────────── Tests ───────────────────


class PromptKitContractTests(unittest.TestCase):

    def test_passing_fixture_satisfies_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _build_passing_fixture(Path(tmp))
            report = validate_prompt_kit_contract(str(path))
            self.assertTrue(report.contract_valid, report.render_text())
            self.assertFalse(report.failures)

    def test_cross_surface_failures_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.xlsx"
            # Missing several sheets, bad headers, wrong font
            lib_rows: dict[int, dict[str, str]] = {1: {"A": "Wrong", "B": "Header"}}
            lib_rows[2] = _make_library_data_row(0, "P00", "Slate", "P00_COPY_SAFE")
            lib_font_map: dict[str, int] = {"H1": 0, "H2": 0}  # font 0 = Aptos 11pt, not 12pt
            lib_xml = _make_sheet_xml(lib_rows, font_map=lib_font_map)

            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("[Content_Types].xml", CONTENT_TYPES)
                z.writestr("_rels/.rels", ROOT_RELS)
                z.writestr("xl/styles.xml", STYLES_APTOS)
                z.writestr("xl/workbook.xml", _make_workbook_xml([
                    ("Prompt_Library", 1, "rId1"),
                ]))
                z.writestr("xl/_rels/workbook.xml.rels", _make_workbook_rels([
                    ("rId1", "worksheets/sheet_lib.xml"),
                ]))
                z.writestr("xl/worksheets/sheet_lib.xml", lib_xml)

            report = validate_prompt_kit_contract(str(path))
            self.assertFalse(report.contract_valid)
            by_name = {c.name: c for c in report.checks}
            self.assertEqual("FAIL", by_name["required prompt tabs"].status)
            self.assertEqual("FAIL", by_name["Prompt Library headers"].status)
            self.assertEqual("FAIL", by_name["Prompt_Class_Legend present"].status)

    def test_stale_hyperlink_endpoints_after_compaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stale_links.xlsx"
            # Build a fixture where hyperlinks target A1:A100 but payload is only 3 rows
            lib_rows: dict[int, dict[str, str]] = {1: _make_library_header_row()}
            for i, pid in enumerate(PROMPT_IDS):
                lib_rows[i + 2] = _make_library_data_row(i, pid, "Slate", f"{pid}_COPY_SAFE")
            lib_font_map: dict[str, int] = {"H1": 1}
            for i in range(21):
                lib_font_map[f"H{i + 2}"] = 2

            # Build copy-safe sheets (3 rows each)
            copy_xmls: dict[str, str] = {}
            for pid in PROMPT_IDS:
                copy_xmls[pid] = _make_sheet_xml({1: {"A": "Line 1"}, 2: {"A": "Line 2"}, 3: {"A": "Line 3"}})

            # Build library XML with hyperlinks targeting A1:A100 (stale)
            lib_base = _make_sheet_xml(lib_rows, font_map=lib_font_map)
            hl_parts: list[str] = []
            rels_parts: list[str] = []
            for i, pid in enumerate(PROMPT_IDS):
                row_num = i + 2
                rid = f"rIdHL{i}"
                rels_parts.append(
                    f'  <Relationship Id="{rid}" '
                    f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                    f'Target="{pid}_COPY_SAFE!A1:A100" TargetMode="External"/>'
                )
                hl_parts.append(f'  <hyperlink ref="N{row_num}" r:id="{rid}"/>')
                hl_parts.append(f'  <hyperlink ref="B{row_num}" r:id="{rid}"/>')

            lib_with_hl = lib_base.replace(
                "  </sheetData>\n</worksheet>",
                f"  </sheetData>\n  <hyperlinks>\n" + "\n".join(hl_parts) + "\n  </hyperlinks>\n</worksheet>",
            )

            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("[Content_Types].xml", CONTENT_TYPES)
                z.writestr("_rels/.rels", ROOT_RELS)
                z.writestr("xl/styles.xml", STYLES_APTOS)
                entries = [("Prompt_Library", 1, "rId1")]
                rels = [("rId1", "worksheets/sheet_lib.xml")]
                for j, pid in enumerate(PROMPT_IDS):
                    entries.append((f"{pid}_COPY_SAFE", j + 2, f"rId{j + 2}"))
                    rels.append((f"rId{j + 2}", f"worksheets/sheet_{pid.lower()}.xml"))
                z.writestr("xl/workbook.xml", _make_workbook_xml(entries))
                z.writestr("xl/_rels/workbook.xml.rels", _make_workbook_rels(rels))
                z.writestr("xl/worksheets/sheet_lib.xml", lib_with_hl)
                rels_xml = (
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    + "".join(rels_parts)
                    + "</Relationships>"
                )
                z.writestr("xl/worksheets/_rels/sheet_lib.xml.rels", rels_xml)
                for pid in PROMPT_IDS:
                    z.writestr(f"xl/worksheets/sheet_{pid.lower()}.xml", copy_xmls[pid])

            report = validate_prompt_kit_contract(str(path))
            by_name = {c.name: c for c in report.checks}
            self.assertEqual("FAIL", by_name["hyperlink endpoints"].status)
            # Verify expected endpoint is A1:A3, not A1:A100
            first_finding = by_name["hyperlink endpoints"].findings[0]
            self.assertIn("A1:A3", first_finding["expected"])
            self.assertIn("A1:A100", first_finding["actual"])

    def test_requires_all_21_prompt_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incomplete.xlsx"
            # Only provide 5 copy-safe sheets
            lib_rows: dict[int, dict[str, str]] = {1: _make_library_header_row()}
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("[Content_Types].xml", CONTENT_TYPES)
                z.writestr("_rels/.rels", ROOT_RELS)
                z.writestr("xl/styles.xml", STYLES_APTOS)

                entries = [("Prompt_Library", 1, "rId1")]
                rels = [("rId1", "worksheets/sheet_lib.xml")]

                for i in range(5):
                    pid = PROMPT_IDS[i]
                    sn = f"{pid}_COPY_SAFE"
                    entries.append((sn, i + 2, f"rId{i + 2}"))
                    rels.append((f"rId{i + 2}", f"worksheets/sheet_{pid.lower()}.xml"))
                    lib_rows[i + 2] = _make_library_data_row(i, pid, "Slate", sn)
                    z.writestr(f"xl/worksheets/sheet_{pid.lower()}.xml", _make_sheet_xml(
                        {1: {"A": f"Line for {pid}"}},
                    ))

                lib_xml = _make_sheet_xml(lib_rows)
                z.writestr("xl/workbook.xml", _make_workbook_xml(entries))
                z.writestr("xl/_rels/workbook.xml.rels", _make_workbook_rels(rels))
                z.writestr("xl/worksheets/sheet_lib.xml", lib_xml)

            report = validate_prompt_kit_contract(str(path))
            by_name = {c.name: c for c in report.checks}
            self.assertEqual("FAIL", by_name["required prompt tabs"].status)
            self.assertEqual(16, len(by_name["required prompt tabs"].findings))


if __name__ == "__main__":
    unittest.main()
