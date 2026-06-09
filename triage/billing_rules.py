"""Reusable billing-hour rules for roster-derived artifacts.

These rules are deliberately boring. Boring rules survive month-end.

The Active Roster Log controls client-billable work. Payroll systems such as
Paylocity are variance evidence only; they do not create Northwell billable
hours without roster-backed work.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BillingStatus(str, Enum):
    BILLABLE = "billable"
    REVIEW = "review"
    HOLIDAY_NON_BILLABLE = "holiday_non_billable"
    UNCLASSIFIED_REVIEW = "unclassified_review"
    PARTIAL = "partial"
    LONG_SHIFT_REVIEW = "long_shift_review"


@dataclass(frozen=True)
class BillingDecision:
    gross_hours: float
    lunch_deduction: float
    net_hours: float
    status: BillingStatus
    explanation: str


def lunch_deduction(gross_hours: float) -> float:
    """Return unpaid lunch deduction for a roster gross shift span.

    Policy:
    - gross >= 8.0 hours: deduct 1.0 hour
    - gross >= 6.0 and < 8.0 hours: deduct 0.5 hour
    - gross < 6.0 hours: deduct 0.0 hours
    """
    gross = max(float(gross_hours or 0.0), 0.0)
    if gross >= 8.0:
        return 1.0
    if gross >= 6.0:
        return 0.5
    return 0.0


def net_billable_hours(gross_hours: float) -> float:
    """Gross roster span minus rule-based lunch deduction."""
    gross = max(float(gross_hours or 0.0), 0.0)
    return round(max(0.0, gross - lunch_deduction(gross)), 4)


def classify_billing_row(
    *,
    gross_hours: float,
    project: Optional[str],
    is_holiday: bool = False,
    has_roster_work: bool = True,
    long_shift_threshold: float = 12.0,
) -> BillingDecision:
    """Classify one roster/payroll row for billing submission.

    This is intentionally simple and explicit so PM-facing artifacts can explain
    themselves without rediscovering the rules.
    """
    gross = max(float(gross_hours or 0.0), 0.0)
    lunch = lunch_deduction(gross)
    net = net_billable_hours(gross)
    project_text = (project or "").strip()

    if is_holiday and not has_roster_work:
        return BillingDecision(
            gross_hours=gross,
            lunch_deduction=0.0,
            net_hours=0.0,
            status=BillingStatus.HOLIDAY_NON_BILLABLE,
            explanation="Paid holiday / company payroll item; excluded unless roster work exists.",
        )

    if not project_text or project_text.lower() in {"unassigned", "unassigned / review"}:
        return BillingDecision(
            gross_hours=gross,
            lunch_deduction=lunch,
            net_hours=net,
            status=BillingStatus.UNCLASSIFIED_REVIEW,
            explanation="Roster has hours but no resolved project; hold for classification review.",
        )

    if gross > long_shift_threshold:
        return BillingDecision(
            gross_hours=gross,
            lunch_deduction=lunch,
            net_hours=net,
            status=BillingStatus.LONG_SHIFT_REVIEW,
            explanation="Long shift; keep actual hours but flag for review.",
        )

    if 0 < gross < 8.0:
        return BillingDecision(
            gross_hours=gross,
            lunch_deduction=lunch,
            net_hours=net,
            status=BillingStatus.PARTIAL,
            explanation="Partial shift; bill actual net hours after rule-based lunch.",
        )

    return BillingDecision(
        gross_hours=gross,
        lunch_deduction=lunch,
        net_hours=net,
        status=BillingStatus.BILLABLE,
        explanation="Roster-backed billable work.",
    )
