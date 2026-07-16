from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from triage.prompt_kit_v33_generator import generate_v33
from triage.prompt_kit_v33_ooxml import CREAM_TAB_COLOR, MAIN_NS, NS, PROMPT_IDS, finalize_workbook

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _inline_cell(ref: str, text: str, style: int = 0) -> ET.Element:
    cell = ET.Element(f"{{{MAIN_NS}}}c", {"r": ref, "t": "inlineStr", "s": str(style)})
    inline = ET.SubElement(cell, f"{{{MAIN_NS}}}is")
    node = ET.SubElement(inline, f"{{{MAIN_NS}}}t")
    node.text = text
    return cell


def _worksheet(cells: list[ET.Element]) -> bytes:
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    rows = {}
    for cell in cells:
        row_number = int("".join(char for char in cell.attrib["r"] if char.isdigit()))
        row = rows.get(row_number)
        if row is None:
            row = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": str(row_number)})
            rows[row_number] = row
        row.append(cell)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _styles() -> bytes:
    root = ET.Element(f"{{{MAIN_NS}}}styleSheet")
    fonts = ET.SubElement(root, f"{{{MAIN_NS}}}fonts", {"count": "1"})
    font = ET.SubElement(fonts, f"{{{MAIN_NS}}}font")
    ET.SubElement(font, f"{{{MAIN_NS}}}sz", {"val": "11"})
    ET.SubElement(font, f"{{{MAIN_NS}}}name", {"val": "Aptos"})
    fills = ET.SubElement(root, f"{{{MAIN_NS}}}fills", {"count": "2"})
    ET.SubElement(ET.SubElement(fills, f"{{{MAIN_NS}}}fill"), f"{{{MAIN_NS}}}patternFill", {"patternType": "none"})
    ET.SubElement(ET.SubElement(fills, f"{{{MAIN_NS}}}fill"), f"{{{MAIN_NS}}}patternFill", {"patternType": "gray125"})
    borders = ET.SubElement(root, f"{{{MAIN_NS}}}borders", {"count": "1"})
    ET.SubElement(borders, f"{{{MAIN_NS}}}border")
    style_xfs = ET.SubElement(root, f"{{{MAIN_NS}}}cellStyleXfs", {"count": "1"})
    ET.SubElement(style_xfs, f"{{{MAIN_NS}}}xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0"})
    xfs = ET.SubElement(root, f"{{{MAIN_NS}}}cellXfs", {"count": "1"})
    ET.SubElement(xfs, f"{{{MAIN_NS}}}xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0", "xfId": "0"})
    styles = ET.SubElement(root, f"{{{MAIN_NS}}}cellStyles", {"count": "1"})
    ET.SubElement(styles, f"{{{MAIN_NS}}}cellStyle", {"name": "Normal", "xfId": "0", "builtinId": "0"})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_source(path: Path, *, executable_p02: bool = True) -> None:
    sheet_names = ["Prompt_Library", "Opportunity_Discovery", *(f"{prompt_id}_COPY_SAFE" for prompt_id in PROMPT_IDS)]
    workbook = ET.Element(f"{{{MAIN_NS}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{MAIN_NS}}}sheets")
    relationships = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    parts = {}
    for index, name in enumerate(sheet_names, start=1):
        rid = f"rId{index}"
        ET.SubElement(
            sheets,
            f"{{{MAIN_NS}}}sheet",
            {"name": name, "sheetId": str(index), f"{{{REL_NS}}}id": rid},
        )
        ET.SubElement(
            relationships,
            f"{{{PKG_REL_NS}}}Relationship",
            {"Id": rid, "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "Target": f"worksheets/sheet{index}.xml"},
        )
        if name == "Prompt_Library":
            cells = [_inline_cell("B1", "Seq"), _inline_cell("C1", "Prompt ID"), _inline_cell("P1", "rail")]
            for prompt_index, prompt_id in enumerate(PROMPT_IDS, start=2):
                cells.extend([
                    _inline_cell(f"B{prompt_index}", f"{prompt_index - 2:02d}"),
                    _inline_cell(f"C{prompt_index}", prompt_id),
                    _inline_cell(f"N{prompt_index}", "Slate"),
                    _inline_cell(f"O{prompt_index}", f"{prompt_id}_COPY_SAFE"),
                ])
            cells.extend([_inline_cell("A47", "bottom"), _inline_cell("P47", "bottom")])
            parts[f"xl/worksheets/sheet{index}.xml"] = _worksheet(cells)
        elif name == "Opportunity_Discovery":
            parts[f"xl/worksheets/sheet{index}.xml"] = _worksheet([_inline_cell("A1", "Editable")])
        else:
            prompt_id = name[:3]
            if prompt_id == "P02":
                lines = [
                    "5. HARNESS BUILD OWNERSHIP" if executable_p02 else "5. HARNESS DESCRIPTION",
                    "Do not stop at describing, classifying, or mapping the harness." if executable_p02 else "Describe the harness.",
                    "- commit coherent changes" if executable_p02 else "- explain changes",
                    "- push normally" if executable_p02 else "- provide a plan",
                ]
            else:
                lines = [f"{prompt_id} first line", f"{prompt_id} final line"]
            parts[f"xl/worksheets/sheet{index}.xml"] = _worksheet([
                _inline_cell(f"A{row}", text) for row, text in enumerate(lines, start=1)
            ])

    content_types = ET.Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
    ET.SubElement(content_types, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(content_types, "Default", {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(content_types, "Override", {"PartName": "/xl/workbook.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"})
    ET.SubElement(content_types, "Override", {"PartName": "/xl/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"})
    for index in range(1, len(sheet_names) + 1):
        ET.SubElement(content_types, "Override", {"PartName": f"/xl/worksheets/sheet{index}.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"})

    root_rels = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    ET.SubElement(root_rels, f"{{{PKG_REL_NS}}}Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "xl/workbook.xml"})

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", ET.tostring(content_types, encoding="utf-8", xml_declaration=True))
        archive.writestr("_rels/.rels", ET.tostring(root_rels, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(relationships, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/styles.xml", _styles())
        for name, content in parts.items():
            archive.writestr(name, content)


def _sheet_map(zf: zipfile.ZipFile):
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    return {
        sheet.attrib["name"]: "xl/" + targets[sheet.attrib[f"{{{REL_NS}}}id"]]
        for sheet in workbook.findall("m:sheets/m:sheet", NS)
    }


def _formula(root: ET.Element, ref: str) -> str:
    cell = root.find(f".//m:c[@r='{ref}']", NS)
    assert cell is not None
    formula = cell.find("m:f", NS)
    assert formula is not None
    return formula.text or ""


def test_finalize_codifies_navigation_ranges_cream_tabs_and_protection(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    output = tmp_path / "output.xlsx"
    _build_source(source)
    ranges = finalize_workbook(source, output)
    assert len(ranges) == 45
    assert ranges[2].range == "A1:A4"

    with zipfile.ZipFile(output) as zf:
        sheets = _sheet_map(zf)
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        assert workbook.find("m:workbookProtection", NS).attrib["lockStructure"] == "1"
        library = ET.fromstring(zf.read(sheets["Prompt_Library"]))
        assert _formula(library, "A1") == 'HYPERLINK("#\'Prompt_Library\'!A47","↓ Bottom")'
        assert _formula(library, "C4") == 'HYPERLINK("#\'P02_COPY_SAFE\'!A1:A4","P02")'
        assert _formula(library, "P47") == 'HYPERLINK("#\'Prompt_Library\'!P1","↑ Top")'

        p02 = ET.fromstring(zf.read(sheets["P02_COPY_SAFE"]))
        assert _formula(p02, "B1") == 'HYPERLINK("#\'Prompt_Library\'!A4:P4","← Prompt Library · P02")'
        assert _formula(p02, "E4") == 'HYPERLINK("#\'Prompt_Library\'!A4:P4","P02 · Prompt Library →")'

        for name in ("Prompt_Library", "Opportunity_Discovery", "P07_COPY_SAFE", "P39_COPY_SAFE"):
            root = ET.fromstring(zf.read(sheets[name]))
            assert root.find("m:sheetPr/m:tabColor", NS).attrib["rgb"] == CREAM_TAB_COLOR

        for part in sheets.values():
            root = ET.fromstring(zf.read(part))
            assert root.find("m:sheetProtection", NS) is not None

        opportunity = ET.fromstring(zf.read(sheets["Opportunity_Discovery"]))
        rows = {int(row.attrib["r"]): row for row in opportunity.findall("m:sheetData/m:row", NS)}
        assert set(range(1, 101)).issubset(rows)
        styles = ET.fromstring(zf.read("xl/styles.xml"))
        xfs = list(styles.find("m:cellXfs", NS))
        row_style = xfs[int(rows[100].attrib["s"])]
        assert row_style.find("m:protection", NS).attrib["locked"] == "0"


def test_p02_must_assign_harness_build_work(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    output = tmp_path / "output.xlsx"
    _build_source(source, executable_p02=False)
    with pytest.raises(ValueError, match="P02 does not assign executable harness construction"):
        finalize_workbook(source, output)


def test_generate_bundle_preserves_support_files_and_writes_manifest(tmp_path: Path) -> None:
    source_workbook = tmp_path / "source.xlsx"
    _build_source(source_workbook)
    source_bundle = tmp_path / "source_bundle.zip"
    with zipfile.ZipFile(source_bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(source_workbook, "AI_Harness_Prompt_Kit_v33.xlsx")
        archive.writestr("AI_Harness_Prompt_Kit_v33_Night_Shift_Quickstart.md", "quickstart")

    result = generate_v33(source_bundle, tmp_path / "out")
    manifest = json.loads((tmp_path / "out" / "AI_Harness_Prompt_Kit_v33_manifest.json").read_text())
    assert manifest["gnhf_build_prompt"] == "P39"
    assert manifest["editable_range"] == "Opportunity_Discovery!A1:R100"
    assert len(manifest["prompt_ranges"]) == 45
    with zipfile.ZipFile(result["bundle"]) as archive:
        names = set(archive.namelist())
        assert "AI_Harness_Prompt_Kit_v33.xlsx" in names
        assert "AI_Harness_Prompt_Kit_v33_manifest.json" in names
        assert "AI_Harness_Prompt_Kit_v33_Night_Shift_Quickstart.md" in names
