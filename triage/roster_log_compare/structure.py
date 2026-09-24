"""Sheet structure comparison (section B)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.roster_log_compare.load import load_workbook


def _sheet_row(ws) -> Dict[str, Any]:
    merges = sorted(str(m) for m in ws.merged_cells.ranges)
    tables = sorted(ws.tables.keys()) if ws.tables else []
    return {
        "max_row": ws.max_row,
        "max_column": ws.max_column,
        "merged_cells": merges,
        "freeze_panes": str(ws.freeze_panes) if ws.freeze_panes else None,
        "table_names": tables,
    }


def compare_structure(left_path: Path, right_path: Path) -> Dict[str, Any]:
    wl = load_workbook(left_path, data_only=True)
    wr = load_workbook(right_path, data_only=True)
    rows: List[Dict[str, Any]] = []
    try:
        all_names = sorted(set(wl.sheetnames) | set(wr.sheetnames))
        for name in all_names:
            in_l = name in wl.sheetnames
            in_r = name in wr.sheetnames
            if in_l and in_r:
                sl = _sheet_row(wl[name])
                sr = _sheet_row(wr[name])
                status = "both"
                if sl != sr:
                    status = "both_differ"
            elif in_l:
                sl, sr = _sheet_row(wl[name]), {}
                status = "left_only"
            else:
                sl, sr = {}, _sheet_row(wr[name])
                status = "right_only"
            rows.append({
                "sheet": name,
                "status": status,
                "left": sl,
                "right": sr,
                "row_delta": (sr.get("max_row") or 0) - (sl.get("max_row") or 0),
                "col_delta": (sr.get("max_column") or 0) - (sl.get("max_column") or 0),
            })
        return {"rows": rows, "sheet_count": len(all_names)}
    finally:
        wl.close()
        wr.close()
