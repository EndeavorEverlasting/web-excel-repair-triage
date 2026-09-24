"""Data models for roster log review queue graft engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClockPair:
    in_col: str
    out_col: str
    in_index: int  # 1-based column index
    out_index: int


@dataclass
class LiveCFPatchStats:
    sheet_name: str
    worksheet_part: str
    patched: bool = False
    clock_pairs: int = 0
    new_cf_groups: int = 0
    new_cf_rules: int = 0
    cf_groups_before: int = 0
    cf_groups_after: int = 0
    priority_start: int = 0
    priority_end: int = 0
    last_clock_col: str = ""
    last_data_row: int = 202

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patched": self.patched,
            "clock_pairs": self.clock_pairs,
            "new_cf_groups": self.new_cf_groups,
            "new_cf_rules": self.new_cf_rules,
            "priority_start": self.priority_start,
            "priority_end": self.priority_end,
            "last_clock_col": self.last_clock_col,
            "last_data_row": self.last_data_row,
            "cf_groups_before": self.cf_groups_before,
            "cf_groups_after": self.cf_groups_after,
            "worksheet_part": self.worksheet_part,
        }


@dataclass
class ReviewQueueRow:
    review_id: str
    month: str
    date: str
    staff: str
    source_sheet: str
    source_cells: str
    rule_code: str
    severity: str
    current_status: str = "Open"
    detected_value: str = ""
    expected_value: str = ""
    suggested_resolution: str = ""
    resolution_value: str = ""
    resolution_source: str = ""
    owner: str = ""
    last_reviewed: str = ""
    notes: str = ""


@dataclass
class GraftResult:
    output_path: str
    provenance: Dict[str, Any]
    live_cf_stats: Dict[str, LiveCFPatchStats] = field(default_factory=dict)
    review_queue_rows: int = 0
    preflight_pass: bool = True
    errors: List[str] = field(default_factory=list)
