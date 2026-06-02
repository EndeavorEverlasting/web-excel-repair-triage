"""Row + report models and the project -> billing-bucket map."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


# ── Billing-bucket mapping ──────────────────────────────────────────────────
BUCKET_NEURONS = "Neurons"
BUCKET_DELIVERY = "Delivery / Transport / Disposal"
BUCKET_PROJECTS_TEAM = "Projects Team"
BUCKET_IPHONES = "iPhones"
BUCKET_OTHER = "Other"


def billing_bucket(project: str) -> str:
    p = (project or "").lower()
    if "neuron" in p:
        return BUCKET_NEURONS
    if "delivery" in p or "transport" in p or "disposal" in p:
        return BUCKET_DELIVERY
    if "projects team" in p or "project team" in p:
        return BUCKET_PROJECTS_TEAM
    if "iphone" in p:
        return BUCKET_IPHONES
    return BUCKET_OTHER


def is_neuron(project: str) -> bool:
    return "neuron" in (project or "").lower()


@dataclass
class DailyRecord:
    """One resolved staff/date worked shift (multi-project, override-aware)."""
    date: date
    day: str
    tech: str
    project: str
    project_source: str           # override | worked | assignment | live_default
    clock_in: str                 # display "9:00 AM"
    clock_out: str
    gross_span: float
    lunch: float
    net_hours: float
    long_shift: bool = False
    note: str = ""
    worked_label: str = ""

    def to_detail_dict(self) -> Dict[str, Any]:
        return {
            "Date": self.date.isoformat(),
            "Day": self.day,
            "Tech": self.tech,
            "Project": self.project,
            "Clock In": self.clock_in,
            "Clock Out": self.clock_out,
            "Gross Span": round(self.gross_span, 2),
            "Lunch": round(self.lunch, 2),
            "Net Hours": round(self.net_hours, 2),
            "Flag": "Long shift" if self.long_shift else "",
        }


@dataclass
class ProjectSummaryRow:
    project: str
    tech_count: int
    worked_days: int
    gross_span: float
    lunch_deducted: float
    net_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Project": self.project,
            "Tech Count": self.tech_count,
            "Worked Days": self.worked_days,
            "Gross Span Hours": round(self.gross_span, 2),
            "Lunch Deducted": round(self.lunch_deducted, 2),
            "Net Hours": round(self.net_hours, 2),
        }


@dataclass
class TechSummaryRow:
    tech: str
    projects: str
    worked_days: int
    gross_span: float
    lunch_deducted: float
    net_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Tech": self.tech,
            "Project(s)": self.projects,
            "Worked Days": self.worked_days,
            "Gross Span Hours": round(self.gross_span, 2),
            "Lunch Deducted": round(self.lunch_deducted, 2),
            "Net Hours": round(self.net_hours, 2),
        }


@dataclass
class TechProjectRow:
    tech: str
    project: str
    worked_days: int
    gross_span: float
    lunch_deducted: float
    net_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Tech": self.tech,
            "Project": self.project,
            "Worked Days": self.worked_days,
            "Gross Span Hours": round(self.gross_span, 2),
            "Lunch Deducted": round(self.lunch_deducted, 2),
            "Net Hours": round(self.net_hours, 2),
        }


@dataclass
class BillingBucketRow:
    bucket: str
    tech_count: int
    worked_rows: int
    billable_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Billing Bucket": self.bucket,
            "Tech Count": self.tech_count,
            "Worked Rows": self.worked_rows,
            "Billable Hours": round(self.billable_hours, 2),
        }


@dataclass
class MonthSummary:
    month_key: str                # "2026-05"
    month_name: str               # "May 2026"
    records: List[DailyRecord] = field(default_factory=list)
    project_rows: List[ProjectSummaryRow] = field(default_factory=list)
    tech_rows: List[TechSummaryRow] = field(default_factory=list)
    tech_project_rows: List[TechProjectRow] = field(default_factory=list)
    bucket_rows: List[BillingBucketRow] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    malformed: List[str] = field(default_factory=list)

    # ── Executive metrics ──
    @property
    def total_net(self) -> float:
        return round(sum(r.net_hours for r in self.records), 2)

    @property
    def total_gross(self) -> float:
        return round(sum(r.gross_span for r in self.records), 2)

    @property
    def total_lunch(self) -> float:
        return round(sum(r.lunch for r in self.records), 2)

    @property
    def techs_reflected(self) -> int:
        return len({r.tech for r in self.records})

    @property
    def projects_reflected(self) -> int:
        return len({r.project for r in self.records})

    def net_for_bucket(self, bucket: str) -> float:
        return round(
            sum(r.net_hours for r in self.records if billing_bucket(r.project) == bucket), 2
        )

    def neuron_records(self) -> List[DailyRecord]:
        return [r for r in self.records if is_neuron(r.project)]
