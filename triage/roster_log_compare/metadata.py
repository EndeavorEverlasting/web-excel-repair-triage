"""Workbook metadata comparison (section A)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.roster_log_compare.load import load_workbook, workbook_side_meta


def compare_metadata(left_path: Path, right_path: Path) -> Dict[str, Any]:
    wl = load_workbook(left_path, data_only=True)
    wr = load_workbook(right_path, data_only=True)
    try:
        left = workbook_side_meta(left_path, wl)
        right = workbook_side_meta(right_path, wr)
        left_set = set(left["sheetnames"])
        right_set = set(right["sheetnames"])
        return {
            "left": left,
            "right": right,
            "diff": {
                "sheets_only_left": sorted(left_set - right_set),
                "sheets_only_right": sorted(right_set - left_set),
                "sheet_count_delta": right["sheet_count"] - left["sheet_count"],
            },
        }
    finally:
        wl.close()
        wr.close()
