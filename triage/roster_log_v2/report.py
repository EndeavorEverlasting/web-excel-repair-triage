"""Deterministic reporting derived from normalized Roster Log V2 allocations."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Set, Tuple

from .schema import normalize_state, reconcile_state

REPORT_VERSION = "roster-log-v2-project-report/v1"


@dataclass(frozen=True)
class ProjectReportRow:
    project: str
    allocated_hours: float
    day_count: int
    staff_count: int
    allocation_count: int


def project_report_rows(payload: Dict[str, Any]) -> List[ProjectReportRow]:
    """Return stable per-project totals from actual allocation rows.

    Attendance ``default_project`` is deliberately ignored here. Normalization
    creates a DEFAULT allocation only when a paid day has no explicit allocations,
    so every reported project hour has exactly one allocation-row explanation.
    """
    state = normalize_state(payload)
    hours: Dict[str, float] = defaultdict(float)
    days: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)
    staff: Dict[str, Set[str]] = defaultdict(set)
    counts: Dict[str, int] = defaultdict(int)

    for row in state["allocations"]:
        project = str(row["project"]).strip()
        hours[project] += float(row["hours"])
        days[project].add((str(row["date"]), str(row["staff"])))
        staff[project].add(str(row["staff"]))
        counts[project] += 1

    return [
        ProjectReportRow(
            project=project,
            allocated_hours=round(hours[project], 4),
            day_count=len(days[project]),
            staff_count=len(staff[project]),
            allocation_count=counts[project],
        )
        for project in sorted(hours)
    ]


def report_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable machine-readable report for humans, agents, and exports."""
    state = normalize_state(payload)
    reconciliation = reconcile_state(state)
    paid_hours = round(sum(float(row["paid_hours"]) for row in state["attendance"]), 4)
    allocated_hours = round(sum(float(row["hours"]) for row in state["allocations"]), 4)
    return {
        "report_version": REPORT_VERSION,
        "schema_version": state["schema_version"],
        "attendance_days": len(state["attendance"]),
        "allocation_rows": len(state["allocations"]),
        "paid_hours": paid_hours,
        "allocated_hours": allocated_hours,
        "variance": round(paid_hours - allocated_hours, 4),
        "multi_project_days": sum(1 for row in reconciliation if row.mode == "MULTI"),
        "unreconciled_days": sum(1 for row in reconciliation if not row.reconciled),
        "projects": [asdict(row) for row in project_report_rows(state)],
    }
