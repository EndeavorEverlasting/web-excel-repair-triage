"""Read-only OOXML package hygiene validator for generated .xlsx artifacts.

This module inspects the ZIP/XML package directly. It does not load or rewrite the
workbook with Excel, openpyxl, or another serializer.

Package-valid is not the same as Web Excel accepted, clipboard accepted, or
operator accepted. Clipboard checks here identify risky worksheet shapes only;
the real Ctrl+A/Ctrl+C workflow remains an operator gate.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")
ERROR_TOKENS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")
COPY_GUIDANCE_MARKERS = (
    "paste this directly",
    "do not wrap it in quotes",
    "do not put it inside a markdown",
    "end prompt",
    "do not copy this cell",
)


def _col_num(col: str) -> int:
    out = 0
    for ch in col:
        out = out * 26 + ord(ch) - 64
    return out


def _parse_range(ref: str) -> Optional[Tuple[int, int, int, int]]:
    m = RANGE_RE.fullmatch(ref or "")
    if not m:
        return None
    c1, r1, c2, r2 = m.groups()
    return _col_num(c1), int(r1), _col_num(c2), int(r2)


def _rects_overlap(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> bool:
    ac1, ar1, ac2, ar2 = a
    bc1, br1, bc2, br2 = b
    return not (ac2 < bc1 or bc2 < ac1 or ar2 < br1 or br2 < ar1)


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


def _rels_part(owner_part: str) -> str:
    owner = PurePosixPath(owner_part)
    return str(owner.parent / "_rels" / f"{owner.name}.rels")


def _xml(z: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(z.read(part))


def _shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = _xml(z, "xl/sharedStrings.xml")
    return ["".join(t.text or "" for t in si.iter(f"{{{MAIN_NS}}}t")) for si in root.findall("m:si", NS)]


def _cell_value(cell: ET.Element, shared: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.find("m:v", NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def _workbook_sheets(z: zipfile.ZipFile) -> Dict[str, str]:
    workbook = _xml(z, "xl/workbook.xml")
    rels = _xml(z, "xl/_rels/workbook.xml.rels")
    targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
    out: Dict[str, str] = {}
    for sheet in workbook.findall("m:sheets/m:sheet", NS):
        rid = sheet.attrib.get(f"{{{REL_NS}}}id")
        if rid and rid in targets:
            out[sheet.attrib["name"]] = _resolve_target("xl/workbook.xml", targets[rid])
    return out


def _worksheet_table_parts(z: zipfile.ZipFile, worksheet_part: str) -> List[str]:
    rels_name = _rels_part(worksheet_part)
    if rels_name not in z.namelist():
        return []
    rels = _xml(z, rels_name)
    targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
    root = _xml(z, worksheet_part)
    out: List[str] = []
    for tp in root.findall("m:tableParts/m:tablePart", NS):
        rid = tp.attrib.get(f"{{{REL_NS}}}id")
        if rid and rid in targets:
            out.append(_resolve_target(worksheet_part, targets[rid]))
    return out


@dataclass
class Check:
    name: str
    status: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "findings": self.findings,
        }


@dataclass
class WorkbookPackageHygieneReport:
    path: str
    checks: List[Check] = field(default_factory=list)
    package_valid: bool = False
    clipboard_acceptance: str = "not_tested"

    @property
    def failures(self) -> List[Check]:
        return [c for c in self.checks if c.status == "FAIL"]

    @property
    def warnings(self) -> List[Check]:
        return [c for c in self.checks if c.status == "WARN"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "package_valid": self.package_valid,
            "clipboard_acceptance": self.clipboard_acceptance,
            "counts": {
                "pass": sum(c.status == "PASS" for c in self.checks),
                "warn": len(self.warnings),
                "fail": len(self.failures),
            },
            "checks": [c.to_dict() for c in self.checks],
        }

    def render_text(self) -> str:
        lines = ["WORKBOOK PACKAGE HYGIENE"]
        for check in self.checks:
            suffix = f": {check.summary}" if check.summary else ""
            lines.append(f"[{check.status}] {check.name}{suffix}")
        lines.append("")
        lines.append(
            f"Result: package_valid={str(self.package_valid).lower()}, "
            f"clipboard_acceptance={self.clipboard_acceptance}"
        )
        return "\n".join(lines)


def validate_workbook_package(
    path: str,
    *,
    expected_freeze_sheets: Iterable[str] = (),
    copy_surface_sheets: Iterable[str] = (),
) -> WorkbookPackageHygieneReport:
    workbook_path = Path(path)
    report = WorkbookPackageHygieneReport(path=str(workbook_path.resolve()))
    expected_freeze = set(expected_freeze_sheets)
    copy_surfaces = set(copy_surface_sheets)

    if not workbook_path.exists():
        report.checks.append(Check("file exists", "FAIL", [{"path": str(workbook_path)}]))
        return report

    try:
        with zipfile.ZipFile(workbook_path, "r") as z:
            crc_bad = z.testzip()
            report.checks.append(
                Check(
                    "ZIP integrity",
                    "FAIL" if crc_bad else "PASS",
                    [{"first_bad_part": crc_bad}] if crc_bad else [],
                )
            )

            malformed: List[Dict[str, Any]] = []
            for part in z.namelist():
                if part.endswith((".xml", ".rels")):
                    try:
                        _xml(z, part)
                    except Exception as exc:  # exact parser failure is evidence
                        malformed.append({"part": part, "error": f"{type(exc).__name__}: {exc}"})
            report.checks.append(Check("XML well-formed", "FAIL" if malformed else "PASS", malformed[:25]))

            sheets = _workbook_sheets(z)
            shared = _shared_strings(z)
            table_parts = [p for p in z.namelist() if p.startswith("xl/tables/table") and p.endswith(".xml")]

            table_ids: Dict[str, str] = {}
            table_names: Dict[str, str] = {}
            duplicate_ids: List[Dict[str, Any]] = []
            duplicate_names: List[Dict[str, Any]] = []
            table_ref_issues: List[Dict[str, Any]] = []
            table_column_issues: List[Dict[str, Any]] = []
            table_meta: Dict[str, Dict[str, Any]] = {}

            for part in table_parts:
                root = _xml(z, part)
                table_id = root.attrib.get("id", "")
                if table_id in table_ids:
                    duplicate_ids.append({"id": table_id, "first_part": table_ids[table_id], "duplicate_part": part})
                else:
                    table_ids[table_id] = part
                for attr in ("name", "displayName"):
                    value = root.attrib.get(attr, "")
                    key = f"{attr}:{value}"
                    if value and key in table_names:
                        duplicate_names.append({"attribute": attr, "value": value, "first_part": table_names[key], "duplicate_part": part})
                    elif value:
                        table_names[key] = part

                ref = root.attrib.get("ref", "")
                parsed = _parse_range(ref)
                auto = root.find("m:autoFilter", NS)
                auto_ref = auto.attrib.get("ref") if auto is not None else None
                if not parsed:
                    table_ref_issues.append({"part": part, "issue": "invalid_table_ref", "ref": ref})
                if auto_ref != ref:
                    table_ref_issues.append({"part": part, "issue": "autofilter_ref_mismatch", "table_ref": ref, "autofilter_ref": auto_ref})

                columns = root.find("m:tableColumns", NS)
                column_nodes = columns.findall("m:tableColumn", NS) if columns is not None else []
                declared_count = int(columns.attrib.get("count", "0")) if columns is not None else 0
                if declared_count != len(column_nodes):
                    table_column_issues.append({"part": part, "issue": "declared_column_count_mismatch", "declared": declared_count, "actual": len(column_nodes)})
                if parsed:
                    range_count = parsed[2] - parsed[0] + 1
                    if range_count != len(column_nodes):
                        table_column_issues.append({"part": part, "issue": "range_column_count_mismatch", "range_count": range_count, "table_columns": len(column_nodes)})
                table_meta[part] = {
                    "ref": ref,
                    "columns": [n.attrib.get("name", "") for n in column_nodes],
                    "name": root.attrib.get("name"),
                }

            report.checks.append(Check("table IDs unique", "FAIL" if duplicate_ids else "PASS", duplicate_ids))
            report.checks.append(Check("table names unique", "FAIL" if duplicate_names else "PASS", duplicate_names))
            report.checks.append(Check("table refs and filters", "FAIL" if table_ref_issues else "PASS", table_ref_issues))
            report.checks.append(Check("table column counts", "FAIL" if table_column_issues else "PASS", table_column_issues))

            header_issues: List[Dict[str, Any]] = []
            for sheet_name, worksheet_part in sheets.items():
                root = _xml(z, worksheet_part)
                cells = {c.attrib.get("r", ""): _cell_value(c, shared) for c in root.findall(".//m:c", NS)}
                for table_part in _worksheet_table_parts(z, worksheet_part):
                    meta = table_meta.get(table_part)
                    if not meta:
                        header_issues.append({"sheet": sheet_name, "part": table_part, "issue": "missing_table_part"})
                        continue
                    parsed = _parse_range(meta["ref"])
                    if not parsed:
                        continue
                    c1, row, c2, _ = parsed
                    visible: List[str] = []
                    for col_num in range(c1, c2 + 1):
                        n = col_num
                        col = ""
                        while n:
                            n, rem = divmod(n - 1, 26)
                            col = chr(65 + rem) + col
                        visible.append(cells.get(f"{col}{row}", ""))
                    if visible != meta["columns"]:
                        header_issues.append({"sheet": sheet_name, "table": meta["name"], "visible_headers": visible, "table_columns": meta["columns"]})
            report.checks.append(Check("visible headers match table XML", "FAIL" if header_issues else "PASS", header_issues[:25]))

            merge_issues: List[Dict[str, Any]] = []
            panes: Dict[str, Dict[str, str]] = {}
            dimensions: Dict[str, Optional[str]] = {}
            copy_findings: List[Dict[str, Any]] = []

            for sheet_name, worksheet_part in sheets.items():
                root = _xml(z, worksheet_part)
                dim = root.find("m:dimension", NS)
                dimensions[sheet_name] = dim.attrib.get("ref") if dim is not None else None
                pane = root.find("m:sheetViews/m:sheetView/m:pane", NS)
                if pane is not None:
                    panes[sheet_name] = dict(pane.attrib)

                merge_nodes = root.findall("m:mergeCells/m:mergeCell", NS)
                parsed_merges: List[Tuple[str, Tuple[int, int, int, int]]] = []
                for merge in merge_nodes:
                    ref = merge.attrib.get("ref", "")
                    parsed = _parse_range(ref)
                    if parsed:
                        parsed_merges.append((ref, parsed))
                for i, (left_ref, left) in enumerate(parsed_merges):
                    for right_ref, right in parsed_merges[i + 1 :]:
                        if _rects_overlap(left, right):
                            merge_issues.append({"sheet": sheet_name, "left": left_ref, "right": right_ref})

                if sheet_name in copy_surfaces:
                    populated: List[Tuple[str, str]] = []
                    for cell in root.findall(".//m:c", NS):
                        ref = cell.attrib.get("r", "")
                        value = _cell_value(cell, shared)
                        if value:
                            populated.append((ref, value))
                    columns = sorted({CELL_RE.match(ref).group(1) for ref, _ in populated if CELL_RE.match(ref)})
                    multiline = [{"cell": ref, "line_count": value.count("\n") + 1} for ref, value in populated if "\n" in value]
                    guidance = [
                        {"cell": ref, "marker": marker}
                        for ref, value in populated
                        for marker in COPY_GUIDANCE_MARKERS
                        if marker in value.lower()
                    ]
                    if len(columns) > 1:
                        copy_findings.append({"sheet": sheet_name, "issue": "multiple_populated_columns", "columns": columns})
                    if multiline:
                        copy_findings.append({"sheet": sheet_name, "issue": "multiline_cells_risk_wrapper_quotes", "samples": multiline[:10]})
                    if guidance:
                        copy_findings.append({"sheet": sheet_name, "issue": "guidance_contaminates_payload", "samples": guidance[:10]})
                    if not populated:
                        copy_findings.append({"sheet": sheet_name, "issue": "empty_copy_surface"})

            report.checks.append(Check("merge ranges non-overlapping", "FAIL" if merge_issues else "PASS", merge_issues[:25]))

            missing_freeze = [{"sheet": name, "issue": "expected_pane_missing"} for name in sorted(expected_freeze) if name not in panes]
            freeze_status = "FAIL" if missing_freeze else "PASS"
            freeze_summary = f"{len(panes)} sheet(s) contain pane nodes"
            report.checks.append(Check("freeze panes", freeze_status, missing_freeze, freeze_summary))

            missing_dimensions = [{"sheet": name, "issue": "dimension_node_missing"} for name, ref in dimensions.items() if ref is None]
            report.checks.append(
                Check(
                    "worksheet dimensions",
                    "WARN" if missing_dimensions else "PASS",
                    missing_dimensions[:25],
                    "missing dimensions are metadata drift, not automatic corruption",
                )
            )

            error_hits: List[Dict[str, Any]] = []
            for part in z.namelist():
                if not part.endswith((".xml", ".rels")):
                    continue
                text = z.read(part).decode("utf-8", errors="ignore")
                for token in ERROR_TOKENS:
                    if token in text:
                        error_hits.append({"part": part, "token": token})
            report.checks.append(Check("formula/error literal scan", "FAIL" if error_hits else "PASS", error_hits[:25]))

            missing_copy_sheets = [{"sheet": name, "issue": "copy_surface_sheet_missing"} for name in sorted(copy_surfaces) if name not in sheets]
            copy_findings.extend(missing_copy_sheets)
            report.checks.append(
                Check(
                    "copy-surface package shape",
                    "WARN" if copy_findings else "PASS",
                    copy_findings[:25],
                    "operator Ctrl+A/Ctrl+C acceptance is still required",
                )
            )
            report.clipboard_acceptance = "manual_test_required" if copy_surfaces else "not_tested"

    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        report.checks.append(Check("package readable", "FAIL", [{"error": f"{type(exc).__name__}: {exc}"}]))

    report.package_valid = not report.failures
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an .xlsx package without rewriting it")
    parser.add_argument("workbook")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON instead of the English matrix")
    parser.add_argument("--expect-freeze", action="append", default=[], metavar="SHEET")
    parser.add_argument("--copy-surface", action="append", default=[], metavar="SHEET")
    args = parser.parse_args()

    report = validate_workbook_package(
        args.workbook,
        expected_freeze_sheets=args.expect_freeze,
        copy_surface_sheets=args.copy_surface,
    )
    print(json.dumps(report.to_dict(), indent=2) if args.as_json else report.render_text())
    raise SystemExit(0 if report.package_valid else 1)


if __name__ == "__main__":
    main()
