"""Payable-hours correction rules for roster/payroll reconciliation.

The roster punch cells are operational attendance evidence. When a day was entered
with standard hours even though payroll evidence shows overtime, the smoothest
pipeline correction is a roster-side payable-hours correction row.

Corrections are intentionally keyed by staff/date and can be stored in a private
workbook tab or private CSV. The public repo stores the schema and behavior, not
private evidence rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Mapping, Optional

CorrectionMode = Literal["set_payable_hours", "add_payable_hours"]
CorrectionScope = Literal["payroll_delta", "billing", "both"]


@dataclass(frozen=True)
class PayableHoursCorrection:
    """A reviewed correction to roster-derived payable hours."""

    work_date: date
    staff_name: str
    mode: CorrectionMode
    hours: float
    reason: str
    evidence_source: str = ""
    evidence_hours: Optional[float] = None
    scope: CorrectionScope = "payroll_delta"
    project_name: str = ""

    @property
    def key(self) -> tuple[date, str]:
        return (self.work_date, normalize_staff_name(self.staff_name))


def normalize_staff_name(value: object) -> str:
    return " ".join(str(value or "").strip().lower().replace(",", " ").split())


def normalize_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Cannot normalize correction date: {value!r}")


def parse_correction_row(row: Mapping[str, object]) -> PayableHoursCorrection:
    """Parse a private correction row from a workbook/CSV-like mapping.

    Accepted column names are intentionally boring so admins can maintain the tab.
    """
    normalized = {str(k).strip().lower().replace(" ", "_"): v for k, v in row.items()}
    mode = str(normalized.get("mode") or normalized.get("correction_mode") or "set_payable_hours").strip()
    if mode not in {"set_payable_hours", "add_payable_hours"}:
        raise ValueError(f"Unsupported payable-hours correction mode: {mode!r}")

    raw_hours = normalized.get("hours")
    if raw_hours in (None, ""):
        raw_hours = normalized.get("payable_hours")
    if raw_hours in (None, ""):
        raw_hours = normalized.get("payable_hours_target")
    if raw_hours in (None, ""):
        raise ValueError("Payable-hours correction row is missing hours/payable_hours_target")

    scope = str(normalized.get("scope") or "payroll_delta").strip().lower()
    if scope not in {"payroll_delta", "billing", "both"}:
        raise ValueError(f"Unsupported payable-hours correction scope: {scope!r}")

    evidence_hours = normalized.get("evidence_hours")
    return PayableHoursCorrection(
        work_date=normalize_date(normalized.get("date") or normalized.get("work_date")),
        staff_name=str(normalized.get("staff_name") or normalized.get("tech_name") or "").strip(),
        mode=mode,  # type: ignore[arg-type]
        hours=float(raw_hours),
        reason=str(normalized.get("reason") or normalized.get("notes") or "").strip(),
        evidence_source=str(normalized.get("evidence_source") or "").strip(),
        evidence_hours=float(evidence_hours) if evidence_hours not in (None, "") else None,
        scope=scope,  # type: ignore[arg-type]
        project_name=str(normalized.get("project_name") or "").strip(),
    )


def apply_payable_hours_correction(
    roster_payable_hours: float,
    correction: PayableHoursCorrection | None,
    *,
    scope: CorrectionScope = "payroll_delta",
) -> float:
    """Return corrected payable hours for a staff/date row.

    `set_payable_hours` is preferred because it is idempotent. `add_payable_hours`
    is supported for quick field correction but can double-count if base roster
    hours are later corrected without removing the additive row.
    """
    base = float(roster_payable_hours or 0.0)
    if correction is None:
        return base
    if correction.scope not in {scope, "both"}:
        return base
    if correction.mode == "set_payable_hours":
        return round(float(correction.hours), 4)
    if correction.mode == "add_payable_hours":
        return round(base + float(correction.hours), 4)
    raise ValueError(f"Unsupported correction mode: {correction.mode!r}")
