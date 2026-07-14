"""Validate that copy-safe worksheet payloads end at their final populated row.

Whole-sheet clipboard operations may include explicit row nodes, styled blank cells,
or worksheet dimensions below the real prompt payload. This validator inspects the
OOXML package without loading or rewriting the workbook.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")


def _col_num(value: str) -> int:
    result = 0
    for char in value:
        result = result * 26 + ord(char) - 64
    return result


def _cell_position(ref: str) -> Optional[Tuple[int, int]]:
    match = CELL_RE.fullmatch(ref or "")
    if not match:
        return None
    return _col_num(match.group(1)), int(match.group(2))


def _dimension_end_row(ref: Optional[str]) -> int:
    if not ref:
        return 0
    range_match = RANGE_RE.fullmatch(ref)
    if range_match:
        return int(range_match.group(4))
    cell = _cell_position(ref)
    return cell[1] if cell else 0


def _resolve_target(owner_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    base = PurePosixPath(owner_part).parent
    parts: List[str] = []
    for piece in (base / target).parts:
        if piece in ("", "."):
            continue
        if piece == "..":
            if parts:
                parts.pop()
        else:
            parts.append(piece)
    return "/".join(parts)


def _xml(archive: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(archive.read(part))


def _sheet_parts(archive: zipfile.ZipFile) -> Dict[str, str]:
    workbook = _xml(archive, "xl/workbook.xml")
    rels = _xml(archive, "xl/_rels/workbook.xml.rels")
    targets = {relationship.attrib["Id"]: relationship.attrib["Target"] for relationship in rels}
    result: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        relationship_id = sheet.attrib.get(f"{{{REL_NS}}}id")
        if relationship_id and relationship_id in targets:
            result[sheet.attrib["name"]] = _resolve_target(
                "xl/workbook.xml", targets[relationship_id]
            )
    return result


def _shared_strings(archive: zipfile.ZipFile) -> Sequence[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _xml(archive, "xl/sharedStrings.xml")
    return [
        "".join(text.text or "" for text in item.iter(f"{{{MAIN_NS}}}t"))
        for item in root.findall("m:si", NS)
    ]


def _cell_value(cell: ET.Element, shared: Sequence[str]) -> str:
    if cell.attrib.get("t") == "inlineStr":
        return "".join(text.text or "" for text in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell.attrib.get("t") == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


@dataclass(frozen=True)
class CopySurfaceBound:
    sheet: str
    status: str
    last_payload_row: int
    package_end_row: int
    trailing_rows: int
    allowed_trailing_rows: int
    dimension_ref: Optional[str]
    max_row_node: int
    max_cell_row: int


@dataclass(frozen=True)
class CopySurfaceBoundsReport:
    path: str
    pass_all: bool
    missing_sheets: List[str]
    surfaces: List[CopySurfaceBound]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.pass_all,
            "missing_sheets": self.missing_sheets,
            "surfaces": [asdict(surface) for surface in self.surfaces],
        }


def inspect_copy_surface_bounds(
    path: str,
    *,
    sheets: Iterable[str],
    max_trailing_rows: int = 0,
) -> CopySurfaceBoundsReport:
    if max_trailing_rows < 0:
        raise ValueError("max_trailing_rows must be zero or greater")

    workbook = Path(path)
    requested = list(dict.fromkeys(sheets))
    missing: List[str] = []
    surfaces: List[CopySurfaceBound] = []

    with zipfile.ZipFile(workbook, "r") as archive:
        parts = _sheet_parts(archive)
        shared = _shared_strings(archive)

        for sheet_name in requested:
            worksheet_part = parts.get(sheet_name)
            if worksheet_part is None:
                missing.append(sheet_name)
                continue

            root = _xml(archive, worksheet_part)
            dimension = root.find("m:dimension", NS)
            dimension_ref = dimension.attrib.get("ref") if dimension is not None else None

            populated_rows: List[int] = []
            all_cell_rows: List[int] = []
            for cell in root.findall(".//m:c", NS):
                position = _cell_position(cell.attrib.get("r", ""))
                if position is None:
                    continue
                _, row = position
                all_cell_rows.append(row)
                if _cell_value(cell, shared):
                    populated_rows.append(row)

            row_nodes = [
                int(row.attrib["r"])
                for row in root.findall("m:sheetData/m:row", NS)
                if row.attrib.get("r", "").isdigit()
            ]
            last_payload_row = max(populated_rows, default=0)
            max_row_node = max(row_nodes, default=0)
            max_cell_row = max(all_cell_rows, default=0)
            package_end_row = max(
                _dimension_end_row(dimension_ref),
                max_row_node,
                max_cell_row,
            )
            trailing_rows = max(0, package_end_row - last_payload_row)
            if last_payload_row == 0:
                status = "EMPTY"
            elif trailing_rows > max_trailing_rows:
                status = "FAIL"
            else:
                status = "PASS"

            surfaces.append(
                CopySurfaceBound(
                    sheet=sheet_name,
                    status=status,
                    last_payload_row=last_payload_row,
                    package_end_row=package_end_row,
                    trailing_rows=trailing_rows,
                    allowed_trailing_rows=max_trailing_rows,
                    dimension_ref=dimension_ref,
                    max_row_node=max_row_node,
                    max_cell_row=max_cell_row,
                )
            )

    pass_all = not missing and all(surface.status == "PASS" for surface in surfaces)
    return CopySurfaceBoundsReport(
        path=str(workbook.resolve()),
        pass_all=pass_all,
        missing_sheets=missing,
        surfaces=surfaces,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fail when copy-safe worksheet package rows extend below the prompt payload"
    )
    parser.add_argument("workbook")
    parser.add_argument("--sheet", action="append", required=True, dest="sheets")
    parser.add_argument("--max-trailing-rows", type=int, default=0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    report = inspect_copy_surface_bounds(
        args.workbook,
        sheets=args.sheets,
        max_trailing_rows=args.max_trailing_rows,
    )
    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for surface in report.surfaces:
            print(
                f"[{surface.status}] {surface.sheet}: payload={surface.last_payload_row}, "
                f"package_end={surface.package_end_row}, trailing={surface.trailing_rows}"
            )
        for sheet in report.missing_sheets:
            print(f"[MISSING] {sheet}")
    raise SystemExit(0 if report.pass_all else 1)


if __name__ == "__main__":
    main()
