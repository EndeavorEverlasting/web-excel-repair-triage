from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from triage.prompt_kit_copy_range_links import MAIN_NS, NS, apply_copy_range_links

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sheet(cells: list[tuple[str, str, str]]) -> bytes:
    root = ET.Element(f"{{{MAIN_NS}}}worksheet")
    data = ET.SubElement(root, f"{{{MAIN_NS}}}sheetData")
    rows: dict[int, ET.Element] = {}
    for ref, kind, value in cells:
        row_number = int("".join(ch for ch in ref if ch.isdigit()))
        row = rows.get(row_number)
        if row is None:
            row = ET.SubElement(data, f"{{{MAIN_NS}}}row", {"r": str(row_number)})
            rows[row_number] = row
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


def _build_fixture(path: Path) -> None:
    names = ["Prompt_Library", "P00_COPY_SAFE", "P01_COPY_SAFE"]
    workbook = ET.Element(f"{{{MAIN_NS}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{MAIN_NS}}}sheets")
    rels = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    for index, name in enumerate(names, start=1):
        rid = f"rId{index}"
        ET.SubElement(sheets, f"{{{MAIN_NS}}}sheet", {
            "name": name,
            "sheetId": str(index),
            f"{{{REL_NS}}}id": rid,
        })
        ET.SubElement(rels, f"{{{PKG_REL_NS}}}Relationship", {
            "Id": rid,
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
            "Target": f"worksheets/sheet{index}.xml",
        })

    shared = ET.Element(f"{{{MAIN_NS}}}sst", {"count": "2", "uniqueCount": "2"})
    for text in ("Copy A1:A3 only", "Copy A1:A2 only"):
        item = ET.SubElement(shared, f"{{{MAIN_NS}}}si")
        ET.SubElement(item, f"{{{MAIN_NS}}}t").text = text

    library = _sheet([
        ("C2", "formula", 'HYPERLINK("#\'P00_COPY_SAFE\'!A1:A3","P00")'),
        ("C3", "formula", 'HYPERLINK("#\'P01_COPY_SAFE\'!A1:A2","P01")'),
    ])
    p00 = _sheet([
        ("A1", "text", "first"), ("A3", "text", "last"),
        ("B1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A2:P2","back")'),
        ("C1", "shared", "0"), ("C3", "shared", "0"),
        ("E1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A2:P2","back")'),
    ])
    p01 = _sheet([
        ("A1", "text", "first"), ("A2", "text", "last"),
        ("B1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A3:P3","back")'),
        ("C1", "shared", "1"), ("C2", "shared", "1"),
        ("E1", "formula", 'HYPERLINK("#\'Prompt_Library\'!A3:P3","back")'),
    ])
    chain = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<calcChain xmlns="{MAIN_NS}">'
        '<c r="C2" i="0"/><c r="C3" i="0"/>'
        '<c r="B1" i="1"/><c r="E1" i="1"/>'
        '<c r="B1" i="2"/><c r="E1" i="2"/>'
        '</calcChain>'
    ).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("xl/workbook.xml", ET.tostring(workbook, encoding="utf-8", xml_declaration=True))
        zf.writestr("xl/_rels/workbook.xml.rels", ET.tostring(rels, encoding="utf-8", xml_declaration=True))
        zf.writestr("xl/sharedStrings.xml", ET.tostring(shared, encoding="utf-8", xml_declaration=True))
        zf.writestr("xl/worksheets/sheet1.xml", library)
        zf.writestr("xl/worksheets/sheet2.xml", p00)
        zf.writestr("xl/worksheets/sheet3.xml", p01)
        zf.writestr("xl/calcChain.xml", chain)
        zf.writestr("docProps/core.xml", b"unchanged")


def _formulas(path: Path, part: str) -> dict[str, str]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read(part))
    return {
        cell.attrib["r"]: cell.find("m:f", NS).text
        for cell in root.findall(".//m:c", NS)
        if cell.find("m:f", NS) is not None
    }


def test_copy_range_links_are_package_preserving_calc_chain_aware_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "v37.xlsx"
    output = tmp_path / "v38.xlsx"
    second = tmp_path / "v38-second.xlsx"
    _build_fixture(source)

    result = apply_copy_range_links(source, output)
    assert result.prompt_count == 2
    assert result.links_written == 4
    assert result.formula_count_before == 6
    assert result.formula_count_after == 10
    assert result.changed_parts == (
        "xl/calcChain.xml",
        "xl/worksheets/sheet2.xml",
        "xl/worksheets/sheet3.xml",
    )

    p00 = _formulas(output, "xl/worksheets/sheet2.xml")
    assert p00["C1"] == 'HYPERLINK("#\'P00_COPY_SAFE\'!A1:A3","Copy A1:A3 only")'
    assert p00["C3"] == p00["C1"]
    p01 = _formulas(output, "xl/worksheets/sheet3.xml")
    assert p01["C1"] == 'HYPERLINK("#\'P01_COPY_SAFE\'!A1:A2","Copy A1:A2 only")'
    assert p01["C2"] == p01["C1"]

    with zipfile.ZipFile(source) as before, zipfile.ZipFile(output) as after:
        assert before.namelist() == after.namelist()
        allowed = set(result.changed_parts)
        for name in before.namelist():
            if name not in allowed:
                assert before.read(name) == after.read(name), name
        chain = ET.fromstring(after.read("xl/calcChain.xml"))
        entries = {(int(cell.attrib["i"]), cell.attrib["r"]) for cell in chain.findall("m:c", NS)}
        assert {(1, "C1"), (1, "C3"), (2, "C1"), (2, "C2")} <= entries

    apply_copy_range_links(output, second)
    assert _sha(output) == _sha(second)
    assert output.read_bytes() == second.read_bytes()
