"""Overnight-punch classification and unassigned-hours rules for the May roster.

Hard rules (see docs/MAY_ROSTER_WEBEXCEL_CF_PREFLIGHT_CONTRACT.md):

- An after-midnight clock-out is NOT automatically malformed. When
  ``clock_out < clock_in`` the shift is *overnight*; gross duration is
  ``(24 - clock_in) + clock_out`` (i.e. the work crosses midnight).
- A blank Sunday paired with a blank cell is *neutral*, never malformed.
- Weekend no-work is neutral, never malformed.
- A row is *malformed* only when one of the strict criteria below holds.

All punch math is done in decimal hours in ``[0, 24)`` so the contract's
``(1 - clock_in) + clock_out`` (day-fraction form) is equivalent to the
``(24 - clock_in) + clock_out`` used here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional, Tuple

from triage.nw_prj_neuron_track_hours.reader import split_note_bearing_punch

# A computed shift longer than this many hours cannot be a real same-day or
# overnight shift and is treated as a data error (malformed), not overnight.
ABSURD_DURATION_HOURS = 20.0

# Project / assignment cell values that mean "no real billable project".
_UNASSIGNED_PROJECT_TOKENS = {"", "0", "0.0", "none", "n/a", "na", "unknown", "tbd", "?"}

# Day-type markers that exempt a row from the unassigned rule.
_NON_BILLABLE_DAYTYPES = {"pto", "unpaid", "off-project", "off project", "weekend", "weekend-no-work", "holiday"}

# Classification status labels.
STATUS_OK = "ok"
STATUS_OVERNIGHT = "overnight"
STATUS_MALFORMED = "malformed"
STATUS_NEUTRAL = "neutral"

# Human-facing status label for unassigned rows.
UNASSIGNED_LABEL = "Unassigned / Needs Project"
OVERNIGHT_LABEL = "Overnight / Needs Confirmation"


@dataclass
class PunchClassification:
    status: str
    gross_hours: float = 0.0
    reason: str = ""
    clock_in: Optional[float] = None
    clock_out: Optional[float] = None
    is_overnight: bool = False
    note: str = ""

    def to_dict(self) -> dict:
        import dataclasses

        return dataclasses.asdict(self)


def parse_punch(value: Any) -> Tuple[Optional[float], str, bool]:
    """Parse a punch cell into ``(decimal_hours, note, parseable)``.

    ``parseable`` is False only when the cell carries non-empty content that
    cannot be read as a time (e.g. ``"ASK MGR"``). A truly blank cell returns
    ``(None, "", True)`` so that blank/blank pairs stay neutral.
    """
    if value is None:
        return None, "", True
    if isinstance(value, str) and not value.strip():
        return None, "", True
    decimal, note = split_note_bearing_punch(value)
    if decimal is None:
        # Non-empty but no parseable time component.
        has_content = bool(str(value).strip())
        return None, note, not has_content
    return decimal, note, True


def compute_overnight_gross(clock_in: float, clock_out: float) -> float:
    """Gross hours for a punch pair, wrapping past midnight when needed."""
    diff = clock_out - clock_in
    if diff < 0:
        diff += 24.0
    return round(diff, 4)


def classify_punch(
    clock_in_raw: Any,
    clock_out_raw: Any,
    *,
    is_weekend: bool = False,
    absurd_hours: float = ABSURD_DURATION_HOURS,
) -> PunchClassification:
    """Classify a single (clock-in, clock-out) pair.

    Returns a :class:`PunchClassification`. Overnight shifts are reported with
    ``status == STATUS_OVERNIGHT`` and ``is_overnight == True`` so callers can
    surface "Overnight / Needs Confirmation" without treating them as errors.
    """
    ci, note_in, ci_ok = parse_punch(clock_in_raw)
    co, note_out, co_ok = parse_punch(clock_out_raw)
    note = " ".join(n for n in (note_in, note_out) if n).strip()

    # Both blank -> neutral (covers blank Sunday, and blank Sunday + populated
    # Monday since Monday is a different column / classification call).
    if ci is None and co is None:
        if ci_ok and co_ok:
            return PunchClassification(STATUS_NEUTRAL, 0.0, "both punches blank", note=note)
        return PunchClassification(
            STATUS_MALFORMED, 0.0, "punch value not parseable as time", note=note
        )

    # Non-parseable content in either punch -> malformed.
    if not ci_ok or not co_ok:
        return PunchClassification(
            STATUS_MALFORMED, 0.0, "punch value not parseable as time",
            clock_in=ci, clock_out=co, note=note,
        )

    # Exactly one punch present -> malformed (single missing punch).
    if (ci is None) != (co is None):
        which = "clock-out missing" if co is None else "clock-in missing"
        return PunchClassification(
            STATUS_MALFORMED, 0.0, f"single punch present ({which})",
            clock_in=ci, clock_out=co, note=note,
        )

    # Both present and equal -> zero/ambiguous duration -> malformed.
    if ci == co:
        return PunchClassification(
            STATUS_MALFORMED, 0.0, "clock-in equals clock-out (zero duration)",
            clock_in=ci, clock_out=co, note=note,
        )

    overnight = co < ci
    gross = compute_overnight_gross(ci, co)

    if gross > absurd_hours:
        return PunchClassification(
            STATUS_MALFORMED, gross,
            f"computed duration {gross:g}h exceeds absurd threshold {absurd_hours:g}h",
            clock_in=ci, clock_out=co, is_overnight=overnight, note=note,
        )

    if overnight:
        return PunchClassification(
            STATUS_OVERNIGHT, gross, "clock-out after midnight (overnight shift)",
            clock_in=ci, clock_out=co, is_overnight=True, note=note,
        )

    return PunchClassification(
        STATUS_OK, gross, "same-day shift",
        clock_in=ci, clock_out=co, is_overnight=False, note=note,
    )


def is_unassigned(
    paid_hours: float,
    project: Any,
    *,
    day_type: str = "",
) -> bool:
    """True when a paid row has no real billable project assignment.

    A row/date is unassigned when:
      1. actual paid hours > 0,
      2. project is blank / unknown / weakly mapped / ``0`` / not billable,
      3. the entry is not clearly PTO, unpaid, off-project, or weekend no-work.
    """
    if paid_hours is None or paid_hours <= 0:
        return False
    dt = (day_type or "").strip().lower()
    if dt in _NON_BILLABLE_DAYTYPES:
        return False
    proj = str(project if project is not None else "").strip().lower()
    return proj in _UNASSIGNED_PROJECT_TOKENS


@dataclass
class UnassignedRow:
    tech: str
    date: Optional[date]
    paid_hours: float
    project: str
    status: str = UNASSIGNED_LABEL

    def to_dict(self) -> dict:
        return {
            "Tech": self.tech,
            "Date": self.date.isoformat() if self.date else "",
            "Actual Paid Hours": self.paid_hours,
            "Current Project / Assignment": self.project,
            "Status": self.status,
        }


def build_unassigned_rows(records: List[dict]) -> List[UnassignedRow]:
    """Build named unassigned-hours rows from roster records.

    Each record is a dict with keys ``tech``, ``date``, ``paid_hours``,
    ``project`` and optional ``day_type``. The summary names names: every
    returned row carries the tech, date, hours, and current assignment.
    """
    out: List[UnassignedRow] = []
    for rec in records:
        paid = float(rec.get("paid_hours") or 0.0)
        if is_unassigned(paid, rec.get("project"), day_type=rec.get("day_type", "")):
            out.append(
                UnassignedRow(
                    tech=str(rec.get("tech", "")).strip(),
                    date=rec.get("date"),
                    paid_hours=paid,
                    project=str(rec.get("project") or "").strip(),
                )
            )
    out.sort(key=lambda r: (r.date or date.min, r.tech))
    return out
