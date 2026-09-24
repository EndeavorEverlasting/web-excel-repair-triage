"""Override table structural check (section F)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.roster_log_compare.load import load_workbook
from triage.roster_parser import _find_assignments_sheet

DEFAULT_OVERRIDE_RANGE = "A206:C505"
_OVERRIDE_REF_RE = re.compile(r"\$?A\$?206:\$?C\$?505", re.I)
_INT_DATE_RE = re.compile(r"\bINT\s*\(", re.I)


def _find_overrides_header(ws) -> Optional[int]:
    for r in range(1, min(ws.max_row, 300) + 1):
        v = ws.cell(r, 1).value
        if not v:
            continue
        s = str(v).strip().lower()
        if "override staff" in s or (s.startswith("override") and "staff" in s):
            return r
        if s in ("staff name", "staff") and r > 5:
            prev = ws.cell(r - 1, 1).value
            if prev and "override" in str(prev).lower():
                return r
    return None


def _overrides_banner(ws) -> bool:
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v and "override" in str(v).strip().lower() and "different" in str(v).lower():
            return True
        if v and "overrides" in str(v).strip().lower():
            return True
    return False


def _scan_formulas(ws, hdr_main: int, overrides_start: Optional[int]) -> Dict[str, Any]:
    end = overrides_start - 1 if overrides_start else ws.max_row
    refs_override = False
    int_date = False
    for r in range(hdr_main + 1, max(hdr_main + 1, end)):
        for c in range(3, ws.max_column + 1):
            cell = ws.cell(r, c)
            if not isinstance(cell.value, str) or not cell.value.startswith("="):
                continue
            f = cell.value
            if _OVERRIDE_REF_RE.search(f):
                refs_override = True
            if _INT_DATE_RE.search(f):
                int_date = True
    return {"formulas_reference_override_range": refs_override, "date_logic_present": int_date}


def _check_side(ws, label: str) -> Dict[str, Any]:
    if ws is None:
        return {
            "sheet": label,
            "override_table_present": False,
            "formulas_reference_override_range": False,
            "structurally_functional": False,
            "validated_by_recalculation": False,
        }
    banner = _overrides_banner(ws)
    ov_hdr = _find_overrides_header(ws)
    hdr_main = 2
    for r in range(1, 10):
        v = ws.cell(r, 1).value
        if v and "staff" in str(v).lower():
            hdr_main = r
            break
    overrides_start = None
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v and "override" in str(v).strip().lower() and r > hdr_main + 2:
            overrides_start = r
            break
    formula_info = _scan_formulas(ws, hdr_main, overrides_start)
    present = banner and ov_hdr is not None
    functional = present and formula_info["formulas_reference_override_range"]
    return {
        "sheet": ws.title,
        "expected_override_range": DEFAULT_OVERRIDE_RANGE,
        "override_table_present": present,
        **formula_info,
        "structurally_functional": functional,
        "validated_by_recalculation": False,
    }


def compare_override_tables(left_path: Path, right_path: Path) -> Dict[str, Any]:
    wl = load_workbook(left_path, data_only=False)
    wr = load_workbook(right_path, data_only=False)
    rows: List[Dict[str, Any]] = []
    try:
        months = sorted(
            {n for n in wl.sheetnames if n.startswith("Assignments")}
            | {n for n in wr.sheetnames if n.startswith("Assignments")}
        )
        for name in months:
            ws_l = wl[name] if name in wl.sheetnames else None
            ws_r = wr[name] if name in wr.sheetnames else None
            rows.append({
                "sheet": name,
                "left": _check_side(ws_l, name),
                "right": _check_side(ws_r, name),
            })
        if not rows:
            label = "May 2026"
            rows.append({
                "sheet": "(assignments)",
                "left": _check_side(_find_assignments_sheet(wl, label), "left"),
                "right": _check_side(_find_assignments_sheet(wr, label), "right"),
            })
        return {"rows": rows}
    finally:
        wl.close()
        wr.close()
