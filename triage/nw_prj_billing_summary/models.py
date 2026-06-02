"""Data models for the NW PRJ billing summary engine."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class BillingRow:
    """One resolved staff/date billing record."""

    staff: str
    project: str
    date: date
    month_key: str  # "2026-04"
    clock_in: str
    clock_out: str
    gross_hours: float
    lunch_deduction: float
    net_hours: float
    friday_batch: date  # the Friday this row reports under
    weekend: bool = False
    project_source: str = "live"  # "worked" | "override" | "live"
    note: str = ""
    partial: bool = False

    def to_dict(self) -> Dict:
        d = dataclasses.asdict(self)
        d["date"] = self.date.isoformat()
        d["friday_batch"] = self.friday_batch.isoformat()
        return d


@dataclass
class ReviewFlag:
    """An item routed to the internal review queue (never shown to admin)."""

    category: str  # partial_hours | missing_roster | note_bearing | mismatch | excluded_name | long_shift
    staff: str
    detail: str
    date_iso: str = ""

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


@dataclass
class MonthSummary:
    """Per-month rollup."""

    month_key: str
    month_label: str
    gross_hours: float = 0.0
    lunch_deduction: float = 0.0
    net_hours: float = 0.0
    staff_count: int = 0
    daily_rows: int = 0
    by_project: Dict[str, float] = field(default_factory=dict)
    by_friday_batch: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


@dataclass
class BillingReport:
    """Top-level report serialized into manifest/preflight sidecars."""

    roster_path: str = ""
    output_workbook: str = ""
    months: List[str] = field(default_factory=list)
    rows: List[BillingRow] = field(default_factory=list)
    month_summaries: List[MonthSummary] = field(default_factory=list)
    review_flags: List[ReviewFlag] = field(default_factory=list)
    invoice_count: int = 0
    excluded_names: List[str] = field(default_factory=list)
    combined_gross: float = 0.0
    combined_lunch: float = 0.0
    combined_net: float = 0.0
    webexcel_preflight_pass: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def admin_rows(self) -> List[BillingRow]:
        """Rows safe for admin output (notes stripped at render time)."""
        return self.rows

    def to_manifest(self) -> Dict:
        return {
            "roster_path": self.roster_path,
            "output_workbook": self.output_workbook,
            "months": self.months,
            "row_count": len(self.rows),
            "invoice_count": self.invoice_count,
            "excluded_names": self.excluded_names,
            "combined_gross": round(self.combined_gross, 2),
            "combined_lunch": round(self.combined_lunch, 2),
            "combined_net": round(self.combined_net, 2),
            "review_flag_count": len(self.review_flags),
            "month_summaries": [m.to_dict() for m in self.month_summaries],
            "webexcel_preflight_pass": self.webexcel_preflight_pass,
            "warnings": self.warnings,
        }
