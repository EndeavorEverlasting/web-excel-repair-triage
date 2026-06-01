"""Review-flag classification, Rich Guard, pinned-name and summary logic."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from triage.nw_prj_neuron_track_hours.models import (
    NeuronHoursRow,
    ReviewFlag,
    TechSummaryRow,
)

LONG_SHIFT_AMBER = 12.0
LONG_SHIFT_RED = 16.0


def build_tech_summary(rows: List[NeuronHoursRow]) -> List[TechSummaryRow]:
    agg: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(
        lambda: {"days": 0, "gross": 0.0, "weekend": 0.0, "golive": 0.0}
    )
    for r in rows:
        key = (r.month, r.tech)
        agg[key]["days"] += 1
        agg[key]["gross"] += r.gross_hours
        if r.weekend:
            agg[key]["weekend"] += r.gross_hours
        if r.go_live_weekend:
            agg[key]["golive"] += r.gross_hours

    out: List[TechSummaryRow] = []
    for (month, tech), v in agg.items():
        out.append(TechSummaryRow(
            month=month,
            tech=tech,
            worked_days=int(v["days"]),
            gross_hours=v["gross"],
            weekend_hours=v["weekend"],
            go_live_weekend_hours=v["golive"],
        ))
    # Sort: month, then descending gross hours
    out.sort(key=lambda s: (s.month, -s.gross_hours))
    return out


def build_review_flags(
    rows: List[NeuronHoursRow],
    long_amber: float = LONG_SHIFT_AMBER,
    long_red: float = LONG_SHIFT_RED,
) -> List[ReviewFlag]:
    flags: List[ReviewFlag] = []
    for r in rows:
        issues: List[Tuple[str, str]] = []  # (severity, issue_type)

        if r.go_live_weekend:
            issues.append(("PURPLE", "Go Live Weekend"))
        if r.gross_hours >= long_red:
            issues.append(("RED", "Long Shift"))
        elif r.gross_hours >= long_amber:
            issues.append(("AMBER", "Long Shift"))
        if _is_overnight(r.clock_in, r.clock_out):
            issues.append(("AMBER", "Overnight"))
        if r.weekend and not r.go_live_weekend:
            issues.append(("AMBER", "Weekend Work"))
        if r.note:
            issues.append(("BLUE", "Note Present"))

        for severity, issue_type in issues:
            flags.append(ReviewFlag(
                severity=severity,
                issue_type=issue_type,
                month=r.month,
                date=r.date,
                day=r.day,
                tech=r.tech,
                project=r.project,
                clock_in=r.clock_in,
                clock_out=r.clock_out,
                gross_hours=r.gross_hours,
                note=r.note,
            ))
    flags.sort(key=lambda f: (_severity_rank(f.severity), f.date or date.min, f.tech))
    return flags


def rich_guard_review(
    tech: str,
    when: Optional[date],
    roster_hours: float,
    admin_hours: float,
    month: str = "",
) -> Optional[ReviewFlag]:
    """Preserve a confirmed admin full/long day; never downgrade it.

    When admin documents a full day (>= 8h) and the roster under-reports
    (roster < admin), emit a PURPLE protected review row so the admin value
    is not silently lost. Returns None when no protection is needed.
    """
    if admin_hours is None or roster_hours is None:
        return None
    if admin_hours >= 8.0 and roster_hours < admin_hours:
        return ReviewFlag(
            severity="PURPLE",
            issue_type="Rich Guard - Preserve Admin Full Day",
            month=month,
            date=when,
            day=when.strftime("%a") if when else "",
            tech=tech,
            project="Neuron Deployments",
            clock_in="",
            clock_out="",
            gross_hours=admin_hours,
            note=(
                f"Admin documents {admin_hours:g}h; roster shows {roster_hours:g}h. "
                "Preserve admin full day for review; do not downgrade."
            ),
            review_result="Pending",
        )
    return None


def flag_missing_roster(
    expected_techs: Iterable[str],
    present_techs: Iterable[str],
    pinned_techs: Optional[Iterable[str]] = None,
    month: str = "",
) -> List[ReviewFlag]:
    """Flag expected techs absent from roster, EXCEPT pinned techs.

    Pinned names are known/approved absences (PTO, off-project, leadership)
    and must not become RED 'missing roster' failures.
    """
    present = {t.strip().lower() for t in present_techs}
    pinned = {t.strip().lower() for t in (pinned_techs or [])}
    flags: List[ReviewFlag] = []
    for tech in expected_techs:
        key = tech.strip().lower()
        if key in present:
            continue
        if key in pinned:
            continue
        flags.append(ReviewFlag(
            severity="RED",
            issue_type="Missing Roster Evidence",
            month=month,
            date=None,
            day="",
            tech=tech,
            project="Neuron Deployments",
            clock_in="",
            clock_out="",
            gross_hours=0.0,
            note="Expected Neuron tech has no roster punches and is not pinned.",
        ))
    return flags


def _is_overnight(clock_in: str, clock_out: str) -> bool:
    ci = _hhmm(clock_in)
    co = _hhmm(clock_out)
    if ci is None or co is None:
        return False
    return co < ci


def _hhmm(label: str) -> Optional[float]:
    import re
    if not label:
        return None
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", label.strip(), re.IGNORECASE)
    if not m:
        return None
    h = int(m.group(1))
    mi = int(m.group(2))
    ap = (m.group(3) or "").upper()
    if ap == "PM" and h != 12:
        h += 12
    elif ap == "AM" and h == 12:
        h = 0
    return h + mi / 60.0


def _severity_rank(sev: str) -> int:
    order = {"RED": 0, "AMBER": 1, "PURPLE": 2, "BLUE": 3, "GREEN": 4, "GRAY": 5}
    return order.get(sev.upper(), 9)
