from __future__ import annotations

from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_ooxml_base as ooxml

M = ooxml.MAIN_NS
R = ooxml.REL_NS
PR = ooxml.PKG_REL_NS


def _cell(ref: str, value: str, *, formula: str | None = None) -> ET.Element:
    cell = ET.Element(f"{{{M}}}c", {"r": ref, "s": "0", "t": "inlineStr" if formula is None else "str"})
    if formula is not None:
        ET.SubElement(cell, f"{{{M}}}f").text = formula
        ET.SubElement(cell, f"{{{M}}}v").text = value
    else:
        inline = ET.SubElement(cell, f"{{{M}}}is")
        ET.SubElement(inline, f"{{{M}}}t").text = value
    return cell


def _parts() -> dict[str, bytes]:
    workbook = ET.Element(f"{{{M}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{M}}}sheets")
    ET.SubElement(sheets, f"{{{M}}}sheet", {"name": "Prompt_Library", "sheetId": "1", f"{{{R}}}id": "rId1"})
    ET.SubElement(sheets, f"{{{M}}}sheet", {"name": "P00_COPY_SAFE", "sheetId": "2", f"{{{R}}}id": "rId2"})
    rels = ET.Element(f"{{{PR}}}Relationships")
    ET.SubElement(rels, f"{{{PR}}}Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": "worksheets/sheet1.xml"})
    ET.SubElement(rels, f"{{{PR}}}Relationship", {"Id": "rId2", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": "worksheets/sheet2.xml"})

    library = ET.Element(f"{{{M}}}worksheet")
    data = ET.SubElement(library, f"{{{M}}}sheetData")
    header = ET.SubElement(data, f"{{{M}}}row", {"r": "1"})
    for index, label in enumerate(("", "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role", "Use For Progress?", "Prompt Name", "Use This When", "Inspect First", "Expected Output", "Next Step", "Proof / Acceptance Gate", "Color", "Copy-Safe Sheet", ""), start=1):
        header.append(_cell(f"{ooxml._impl._column_name(index)}1", label))
    row = ET.SubElement(data, f"{{{M}}}row", {"r": "2"})
    values = ["", "00", "P00", "INSTALL", "STANDARD AI", "role", "YES", "name", "when", "inspect", "output", "next", "proof", "Cream", "P00_COPY_SAFE", ""]
    for index, value in enumerate(values, start=1):
        column = ooxml._impl._column_name(index)
        formula = None
        if column == "C":
            formula = 'HYPERLINK("#\'P00_COPY_SAFE\'!A1:A2","P00")'
        row.append(_cell(f"{column}2", value, formula=formula))

    prompt = ET.Element(f"{{{M}}}worksheet")
    prompt_data = ET.SubElement(prompt, f"{{{M}}}sheetData")
    prow = ET.SubElement(prompt_data, f"{{{M}}}row", {"r": "1"})
    prow.append(_cell("A1", '$Repo = "xyz_repo_or_path"'))

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

    return {
        "xl/workbook.xml": ooxml._xml(workbook),
        "xl/_rels/workbook.xml.rels": ooxml._xml(rels),
        "xl/worksheets/sheet1.xml": ooxml._xml(library),
        "xl/worksheets/sheet2.xml": ooxml._xml(prompt),
        "xl/styles.xml": ooxml._xml(styles),
    }


def test_placeholder_normalization_and_semantic_row_tab_colors() -> None:
    parts = _parts()
    placeholder_changed, placeholder_report = ooxml._normalize_prompt_placeholders(parts)
    visual_changed, visual_report = ooxml._apply_prompt_visual_coordination(parts)
    assert placeholder_report["replacement_count"] == 1
    assert "xl/worksheets/sheet2.xml" in placeholder_changed
    assert visual_report["prompt_count"] == 1
    assert "xl/styles.xml" in visual_changed
    assert ooxml._validate_prompt_placeholder_ergonomics(parts) == ()
    assert ooxml._validate_prompt_visual_coordination(parts) == ()
    prompt_root = ooxml._root(parts["xl/worksheets/sheet2.xml"], "prompt")
    assert ooxml._cell_display(ooxml._cells(prompt_root)["A1"], ()) == "$Repo = xyz_repo_or_path"
    assert prompt_root.find("m:sheetPr/m:tabColor", ooxml.NS).attrib["rgb"] == "FFF7E6C4"
