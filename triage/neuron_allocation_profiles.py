"""Declared Neuron task allocation profiles.

The roster can prove who worked, when they worked, and whether the work was in
Neuron scope. It cannot always preserve the exact intra-day task context. This
module converts thin-context Neuron roster hours into declared, repeatable task
allocations without hardcoding private tech names in the public repo.

Private artifacts may supply date/person cohort overrides such as
``may_deployment_cohort``. The repo stores the rule, not the names.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Mapping, Optional

CONFIGURATIONS = "Configurations"
DEPLOYMENTS = "Deployments"
LOGISTICS = "Logistics"
INVENTORY_MANAGEMENT = "Inventory Management"
DOCUMENTATION = "Documentation"
CLIENT_COORDINATION = "Client Coordination"
TICKET_FORWARDING = "Ticket Forwarding"
INCIDENT_RESPONSE = "Troubleshooting / Incident Response"
WAREHOUSE_MAINTENANCE = "Warehouse Maintenance"
SURVEY = "Survey"

# Canonical distribution supplied by operations. Percent values must total 100.
GENERAL_SUPPORT_PROFILE: Dict[str, float] = {
    CONFIGURATIONS: 55.0,
    DEPLOYMENTS: 5.0,
    LOGISTICS: 20.0,
    INVENTORY_MANAGEMENT: 10.0,
    DOCUMENTATION: 5.0,
    CLIENT_COORDINATION: 5.0,
}

# Deployment days outside May logistics-heavy deployment support.
DEPLOYMENT_WITH_DOCUMENTATION_PROFILE: Dict[str, float] = {
    DEPLOYMENTS: 80.0,
    DOCUMENTATION: 20.0,
}

# May deployment cohort: techs doing the deployment/logistics field work.
MAY_DEPLOYMENT_LOGISTICS_PROFILE: Dict[str, float] = {
    LOGISTICS: 30.0,
    DEPLOYMENTS: 50.0,
    DOCUMENTATION: 20.0,
}

SUNDAY_LOGISTICS_PROFILE: Dict[str, float] = {
    LOGISTICS: 100.0,
}

APRIL_EVENING_CONFIGURATION_PROFILE: Dict[str, float] = {
    CONFIGURATIONS: 100.0,
}

# May weekend and evening work was configurations + inventory. The exact split
# was not separately specified, so derive it from the declared general profile
# restricted to those two lanes: 55 config / (55 + 10), 10 inventory / (55 + 10).
def _normalize_subset(base: Mapping[str, float], keep: Iterable[str]) -> Dict[str, float]:
    keys = list(keep)
    total = sum(float(base.get(k, 0.0)) for k in keys)
    if total <= 0:
        raise ValueError("Cannot normalize an empty allocation subset")
    return {k: round(float(base.get(k, 0.0)) / total * 100.0, 4) for k in keys}


MAY_CONFIG_INVENTORY_PROFILE: Dict[str, float] = _normalize_subset(
    GENERAL_SUPPORT_PROFILE,
    [CONFIGURATIONS, INVENTORY_MANAGEMENT],
)

# May daytime support excludes deployment/documentation unless explicit evidence
# or a private cohort override says otherwise. Ticket forwarding stays explicit
# until a fixed default percentage is supplied.
MAY_DAYTIME_SUPPORT_PROFILE: Dict[str, float] = _normalize_subset(
    GENERAL_SUPPORT_PROFILE,
    [CONFIGURATIONS, LOGISTICS, INVENTORY_MANAGEMENT, CLIENT_COORDINATION],
)

PROFILE_ALIASES: Dict[str, Dict[str, float]] = {
    "general_support": GENERAL_SUPPORT_PROFILE,
    "standard_support": GENERAL_SUPPORT_PROFILE,
    "april_deployment": DEPLOYMENT_WITH_DOCUMENTATION_PROFILE,
    "deployment_with_documentation": DEPLOYMENT_WITH_DOCUMENTATION_PROFILE,
    "may_deployment_cohort": MAY_DEPLOYMENT_LOGISTICS_PROFILE,
    "delivery_turned_deployment": MAY_DEPLOYMENT_LOGISTICS_PROFILE,
    "may_delivery_turned_deployment": MAY_DEPLOYMENT_LOGISTICS_PROFILE,
    "sunday_logistics": SUNDAY_LOGISTICS_PROFILE,
    "april_sunday_logistics": SUNDAY_LOGISTICS_PROFILE,
    "april_evening_configuration": APRIL_EVENING_CONFIGURATION_PROFILE,
    "may_config_inventory": MAY_CONFIG_INVENTORY_PROFILE,
    "may_weekend_config_inventory": MAY_CONFIG_INVENTORY_PROFILE,
    "may_daytime_support": MAY_DAYTIME_SUPPORT_PROFILE,
}

PRIVATE_COHORT_OVERRIDE_VALUES = frozenset({
    "may_deployment_cohort",
    "delivery_turned_deployment",
    "may_delivery_turned_deployment",
    "deployment_with_documentation",
    "standard_support",
    "general_support",
})


@dataclass(frozen=True)
class AllocationDecision:
    """Allocation profile selected for one roster-backed Neuron shift."""

    profile_name: str
    weights: Dict[str, float]
    rule: str
    private_override_used: bool = False


def validate_profile(weights: Mapping[str, float]) -> None:
    """Raise ValueError if a profile is malformed."""
    total = round(sum(float(v) for v in weights.values()), 4)
    if total != 100.0:
        raise ValueError(f"Allocation profile must total 100.0, got {total}")
    for task, pct in weights.items():
        if not task or float(pct) < 0:
            raise ValueError(f"Invalid allocation entry: {task!r}={pct!r}")


def profile_for_alias(alias: str) -> Dict[str, float]:
    """Return a named profile by override/profile alias."""
    key = (alias or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key not in PROFILE_ALIASES:
        raise KeyError(f"Unknown Neuron allocation profile alias: {alias!r}")
    return dict(PROFILE_ALIASES[key])


def choose_neuron_allocation_profile(
    work_date: date,
    *,
    start_hour: Optional[float] = None,
    end_hour: Optional[float] = None,
    private_cohort_override: Optional[str] = None,
) -> AllocationDecision:
    """Choose the allocation profile for a roster-backed Neuron shift.

    Rules are intentionally not tech-name based. If a specific date has a
    deployment cohort, the private workbook/override layer should pass a cohort
    label such as ``may_deployment_cohort`` for those rows only.
    """

    if private_cohort_override:
        key = private_cohort_override.strip().lower().replace(" ", "_").replace("-", "_")
        weights = profile_for_alias(key)
        return AllocationDecision(
            profile_name=key,
            weights=weights,
            rule="private-cohort-override",
            private_override_used=True,
        )

    weekday = work_date.weekday()  # Mon=0, Sat=5, Sun=6
    month = work_date.month
    start = float(start_hour) if start_hour is not None else None
    end = float(end_hour) if end_hour is not None else None
    overlaps_evening = False
    if start is not None and end is not None:
        overlaps_evening = end < start or end >= 17.0 or start >= 17.0
    elif start is not None:
        overlaps_evening = start >= 17.0

    if month == 4:
        if weekday == 5:
            return AllocationDecision(
                "april_saturday_deployment",
                dict(DEPLOYMENT_WITH_DOCUMENTATION_PROFILE),
                "april-saturday-deployment",
            )
        if weekday == 6:
            return AllocationDecision(
                "april_sunday_logistics",
                dict(SUNDAY_LOGISTICS_PROFILE),
                "april-sunday-logistics",
            )
        if overlaps_evening:
            return AllocationDecision(
                "april_evening_configuration",
                dict(APRIL_EVENING_CONFIGURATION_PROFILE),
                "april-evening-configuration",
            )
        if weekday in (0, 2):
            return AllocationDecision(
                "april_mon_wed_deployment",
                dict(DEPLOYMENT_WITH_DOCUMENTATION_PROFILE),
                "april-mon-wed-deployment",
            )
        if start is not None and start >= 14.0:
            return AllocationDecision(
                "april_weekday_after_2pm_deployment",
                dict(DEPLOYMENT_WITH_DOCUMENTATION_PROFILE),
                "april-weekday-after-2pm-deployment",
            )
        return AllocationDecision(
            "general_support",
            dict(GENERAL_SUPPORT_PROFILE),
            "april-general-support",
        )

    if month == 5:
        if weekday >= 5 or overlaps_evening:
            return AllocationDecision(
                "may_config_inventory",
                dict(MAY_CONFIG_INVENTORY_PROFILE),
                "may-weekend-or-evening-config-inventory",
            )
        return AllocationDecision(
            "may_daytime_support",
            dict(MAY_DAYTIME_SUPPORT_PROFILE),
            "may-daytime-support",
        )

    return AllocationDecision(
        "general_support",
        dict(GENERAL_SUPPORT_PROFILE),
        "default-general-support",
    )


def allocate_hours(total_hours: float, weights: Mapping[str, float]) -> Dict[str, float]:
    """Split total hours by a validated percentage profile."""
    validate_profile(weights)
    hours = max(float(total_hours or 0.0), 0.0)
    return {task: round(hours * float(pct) / 100.0, 4) for task, pct in weights.items() if pct}
