"""Read-only OOXML helpers shared by AI Harness Prompt Kit validators."""
from __future__ import annotations

import posixpath
import re
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
XDR_NS = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS, "a": DRAWING_NS, "xdr": XDR_NS}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$")


def xml_root(zf: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(zf.read(part))


def shared_strings(zf: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = xml_root(zf, "xl/sharedStrings.xml")
    return [
        "".join(node.text or "" for node in si.iter(f"{{{MAIN_NS}}}t"))
        for si in root.findall("m:si", NS)
    ]


def cell_value(cell: ET.Element, shared: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def workbook_sheet_map(zf: zipfile.ZipFile) -> Dict[str, str]:
    workbook = xml_root(zf, "xl/workbook.xml")
    rels = xml_root(zf, "xl/_rels/workbook.xml.rels")
    targets = {rel.attrib["Id"]: rel.attrib.get("Target", "") for rel in rels}
    result: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        rid = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        target = targets.get(rid, "")
        if not target:
            continue
        if target.startswith("/"):
            part = target.lstrip("/")
        elif target.startswith("xl/"):
            part = target
        else:
            part = posixpath.normpath(posixpath.join("xl", target))
        result[sheet.attrib["name"]] = part
    return result


def workbook_sheet_order(zf: zipfile.ZipFile) -> List[str]:
    root = xml_root(zf, "xl/workbook.xml")
    return [sheet.attrib["name"] for sheet in root.findall("m:sheets/m:sheet", NS)]


def worksheet_cells(root: ET.Element, shared: Sequence[str]) -> Dict[str, Tuple[ET.Element, str]]:
    result: Dict[str, Tuple[ET.Element, str]] = {}
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        result[ref] = (cell, cell_value(cell, shared))
    return result


def column_number(column: str) -> int:
    value = 0
    for char in column:
        value = value * 26 + ord(char) - 64
    return value


def parse_ref(ref: str) -> Optional[Tuple[int, int, int, int]]:
    match = RANGE_RE.fullmatch(ref or "")
    if not match:
        return None
    c1, r1, c2, r2 = match.groups()
    return (
        column_number(c1),
        int(r1),
        column_number(c2 or c1),
        int(r2 or r1),
    )


def relationship_part_for(source_part: str) -> str:
    directory, name = posixpath.split(source_part)
    return posixpath.join(directory, "_rels", f"{name}.rels")


def relationship_base(rel_part: str) -> str:
    if rel_part == "_rels/.rels":
        return ""
    if "/_rels/" not in rel_part or not rel_part.endswith(".rels"):
        return ""
    prefix, rel_name = rel_part.split("/_rels/", 1)
    source_part = f"{prefix}/{rel_name[:-5]}"
    return posixpath.dirname(source_part)


def resolve_relationship_target(rel_part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(relationship_base(rel_part), target)).lstrip("/")


def relationship_map(zf: zipfile.ZipFile, rel_part: str) -> Dict[str, Tuple[str, str]]:
    if rel_part not in zf.namelist():
        return {}
    root = xml_root(zf, rel_part)
    return {
        rel.attrib.get("Id", ""): (rel.attrib.get("Target", ""), rel.attrib.get("TargetMode", ""))
        for rel in root
    }


def sheet_hyperlinks(zf: zipfile.ZipFile, sheet_part: str) -> Dict[str, str]:
    root = xml_root(zf, sheet_part)
    result: Dict[str, str] = {}
    rels = relationship_map(zf, relationship_part_for(sheet_part))
    for link in root.findall(".//m:hyperlinks/m:hyperlink", NS):
        ref = link.attrib.get("ref", "")
        if not ref:
            continue
        location = link.attrib.get("location")
        if location is not None:
            result[ref] = location
            continue
        rid = link.attrib.get(f"{{{REL_NS}}}id", "")
        result[ref] = rels.get(rid, ("", ""))[0]
    return result


def drawing_backlink_target(zf: zipfile.ZipFile, sheet_part: str) -> Tuple[str, str]:
    """Return (visible label, relationship target) for a sheet drawing hyperlink."""
    sheet_root = xml_root(zf, sheet_part)
    drawing = sheet_root.find("m:drawing", NS)
    if drawing is None:
        return "", ""
    sheet_rels = relationship_map(zf, relationship_part_for(sheet_part))
    rid = drawing.attrib.get(f"{{{REL_NS}}}id", "")
    target = sheet_rels.get(rid, ("", ""))[0]
    if not target:
        return "", ""
    drawing_part = resolve_relationship_target(relationship_part_for(sheet_part), target)
    if drawing_part not in zf.namelist():
        return "", ""
    drawing_root = xml_root(zf, drawing_part)
    label = "".join(node.text or "" for node in drawing_root.findall(".//a:t", NS))
    hyperlink = drawing_root.find(".//a:hlinkClick", NS)
    if hyperlink is None:
        return label, ""
    hyperlink_rid = hyperlink.attrib.get(f"{{{REL_NS}}}id", "")
    drawing_rels = relationship_map(zf, relationship_part_for(drawing_part))
    return label, drawing_rels.get(hyperlink_rid, ("", ""))[0]


def styles(zf: zipfile.ZipFile) -> Tuple[List[dict], List[dict]]:
    root = xml_root(zf, "xl/styles.xml")
    fonts: List[dict] = []
    fonts_node = root.find("m:fonts", NS)
    if fonts_node is not None:
        for font in fonts_node.findall("m:font", NS):
            name = font.find("m:name", NS)
            size = font.find("m:sz", NS)
            fonts.append({
                "name": name.attrib.get("val", "") if name is not None else "",
                "size": float(size.attrib.get("val", "0")) if size is not None else 0.0,
                "bold": font.find("m:b", NS) is not None,
                "italic": font.find("m:i", NS) is not None,
            })
    xfs: List[dict] = []
    xfs_node = root.find("m:cellXfs", NS)
    if xfs_node is not None:
        for xf in xfs_node.findall("m:xf", NS):
            try:
                font_id = int(xf.attrib.get("fontId", "0"))
            except ValueError:
                font_id = -1
            xfs.append({"font_id": font_id})
    return fonts, xfs


def font_for_cell(cell: ET.Element, fonts: Sequence[dict], xfs: Sequence[dict]) -> Optional[dict]:
    try:
        style_id = int(cell.attrib.get("s", "0"))
        font_id = xfs[style_id]["font_id"]
        return fonts[font_id]
    except (ValueError, IndexError, KeyError):
        return None


def prompt_surface(root: ET.Element, shared: Sequence[str]) -> dict:
    refs: List[str] = []
    rows: List[int] = []
    non_a: List[str] = []
    blank_cells: List[str] = []
    duplicates: List[str] = []
    seen = set()
    for cell in root.findall(".//m:c", NS):
        ref = cell.attrib.get("r", "")
        refs.append(ref)
        if ref in seen:
            duplicates.append(ref)
        seen.add(ref)
        match = CELL_RE.fullmatch(ref)
        if not match:
            continue
        col, row = match.groups()
        if col != "A":
            non_a.append(ref)
        value = cell_value(cell, shared)
        if value:
            rows.append(int(row))
        else:
            blank_cells.append(ref)
    last = max(rows) if rows else 0
    dimension = root.find("m:dimension", NS)
    dimension_ref = dimension.attrib.get("ref", "") if dimension is not None else ""
    return {
        "refs": refs,
        "payload_rows": rows,
        "last_payload_row": last,
        "non_a_cells": non_a,
        "blank_explicit_cells": blank_cells,
        "duplicates": duplicates,
        "dimension": dimension_ref,
        "dense": rows == list(range(1, last + 1)),
        "exact_cell_endpoint": len(refs) == last,
    }
