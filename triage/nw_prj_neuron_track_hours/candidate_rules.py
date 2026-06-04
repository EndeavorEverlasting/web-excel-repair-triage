"""Candidate Neuron Track Hours transformation rules.

This layer sits between the roster-derived Bonita resolution and the polished
Candidate workbook. It applies business rules that are specific to the current
candidate artifact without weakening the lower-level roster resolver.

Rules captured here:

- Client Coordination is allowed only for approved coordination owners.
- Unauthorized Client Coordination rows are removed from clean time sheets.
- Rezaul Roman's April 2026 Neuron work is represented as mixed Inventory
  Management and Configurations through a deterministic split.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timedelta
from typing import Iterable, List, Tuple

from triage.neuron_work_context_rules import (
    CLIENT_COORDINATION,
    CONFIGURATIONS,
    INVENTORY_MANAGEMENT,
)
from triage.nw_prj_neuron_track_hours.bonita_resolver import (
    BonitaResolution,
    BonitaReviewItem,
    BonitaShift,
)

APPROVED_CLIENT_COORDINATORS = frozenset({
    "richard perez",
    "rich perez",
    "khadejah harrison",
    "alejandro perales",
    "geoff gerber",
})

REZAUL_ROMAN = "rezaul roman"


def normalize_person_name(value: str) -> str:
    """Normalize a person name for rule checks."""

    return " ".join(str(value or "").strip().lower().split())


def is_approved_client_coordinator(name: str) -> bool:
    return normalize_person_name(name) in APPROVED_CLIENT_COORDINATORS


def is_client_coordination_shift(shift: BonitaShift) -> bool:
    return str(shift.assignment_type or "").strip().lower() == CLIENT_COORDINATION.lower()


def should_remove_from_clean_candidate(shift: BonitaShift) -> bool:
    """Return True when a shift must not appear in clean candidate sheets."""

    return is_client_coordination_shift(shift) and not is_approved_client_coordinator(shift.tech)


def is_rezaul_april_shift(shift: BonitaShift) -> bool:
    return normalize_person_name(shift.tech) == REZAUL_ROMAN and shift.date.year == 2026 and shift.date.month == 4


def _minutes(t: time | None) -> int | None:
    if t is None:
        return None
    return int(t.hour) * 60 + int(t.minute)


def _time_from_minutes(value: int) -> time:
    value = value % (24 * 60)
    return time(value // 60, value % 60)


def _duration_hours(start: time | None, end: time | None, fallback: float) -> float:
    sm = _minutes(start)
    em = _minutes(end)
    if sm is None or em is None:
        return round(float(fallback or 0.0), 2)
    if em < sm:
        em += 24 * 60
    return round((em - sm) / 60.0, 2)


def _split_time_window(start: time | None, end: time | None) -> time | None:
    sm = _minutes(start)
    em = _minutes(end)
    if sm is None or em is None:
        return None
    if em < sm:
        em += 24 * 60
    midpoint = sm + int(round((em - sm) / 2.0))
    return _time_from_minutes(midpoint)


def _display_clock(t: time | None, original: str = "") -> str:
    if t is None:
        return original
    hour = t.hour
    suffix = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return f"{h12}:{t.minute:02d} {suffix}"


def split_rezaul_shift(shift: BonitaShift) -> List[BonitaShift]:
    """Split a Rezaul April shift into inventory + configuration segments.

    The split is deterministic: use the exact time-window midpoint when start/end
    times are available. This preserves the row total while making the mixed work
    visible in the workbook.
    """

    midpoint = _split_time_window(shift.start_time, shift.end_time)
    if midpoint is None:
        first_hours = round(float(shift.total_hours or 0.0) / 2.0, 2)
        second_hours = round(float(shift.total_hours or 0.0) - first_hours, 2)
        return [
            replace(
                shift,
                total_hours=first_hours,
                assignment_type=INVENTORY_MANAGEMENT,
                assignment_rule="candidate-rezaul-mixed-work-split-inventory",
                assignment_confidence="manual-rule",
            ),
            replace(
                shift,
                total_hours=second_hours,
                assignment_type=CONFIGURATIONS,
                assignment_rule="candidate-rezaul-mixed-work-split-configurations",
                assignment_confidence="manual-rule",
            ),
        ]

    first_hours = _duration_hours(shift.start_time, midpoint, shift.total_hours / 2.0)
    second_hours = _duration_hours(midpoint, shift.end_time, shift.total_hours - first_hours)

    return [
        replace(
            shift,
            clock_out=_display_clock(midpoint, shift.clock_out),
            end_time=midpoint,
            total_hours=first_hours,
            assignment_type=INVENTORY_MANAGEMENT,
            assignment_rule="candidate-rezaul-mixed-work-split-inventory",
            assignment_confidence="manual-rule",
        ),
        replace(
            shift,
            clock_in=_display_clock(midpoint, shift.clock_in),
            start_time=midpoint,
            total_hours=second_hours,
            assignment_type=CONFIGURATIONS,
            assignment_rule="candidate-rezaul-mixed-work-split-configurations",
            assignment_confidence="manual-rule",
        ),
    ]


def build_candidate_resolution(resolution: BonitaResolution) -> Tuple[BonitaResolution, dict]:
    """Apply candidate artifact rules to an existing Bonita resolution."""

    out = BonitaResolution(warnings=list(resolution.warnings))
    removed: List[BonitaReviewItem] = []
    rezaul_rows = 0

    for shift in resolution.shifts:
        if should_remove_from_clean_candidate(shift):
            removed.append(BonitaReviewItem(
                category="removed_client_coordination",
                month_name=shift.month_name,
                date=shift.date,
                day=shift.day,
                tech=shift.tech,
                clock_in=shift.clock_in,
                clock_out=shift.clock_out,
                total_hours=shift.total_hours,
                project=shift.project_name,
                note=shift.note,
                source_cell="",
                detail="removed from clean Candidate workbook: unauthorized Client Coordination owner",
            ))
            continue

        if is_rezaul_april_shift(shift):
            split = split_rezaul_shift(shift)
            out.shifts.extend(split)
            rezaul_rows += len(split)
            continue

        out.shifts.append(shift)

    out.review = list(resolution.review) + removed
    out.shifts.sort(key=lambda s: (s.date, s.tech.lower(), s.start_time or time(0, 0), s.assignment_type))

    stats = {
        "removed_client_coordination_rows": len(removed),
        "rezaul_rows": rezaul_rows,
        "rezaul_total_hours": round(
            sum(s.total_hours for s in out.shifts if is_rezaul_april_shift(s)), 2
        ),
        "approved_client_coordinators": sorted(APPROVED_CLIENT_COORDINATORS),
    }
    return out, stats
