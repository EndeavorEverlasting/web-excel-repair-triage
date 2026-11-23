"""Fail closed when a workbook rewrite drops Excel-for-Web user affordances.

This is a *pairwise* check, complementary to the single-package compatibility
scanner and cell-level semantic preservation. Never print workbook cell values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"
D = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _resolve(base: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), target))


def _relationships(z: zipfile.ZipFile, part: str) -> dict[str, str]:
    rels = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
    if rels not in z.namelist():
        return {}
    root = ET.fromstring(z.read(rels))
    return {
        e.attrib["Id"]: _resolve(part, e.attrib["Target"])
        for e in root.findall(f"{{{P}}}Relationship")
        if e.attrib.get("TargetMode") != "External"
    }


def _images(z: zipfile.ZipFile, sheet_part: str, root: ET.Element) -> list[tuple]:
    images = []
    sheet_rels = _relationships(z, sheet_part)
    for drawing in root.findall(f"{{{S}}}drawing"):
        drawing_part = sheet_rels.get(drawing.attrib.get(f"{{{R}}}id", ""), "")
        if drawing_part not in z.namelist():
            images.append(("broken_drawing",))
            continue
        drawing_root = ET.fromstring(z.read(drawing_part))
        drawing_rels = _relationships(z, drawing_part)
        for anchor in drawing_root:
            start = anchor.find(f"{{{D}}}from")
            position = tuple(
                (start.findtext(f"{{{D}}}{tag}") or "0") if start is not None else ""
                for tag in ("row", "col", "rowOff", "colOff")
            )
            extent = anchor.find(f"{{{D}}}ext")
            size = tuple(extent.attrib.get(tag, "") for tag in ("cx", "cy")) if extent is not None else ()
            for blip in anchor.iter(f"{{{A}}}blip"):
                media = drawing_rels.get(blip.attrib.get(f"{{{R}}}embed", ""), "")
                digest = hashlib.sha256(z.read(media)).hexdigest() if media in z.namelist() else "broken_image"
                images.append((digest, position, size))
    return sorted(images)


def _tables(z: zipfile.ZipFile, sheet_part: str, root: ET.Element) -> list[tuple]:
    rels = _relationships(z, sheet_part)
    tables = []
    for node in root.findall(f"{{{S}}}tableParts/{{{S}}}tablePart"):
        part = rels.get(node.attrib.get(f"{{{R}}}id", ""), "")
        if part not in z.namelist():
            tables.append(("broken_table",))
            continue
        table = ET.fromstring(z.read(part))
        columns = tuple(c.attrib.get("name", "") for c in table.findall(f"{{{S}}}tableColumns/{{{S}}}tableColumn"))
        auto_filter = table.find(f"{{{S}}}autoFilter")
        tables.append((table.attrib.get("name", ""), table.attrib.get("ref", ""),
                       columns, auto_filter.attrib.get("ref", "") if auto_filter is not None else ""))
    return sorted(tables)


def _conditional_formats(root: ET.Element) -> list[tuple]:
    blocks = []
    for block in root.findall(f"{{{S}}}conditionalFormatting"):
        rules = []
        for rule in block.findall(f"{{{S}}}cfRule"):
            formulas = tuple((e.text or "") for e in rule.findall(f"{{{S}}}formula"))
            rules.append((rule.attrib.get("type", ""), formulas, rule.attrib.get("stopIfTrue", "")))
        blocks.append((block.attrib.get("sqref", ""), tuple(rules)))
    return sorted(blocks)


def snapshot(path: str | Path) -> dict:
    """Capture only structural signatures, never workbook cell values."""
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read("xl/workbook.xml"))
        book_rels = _relationships(z, "xl/workbook.xml")
        names = []
        sheets = {}
        for node in book.findall(f"{{{S}}}sheets/{{{S}}}sheet"):
            name = node.attrib["name"]
            part = book_rels[node.attrib[f"{{{R}}}id"]]
            root = ET.fromstring(z.read(part))
            names.append(name)
            filters = sorted(e.attrib.get("ref", "") for e in root.findall(f"{{{S}}}autoFilter"))
            panes = sorted(tuple(sorted(e.attrib.items())) for e in root.findall(f"{{{S}}}sheetViews/{{{S}}}sheetView/{{{S}}}pane"))
            validations = []
            for e in root.findall(f"{{{S}}}dataValidations/{{{S}}}dataValidation"):
                formulas = tuple(e.findtext(f"{{{S}}}{tag}") or "" for tag in ("formula1", "formula2"))
                validations.append((e.attrib.get("sqref", ""), e.attrib.get("type", ""), formulas))
            sheets[name] = {
                "filters": filters,
                "panes": panes,
                "validations": sorted(validations),
                "images": _images(z, part, root),
                "tables": _tables(z, part, root),
                "conditional_formats": _conditional_formats(root),
            }
        return {"sheet_names": names, "sheets": sheets}


def compare_features(before: str | Path, after: str | Path) -> dict:
    baseline = snapshot(before)
    candidate = snapshot(after)
    issues = []
    if baseline["sheet_names"] != candidate["sheet_names"]:
        issues.append({"code": "sheet_order_or_name_changed", "sheet": "(workbook)"})
    for name, features in baseline["sheets"].items():
        other = candidate["sheets"].get(name)
        if other is None:
            continue
        for feature in ("filters", "panes", "validations", "images", "tables", "conditional_formats"):
            if features[feature] != other[feature]:
                issues.append({"code": f"{feature}_changed", "sheet": name,
                               "baseline_count": len(features[feature]),
                               "candidate_count": len(other[feature])})
    return {
        "pass": not issues,
        "baseline_sha256": hashlib.sha256(Path(before).read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(after).read_bytes()).hexdigest(),
        "baseline_sheet_count": len(baseline["sheet_names"]),
        "candidate_sheet_count": len(candidate["sheet_names"]),
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Web Excel workbook features before and after a rewrite.")
    parser.add_argument("before", help="known-good baseline XLSX")
    parser.add_argument("after", help="candidate XLSX")
    args = parser.parse_args(argv)
    result = compare_features(args.before, args.after)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
