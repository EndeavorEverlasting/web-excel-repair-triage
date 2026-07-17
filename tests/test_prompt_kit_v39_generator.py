from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from triage import prompt_kit_v39_ooxml_base as ooxml
from triage.prompt_kit_v39_generator import (
    APPEND_ORDER,
    ARTIFACT_NAME,
    GNHF_HARNESS_IDS,
    STANDARD_AI_EXTENSION_IDS,
    generate_v39,
    validate_v39,
)

MAIN_NS = ooxml.MAIN_NS
REL_NS = ooxml.REL_NS
PKG_REL_NS = ooxml.PKG_REL_NS
CONTENT_TYPES_NS = ooxml.CONTENT_TYPES_NS
APP_NS = ooxml.APP_NS
VT_NS = ooxml.VT_NS

STANDARD_SPEC = Path(__file__).parents[1] / "configs/prompt_kit/v39_standard_ai_extensions.json"
GNHF_SPEC = Path(__file__).parents[1] / "configs/prompt_kit/v39_gnhf_harness_prompts.json"


def _cell(ref: str, value: str, *, formula: str | None = None, style: str = "1") -> ET.Element:
    cell = ET.Element(f"{{{MAIN_NS}}}c", {"r": ref, "s": style, "t": "str"})
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
        "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role",
        "Use For Progress?", "Prompt Name", "Use This When", "Inspect First",
        "Expected Output", "Next Step", "Proof / Acceptance Gate", "Color", "Copy-Safe Sheet",
    ]
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    ET.SubElement(root, f"{{{MAIN_NS}}}dimension", {"ref": "A1:P46"})
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    header = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": "1", "spans": "1:16"})
    header.append(_cell("A1", "↓ Bottom"))
    for offset, value in enumerate(headers, start=2):
        header.append(_cell(f"{chr(64 + offset)}1", value))
    header.append(_cell("P1", "↓ Bottom"))
    links: list[tuple[str, str, str]] = []
    for number in range(45):
        prompt_id = f"P{number:02d}"
        row_number = number + 2
        row = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": str(row_number), "spans": "1:16"})
        prompt_class = "GNHF / TERMINAL" if 26 <= number <= 36 else "STANDARD AI / REPOSITORY"
        values = {
            "B": str(number), "D": "GNHF COMMAND" if 26 <= number <= 36 else "STANDARD AI",
            "E": prompt_class, "F": "role", "G": "YES", "H": f"Prompt {prompt_id}",
            "I": "when", "J": "inspect", "K": "output", "L": "next", "M": "proof", "N": "Blue",
        }
        row.append(_cell(f"A{row_number}", ""))
        for column in "BDEFGHIJKLMN":
            row.append(_cell(f"{column}{row_number}", values[column]))
        row.append(_cell(f"C{row_number}", prompt_id, formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","{prompt_id}")'))
        row.append(_cell(f"O{row_number}", f"{prompt_id}_COPY_SAFE", formula=f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!A1:A2","{prompt_id}_COPY_SAFE")'))
        row.append(_cell(f"P{row_number}", ""))
        links.extend([
            (f"C{row_number}", f"'{prompt_id}_COPY_SAFE'!A1:A2", prompt_id),
            (f"O{row_number}", f"'{prompt_id}_COPY_SAFE'!A1:A2", f"{prompt_id}_COPY_SAFE"),
        ])
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
        ET.SubElement(rels, f"{{{PKG_REL_NS}}}Relationship", {
            "Id": rid,
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
            "Target": f"worksheets/sheet{index}.xml",
        })
        ET.SubElement(content_types, f"{{{CONTENT_TYPES_NS}}}Override", {
            "PartName": f"/xl/worksheets/sheet{index}.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        })
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

    formulas: list[tuple[int, str]] = []
    for row in range(2, 47):
        formulas.extend([(1, f"C{row}"), (1, f"O{row}")])
    for sheet_id in range(2, 47):
        formulas.extend([(sheet_id, "B1"), (sheet_id, "C1"), (sheet_id, "B2"), (sheet_id, "C2")])
    chain = ET.Element(f"{{{MAIN_NS}}}calcChain")
    for sheet_id, ref in formulas:
        ET.SubElement(chain, f"{{{MAIN_NS}}}c", {"r": ref, "i": str(sheet_id)})

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", ET.tostring(content_types, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(rels, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/worksheets/sheet1.xml", _library_sheet())
        for index, number in enumerate(range(45), start=2):
            prompt_id = f"P{number:02d}"
            text = "gnhf `" if 26 <= number <= 36 else "PROMPT SURFACE: STANDARD AI."
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _prompt_sheet(prompt_id, text))
        archive.writestr("xl/calcChain.xml", ET.tostring(chain, encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/app.xml", ET.tostring(app, encoding="utf-8", xml_declaration=True))
        archive.writestr("docProps/core.xml", b"unchanged")


def test_v39_preserves_semantic_sections_and_adds_p55(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    output = tmp_path / "out"
    _build_v38(source)

    manifest = generate_v39(source, output, standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)

    workbook = output / f"{ARTIFACT_NAME}.xlsx"
    report = validate_v39(workbook, standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)
    assert report.valid, report.findings
    assert report.prompt_count == 56
    assert report.standard_ai_extension == STANDARD_AI_EXTENSION_IDS
    assert report.gnhf_harness_section == GNHF_HARNESS_IDS
    assert report.append_order == APPEND_ORDER
    assert report.directory_gate_prompts == STANDARD_AI_EXTENSION_IDS
    assert report.zero_token_prompts == ("P51",)
    assert manifest["github_cli_bootstrap_prompt"] == "P55"
    assert manifest["append_order"] == list(APPEND_ORDER)
    assert manifest["byte_deterministic"] is True

    package = ooxml._read_workbook(workbook)
    order, mapping, _, _ = ooxml._sheet_map(package.parts)
    expected_suffix = [f"{prompt_id}_COPY_SAFE" for prompt_id in APPEND_ORDER]
    assert order[-len(expected_suffix):] == expected_suffix
    rows, ranges = ooxml._prompt_rows_and_ranges(package.parts)
    assert [rows[prompt_id] for prompt_id in APPEND_ORDER] == list(range(rows[APPEND_ORDER[0]], rows[APPEND_ORDER[0]] + len(APPEND_ORDER)))
    p55_last = int(ranges["P55"].rsplit("A", 1)[-1])
    p55 = "\n".join(ooxml._prompt_payload(package.parts, mapping["P55_COPY_SAFE"], p55_last))
    assert "gh auth status --active --hostname github.com" in p55
    assert "gh repo create" in p55
    assert "--clone" in p55 and "--source" in p55
    assert not p55.startswith("gnhf `")
    p45_last = int(ranges["P45"].rsplit("A", 1)[-1])
    p45 = "\n".join(ooxml._prompt_payload(package.parts, mapping["P45_COPY_SAFE"], p45_last))
    assert p45.startswith("COMPILE ONLY")
    assert not p45.startswith("gnhf `")
    p46_last = int(ranges["P46"].rsplit("A", 1)[-1])
    p46 = "\n".join(ooxml._prompt_payload(package.parts, mapping["P46_COPY_SAFE"], p46_last))
    assert p46.startswith("gnhf `")


def test_v39_generation_is_byte_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)
    generate_v39(source, tmp_path / "one", standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)
    generate_v39(source, tmp_path / "two", standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)
    assert (tmp_path / "one" / f"{ARTIFACT_NAME}.xlsx").read_bytes() == (tmp_path / "two" / f"{ARTIFACT_NAME}.xlsx").read_bytes()


def test_v39_fails_closed_when_source_is_not_exact_v38_floor(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)
    with zipfile.ZipFile(source, "a") as archive:
        archive.writestr("xl/worksheets/sheet47.xml", _prompt_sheet("P50", "unexpected"))
    with pytest.raises(ValueError, match="exact P00-P44 V38 prompt floor"):
        generate_v39(source, tmp_path / "out", standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC)


def test_standard_ai_contract_cannot_take_reserved_p45_slot(tmp_path: Path) -> None:
    payload = json.loads(STANDARD_SPEC.read_text(encoding="utf-8"))
    payload["section"]["prompt_ids"][0] = "P45"
    payload["prompts"][0]["prompt_id"] = "P45"
    bad = tmp_path / "bad-standard.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="standard-AI extension must define"):
        generate_v39(tmp_path / "missing.xlsx", tmp_path / "out", standard_ai_spec=bad, gnhf_spec=GNHF_SPEC)
