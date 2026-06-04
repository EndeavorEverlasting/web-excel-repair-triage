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

Work-context rule:
  Included Neuron shifts are classified through ``triage.neuron_work_context_rules``.
  The submission workbook receives the resulting task lane only. Rule reasons and
  confidence belong in the internal review/audit sidecars, not the clean tracker.

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
from typing import Dict, List, Optional

from triage.neuron_work_context_rules import (
    CLIENT_COORDINATION,
    CONFIGURATIONS,
    INVENTORY_MANAGEMENT,
    LOGISTICS,
    classify_neuron_work_context,
)
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

# Backward-compatible constant name. This is no longer a universal default.
DEFAULT_ASSIGNMENT_TYPE = CONFIGURATIONS
DELIVERY_ASSIGNMENT_TYPE = LOGISTICS

LONG_SHIFT_HOURS = 12.0

# Off-project coverage signals seen in punch notes (parsed but not counted).
_OFF_PROJECT_NOTE = re.compile(r"\bbonita\b", re.IGNORECASE)

# Excluded names (never counted, recorded in review).
EXCLUDED_NAMES = {"yostinn minaya", "steven marques", "inventory"}

# Non-work markers (whole-cell text instead of a punch time).
_NON_WORK_MARKER = re.compile(
    r"^\s*(pto|non[\s-]*pto|n/?a|out\s*sick|sick|vacation|off\b.*|holiday|"
    r"unpaid|leave|absent|car\s*issue|off\s*/\s*car\s*issue)\s*$",
    re.IGNORECASE,
)

# Client Coordination may appear on the submission sheet only for approved coordinators.
CLIENT_COORDINATION_ALLOWLIST = frozenset({
    "richard perez",
    "rich perez",
    "khadejah harrison",
    "alejandro perales",
})

TECH_DISPLAY_ALIASES: Dict[str, str] = {
    "rich perez": "Richard Perez",
    "eman": "Emmanuel Perales",
    "emmanuel perales": "Emmanuel Perales",
    "suhan": "Md Suhan Newaz",
    "md suhan newaz": "Md Suhan Newaz",
    "val": "Valentin Nikoliuch",
    "valentin nikoliuch": "Valentin Nikoliuch",
}

_MIXED_INV_CONFIG_NOTE = re.compile(
    r"(inventory|stock|warehouse|recon).*(config|configuration|image|baseline)|"
    r"(config|configuration|image|baseline).*(inventory|stock|warehouse|recon)",
    re.IGNORECASE,
)


def normalize_tech_display(name: str) -> str:
    key = name.strip().lower()
    return TECH_DISPLAY_ALIASES.get(key, name.strip())


def _client_coordination_allowed(tech: str) -> bool:
    return tech.strip().lower() in CLIENT_COORDINATION_ALLOWLIST


def _notes_indicate_mixed_inv_config(note: str) -> bool:
    return bool(note and _MIXED_INV_CONFIG_NOTE.search(note))


def _append_shift_or_split(
    resolution: BonitaResolution,
    *,
    month_key: str,
    short: str,
    d: date,
    day: str,
    staff: str,
    ci,
    co,
    gross: float,
    note: str,
    cell_ref: str,
    worked_label: str,
    assign_label: str,
    resolved: str,
    decision,
) -> None:
    """Include shift row(s), applying mixed inventory/configuration split when needed."""
    long_shift = gross >= LONG_SHIFT_HOURS
    base_kwargs = dict(
        month_key=month_key,
        month_name=short,
        date=d,
        day=day,
        tech=staff,
        clock_in=_format_clock(ci),
        clock_out=_format_clock(co),
        project_name=NEURON_DISPLAY_NAME,
        note=note,
        long_shift=long_shift,
        start_time=_decimal_to_time(ci),
        end_time=_decimal_to_time(co),
        assignment_rule=decision.rule,
        assignment_confidence=decision.confidence,
    )

    if _notes_indicate_mixed_inv_config(note):
        half = round(gross / 2, 2)
        remainder = round(gross - half, 2)
        resolution.shifts.append(BonitaShift(
            **base_kwargs,
            total_hours=half,
            assignment_type=INVENTORY_MANAGEMENT,
        ))
        resolution.shifts.append(BonitaShift(
            **base_kwargs,
            total_hours=remainder,
            assignment_type=CONFIGURATIONS,
        ))
        resolution.review.append(BonitaReviewItem(
            category="mixed_assignment_split",
            month_name=short,
            date=d,
            day=day,
            tech=staff,
            clock_in=_format_clock(ci),
            clock_out=_format_clock(co),
            total_hours=gross,
            project=NEURON_DISPLAY_NAME,
            note=note,
            source_cell=cell_ref,
            detail=(
                f"split {gross:g}h -> {half:g}h Inventory Management + "
                f"{remainder:g}h Configurations"
            ),
        ))
        return

    resolution.shifts.append(BonitaShift(
        **base_kwargs,
        total_hours=gross,
        assignment_type=decision.assignment_type,
    ))

    if long_shift:
        resolution.review.append(BonitaReviewItem(
            category="long_shift",
            month_name=short,
            date=d,
            day=day,
            tech=staff,
            clock_in=_format_clock(ci),
            clock_out=_format_clock(co),
            total_hours=gross,
            project=NEURON_DISPLAY_NAME,
            note=note,
            source_cell=cell_ref,
            detail=f"long shift {gross:g}h included; verify",
        ))
    if decision.confidence == "low":
        resolution.review.append(BonitaReviewItem(
            category="assignment_heuristic_low_confidence",
            month_name=short,
            date=d,
            day=day,
            tech=staff,
            clock_in=_format_clock(ci),
            clock_out=_format_clock(co),
            total_hours=gross,
            project=NEURON_DISPLAY_NAME,
            note="",
            source_cell=cell_ref,
            detail=f"assignment resolved by heuristic rule: {decision.rule}",
        ))


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
    assignment_rule: str = ""
    assignment_confidence: str = ""


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

    assignments: Dict[tuple[date, str], str] = {}
    overrides: Dict[tuple[date, str], str] = {}
    try:
        from triage.roster_parser import (
            _find_assignments_sheet,
            _load_assignments,
            _load_overrides_only,
        )
        assignments_sheet = _find_assignments_sheet(wb, label)
        assignments = _load_assignments(assignments_sheet)
        overrides = _load_overrides_only(assignments_sheet)
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
        staff = normalize_tech_display(str(staff_val).strip())
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
                marker = (note_in or note_out or "").strip()
                if _is_non_work_marker(marker):
                    resolution.review.append(BonitaReviewItem(
                        category="non_work_marker",
                        month_name=short,
                        date=d,
                        day=d.strftime("%a"),
                        tech=staff,
                        project=default_proj,
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
            override_label = overrides.get((d, staff), "")
            resolved = override_label or worked_label or assign_label or default_proj

            if _excluded_name(staff):
                if _is_neuron(resolved):
                    resolution.review.append(BonitaReviewItem(
                        category="excluded_name",
                        month_name=short,
                        date=d,
                        day=day,
                        tech=staff,
                        clock_in=_format_clock(ci),
                        clock_out=_format_clock(co),
                        total_hours=_compute_gross(ci, co),
                        project=resolved,
                        note=note,
                        source_cell=cell_ref,
                        detail="excluded name, not counted",
                    ))
                continue

            if _OFF_PROJECT_NOTE.search(note):
                resolution.review.append(BonitaReviewItem(
                    category="off_project",
                    month_name=short,
                    date=d,
                    day=day,
                    tech=staff,
                    clock_in=_format_clock(ci),
                    clock_out=_format_clock(co),
                    total_hours=_compute_gross(ci, co),
                    project=resolved,
                    note=note,
                    source_cell=cell_ref,
                    detail="off-project coverage punch, excluded from totals",
                ))
                continue

            if not _is_neuron(resolved):
                continue

            gross = _compute_gross(ci, co)
            decision = classify_neuron_work_context(
                work_date=d,
                start_hour=ci,
                end_hour=co,
                notes=note,
                worked_label=worked_label or assign_label,
                resolved_project=resolved,
            )

            if (
                decision.assignment_type == CLIENT_COORDINATION
                and not _client_coordination_allowed(staff)
            ):
                resolution.review.append(BonitaReviewItem(
                    category="client_coordination_outside_allowlist",
                    month_name=short,
                    date=d,
                    day=day,
                    tech=staff,
                    clock_in=_format_clock(ci),
                    clock_out=_format_clock(co),
                    total_hours=gross,
                    project=NEURON_DISPLAY_NAME,
                    note=note,
                    source_cell=cell_ref,
                    detail="Client Coordination not allowed for this tech; excluded from workbook",
                ))
                continue

            _append_shift_or_split(
                resolution,
                month_key=month_key,
                short=short,
                d=d,
                day=day,
                staff=staff,
                ci=ci,
                co=co,
                gross=gross,
                note=note,
                cell_ref=cell_ref,
                worked_label=worked_label,
                assign_label=assign_label,
                resolved=resolved,
                decision=decision,
            )


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
    resolution.shifts.sort(key=lambda s: (s.month_key, s.date, s.tech))
    resolution.review.sort(
        key=lambda x: (x.category, x.date or date.min, x.tech)
    )
    return resolution
