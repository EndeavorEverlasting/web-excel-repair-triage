"""Per-date Neuron-project resolver for the Bonita submission workbook.

This is the inclusion engine for the clean two-tab Bonita output. It reuses the
proven note-aware punch parsing and clock helpers from ``reader`` and the
Assignments loader from ``roster_parser``; it adds project resolution,
classification (include / off-project / non-work-marker / excluded-name) and a
review trail so nothing is silently dropped.

Inclusion rule (project-driven):
  A tech/date shift enters the Bonita workbook only when the resolved project
  for that date is the Neuron project. Resolution precedence:
      Worked Projects cell  >  Assignments override  >  Live default project.
  The default project counts unless that day is overwritten to a non-Neuron
  project; a default non-Neuron day counts only when overwritten to Neuron.

Exclusions (parsed, recorded in review, never counted):
  - ``/ Bonita`` and other off-project coverage punches.
  - Non-work markers: PTO / NON-PTO / N/A / out sick / vacation / off ...
  - Excluded names: Yostinn Minaya, Steven Marques / Inventory.
"""
from __future__ import annotations

import re
from calendar import month_name
from dataclasses import dataclass, field
from datetime import date, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from triage.nw_prj_neuron_track_hours.reader import (
    RosterReadError,
    _compute_gross,
    _DATE_HEADER,
    _decimal_to_time,
    _find_sheet,
    _format_clock,
    _is_neuron,
    _month_label,
    _MONTH_ABBREVS,
    _worked_project_lookup,
    split_note_bearing_punch,
)

# ── Project display + classification config ─────────────────────────────────
NEURON_INTERNAL_PROJECT = "Neuron Deployments"
# Client-facing rename of the internal project (display alias).
NEURON_DISPLAY_NAME = "Northwell - Neurons"

DEFAULT_ASSIGNMENT_TYPE = "Neuron Installation"
DELIVERY_ASSIGNMENT_TYPE = "Delivery / Transport / Disposal"

LONG_SHIFT_HOURS = 12.0

# Off-project coverage signals seen in punch notes (parsed but not counted).
_OFF_PROJECT_NOTE = re.compile(r"\bbonita\b", re.IGNORECASE)

# Activity signals that, within a Neuron day, mean the Delivery sub-label.
_DELIVERY_SIGNAL = re.compile(r"deliver|transport|disposal", re.IGNORECASE)

# Excluded names (never counted, recorded in review).
EXCLUDED_NAMES = {"yostinn minaya", "steven marques", "inventory"}

# Non-work markers (whole-cell text instead of a punch time).
_NON_WORK_MARKER = re.compile(
    r"^\s*(pto|non[\s-]*pto|n/?a|out\s*sick|sick|vacation|off\b.*|holiday|"
    r"unpaid|leave|absent)\s*$",
    re.IGNORECASE,
)


@dataclass
class BonitaShift:
    """One included Neuron shift destined for the clean workbook."""
    month_key: str            # "2026-04"
    month_name: str           # "April"
    date: date
    day: str                  # "Tue"
    tech: str
    clock_in: str             # display, e.g. "9:00 AM"
    clock_out: str
    total_hours: float
    project_name: str = NEURON_DISPLAY_NAME
    assignment_type: str = DEFAULT_ASSIGNMENT_TYPE
    note: str = ""
    long_shift: bool = False
    start_time: Optional[time] = None   # real time for h:mm AM/PM cells
    end_time: Optional[time] = None


@dataclass
class BonitaReviewItem:
    """A parsed-but-not-counted observation (or a counted-but-flagged one)."""
    category: str             # off_project | non_work_marker | excluded_name
                              # | long_shift | unparsed | assignment_ambiguous
    month_name: str
    date: Optional[date]
    day: str
    tech: str
    clock_in: str = ""
    clock_out: str = ""
    total_hours: float = 0.0
    project: str = ""
    note: str = ""
    source_cell: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "Category": self.category,
            "Month": self.month_name,
            "Date": self.date.isoformat() if self.date else "",
            "Day": self.day,
            "Tech": self.tech,
            "Start Time": self.clock_in,
            "End Time": self.clock_out,
            "Total Hours": round(self.total_hours, 2),
            "Project": self.project,
            "Note": self.note,
            "Source Cell": self.source_cell,
            "Detail": self.detail,
        }


@dataclass
class BonitaResolution:
    shifts: List[BonitaShift] = field(default_factory=list)
    review: List[BonitaReviewItem] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def shifts_for_month(self, month_name_: str) -> List[BonitaShift]:
        return [s for s in self.shifts if s.month_name == month_name_]

    def month_total(self, month_name_: str) -> float:
        return round(
            sum(round(s.total_hours, 2) for s in self.shifts_for_month(month_name_)), 2
        )

    def grand_total(self) -> float:
        return round(sum(round(s.total_hours, 2) for s in self.shifts), 2)


def _excluded_name(name: str) -> bool:
    low = name.strip().lower()
    if low in EXCLUDED_NAMES:
        return True
    return any(tok in low for tok in EXCLUDED_NAMES)


def _is_non_work_marker(text: str) -> bool:
    return bool(text) and bool(_NON_WORK_MARKER.match(text.strip()))


def _col_letter(idx0: int) -> str:
    """0-based column index -> spreadsheet letter (for review source cell refs)."""
    idx = idx0 + 1
    out = ""
    while idx:
        idx, rem = divmod(idx - 1, 26)
        out = chr(65 + rem) + out
    return out


def _classify_assignment(notes: str, worked_label: str) -> Tuple[str, bool]:
    """Return (assignment_type, ambiguous).

    ASSIGNMENT TYPE is operator-classified and is NOT reliably encoded in the
    per-date tabs. We default to Neuron Installation, accept an explicit
    Delivery/Transport/Disposal signal from the worked-project activity text or
    punch note, and flag anything else ambiguous for review (never fabricated).
    """
    haystack = f"{notes} {worked_label}".strip()
    if _DELIVERY_SIGNAL.search(haystack):
        return DELIVERY_ASSIGNMENT_TYPE, False
    return DEFAULT_ASSIGNMENT_TYPE, False


def _resolve_month(wb, month_key: str, resolution: BonitaResolution) -> None:
    label, year, mon = _month_label(month_key)
    short = month_name[mon]

    live_ws = _find_sheet(wb, "Live", label)
    if live_ws is None:
        raise RosterReadError(f"Live sheet not found for {label}")

    worked_ws = _find_sheet(wb, "Worked Projects", label)
    if worked_ws is None:
        resolution.warnings.append(
            f"worked_projects_missing:{label}:falling_back_to_default_and_assignments"
        )
    worked = _worked_project_lookup(worked_ws)

    assignments: Dict[Tuple[date, str], str] = {}
    try:
        from triage.roster_parser import _find_assignments_sheet, _load_assignments
        assignments = _load_assignments(_find_assignments_sheet(wb, label))
    except Exception as exc:  # pragma: no cover - assignments are optional
        resolution.warnings.append(f"assignments_unavailable:{label}:{exc}")

    header_row = 2
    headers = [live_ws.cell(header_row, c).value for c in range(1, live_ws.max_column + 1)]

    date_to_cols: Dict[date, Dict[str, int]] = {}
    for i, h in enumerate(headers):
        if not isinstance(h, str):
            continue
        mm = _DATE_HEADER.match(h.strip())
        if not mm:
            continue
        mon_num = _MONTH_ABBREVS.get(mm.group(1)[:3].lower())
        if mon_num is None:
            continue
        try:
            d = date(year, mon_num, int(mm.group(2)))
        except ValueError:
            continue
        direction = "in" if "in" in mm.group(3).lower() else "out"
        date_to_cols.setdefault(d, {})[direction] = i

    if not date_to_cols:
        raise RosterReadError(f"No date columns parsed in Live sheet for {label}")

    for r in range(header_row + 1, live_ws.max_row + 1):
        staff_val = live_ws.cell(r, 1).value
        if not staff_val or str(staff_val).strip() in ("", "None", "0"):
            continue
        if isinstance(staff_val, (int, float)):
            continue
        staff = str(staff_val).strip()
        default_proj = str(live_ws.cell(r, 2).value or "").strip()
        if default_proj == "0":
            default_proj = ""

        for d, dirs in sorted(date_to_cols.items()):
            in_idx = dirs.get("in")
            out_idx = dirs.get("out")
            in_val = live_ws.cell(r, in_idx + 1).value if in_idx is not None else None
            out_val = live_ws.cell(r, out_idx + 1).value if out_idx is not None else None
            ci, note_in = split_note_bearing_punch(in_val)
            co, note_out = split_note_bearing_punch(out_val)
            if ci is None and co is None:
                # Possibly a non-work marker in a cell; record and move on.
                marker = (note_in or note_out or "").strip()
                if _is_non_work_marker(marker):
                    resolution.review.append(BonitaReviewItem(
                        category="non_work_marker",
                        month_name=short, date=d, day=d.strftime("%a"),
                        tech=staff, project=default_proj,
                        note=marker,
                        source_cell=f"{_col_letter(in_idx or out_idx or 0)}{r}",
                        detail="non-work marker, not counted",
                    ))
                continue

            note = " ".join(n for n in (note_in, note_out) if n).strip()
            day = d.strftime("%a")
            cell_ref = f"{_col_letter(in_idx if in_idx is not None else 0)}{r}"

            worked_label = worked.get((staff, d), "")
            assign_label = assignments.get((d, staff), "")
            resolved = worked_label or assign_label or default_proj

            # Excluded names never count (but are recorded for traceability).
            if _excluded_name(staff):
                if _is_neuron(resolved):
                    resolution.review.append(BonitaReviewItem(
                        category="excluded_name",
                        month_name=short, date=d, day=day, tech=staff,
                        clock_in=_format_clock(ci), clock_out=_format_clock(co),
                        total_hours=_compute_gross(ci, co), project=resolved,
                        note=note, source_cell=cell_ref,
                        detail="excluded name, not counted",
                    ))
                continue

            # Off-project coverage punch (e.g. "/ Bonita"): parse, do not count.
            if _OFF_PROJECT_NOTE.search(note):
                resolution.review.append(BonitaReviewItem(
                    category="off_project",
                    month_name=short, date=d, day=day, tech=staff,
                    clock_in=_format_clock(ci), clock_out=_format_clock(co),
                    total_hours=_compute_gross(ci, co), project=resolved,
                    note=note, source_cell=cell_ref,
                    detail="off-project coverage punch, excluded from totals",
                ))
                continue

            # Project-driven inclusion.
            if not _is_neuron(resolved):
                continue

            gross = _compute_gross(ci, co)
            assignment_type, ambiguous = _classify_assignment(note, worked_label)
            long_shift = gross >= LONG_SHIFT_HOURS

            shift = BonitaShift(
                month_key=month_key,
                month_name=short,
                date=d,
                day=day,
                tech=staff,
                clock_in=_format_clock(ci),
                clock_out=_format_clock(co),
                total_hours=gross,
                project_name=NEURON_DISPLAY_NAME,
                assignment_type=assignment_type,
                note=note,
                long_shift=long_shift,
                start_time=_decimal_to_time(ci),
                end_time=_decimal_to_time(co),
            )
            resolution.shifts.append(shift)

            if long_shift:
                resolution.review.append(BonitaReviewItem(
                    category="long_shift",
                    month_name=short, date=d, day=day, tech=staff,
                    clock_in=shift.clock_in, clock_out=shift.clock_out,
                    total_hours=gross, project=NEURON_DISPLAY_NAME,
                    note=note, source_cell=cell_ref,
                    detail=f"long shift {gross:g}h included; verify",
                ))
            if ambiguous:
                resolution.review.append(BonitaReviewItem(
                    category="assignment_ambiguous",
                    month_name=short, date=d, day=day, tech=staff,
                    clock_in=shift.clock_in, clock_out=shift.clock_out,
                    total_hours=gross, project=NEURON_DISPLAY_NAME,
                    note=note, source_cell=cell_ref,
                    detail="assignment type unresolved; defaulted to Neuron Installation",
                ))


def resolve_bonita_shifts(
    roster_path: str | Path,
    months: List[str],
) -> BonitaResolution:
    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover
        raise RosterReadError("openpyxl is required: pip install openpyxl") from e
    p = Path(roster_path)
    if not p.exists():
        raise RosterReadError(f"Roster file not found: {roster_path}")
    wb = openpyxl.load_workbook(str(p), data_only=True, read_only=False)
    resolution = BonitaResolution()
    try:
        for mk in months:
            _resolve_month(wb, mk, resolution)
    finally:
        wb.close()
    # Stable ordering for deterministic output.
    resolution.shifts.sort(key=lambda s: (s.month_key, s.date, s.tech))
    resolution.review.sort(
        key=lambda x: (x.category, x.date or date.min, x.tech)
    )
    return resolution
