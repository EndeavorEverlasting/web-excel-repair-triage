"""Row and report models for the Neuron Track Hours engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


# Sheet contract (matches the proven reference workbook):
APRIL_MAY_COLUMNS = [
    "Action Status",
    "Review Result",
    "Month",
    "Date",
    "Day",
    "Tech",
    "Project",
    "Clock In",
    "Clock Out",
    "Gross Hours",
    "Weekend",
    "Go Live Weekend",
    "Live Sheet",
]

GO_LIVE_COLUMNS = [
    "Severity",
    "Action Status",
    "Review Result",
    "Month",
    "Date",
    "Day",
    "Tech",
    "Project",
    "Clock In",
    "Clock Out",
    "Gross Hours",
    "Live Sheet",
    "Roster Row",
]

TECH_SUMMARY_COLUMNS = [
    "Month",
    "Tech",
    "Worked Days",
    "Gross Hours",
    "Weekend Hours",
    "Go Live Weekend Hours",
]

REVIEW_FLAG_COLUMNS = [
    "Severity",
    "Issue Type",
    "Action Status",
    "Review Result",
    "Month",
    "Date",
    "Day",
    "Tech",
    "Project",
    "Clock In",
    "Clock Out",
    "Gross Hours",
    "Note",
]

DEFAULT_ACTION_STATUS = "Not Started"
DEFAULT_REVIEW_RESULT = "Pending"

ACTION_STATUS_VALUES = ["Not Started", "In Progress", "Done"]
REVIEW_RESULT_VALUES = ["Pending", "Confirmed", "Adjusted", "Excluded"]

GO_LIVE_WEEKEND_DATES = {date(2026, 5, 30), date(2026, 5, 31)}


@dataclass
class NeuronHoursRow:
    month: str = ""
    date: Optional[date] = None
    day: str = ""
    tech: str = ""
    project: str = "Neuron Deployments"
    clock_in: str = ""
    clock_out: str = ""
    gross_hours: float = 0.0
    weekend: bool = False
    go_live_weekend: bool = False
    live_sheet: str = ""
    roster_row: int = 0
    note: str = ""
    action_status: str = DEFAULT_ACTION_STATUS
    review_result: str = DEFAULT_REVIEW_RESULT

    def date_iso(self) -> str:
        return self.date.isoformat() if self.date else ""

    def to_track_dict(self) -> Dict[str, Any]:
        return {
            "Action Status": self.action_status,
            "Review Result": self.review_result,
            "Month": self.month,
            "Date": self.date_iso(),
            "Day": self.day,
            "Tech": self.tech,
            "Project": self.project,
            "Clock In": self.clock_in,
            "Clock Out": self.clock_out,
            "Gross Hours": round(self.gross_hours, 2),
            "Weekend": "Yes" if self.weekend else "No",
            "Go Live Weekend": "Yes" if self.go_live_weekend else "No",
            "Live Sheet": self.live_sheet,
        }

    def to_go_live_dict(self, severity: str = "PURPLE") -> Dict[str, Any]:
        return {
            "Severity": severity,
            "Action Status": self.action_status,
            "Review Result": self.review_result,
            "Month": self.month,
            "Date": self.date_iso(),
            "Day": self.day,
            "Tech": self.tech,
            "Project": self.project,
            "Clock In": self.clock_in,
            "Clock Out": self.clock_out,
            "Gross Hours": round(self.gross_hours, 2),
            "Live Sheet": self.live_sheet,
            "Roster Row": self.roster_row,
        }

    def to_json(self) -> Dict[str, Any]:
        d = self.to_track_dict()
        d["Roster Row"] = self.roster_row
        d["Note"] = self.note
        return d


@dataclass
class ReviewFlag:
    severity: str
    issue_type: str
    month: str
    date: Optional[date]
    day: str
    tech: str
    project: str
    clock_in: str
    clock_out: str
    gross_hours: float
    note: str = ""
    action_status: str = DEFAULT_ACTION_STATUS
    review_result: str = DEFAULT_REVIEW_RESULT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Severity": self.severity,
            "Issue Type": self.issue_type,
            "Action Status": self.action_status,
            "Review Result": self.review_result,
            "Month": self.month,
            "Date": self.date.isoformat() if self.date else "",
            "Day": self.day,
            "Tech": self.tech,
            "Project": self.project,
            "Clock In": self.clock_in,
            "Clock Out": self.clock_out,
            "Gross Hours": round(self.gross_hours, 2),
            "Note": self.note,
        }


@dataclass
class TechSummaryRow:
    month: str
    tech: str
    worked_days: int
    gross_hours: float
    weekend_hours: float
    go_live_weekend_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Month": self.month,
            "Tech": self.tech,
            "Worked Days": self.worked_days,
            "Gross Hours": round(self.gross_hours, 2),
            "Weekend Hours": round(self.weekend_hours, 2),
            "Go Live Weekend Hours": round(self.go_live_weekend_hours, 2),
        }


@dataclass
class TrackHoursReport:
    rows: List[NeuronHoursRow] = field(default_factory=list)
    review_flags: List[ReviewFlag] = field(default_factory=list)
    tech_summary: List[TechSummaryRow] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def rows_for_month(self, month: str) -> List[NeuronHoursRow]:
        return [r for r in self.rows if r.month == month]

    def go_live_rows(self) -> List[NeuronHoursRow]:
        return [r for r in self.rows if r.go_live_weekend]

    def month_total(self, month: str) -> float:
        # Sum the penny-rounded per-row values (matches the workbook's displayed total).
        return round(sum(round(r.gross_hours, 2) for r in self.rows_for_month(month)), 2)

    def grand_total(self) -> float:
        return round(sum(round(r.gross_hours, 2) for r in self.rows), 2)

    def go_live_hours(self) -> float:
        return round(sum(round(r.gross_hours, 2) for r in self.go_live_rows()), 2)
