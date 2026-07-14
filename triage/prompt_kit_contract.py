"""Read-only V19 prompt-kit contract validator for AI Harness Prompt Kit workbooks.

This module inspects the OOXML package and verifies the structural contract
that the V19 acceptance definition requires.  It does not load or rewrite the
workbook with Excel, openpyxl, or another serializer.

Contract scope:
* required sheets (21 prompt tabs, Prompt_Library, Prompt_Class_Legend);
* approved visible fonts (Aptos family);
* Prompt Library column layout and data integrity;
* Aptos Bold for the H header, regular 12-point Aptos for H body cells;
* copy-surface bounds: contiguous column-A payload, first row, final row,
  internal blank count, package endpoint, populated columns;
* hyperlink endpoints calculated from the actual compacted payload;
* both B and N links target the exact expected range;
* one authoritative nonempty legend meaning for every library color.

Package-valid is not the same as clipboard-accepted or operator-accepted.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS}

CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")
RANGE_RE = re.compile(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$")

REQUIRED_PROMPT_COUNT = 21
PROMPT_IDS = [f"P{i:02d}" for i in range(REQUIRED_PROMPT_COUNT)]
EXPECTED_COPY_SHEETS = [f"P{i:02d}_COPY_SAFE" for i in range(REQUIRED_PROMPT_COUNT)]

APPROVED_FONTS = {"Aptos", "Aptos Display"}
APPROVED_HEADING_FONTS = {"Aptos"}

LIBRARY_HEADERS = [
    "Seq", "Prompt ID", "Prompt Type", "Prompt Class", "Sprint Path Role",
    "Use For Progress?", "Prompt Name", "Use This When", "Inspect First",
    "Expected Output", "Next Step", "Proof / Acceptance Gate",
    "Color Meaning", "Copy-Safe Sheet",
]

LEGEND_REQUIRED_HEADERS = {"Prompt Type", "Prompt Class", "Color"}


def _col_num(col: str) -> int:
    out = 0
    for ch in col:
        out = out * 26 + ord(ch) - 64
    return out


def _num_to_col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _parse_range(ref: str) -> Optional[Tuple[int, int, int, int]]:
    m = RANGE_RE.fullmatch(ref or "")
    if not m:
        return None
    c1, r1, c2, r2 = m.groups()
    return _col_num(c1), int(r1), _col_num(c2), int(r2)


def _xml(z: zipfile.ZipFile, part: str) -> ET.Element:
    return ET.fromstring(z.read(part))


def _shared_strings(z: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = _xml(z, "xl/sharedStrings.xml")
    return [
        "".join(t.text or "" for t in si.iter(f"{{{MAIN_NS}}}t"))
        for si in root.findall("m:si", NS)
    ]


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
            target = targets[rid]
            if not target.startswith("xl/"):
                target = "xl/" + target
            out[sheet.attrib["name"]] = target
    return out


def _styles_font_map(z: zipfile.ZipFile) -> Dict[int, Dict[str, Any]]:
    if "xl/styles.xml" not in z.namelist():
        return {}
    root = _xml(z, "xl/styles.xml")
    fonts_node = root.find("m:fonts", NS)
    if fonts_node is None:
        return {}
    out: Dict[int, Dict[str, Any]] = {}
    for i, font in enumerate(fonts_node.findall("m:font", NS)):
        name_el = font.find("m:name", NS)
        sz_el = font.find("m:sz", NS)
        b_el = font.find("m:b", NS)
        i_el = font.find("m:i", NS)
        out[i] = {
            "name": name_el.attrib.get("val", "") if name_el is not None else "",
            "size": float(sz_el.attrib.get("val", "0")) if sz_el is not None else 0,
            "bold": b_el is not None,
            "italic": i_el is not None,
        }
    return out


def _cell_font_info(
    cell: ET.Element,
    font_map: Dict[int, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    style_idx = cell.attrib.get("s")
    if style_idx is None:
        return None
    try:
        si = int(style_idx)
    except ValueError:
        return None
    return font_map.get(si)


def _sheet_hyperlinks(z: zipfile.ZipFile, sheet_part: str) -> Dict[str, str]:
    parent = sheet_part.rsplit("/", 1)[0] if "/" in sheet_part else ""
    base_name = sheet_part.rsplit("/", 1)[-1] if "/" in sheet_part else sheet_part
    rels_name = f"{parent}/_rels/{base_name}.rels" if parent else f"_rels/{base_name}.rels"
    rid_target: Dict[str, str] = {}
    if rels_name in z.namelist():
        rels = _xml(z, rels_name)
        for r in rels:
            rid_target[r.attrib["Id"]] = r.attrib.get("Target", "")
    root = _xml(z, sheet_part)
    out: Dict[str, str] = {}
    for hl in root.findall(".//m:hyperlinks/m:hyperlink", NS):
        ref = hl.attrib.get("ref", "")
        rid = hl.attrib.get(f"{{{REL_NS}}}id", "")
        if ref and rid:
            out[ref] = rid_target.get(rid, "")
        elif ref:
            out[ref] = ""
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
class PromptKitContractReport:
    path: str
    checks: List[Check] = field(default_factory=list)
    contract_valid: bool = False

    @property
    def failures(self) -> List[Check]:
        return [c for c in self.checks if c.status == "FAIL"]

    @property
    def warnings(self) -> List[Check]:
        return [c for c in self.checks if c.status == "WARN"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "contract_valid": self.contract_valid,
            "counts": {
                "pass": sum(c.status == "PASS" for c in self.checks),
                "warn": len(self.warnings),
                "fail": len(self.failures),
            },
            "checks": [c.to_dict() for c in self.checks],
        }

    def render_text(self) -> str:
        lines = ["PROMPT KIT V19 CONTRACT"]
        for check in self.checks:
            suffix = f": {check.summary}" if check.summary else ""
            lines.append(f"[{check.status}] {check.name}{suffix}")
        lines.append("")
        lines.append(f"Result: contract_valid={str(self.contract_valid).lower()}")
        return "\n".join(lines)


def validate_prompt_kit_contract(path: str) -> PromptKitContractReport:
    workbook_path = Path(path)
    report = PromptKitContractReport(path=str(workbook_path.resolve()))

    if not workbook_path.exists():
        report.checks.append(Check("file exists", "FAIL", [{"path": str(workbook_path)}]))
        return report

    try:
        with zipfile.ZipFile(workbook_path, "r") as z:
            shared = _shared_strings(z)
            sheets = _workbook_sheets(z)
            font_map = _styles_font_map(z)

            # --- Required sheets ---
            missing_sheets = [s for s in EXPECTED_COPY_SHEETS if s not in sheets]
            has_library = "Prompt_Library" in sheets
            has_legend = "Prompt_Class_Legend" in sheets

            report.checks.append(Check(
                "required prompt tabs",
                "FAIL" if missing_sheets else "PASS",
                [{"missing": s} for s in missing_sheets],
                f"{len(EXPECTED_COPY_SHEETS) - len(missing_sheets)}/{len(EXPECTED_COPY_SHEETS)} present",
            ))
            report.checks.append(Check(
                "Prompt_Library present",
                "FAIL" if not has_library else "PASS",
            ))
            report.checks.append(Check(
                "Prompt_Class_Legend present",
                "FAIL" if not has_legend else "PASS",
            ))

            # --- Font inventory ---
            font_names = {v["name"] for v in font_map.values() if v["name"]}
            disallowed = font_names - APPROVED_FONTS
            report.checks.append(Check(
                "approved visible fonts",
                "WARN" if disallowed else "PASS",
                [{"font": f} for f in sorted(disallowed)],
                f"non-Aptos fonts detected" if disallowed else "all fonts approved",
            ))

            if not has_library:
                report.contract_valid = not report.failures
                return report

            # --- Prompt Library structure ---
            lib_part = sheets["Prompt_Library"]
            lib_root = _xml(z, lib_part)
            lib_cells = {}
            for c in lib_root.findall(".//m:c", NS):
                ref = c.attrib.get("r", "")
                lib_cells[ref] = _cell_value(c, shared)

            # Parse library into rows
            lib_rows: Dict[int, Dict[str, str]] = {}
            for ref, val in lib_cells.items():
                m = CELL_RE.match(ref)
                if m:
                    col = m.group(1)
                    row = int(m.group(2))
                    lib_rows.setdefault(row, {})[col] = val

            # Check header row
            header_row = lib_rows.get(1, {})
            header_vals = [header_row.get(_num_to_col(i + 1), "") for i in range(len(LIBRARY_HEADERS))]
            header_issues = []
            for i, expected in enumerate(LIBRARY_HEADERS):
                actual = header_vals[i] if i < len(header_vals) else ""
                if actual != expected:
                    header_issues.append({
                        "column": _num_to_col(i + 1),
                        "expected": expected,
                        "actual": actual,
                    })
            report.checks.append(Check(
                "Prompt Library headers",
                "FAIL" if header_issues else "PASS",
                header_issues[:10],
            ))

            # Extract prompt data rows (rows 2-22 for P00-P20)
            lib_data: Dict[str, Dict[str, str]] = {}
            for row_num in range(2, 2 + REQUIRED_PROMPT_COUNT):
                row = lib_rows.get(row_num, {})
                pid = row.get("B", "")
                lib_data[pid] = row

            # Check prompt IDs
            pid_issues = []
            for i, expected_pid in enumerate(PROMPT_IDS):
                actual = lib_data.get(expected_pid, {}).get("B", "")
                if actual != expected_pid:
                    pid_issues.append({"row": i + 2, "expected": expected_pid, "actual": actual})
            report.checks.append(Check(
                "Prompt Library prompt IDs",
                "FAIL" if pid_issues else "PASS",
                pid_issues[:10],
            ))

            # Check copy-safe sheet references
            copy_ref_issues = []
            for i, expected_pid in enumerate(PROMPT_IDS):
                row = lib_data.get(expected_pid, {})
                expected_sheet = f"{expected_pid}_COPY_SAFE"
                actual_sheet = row.get("N", "")
                if actual_sheet != expected_sheet:
                    copy_ref_issues.append({
                        "row": i + 2,
                        "expected": expected_sheet,
                        "actual": actual_sheet,
                    })
            report.checks.append(Check(
                "copy-safe sheet references",
                "FAIL" if copy_ref_issues else "PASS",
                copy_ref_issues[:10],
            ))

            # --- Column H font check (Aptos Bold header, 12pt regular body) ---
            h_font_issues: List[Dict[str, Any]] = []
            # Check header H1
            h1_cell = None
            for c in lib_root.findall(".//m:c", NS):
                if c.attrib.get("r") == "H1":
                    h1_cell = c
                    break
            if h1_cell is not None:
                fi = _cell_font_info(h1_cell, font_map)
                if fi:
                    if not fi["bold"]:
                        h_font_issues.append({"cell": "H1", "issue": "header_not_bold", "font": fi["name"]})
                    if fi["name"] not in APPROVED_HEADING_FONTS:
                        h_font_issues.append({"cell": "H1", "issue": "header_font_not_aptos", "font": fi["name"]})

            # Check body cells H2-H22
            body_font_issues: List[Dict[str, Any]] = []
            for row_num in range(2, 2 + REQUIRED_PROMPT_COUNT):
                cell_ref = f"H{row_num}"
                for c in lib_root.findall(".//m:c", NS):
                    if c.attrib.get("r") == cell_ref:
                        fi = _cell_font_info(c, font_map)
                        if fi:
                            if fi["bold"]:
                                body_font_issues.append({"cell": cell_ref, "issue": "body_cell_is_bold"})
                            if fi["name"] not in APPROVED_FONTS:
                                body_font_issues.append({"cell": cell_ref, "issue": "body_font_not_aptos", "font": fi["name"]})
                            if fi["size"] != 12:
                                body_font_issues.append({"cell": cell_ref, "issue": "body_font_not_12pt", "size": fi["size"]})
                        break

            all_h_issues = h_font_issues + body_font_issues
            report.checks.append(Check(
                "Prompt Library column H typography",
                "FAIL" if all_h_issues else "PASS",
                all_h_issues[:10],
            ))

            # --- Copy-surface bounds ---
            surface_findings: List[Dict[str, Any]] = []
            surface_details: Dict[str, Dict[str, Any]] = {}

            for sheet_name in EXPECTED_COPY_SHEETS:
                if sheet_name not in sheets:
                    continue
                sheet_part = sheets[sheet_name]
                sheet_root = _xml(z, sheet_part)
                populated: Dict[int, str] = {}
                for c in sheet_root.findall(".//m:c", NS):
                    ref = c.attrib.get("r", "")
                    m = CELL_RE.match(ref)
                    if m:
                        row_num = int(m.group(2))
                        col = m.group(1)
                        val = _cell_value(c, shared)
                        if col == "A" and val:
                            populated[row_num] = val

                if not populated:
                    surface_findings.append({"sheet": sheet_name, "issue": "empty_copy_surface"})
                    surface_details[sheet_name] = {"populated_rows": 0, "first_row": 0, "last_row": 0, "blanks": 0}
                    continue

                rows = sorted(populated.keys())
                first_row = rows[0]
                last_row = rows[-1]
                expected_count = last_row - first_row + 1
                actual_count = len(rows)
                blanks = expected_count - actual_count

                # Check all populated cells are in column A
                non_a_cells: List[str] = []
                for c in sheet_root.findall(".//m:c", NS):
                    ref = c.attrib.get("r", "")
                    cm = CELL_RE.match(ref)
                    if cm and cm.group(1) != "A" and _cell_value(c, shared):
                        non_a_cells.append(ref)

                # Check contiguous from A1
                if first_row != 1:
                    surface_findings.append({
                        "sheet": sheet_name,
                        "issue": "payload_does_not_start_at_A1",
                        "first_row": first_row,
                    })
                if blanks > 0:
                    # Identify internal blanks
                    internal_blanks = [r for r in range(first_row, last_row + 1) if r not in populated]
                    surface_findings.append({
                        "sheet": sheet_name,
                        "issue": "internal_blank_rows",
                        "blank_rows": internal_blanks[:10],
                        "blank_count": blanks,
                    })
                if non_a_cells:
                    surface_findings.append({
                        "sheet": sheet_name,
                        "issue": "non_column_a_populated_cells",
                        "cells": non_a_cells[:10],
                    })

                # Check for trailing rows (rows beyond payload that have data in any column)
                trailing_findings: List[str] = []
                for c in sheet_root.findall(".//m:c", NS):
                    ref = c.attrib.get("r", "")
                    cm = CELL_RE.match(ref)
                    if cm:
                        r_num = int(cm.group(2))
                        if r_num > last_row and _cell_value(c, shared):
                            trailing_findings.append(ref)
                if trailing_findings:
                    surface_findings.append({
                        "sheet": sheet_name,
                        "issue": "trailing_rows_after_payload",
                        "cells": trailing_findings[:10],
                    })

                surface_details[sheet_name] = {
                    "populated_rows": actual_count,
                    "first_row": first_row,
                    "last_row": last_row,
                    "blanks": blanks,
                    "endpoint": f"A{last_row}",
                }

            report.checks.append(Check(
                "copy-surface bounds",
                "FAIL" if surface_findings else "PASS",
                surface_findings[:25],
                f"{len(surface_details)} surfaces measured",
            ))

            # --- Hyperlink endpoint checks ---
            lib_hyperlinks = _sheet_hyperlinks(z, lib_part)
            link_issues: List[Dict[str, Any]] = []

            for i, expected_pid in enumerate(PROMPT_IDS):
                row_num = i + 2
                row = lib_data.get(expected_pid, {})
                expected_sheet = f"{expected_pid}_COPY_SAFE"
                surface = surface_details.get(expected_sheet, {})
                last_row = surface.get("last_row", 0)
                expected_endpoint = f"{expected_sheet}!A1:A{last_row}" if last_row else ""

                # Check N column link
                n_ref = f"N{row_num}"
                n_link = lib_hyperlinks.get(n_ref, "")
                if expected_endpoint and n_link != expected_endpoint:
                    link_issues.append({
                        "cell": n_ref,
                        "expected": expected_endpoint,
                        "actual": n_link or "(no hyperlink)",
                        "column": "N",
                    })

                # Check B column link
                b_ref = f"B{row_num}"
                b_link = lib_hyperlinks.get(b_ref, "")
                if expected_endpoint and b_link != expected_endpoint:
                    link_issues.append({
                        "cell": b_ref,
                        "expected": expected_endpoint,
                        "actual": b_link or "(no hyperlink)",
                        "column": "B",
                    })

            report.checks.append(Check(
                "hyperlink endpoints",
                "FAIL" if link_issues else "PASS",
                link_issues[:20],
            ))

            # --- Color legend coverage ---
            if has_legend:
                legend_part = sheets["Prompt_Class_Legend"]
                legend_root = _xml(z, legend_part)
                legend_cells: Dict[str, str] = {}
                for c in legend_root.findall(".//m:c", NS):
                    ref = c.attrib.get("r", "")
                    legend_cells[ref] = _cell_value(c, shared)

                # Find header row (look for "Color" in column H or "Prompt Type" in column A)
                legend_header_row = 0
                for ref, val in legend_cells.items():
                    m = CELL_RE.match(ref)
                    if m and m.group(1) == "H" and val == "Color":
                        legend_header_row = int(m.group(2))
                        break
                if legend_header_row == 0:
                    for ref, val in legend_cells.items():
                        m = CELL_RE.match(ref)
                        if m and m.group(1) == "A" and val == "Prompt Type":
                            legend_header_row = int(m.group(2))
                            break

                # Collect legend colors (column H below header)
                legend_colors: Dict[str, List[str]] = {}
                if legend_header_row:
                    for ref, val in legend_cells.items():
                        m = CELL_RE.match(ref)
                        if m and m.group(1) == "H" and int(m.group(2)) > legend_header_row and val:
                            row_num = int(m.group(2))
                            prompt_type = legend_cells.get(f"A{row_num}", "")
                            legend_colors.setdefault(val, []).append(prompt_type)

                # Collect library colors (column M below header)
                lib_colors: Dict[str, List[str]] = {}
                for i, pid in enumerate(PROMPT_IDS):
                    row_num = i + 2
                    color = lib_data.get(pid, {}).get("M", "")
                    if color:
                        lib_colors.setdefault(color, []).append(pid)

                legend_issues: List[Dict[str, Any]] = []
                for color, pids in lib_colors.items():
                    meanings = legend_colors.get(color, [])
                    if not meanings:
                        legend_issues.append({
                            "color": color,
                            "issue": "color_missing_from_legend",
                            "used_by": pids,
                        })
                    elif len(meanings) > 1:
                        legend_issues.append({
                            "color": color,
                            "issue": "color_has_multiple_legend_entries",
                            "meanings": meanings,
                        })
                    else:
                        # Check meaning is non-empty
                        meaning_row = 0
                        for ref, val in legend_cells.items():
                            m2 = CELL_RE.match(ref)
                            if m2 and m2.group(1) == "H" and val == color:
                                meaning_row = int(m2.group(2))
                                break
                        if meaning_row:
                            # Check if the "When to Use" or similar field is non-empty
                            when_cell = legend_cells.get(f"D{meaning_row}", "")
                            if not when_cell:
                                legend_issues.append({
                                    "color": color,
                                    "issue": "legend_meaning_empty",
                                    "row": meaning_row,
                                })

                report.checks.append(Check(
                    "color legend coverage",
                    "FAIL" if legend_issues else "PASS",
                    legend_issues[:15],
                ))
            else:
                report.checks.append(Check(
                    "color legend coverage",
                    "SKIP",
                    summary="Prompt_Class_Legend sheet not present",
                ))

    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        report.checks.append(Check(
            "package readable",
            "FAIL",
            [{"error": f"{type(exc).__name__}: {exc}"}],
        ))

    report.contract_valid = not report.failures
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a prompt-kit workbook against the V19 contract",
    )
    parser.add_argument("workbook")
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="emit JSON instead of the English matrix",
    )
    args = parser.parse_args()

    report = validate_prompt_kit_contract(args.workbook)
    print(json.dumps(report.to_dict(), indent=2) if args.as_json else report.render_text())
    raise SystemExit(0 if report.contract_valid else 1)


if __name__ == "__main__":
    main()
