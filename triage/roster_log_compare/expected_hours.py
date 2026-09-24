"""Expected Hours snapshot check (section G)."""
from __future__ import annotations

import calendar
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.roster_log_compare.load import load_workbook

_EH_RE = re.compile(r"^Expected Hours\s*[-–]\s*(.+)$", re.I)
_RULES_NAMES = ("expected hours rules",)


def _month_end_from_label(label: str) -> Optional[date]:
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})", label, re.I)
    if not m:
        return None
    mon = list(calendar.month_name).index(m.group(1).title())
    year = int(m.group(2))
    last = calendar.monthrange(year, mon)[1]
    return date(year, mon, last)


def _max_date_in_sheet(ws) -> Optional[date]:
    import datetime as dt
    best: Optional[date] = None
    for row in ws.iter_rows(min_row=3, values_only=True):
        for v in row:
            if isinstance(v, dt.datetime):
                d = v.date()
            elif isinstance(v, dt.date):
                d = v
            else:
                continue
            if best is None or d > best:
                best = d
    return best


def _sheet_mode(ws) -> str:
    formula_cells = value_cells = 0
    for row in ws.iter_rows(min_row=3, max_row=min(ws.max_row, 200)):
        for cell in row:
            if cell.value is None:
                continue
            if isinstance(cell.value, str) and cell.value.startswith("="):
                formula_cells += 1
            else:
                value_cells += 1
    if formula_cells > value_cells:
        return "rule_derived"
    if value_cells > 0 and formula_cells == 0:
        return "static_snapshot"
    return "mixed"


def compare_expected_hours(left_path: Path, right_path: Path) -> Dict[str, Any]:
    wl = load_workbook(left_path, data_only=True)
    wr = load_workbook(right_path, data_only=True)
    wr_f = load_workbook(right_path, data_only=False)
    rows: List[Dict[str, Any]] = []
    try:
        has_rules_l = any(n.strip().lower() in _RULES_NAMES for n in wl.sheetnames)
        has_rules_r = any(n.strip().lower() in _RULES_NAMES for n in wr.sheetnames)
        for name in sorted(set(wl.sheetnames) | set(wr.sheetnames)):
            m = _EH_RE.match(name.strip())
            if not m:
                continue
            label = m.group(1).strip()
            month_end = _month_end_from_label(label)
            entry: Dict[str, Any] = {"sheet": name, "month_label": label}
            for side, wb, key in (("left", wl, "left"), ("right", wr, "right")):
                if name not in wb.sheetnames:
                    entry[key] = {"present": False}
                    continue
                ws = wb[name]
                max_d = _max_date_in_sheet(ws)
                mode = _sheet_mode(wb[name]) if key == "left" else _sheet_mode(wr_f[name])
                stale = False
                if month_end and max_d and max_d < month_end:
                    stale = True
                entry[key] = {
                    "present": True,
                    "mode": mode,
                    "max_date": max_d.isoformat() if max_d else None,
                    "stale_snapshot_warning": stale,
                }
            rows.append(entry)
        return {
            "rows": rows,
            "rules_tab_left": has_rules_l,
            "rules_tab_right": has_rules_r,
        }
    finally:
        wl.close()
        wr.close()
        wr_f.close()
