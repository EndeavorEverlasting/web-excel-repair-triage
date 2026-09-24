from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, time
from typing import Literal


WorkContext = Literal[
    "Configuration",
    "Inventory Management",
    "Inventory Management & Logistics",
    "Deployment Support",
    "Incident Response",
    "Ticket Coordination",
    "Client Coordination",
    "Logistics",
    "Mixed Operational Support",
    "Unknown / Needs Review",
]


@dataclass(frozen=True)
class WorkEntry:
    source: str
    sheet_name: str
    row_number: int
    tech: str
    work_date: date
    start_time: time | None
    end_time: time | None
    hours: float
    original_assignment: str
    work_context: WorkContext
    context_reason: str
    notes: str = ""
    confidence: str = "medium"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["work_date"] = self.work_date.isoformat()
        d["start_time"] = self.start_time.isoformat() if self.start_time else ""
        d["end_time"] = self.end_time.isoformat() if self.end_time else ""
        return d


@dataclass(frozen=True)
class Mismatch:
    severity: Literal["red", "amber", "blue", "gray"]
    mismatch_type: str
    tech: str
    work_date: str
    source_a: str
    source_b: str
    source_a_value: str
    source_b_value: str
    recommendation: str
    leadership_safe: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExportResult:
    output_path: str
    row_count: int
    total_hours: float
    warnings: list[str]
