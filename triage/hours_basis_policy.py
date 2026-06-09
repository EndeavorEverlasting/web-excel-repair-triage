"""Canonical hours-basis policy for roster-derived artifacts.

This module is intentionally small and boring. It exists so artifact generators,
preflight checks, and tests do not rediscover the same rule differently.

Policy:
    * Billing artifacts use NET hours.
    * Delta dashboards compare roster/admin NET hours to Paylocity-derived paid hours.
    * Operational tracking artifacts, including Neuron Track Hours, use GROSS hours.

Lunch deduction policy for roster-derived NET hours:
    * gross >= 8.0 hours -> deduct 1.0 hour
    * gross >= 6.0 hours -> deduct 0.5 hour
    * gross < 6.0 hours  -> deduct 0.0 hours
"""
from __future__ import annotations

from typing import Final

HOURS_BASIS_GROSS: Final[str] = "gross"
HOURS_BASIS_NET: Final[str] = "net"

LUNCH_DEDUCTION_FULL_DAY_THRESHOLD: Final[float] = 8.0
LUNCH_DEDUCTION_PARTIAL_DAY_THRESHOLD: Final[float] = 6.0
LUNCH_DEDUCTION_FULL_DAY_HOURS: Final[float] = 1.0
LUNCH_DEDUCTION_PARTIAL_DAY_HOURS: Final[float] = 0.5

BILLING_ARTIFACTS: Final[set[str]] = {
    "admin_billing_summary",
    "billing_summary",
    "april_may_billing_summary",
    "delta_dashboard",
    "payroll_delta_dashboard",
}

OPERATIONAL_TRACKING_ARTIFACTS: Final[set[str]] = {
    "neuron_track_hours",
    "bonita_neuron_track_hours",
    "tech_activity_tracker",
}

ARTIFACT_HOURS_BASIS: Final[dict[str, str]] = {
    **{name: HOURS_BASIS_NET for name in BILLING_ARTIFACTS},
    **{name: HOURS_BASIS_GROSS for name in OPERATIONAL_TRACKING_ARTIFACTS},
}


def lunch_deduction(gross_hours: float) -> float:
    """Return the roster lunch deduction for a gross shift span."""
    gross = float(gross_hours or 0.0)
    if gross >= LUNCH_DEDUCTION_FULL_DAY_THRESHOLD:
        return LUNCH_DEDUCTION_FULL_DAY_HOURS
    if gross >= LUNCH_DEDUCTION_PARTIAL_DAY_THRESHOLD:
        return LUNCH_DEDUCTION_PARTIAL_DAY_HOURS
    return 0.0


def net_hours_from_gross(gross_hours: float) -> float:
    """Return billing net hours from a gross roster span."""
    gross = float(gross_hours or 0.0)
    return round(max(0.0, gross - lunch_deduction(gross)), 4)


def hours_basis_for(artifact_name: str) -> str:
    """Return the canonical hours basis for a known artifact family."""
    key = str(artifact_name or "").strip().lower().replace(" ", "_").replace("-", "_")
    try:
        return ARTIFACT_HOURS_BASIS[key]
    except KeyError as exc:
        raise KeyError(f"unknown artifact hours basis: {artifact_name!r}") from exc
