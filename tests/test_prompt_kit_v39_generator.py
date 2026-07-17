from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from triage.prompt_kit_v39_generator import (
    ADVANCED_STANDARD_AI_IDS,
    APP_NS,
    ARTIFACT_NAME,
    CONTENT_TYPES_NS,
    GNHF_PROMPT_IDS,
    MAIN_NS,
    PKG_REL_NS,
    REL_NS,
    VT_NS,
    generate_v39,
    validate_v39,
)


def _cell(ref: str, value: str, *, formula: str | None = None, style: str = "1") -> ET.Element:
    attrs = {"r": ref, "s": style, "t": "str"}
    cell = ET.Element(f"{{{MAIN_NS}}}c", attrs)
    if formula is not None:
        ET.SubElement(cell, f"{{{MAIN_NS}}}f").text = formula
    ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = value
    return cell


def _prompt_sheet(prompt_id: str, text: str) -> bytes:
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    ET.SubElement(root, f"{{{MAIN_NS}}}dimension", {"ref": "A1:C2"})
    views = ET.SubElement(root, f"{{{MAIN_NS}}}sheetViews")
    ET.SubElement(views, f"{{{MAIN_NS}}}sheetView", {"workbookViewId": "0"})
    ET.SubElement(root, f"{{{MAIN_NS}}}sheetFormatPr", {"defaultRowHeight": "15"})
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    top = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": "1", "spans": "1:3"})
    top.append(_cell("A1", text))
    top.append(_cell("B1", "Prompt Library", formula='HYPERLINK("#\'Prompt_Library\'!A2:P2","Prompt Library")'))
    top.append(_cell("C1", "Copy A1:A2 only", formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","Copy A1:A2 only")'))
    bottom = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": "2", "spans": "1:3"})
    bottom.append(_cell("A2", "END"))
    bottom.append(_cell("B2", "Prompt Library", formula='HYPERLINK("#\'Prompt_Library\'!A2:P2","Prompt Library")'))
    bottom.append(_cell("C2", "Copy A1:A2 only", formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","Copy A1:A2 only")'))
    ET.SubElement(root, f"{{{MAIN_NS}}}sheetProtection", {"sheet": "1", "objects": "1", "scenarios": "1"})
    links = ET.SubElement(root, f"{{{MAIN_NS}}}hyperlinks")
    ET.SubElement(links, f"{{{MAIN_NS}}}hyperlink", {"ref": "C1", "location": "'Prompt_Library'!A1"})
    ET.SubElement(links, f"{{{MAIN_NS}}}hyperlink", {"ref": "C2", "location": "'Prompt_Library'!A1"})
    ET.SubElement(root, f"{{{MAIN_NS}}}pageMargins", {"left": "0.7", "right": "0.7", "top": "0.75", "bottom": "0.75", "header": "0.3", "footer": "0.3"})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _library_sheet() -> bytes:
    headers = [
        "Seq",
        "Prompt ID",
        "Prompt Type",
        "Prompt Class",
        "Sprint Path Role",
        "Use For Progress?",
        "Prompt Name",
        "Use This When",
        "Inspect First",
        "Expected Output",
        "Next Step",
        "Proof / Acceptance Gate",
        "Color",
        "Copy-Safe Sheet",
    ]
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    ET.SubElement(root, f"{{{MAIN_NS}}}dimension", {"ref": "A1:P46"})
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    header = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": "1", "spans": "1:16"})
    header.append(_cell("A1", "↓ Bottom"))
    for offset, value in enumerate(headers, start=2):
        header.append(_cell(f"{chr(64 + offset)}1", value))
    header.append(_cell("P1", "↓ Bottom"))
    links = []
    for number in range(45):
        prompt_id = f"P{number:02d}"
        row_number = number + 2
        row = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": str(row_number), "spans": "1:16"})
        values = {
            "B": str(number),
            "D": "GNHF COMMAND" if prompt_id in GNHF_PROMPT_IDS else "STANDARD AI",
            "E": "GNHF / TERMINAL" if prompt_id in GNHF_PROMPT_IDS else "STANDARD AI / REPOSITORY",
            "F": "role",
            "G": "YES",
            "H": f"Prompt {prompt_id}",
            "I": "when",
            "J": "inspect",
            "K": "output",
            "L": "next",
            "M": "proof",
            "N": "Blue",
        }
        row.append(_cell(f"A{row_number}", ""))
        for column in "BDEFGHIJKLMN":
            row.append(_cell(f"{column}{row_number}", values[column]))
        row.append(
            _cell(
                f"C{row_number}",
                prompt_id,
                formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","{prompt_id}")',
            )
        )
        row.append(
            _cell(
                f"O{row_number}",
                f"{prompt_id}_COPY_SAFE",
                formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","{prompt_id}_COPY_SAFE")',
            )
        )
        row.append(_cell(f"P{row_number}", ""))
        links.extend(
            [
                (f"C{row_number}", f"'{prompt_id}_COPY_SAFE'!A1:A2", prompt_id),
                (f"O{row_number}", f"'{prompt_id}_COPY_SAFE'!A1:A2", f"{prompt_id}_COPY_SAFE"),
            ]
        )
    ET.SubElement(root, f"{{{MAIN_NS}}}sheetProtection", {"sheet": "1"})
    hyperlinks = ET.SubElement(root, f"{{{MAIN_NS}}}hyperlinks")
    for ref, location, display in links:
        ET.SubElement(hyperlinks, f"{{{MAIN_NS}}}hyperlink", {"ref": ref, "location": location, "display": display})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_v38(path: Path) -> None:
    names = ["Prompt_Library", *[f"P{number:02d}_COPY_SAFE" for number in range(45)]]
    workbook = ET.Element(f"{{{MAIN_NS}}}workbook")
    ET.SubElement(workbook, f"{{{MAIN_NS}}}workbookProtection", {"lockStructure": "1"})
    sheets = ET.SubElement(workbook, f"{{{MAIN_NS}}}sheets")
    rels = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    content_types = ET.Element(f"{{{CONTENT_TYPES_NS}}}Types")
    ET.SubElement(content_types, f"{{{CONTENT_TYPES_NS}}}Default", {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(content_types, f"{{{CONTENT_TYPES_NS}}}Override", {"PartName": "/xl/workbook.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"})
    for index, name in enumerate(names, start=1):
        rid = f"rId{index}"
        ET.SubElement(sheets, f"{{{MAIN_NS}}}sheet", {"name": name, "sheetId": str(index), f"{{{REL_NS}}}id": rid})
        ET.SubElement(
            rels,
            f"{{{PKG_REL_NS}}}Relationship",
            {
                "Id": rid,
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                "Target": f"worksheets/sheet{index}.xml",
            },
        )
        ET.SubElement(
            content_types,
            f"{{{CONTENT_TYPES_NS}}}Override",
            {
                "PartName": f"/xl/worksheets/sheet{index}.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
            },
        )
    app = ET.Element(f"{{{APP_NS}}}Properties")
    heading_pairs = ET.SubElement(app, f"{{{APP_NS}}}HeadingPairs")
    hp_vector = ET.SubElement(heading_pairs, f"{{{VT_NS}}}vector", {"size": "2", "baseType": "variant"})
    first = ET.SubElement(hp_vector, f"{{{VT_NS}}}variant")
    ET.SubElement(first, f"{{{VT_NS}}}lpstr").text = "Worksheets"
    second = ET.SubElement(hp_vector, f"{{{VT_NS}}}variant")
    ET.SubElement(second, f"{{{VT_NS}}}i4").text = str(len(names))
    titles = ET.SubElement(app, f"{{{APP_NS}}}TitlesOfParts")
    vector = ET.SubElement(titles, f"{{{VT_NS}}}vector", {"size": str(len(names)), "baseType": "lpstr"})
    for name in names:
        ET.SubElement(vector, f"{{{VT_NS}}}lpstr").text = name

    formula_cells = []
    for row in range(2, 47):
        formula_cells.extend([(1, f"C{row}"), (1, f"O{row}")])
    for sheet_id in range(2, 47):
        formula_cells.extend([(sheet_id, "B1"), (sheet_id, "C1"), (sheet_id, "B2"), (sheet_id, "C2")])
    chain = ET.Element(f"{{{MAIN_NS}}}calcChain")
    for sheet_id, ref in formula_cells:
        ET.SubElement(chain, f"{{{MAIN_NS}}}c", {"r": ref, "i": str(sheet_id)})

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", ET.tostring(content_types, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(rels, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/worksheets/sheet1.xml", _library_sheet())
        for index, number in enumerate(range(45), start=2):
            prompt_id = f"P{number:02d}"
            text = "gnhf `" if prompt_id in GNHF_PROMPT_IDS else "PROMPT SURFACE: STANDARD AI."
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _prompt_sheet(prompt_id, text))
        archive.writestr("xl/calcChain.xml", ET.tostring(chain, encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/app.xml", ET.tostring(app, encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/core.xml", b"unchanged")


def test_v39_adds_local_first_prompts_and_separates_surfaces(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    output = tmp_path / "out"
    _build_v38(source)
    spec = Path(__file__).parents[1] / "configs/prompt_kit/v39_local_first_prompts.json"

    manifest = generate_v39(source, output, spec_path=spec)

    workbook = output / f"{ARTIFACT_NAME}.xlsx"
    report = validate_v39(workbook, spec)
    assert report.valid, report.findings
    assert report.prompt_count == 50
    assert report.directory_gate_prompts == ("P45", "P46", "P47", "P48", "P49")
    assert "P46" in report.zero_token_prompts
    assert manifest["new_prompt_ids"] == ["P45", "P46", "P47", "P48", "P49"]
    assert manifest["prompt_surface_taxonomy"]["gnhf"]["name"] == "Goodnight, Have Fun (GNHF) prompt"
    assert manifest["byte_deterministic"] is True
    with zipfile.ZipFile(workbook) as archive:
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        names = [item.attrib["name"] for item in workbook_root.findall(f".//{{{MAIN_NS}}}sheet")]
        assert names[-13:] == [f"{prompt_id}_COPY_SAFE" for prompt_id in ADVANCED_STANDARD_AI_IDS]
        app = ET.fromstring(archive.read("docProps/app.xml"))
        titles = [item.text for item in app.findall(f".//{{{VT_NS}}}lpstr")]
        assert "P49_COPY_SAFE" in titles


def test_v39_is_deterministic_for_identical_source_and_spec(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)
    spec = Path(__file__).parents[1] / "configs/prompt_kit/v39_local_first_prompts.json"

    generate_v39(source, tmp_path / "out1", spec_path=spec)
    generate_v39(source, tmp_path / "out2", spec_path=spec)

    one = (tmp_path / "out1" / f"{ARTIFACT_NAME}.xlsx").read_bytes()
    two = (tmp_path / "out2" / f"{ARTIFACT_NAME}.xlsx").read_bytes()
    assert one == two


def test_v39_fails_closed_when_source_is_not_exact_v38_prompt_floor(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)
    spec = Path(__file__).parents[1] / "configs/prompt_kit/v39_local_first_prompts.json"
    with zipfile.ZipFile(source, "a") as archive:
        archive.writestr("xl/worksheets/sheet47.xml", _prompt_sheet("P45", "unexpected"))
    with pytest.raises(ValueError, match="exact V38 floor"):
        generate_v39(source, tmp_path / "out", spec_path=spec)


def test_spec_rejects_gnhf_markers_in_standard_ai_prompt(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)
    original = json.loads((Path(__file__).parents[1] / "configs/prompt_kit/v39_local_first_prompts.json").read_text())
    original["new_prompts"][0]["lines"].append("gnhf `")
    bad_spec = tmp_path / "bad.json"
    bad_spec.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="contains GNHF command markers"):
        generate_v39(source, tmp_path / "out", spec_path=bad_spec)
