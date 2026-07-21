from __future__ import annotations

from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_ooxml_base as ooxml

M = ooxml.MAIN_NS
R = ooxml.REL_NS
PR = ooxml.PKG_REL_NS

_PALETTE_FILLS = {
    "Cream": "F7E6C4",
    "Slate": "F1F5F9",
    "Sky": "E0F2FE",
    "Amber": "FEF3C7",
    "Blue": "DBEAFE",
    "Green": "DCFCE7",
    "Rose": "FFE4E6",
    "Purple": "F3E8FF",
}


def _cell(ref: str, value: str, *, formula: str | None = None, style: str = "0") -> ET.Element:
    cell = ET.Element(f"{{{M}}}c", {"r": ref, "s": style, "t": "inlineStr" if formula is None else "str"})
    if formula is not None:
        ET.SubElement(cell, f"{{{M}}}f").text = formula
        ET.SubElement(cell, f"{{{M}}}v").text = value
    else:
        inline = ET.SubElement(cell, f"{{{M}}}is")
        ET.SubElement(inline, f"{{{M}}}t").text = value
    return cell


def _styles_xml() -> ET.Element:
    styles = ET.Element(f"{{{M}}}styleSheet")
    fonts = ET.SubElement(styles, f"{{{M}}}fonts", {"count": "1"})
    font = ET.SubElement(fonts, f"{{{M}}}font")
    ET.SubElement(font, f"{{{M}}}sz", {"val": "11"})
    ET.SubElement(font, f"{{{M}}}color", {"rgb": "FF000000"})
    ET.SubElement(font, f"{{{M}}}name", {"val": "Aptos"})
    fills = ET.SubElement(styles, f"{{{M}}}fills", {"count": "1"})
    fill = ET.SubElement(fills, f"{{{M}}}fill")
    ET.SubElement(fill, f"{{{M}}}patternFill", {"patternType": "none"})
    borders = ET.SubElement(styles, f"{{{M}}}borders", {"count": "1"})
    ET.SubElement(borders, f"{{{M}}}border")
    xfs = ET.SubElement(styles, f"{{{M}}}cellXfs", {"count": "1"})
    ET.SubElement(xfs, f"{{{M}}}xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0", "xfId": "0"})
    return styles


def _make_prompt_sheet_xml(sheet_name: str, lines: list[str]) -> ET.Element:
    last = len(lines)
    prompt = ET.Element(f"{{{M}}}worksheet")
    ET.SubElement(prompt, f"{{{M}}}dimension", {"ref": f"A1:C{last}"})
    sheet_views = ET.SubElement(prompt, f"{{{M}}}sheetViews")
    ET.SubElement(sheet_views, f"{{{M}}}sheetView", {"tabSelected": "0", "workbookViewId": "0"})
    data = ET.SubElement(prompt, f"{{{M}}}sheetData")
    for idx, text in enumerate(lines, start=1):
        row = ET.SubElement(data, f"{{{M}}}row", {"r": str(idx), "spans": "1:3"})
        row.append(_cell(f"A{idx}", text))
        if idx == 1 or idx == last:
            back_formula = f'HYPERLINK("#\'Prompt_Library\'!A2:P2","Prompt Library")'
            row.append(_cell(f"B{idx}", "Prompt Library", formula=back_formula))
            copy_formula = f'HYPERLINK("#\'{sheet_name}\'!A1:A{last}","Copy A1:A{last} only")'
            row.append(_cell(f"C{idx}", f"Copy A1:A{last} only", formula=copy_formula))
    hyperlinks = ET.SubElement(prompt, f"{{{M}}}hyperlinks")
    for idx in (1, last):
        ET.SubElement(hyperlinks, f"{{{M}}}hyperlink", {"ref": f"C{idx}", "location": "'Prompt_Library'!A1", "display": f"Copy A1:A{last} only"})
    return prompt


def _multi_prompt_parts(prompts: list[tuple[str, str, str, list[str]]]) -> dict[str, bytes]:
    library_col_n = len(prompts) + 1

    workbook = ET.Element(f"{{{M}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{M}}}sheets")
    ET.SubElement(sheets, f"{{{M}}}sheet", {"name": "Prompt_Library", "sheetId": "1", f"{{{R}}}id": "rId1"})
    sheet_parts: dict[str, bytes] = {}
    for sid, (prompt_id, _, color, lines) in enumerate(prompts, start=2):
        name = f"{prompt_id}_COPY_SAFE"
        ET.SubElement(sheets, f"{{{M}}}sheet", {"name": name, "sheetId": str(sid), f"{{{R}}}id": f"rId{sid}"})

    rels = ET.Element(f"{{{PR}}}Relationships")
    ET.SubElement(rels, f"{{{PR}}}Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": "worksheets/sheet1.xml"})
    for sid in range(2, len(prompts) + 2):
        ET.SubElement(rels, f"{{{PR}}}Relationship", {"Id": f"rId{sid}", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": f"worksheets/sheet{sid}.xml"})

    library = ET.Element(f"{{{M}}}worksheet")
    ET.SubElement(library, f"{{{M}}}dimension", {"ref": f"A1:P{library_col_n}"})
    data = ET.SubElement(library, f"{{{M}}}sheetData")
    header_labels = ("", "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role", "Use For Progress?", "Prompt Name", "Use This When", "Inspect First", "Expected Output", "Next Step", "Proof / Acceptance Gate", "Color", "Copy-Safe Sheet", "")
    header = ET.SubElement(data, f"{{{M}}}row", {"r": "1"})
    for idx, label in enumerate(header_labels, start=1):
        header.append(_cell(f"{ooxml._impl._column_name(idx)}1", label))

    for pidx, (prompt_id, display_name, color, lines) in enumerate(prompts, start=2):
        row = ET.SubElement(data, f"{{{M}}}row", {"r": str(pidx)})
        name = f"{prompt_id}_COPY_SAFE"
        last_line = len(lines)
        values = ["", str(pidx - 1).zfill(2), prompt_id, "INSTALL", "STANDARD AI", "role", "YES", display_name, "when", "inspect", "output", "next", "proof", color, name, ""]
        for idx, value in enumerate(values, start=1):
            col = ooxml._impl._column_name(idx)
            formula = None
            if col in ("C", "O"):
                formula = f'HYPERLINK("#\'{name}\'!A1:A{last_line}","{value}")'
            row.append(_cell(f"{col}{pidx}", value, formula=formula))

    for sid, (prompt_id, _, _, lines) in enumerate(prompts, start=2):
        name = f"{prompt_id}_COPY_SAFE"
        sheet_parts[f"xl/worksheets/sheet{sid}.xml"] = ooxml._xml(_make_prompt_sheet_xml(name, lines))

    return {
        "xl/workbook.xml": ooxml._xml(workbook),
        "xl/_rels/workbook.xml.rels": ooxml._xml(rels),
        "xl/worksheets/sheet1.xml": ooxml._xml(library),
        "xl/styles.xml": ooxml._xml(_styles_xml()),
        **sheet_parts,
    }


def _short_prompt():
    return [
        "INSTALL THE HARNESS DOCTRINE NOW.",
        "This is a short two-line prompt.",
    ]


def _medium_prompt():
    return [
        "PROMPT SURFACE: STANDARD AI.",
        "Line two of the prompt.",
        "Line three with more content.",
        "Line four continues.",
        "Line five concludes.",
    ]


def _long_prompt():
    return [
        "PROMPT SURFACE: STANDARD AI.",
        "Line 2.",
        "Line 3.",
        "Line 4.",
        "Line 5.",
        "Line 6.",
        "Line 7.",
        "Line 8 - long prompt continues.",
        "Line 9.",
        "Line 10 - end.",
    ]


class TestPromptBodyRangeDetection:
    def test_detects_navigation_rows_short(self):
        xml = _make_prompt_sheet_xml("P00_COPY_SAFE", _short_prompt())
        root = ooxml._root(ooxml._xml(xml), "prompt")
        top, bottom = ooxml._detect_prompt_tab_navigation_rows(root)
        assert top == 1
        assert bottom == 2

    def test_detects_navigation_rows_medium(self):
        xml = _make_prompt_sheet_xml("P01_COPY_SAFE", _medium_prompt())
        root = ooxml._root(ooxml._xml(xml), "prompt")
        top, bottom = ooxml._detect_prompt_tab_navigation_rows(root)
        assert top == 1
        assert bottom == 5

    def test_detects_navigation_rows_long(self):
        xml = _make_prompt_sheet_xml("P02_COPY_SAFE", _long_prompt())
        root = ooxml._root(ooxml._xml(xml), "prompt")
        top, bottom = ooxml._detect_prompt_tab_navigation_rows(root)
        assert top == 1
        assert bottom == 10

    def test_body_range_columns_and_string(self):
        xml = _make_prompt_sheet_xml("P00_COPY_SAFE", _short_prompt())
        root = ooxml._root(ooxml._xml(xml), "prompt")
        top, bottom, cols, rang = ooxml._prompt_body_range(root, "P00_COPY_SAFE")
        assert top == 1
        assert bottom == 2
        assert cols == ["A", "B", "C"]
        assert rang == "A1:C2"

    def test_fails_on_missing_navigation(self):
        sheet = ET.Element(f"{{{M}}}worksheet")
        ET.SubElement(sheet, f"{{{M}}}dimension", {"ref": "A1:C3"})
        data = ET.SubElement(sheet, f"{{{M}}}sheetData")
        row = ET.SubElement(data, f"{{{M}}}row", {"r": "1"})
        row.append(_cell("A1", "just text, no hyperlinks"))
        root = ooxml._root(ooxml._xml(sheet), "prompt")
        try:
            ooxml._detect_prompt_tab_navigation_rows(root)
            assert False, "should have raised"
        except ValueError as exc:
            assert "no navigation row" in str(exc).lower()

    def test_fails_on_single_navigation_row(self):
        sheet = ET.Element(f"{{{M}}}worksheet")
        ET.SubElement(sheet, f"{{{M}}}dimension", {"ref": "A1:C3"})
        data = ET.SubElement(sheet, f"{{{M}}}sheetData")
        row = ET.SubElement(data, f"{{{M}}}row", {"r": "1"})
        formula = f'HYPERLINK("#\'Prompt_Library\'!A2:P2","Prompt Library")'
        row.append(_cell("B1", "Prompt Library", formula=formula))
        hyperlinks = ET.SubElement(sheet, f"{{{M}}}hyperlinks")
        ET.SubElement(hyperlinks, f"{{{M}}}hyperlink", {"ref": "B1", "location": "'Prompt_Library'!A2", "display": "Prompt Library"})
        root = ooxml._root(ooxml._xml(sheet), "prompt")
        try:
            ooxml._detect_prompt_tab_navigation_rows(root)
            assert False, "should have raised"
        except ValueError as exc:
            assert "only one" in str(exc).lower() or "cannot determine" in str(exc).lower()


class TestScaffoldFill:
    def test_applies_scaffold_to_all_tabs(self):
        prompts = [
            ("P00", "P00 Install", "Cream", _short_prompt()),
            ("P01", "P01 Medium", "Slate", _medium_prompt()),
            ("P02", "P02 Long", "Sky", _long_prompt()),
        ]
        parts = _multi_prompt_parts(prompts)
        changed, report = ooxml._apply_prompt_body_scaffold(parts)
        assert report["prompt_count"] == 3
        for entry in report["prompts"]:
            assert "error" not in entry, f"scaffold failed for {entry['sheet']}: {entry.get('error')}"
            assert entry["cells_filled"] > 0
        findings = ooxml._validate_prompt_body_scaffold(parts)
        assert findings == (), f"scaffold validation found uncovered cells: {findings}"

    def test_scaffold_materializes_blank_cells_across_claimed_range(self):
        prompts = [("P00", "P00 Test", "Cream", _medium_prompt())]
        parts = _multi_prompt_parts(prompts)
        before = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
        before_cells = ooxml._cells(before)
        assert before_cells.get("B2") is None
        assert before_cells.get("C4") is None

        _, report = ooxml._apply_prompt_body_scaffold(parts)

        after = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
        after_cells = ooxml._cells(after)
        for row_number in range(1, 6):
            for column in ("A", "B", "C"):
                assert after_cells.get(f"{column}{row_number}") is not None
        assert report["prompts"][0]["cells_materialized"] == 6
        assert ooxml._validate_prompt_body_scaffold(parts) == ()

    def test_scaffold_preserves_formulas_and_text(self):
        prompts = [("P00", "P00 Test", "Cream", _medium_prompt())]
        parts = _multi_prompt_parts(prompts)
        prompt_root_before = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
        cells_before = ooxml._cells(prompt_root_before)
        before_a1 = ooxml._cell_display(cells_before.get("A1"), ())
        before_b1_formula = ooxml._formula(cells_before.get("B1"))
        ooxml._apply_prompt_body_scaffold(parts)
        prompt_root_after = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
        cells_after = ooxml._cells(prompt_root_after)
        assert ooxml._cell_display(cells_after.get("A1"), ()) == before_a1
        assert ooxml._formula(cells_after.get("B1")) == before_b1_formula

    def test_scaffold_skip_when_no_styles(self):
        prompts = [("P00", "P00 Test", "Cream", _short_prompt())]
        parts = _multi_prompt_parts(prompts)
        del parts["xl/styles.xml"]
        changed, report = ooxml._apply_prompt_body_scaffold(parts)
        assert report["prompt_count"] == 0
        assert "skipped" in report

    def test_scaffold_covers_variable_lengths(self):
        prompts = [
            ("P00", "Short", "Cream", _short_prompt()),
            ("P01", "Medium", "Slate", _medium_prompt()),
            ("P02", "Long", "Sky", _long_prompt()),
        ]
        parts = _multi_prompt_parts(prompts)
        ooxml._apply_prompt_body_scaffold(parts)
        for sid in range(2, 5):
            prompt_root = ooxml._root(parts[f"xl/worksheets/sheet{sid}.xml"], "prompt")
            top, bottom, cols, _ = ooxml._prompt_body_range(prompt_root, f"P{sid - 2:02d}_COPY_SAFE")
            rows = {int(row.attrib.get("r", "0")): row for row in prompt_root.findall("m:sheetData/m:row", ooxml.NS)}
            expected_refs = {
                f"{col}{row_number}"
                for row_number in range(top, bottom + 1)
                for col in cols
            }
            actual_refs = {
                cell.attrib.get("r", "")
                for row in rows.values()
                for cell in row.findall("m:c", ooxml.NS)
            }
            assert expected_refs <= actual_refs, (
                f"missing scaffold cells for sheet {sid}: "
                f"{sorted(expected_refs - actual_refs)}"
            )



class TestSemanticTabColorCoverage:
    def test_all_prompts_get_tab_color(self):
        prompts = [
            ("P00", "P00 Cream", "Cream", _short_prompt()),
            ("P01", "P01 Slate", "Slate", _short_prompt()),
            ("P02", "P02 Sky", "Sky", _short_prompt()),
            ("P03", "P03 Amber", "Amber", _short_prompt()),
        ]
        parts = _multi_prompt_parts(prompts)
        changed, report = ooxml._apply_prompt_visual_coordination(parts)
        assert report["prompt_count"] == 4
        labels_seen = {entry["color"] for entry in report["prompts"]}
        assert labels_seen == {"Cream", "Slate", "Sky", "Amber"}
        for entry in report["prompts"]:
            sheet_name = entry["sheet"]
            part = next(p for name, p in {f"P00_COPY_SAFE": "xl/worksheets/sheet2.xml", f"P01_COPY_SAFE": "xl/worksheets/sheet3.xml", f"P02_COPY_SAFE": "xl/worksheets/sheet4.xml", f"P03_COPY_SAFE": "xl/worksheets/sheet5.xml"}.items() if name == sheet_name)
            root = ooxml._root(parts[part], part)
            tab = root.find("m:sheetPr/m:tabColor", ooxml.NS)
            assert tab is not None, f"tab {sheet_name} has no tabColor"
            expected_rgb = _PALETTE_FILLS[entry["color"]]
            assert tab.attrib["rgb"] == f"FF{expected_rgb}", f"tab {sheet_name} expected FF{expected_rgb}, got {tab.attrib['rgb']}"

    def test_validator_reports_missing_tab_color(self):
        prompts = [
            ("P00", "P00 Cream", "Cream", _short_prompt()),
            ("P01", "P01 Slate", "Slate", _short_prompt()),
        ]
        parts = _multi_prompt_parts(prompts)
        ooxml._apply_prompt_visual_coordination(parts)
        prompt_root = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
        sheet_pr = prompt_root.find("m:sheetPr", ooxml.NS)
        if sheet_pr is not None:
            tab_color = sheet_pr.find("m:tabColor", ooxml.NS)
            if tab_color is not None:
                sheet_pr.remove(tab_color)
        parts["xl/worksheets/sheet2.xml"] = ooxml._xml(prompt_root)
        findings = ooxml._validate_prompt_visual_coordination(parts)
        assert any("tab color" in str(f).lower() for f in findings)

    def test_validator_passes_all_tabs_valid(self):
        prompts = [
            ("P00", "P00 Cream", "Cream", _short_prompt()),
            ("P01", "P01 Slate", "Slate", _short_prompt()),
            ("P02", "P02 Sky", "Sky", _short_prompt()),
            ("P03", "P03 Amber", "Amber", _short_prompt()),
        ]
        parts = _multi_prompt_parts(prompts)
        ooxml._apply_prompt_visual_coordination(parts)
        findings = ooxml._validate_prompt_visual_coordination(parts)
        assert findings == (), f"unexpected findings in multi-prompt validation: {findings}"


class TestTechnicianColumnVisibility:
    def test_hides_configured_columns(self):
        prompts = [("P00", "P00 Test", "Cream", _short_prompt())]
        parts = _multi_prompt_parts(prompts)
        profile = {
            "schema_version": 1,
            "profile_id": "test",
            "target_sheet": "Prompt_Library",
            "hidden_columns": ["F", "G"],
            "hidden_columns_note": "test",
            "preservation_rule": "test",
        }
        changed, report = ooxml._apply_technician_column_visibility(parts, profile)
        assert "xl/worksheets/sheet1.xml" in changed
        assert report["hidden_count"] == 2
        library_root = ooxml._root(parts["xl/worksheets/sheet1.xml"], "library")
        cols = library_root.find("m:cols", ooxml.NS)
        assert cols is not None
        hidden = 0
        for col_elem in cols.findall("m:col", ooxml.NS):
            if col_elem.attrib.get("hidden") == "1":
                hidden += 1
        assert hidden == 2

    def test_columns_still_contain_data_after_hiding(self):
        prompts = [("P00", "P00 Test", "Cream", _short_prompt())]
        parts = _multi_prompt_parts(prompts)
        profile = {
            "schema_version": 1,
            "profile_id": "test",
            "target_sheet": "Prompt_Library",
            "hidden_columns": ["F", "G"],
            "hidden_columns_note": "test",
            "preservation_rule": "test",
        }
        ooxml._apply_technician_column_visibility(parts, profile)
        library_root = ooxml._root(parts["xl/worksheets/sheet1.xml"], "library")
        cells = ooxml._cells(library_root)
        assert cells.get("F1") is not None, "column F header should still exist"
        assert cells.get("G1") is not None, "column G header should still exist"
        assert cells.get("F2") is not None, "column F data should still exist"

    def test_empty_hidden_columns_noop(self):
        prompts = [("P00", "P00 Test", "Cream", _short_prompt())]
        parts = _multi_prompt_parts(prompts)
        profile = {
            "schema_version": 1,
            "profile_id": "test",
            "target_sheet": "Prompt_Library",
            "hidden_columns": [],
            "hidden_columns_note": "test",
            "preservation_rule": "test",
        }
        changed, report = ooxml._apply_technician_column_visibility(parts, profile)
        assert changed == set()
        assert report["hidden_count"] == 0

    def test_fails_when_column_has_no_cells(self):
        prompts = [("P00", "P00 Test", "Cream", _short_prompt())]
        parts = _multi_prompt_parts(prompts)
        profile = {
            "schema_version": 1,
            "profile_id": "test",
            "target_sheet": "Prompt_Library",
            "hidden_columns": ["Z"],
            "hidden_columns_note": "test",
            "preservation_rule": "test",
        }
        try:
            ooxml._apply_technician_column_visibility(parts, profile)
            assert False, "should have raised"
        except ValueError as exc:
            assert "has no cells" in str(exc).lower()
