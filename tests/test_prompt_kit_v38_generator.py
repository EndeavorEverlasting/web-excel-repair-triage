from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from triage.prompt_kit_copy_range_links import MAIN_NS
from triage.prompt_kit_v38_generator import ARTIFACT_NAME, generate_v38

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _sheet(cells: list[tuple[str, str, str]]) -> bytes:
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    rows: dict[int, ET.Element] = {}
    for ref, kind, value in cells:
        row_number = int("".join(ch for ch in ref if ch.isdigit()))
        row = rows.setdefault(
            row_number,
            ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": str(row_number)}),
        )
        cell = ET.SubElement(row, f"{{{MAIN_NS}}}c", {"r": ref, "s": "1"})
        if kind == "formula":
            cell.attrib["t"] = "str"
            ET.SubElement(cell, f"{{{MAIN_NS}}}f").text = value
            ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = value.rsplit('\",\"', 1)[-1].removesuffix('\")')
        elif kind == "shared":
            cell.attrib["t"] = "s"
            ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = value
        else:
            cell.attrib["t"] = "str"
            ET.SubElement(cell, f"{{{MAIN_NS}}}v").text = value
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_v37(path: Path) -> None:
    names = ["Prompt_Library", "P00_COPY_SAFE", "P01_COPY_SAFE"]
    workbook = ET.Element(f"{{{MAIN_NS}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{MAIN_NS}}}sheets")
    rels = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    for index, name in enumerate(names, start=1):
        rid = f"rId{index}"
        ET.SubElement(
            sheets,
            f"{{{MAIN_NS}}}sheet",
            {"name": name, "sheetId": str(index), f"{{{REL_NS}}}id": rid},
        )
        ET.SubElement(
            rels,
            f"{{{PKG_REL_NS}}}Relationship",
            {
                "Id": rid,
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                "Target": f"worksheets/sheet{index}.xml",
            },
        )

    shared = ET.Element(f"{{{MAIN_NS}}}sst", {"count": "2", "uniqueCount": "2"})
    for text in ("Copy A1:A3 only", "Copy A1:A2 only"):
        item = ET.SubElement(shared, f"{{{MAIN_NS}}}si")
        ET.SubElement(item, f"{{{MAIN_NS}}}t").text = text

    library = _sheet(
        [
            ("C2", "formula", 'HYPERLINK("#\'P00_COPY_SAFE\'!A1:A3","P00")'),
            ("C3", "formula", 'HYPERLINK("#\'P01_COPY_SAFE\'!A1:A2","P01")'),
        ]
    )
    p00 = _sheet(
        [
            ("A1", "text", "first"),
            ("A3", "text", "last"),
            ("B1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A2:P2","back")'),
            ("C1", "shared", "0"),
            ("C3", "shared", "0"),
        ]
    )
    p01 = _sheet(
        [
            ("A1", "text", "first"),
            ("A2", "text", "last"),
            ("B1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A3:P3","back")'),
            ("C1", "shared", "1"),
            ("C2", "shared", "1"),
        ]
    )
    chain = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<calcChain xmlns="{MAIN_NS}">'
        '<c r="C2" i="1"/><c r="C3" i="1"/>'
        '<c r="B1" i="2"/><c r="B1" i="3"/>'
        "</calcChain>"
    ).encode()

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/_rels/workbook.xml.rels", ET.tostring(rels, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/sharedStrings.xml", ET.tostring(shared, encoding="utf-8", xml_declaration=True))
        archive.writestr("xl/worksheets/sheet1.xml", library)
        archive.writestr("xl/worksheets/sheet2.xml", p00)
        archive.writestr("xl/worksheets/sheet3.xml", p01)
        archive.writestr("xl/calcChain.xml", chain)
        archive.writestr("docProps/core.xml", b"unchanged")


def test_v38_generator_names_artifacts_and_preserves_package_contract(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v37.xlsx"
    output = tmp_path / "out"
    _build_v37(source)

    manifest = generate_v38(source, output, expected_prompt_count=2)

    workbook = output / f"{ARTIFACT_NAME}.xlsx"
    manifest_path = output / f"{ARTIFACT_NAME}_manifest.json"
    bundle = output / f"{ARTIFACT_NAME}_bundle.zip"
    assert workbook.exists()
    assert manifest_path.exists()
    assert bundle.exists()
    assert manifest["artifact"] == ARTIFACT_NAME
    assert manifest["generator"] == "triage.prompt_kit_v38_generator"
    assert manifest["copy_range_links"]["prompt_count"] == 2
    assert manifest["copy_range_links"]["links_written"] == 4
    assert manifest["byte_idempotent"] is True
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["artifact"] == ARTIFACT_NAME
    with zipfile.ZipFile(bundle) as archive:
        assert workbook.name in archive.namelist()
        assert manifest_path.name in archive.namelist()


def test_v38_generator_fails_closed_on_wrong_prompt_count(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v37.xlsx"
    _build_v37(source)
    with pytest.raises(ValueError, match="requires 45 prompt tabs"):
        generate_v38(source, tmp_path / "out")
