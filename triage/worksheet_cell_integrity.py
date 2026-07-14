"""Read-only worksheet coordinate and dimension integrity checks for .xlsx files.

The validator addresses two Excel-for-Web repair triggers observed in the AI
Prompt Kit V19 package:

* more than one ``<c>`` element declaring the same worksheet coordinate;
* a worksheet ``dimension`` that does not cover existing explicit cell records.

It inspects OOXML directly and never rewrites the workbook.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")


def _col_num(column: str) -> int:
    value = 0
    for char in column:
        value = value * 26 + ord(char) - 64
    return value


def _cell_position(ref: str) -> Optional[Tuple[int, int]]:
    match = CELL_RE.fullmatch(ref or "")
    if not match:
        return None
    return _col_num(match.group(1)), int(match.group(2))


def _dimension_end(ref: Optional[str]) -> Optional[Tuple[int, int]]:
    if not ref:
        return None
    match = RANGE_RE.fullmatch(ref)
    if match:
        return _col_num(match.group(3)), int(match.group(4))
    return _cell_position(ref)


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


def _sheets(archive: zipfile.ZipFile) -> Dict[str, str]:
    workbook = _xml(archive, "xl/workbook.xml")
    relationships = _xml(archive, "xl/_rels/workbook.xml.rels")
    targets = {node.attrib["Id"]: node.attrib["Target"] for node in relationships}
    sheets: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        relation_id = sheet.attrib.get(f"{{{REL_NS}}}id")
        if relation_id in targets:
            sheets[sheet.attrib["name"]] = _resolve_target(
                "xl/workbook.xml", targets[relation_id]
            )
    return sheets


@dataclass(frozen=True)
class Finding:
    sheet: str
    issue: str
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WorksheetCellIntegrityReport:
    path: str
    passed: bool
    findings: List[Finding]
    checked_sheets: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.passed,
            "checked_sheets": self.checked_sheets,
            "findings": [asdict(item) for item in self.findings],
        }

    def render_text(self) -> str:
        lines = ["WORKSHEET CELL INTEGRITY"]
        if not self.findings:
            lines.append("[PASS] Cell coordinates are unique and dimensions cover explicit cells")
        else:
            for finding in self.findings:
                lines.append(
                    f"[FAIL] {finding.sheet}: {finding.issue} - "
                    f"{json.dumps(finding.details, sort_keys=True)}"
                )
        lines.append("")
        lines.append(f"Result: pass={str(self.passed).lower()}, checked_sheets={self.checked_sheets}")
        return "\n".join(lines)


def validate_worksheet_cell_integrity(path: str) -> WorksheetCellIntegrityReport:
    workbook = Path(path)
    findings: List[Finding] = []
    if not workbook.exists():
        return WorksheetCellIntegrityReport(
            str(workbook),
            False,
            [Finding("<package>", "file_missing", {"path": str(workbook)})],
            0,
        )

    checked_sheets = 0
    try:
        with zipfile.ZipFile(workbook, "r") as archive:
            for sheet_name, worksheet_part in _sheets(archive).items():
                checked_sheets += 1
                root = _xml(archive, worksheet_part)
                refs = [
                    cell.attrib.get("r", "")
                    for cell in root.findall(".//m:c", NS)
                    if cell.attrib.get("r")
                ]
                duplicates = {
                    ref: count
                    for ref, count in Counter(refs).items()
                    if count > 1
                }
                if duplicates:
                    findings.append(
                        Finding(
                            sheet_name,
                            "duplicate_cell_references",
                            {
                                "coordinates": duplicates,
                                "extra_cell_records": sum(
                                    count - 1 for count in duplicates.values()
                                ),
                            },
                        )
                    )

                positions = [position for ref in refs if (position := _cell_position(ref))]
                actual_end = (
                    (max(position[0] for position in positions), max(position[1] for position in positions))
                    if positions
                    else (0, 0)
                )
                dimension = root.find("m:dimension", NS)
                dimension_ref = dimension.attrib.get("ref") if dimension is not None else None
                dimension_end = _dimension_end(dimension_ref)
                if positions and dimension_end is None:
                    findings.append(
                        Finding(
                            sheet_name,
                            "dimension_missing_or_invalid",
                            {"dimension": dimension_ref, "actual_end": actual_end},
                        )
                    )
                elif positions and dimension_end and (
                    dimension_end[0] < actual_end[0] or dimension_end[1] < actual_end[1]
                ):
                    findings.append(
                        Finding(
                            sheet_name,
                            "dimension_excludes_explicit_cells",
                            {
                                "dimension": dimension_ref,
                                "dimension_end": dimension_end,
                                "actual_end": actual_end,
                            },
                        )
                    )
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as error:
        findings.append(
            Finding("<package>", "package_unreadable", {"error": f"{type(error).__name__}: {error}"})
        )

    return WorksheetCellIntegrityReport(
        str(workbook.resolve()), not findings, findings, checked_sheets
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fail duplicate worksheet cell coordinates and dimensions that exclude explicit cells"
    )
    parser.add_argument("workbook")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = validate_worksheet_cell_integrity(args.workbook)
    print(json.dumps(report.to_dict(), indent=2) if args.as_json else report.render_text())
    raise SystemExit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
