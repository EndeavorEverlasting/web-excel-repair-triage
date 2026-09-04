"""Canonical state and reconciliation rules for Roster Log V2."""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA_VERSION = "roster-log-v2/v1"
TOLERANCE_HOURS = 0.01


@dataclass(frozen=True)
class DayReconciliation:
    work_date: str
    staff: str
    paid_hours: float
    allocated_hours: float
    variance: float
    project_count: int
    mode: str
    reconciled: bool


def _number(value: Any, *, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if result < 0:
        raise ValueError(f"{field} must be >= 0")
    return round(result, 4)


def _day_key(row: Dict[str, Any]) -> Tuple[str, str]:
    work_date = str(row.get("date") or "").strip()
    staff = str(row.get("staff") or "").strip()
    if not work_date or not staff:
        raise ValueError("attendance/allocation rows require date and staff")
    try:
        date.fromisoformat(work_date)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {work_date}") from exc
    return work_date, staff


def normalize_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize an operator state document without inventing allocation policy.

    A paid day defaults to one project. When no explicit allocation rows exist for
    that staff/date, one allocation is created for the attendance row's default
    project and the full paid hours. Explicit multi-project rows are preserved.
    """
    if not isinstance(payload, dict):
        raise ValueError("roster state must be an object")
    state = deepcopy(payload)
    version = str(state.get("schema_version") or SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {version}")
    state["schema_version"] = SCHEMA_VERSION
    attendance = list(state.get("attendance") or [])
    allocations = list(state.get("allocations") or [])

    seen_days: set[Tuple[str, str]] = set()
    normalized_attendance: List[Dict[str, Any]] = []
    for raw in attendance:
        row = dict(raw)
        key = _day_key(row)
        if key in seen_days:
            raise ValueError(f"duplicate attendance day: {key[0]} / {key[1]}")
        seen_days.add(key)
        row["paid_hours"] = _number(row.get("paid_hours", 0), field="paid_hours")
        default_project = str(row.get("default_project") or "").strip()
        if row["paid_hours"] > 0 and not default_project:
            raise ValueError(f"default_project required for paid day: {key[0]} / {key[1]}")
        row["default_project"] = default_project
        normalized_attendance.append(row)

    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    normalized_allocations: List[Dict[str, Any]] = []
    ids: set[str] = set()
    for idx, raw in enumerate(allocations, 1):
        row = dict(raw)
        key = _day_key(row)
        if key not in seen_days:
            raise ValueError(f"allocation without attendance day: {key[0]} / {key[1]}")
        project = str(row.get("project") or "").strip()
        if not project:
            raise ValueError(f"allocation project required: {key[0]} / {key[1]}")
        row["project"] = project
        row["hours"] = _number(row.get("hours", 0), field="allocation hours")
        alloc_id = str(row.get("allocation_id") or f"ALLOC-{key[0].replace('-', '')}-{idx:04d}").strip()
        if alloc_id in ids:
            raise ValueError(f"duplicate allocation_id: {alloc_id}")
        ids.add(alloc_id)
        row["allocation_id"] = alloc_id
        row.setdefault("workstream", "")
        row.setdefault("status", "RECONCILED")
        row.setdefault("notes", "")
        grouped[key].append(row)
        normalized_allocations.append(row)

    for attendance_row in normalized_attendance:
        key = _day_key(attendance_row)
        if attendance_row["paid_hours"] <= 0 or grouped.get(key):
            continue
        row = {
            "allocation_id": f"DEFAULT-{key[0].replace('-', '')}-{len(normalized_allocations)+1:04d}",
            "date": key[0],
            "staff": key[1],
            "project": attendance_row["default_project"],
            "workstream": "",
            "hours": attendance_row["paid_hours"],
            "status": "RECONCILED",
            "notes": "Default single-project allocation",
        }
        normalized_allocations.append(row)
        grouped[key].append(row)

    state["attendance"] = normalized_attendance
    state["allocations"] = normalized_allocations
    state.setdefault("projects", [])
    state.setdefault("workstreams", [])
    return state


def reconcile_state(payload: Dict[str, Any]) -> List[DayReconciliation]:
    state = normalize_state(payload)
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in state["allocations"]:
        grouped[_day_key(row)].append(row)

    results: List[DayReconciliation] = []
    for attendance in state["attendance"]:
        key = _day_key(attendance)
        rows = grouped.get(key, [])
        allocated = round(sum(float(row["hours"]) for row in rows), 4)
        paid = float(attendance["paid_hours"])
        variance = round(paid - allocated, 4)
        projects = {str(row["project"]).strip() for row in rows if str(row["project"]).strip()}
        mode = "MULTI" if len(projects) > 1 else "SINGLE"
        results.append(
            DayReconciliation(
                work_date=key[0],
                staff=key[1],
                paid_hours=paid,
                allocated_hours=allocated,
                variance=variance,
                project_count=len(projects),
                mode=mode,
                reconciled=abs(variance) <= TOLERANCE_HOURS,
            )
        )
    return results


def assert_reconciled(payload: Dict[str, Any]) -> List[DayReconciliation]:
    results = reconcile_state(payload)
    bad = [row for row in results if not row.reconciled]
    if bad:
        detail = "; ".join(
            f"{row.work_date}/{row.staff}: paid={row.paid_hours:g}, allocated={row.allocated_hours:g}, variance={row.variance:g}"
            for row in bad
        )
        raise ValueError(f"project allocations must reconcile to attendance: {detail}")
    return results
