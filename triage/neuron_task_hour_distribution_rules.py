"""Neuron task-hour distribution rules.

The Active Roster Log can prove who worked, when they worked, and whether the
work was in Neuron scope. It cannot always preserve the exact intra-day task
context. These rules split roster-backed Neuron hours into declared task lanes
when the day lacks event-level detail.

This module intentionally avoids hardcoding private tech names in the public
repo. Private workbooks or local config may pass role/cohort labels such as
``may_deployment_field_team`` for specific rows.
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

# Canonical support-day split supplied by operations. Percent values total 100.
GENERAL_NEURON_SUPPORT_DAY: Dict[str, float] = {
    CONFIGURATIONS: 55.0,
    DEPLOYMENTS: 5.0,
    LOGISTICS: 20.0,
    INVENTORY_MANAGEMENT: 10.0,
    DOCUMENTATION: 5.0,
    CLIENT_COORDINATION: 5.0,
}

DEPLOYMENT_PLUS_DOCUMENTATION_DAY: Dict[str, float] = {
    DEPLOYMENTS: 80.0,
    DOCUMENTATION: 20.0,
}

# May field team on confirmed deployment/logistics days.
MAY_DEPLOYMENT_FIELD_TEAM_DAY: Dict[str, float] = {
    LOGISTICS: 30.0,
    DEPLOYMENTS: 50.0,
    DOCUMENTATION: 20.0,
}

SUNDAY_LOGISTICS_DAY: Dict[str, float] = {
    LOGISTICS: 100.0,
}

APRIL_EVENING_CONFIGURATION_DAY: Dict[str, float] = {
    CONFIGURATIONS: 100.0,
}


def _normalize_subset(base: Mapping[str, float], keep: Iterable[str]) -> Dict[str, float]:
    """Normalize selected lanes from a larger distribution to total 100."""
    keys = list(keep)
    total = sum(float(base.get(k, 0.0)) for k in keys)
    if total <= 0:
        raise ValueError("Cannot normalize an empty Neuron task distribution")
    return {k: round(float(base.get(k, 0.0)) / total * 100.0, 4) for k in keys}


# May weekends/evenings were configurations + inventory. The split is inherited
# from the configured support-day balance restricted to those lanes.
MAY_CONFIGURATION_AND_INVENTORY_DAY: Dict[str, float] = _normalize_subset(
    GENERAL_NEURON_SUPPORT_DAY,
    [CONFIGURATIONS, INVENTORY_MANAGEMENT],
)

# May daytime support excludes deployments/documentation unless explicit evidence
# or a private cohort override says otherwise.
MAY_DAYTIME_SUPPORT_DAY: Dict[str, float] = _normalize_subset(
    GENERAL_NEURON_SUPPORT_DAY,
    [CONFIGURATIONS, LOGISTICS, INVENTORY_MANAGEMENT, CLIENT_COORDINATION],
)

DISTRIBUTION_ALIASES: Dict[str, Dict[str, float]] = {
    "general_neuron_support_day": GENERAL_NEURON_SUPPORT_DAY,
    "standard_neuron_support_day": GENERAL_NEURON_SUPPORT_DAY,
    "april_deployment_day": DEPLOYMENT_PLUS_DOCUMENTATION_DAY,
    "deployment_plus_documentation_day": DEPLOYMENT_PLUS_DOCUMENTATION_DAY,
    "may_deployment_field_team": MAY_DEPLOYMENT_FIELD_TEAM_DAY,
    "delivery_became_deployment": MAY_DEPLOYMENT_FIELD_TEAM_DAY,
    "may_delivery_became_deployment": MAY_DEPLOYMENT_FIELD_TEAM_DAY,
    "sunday_logistics_day": SUNDAY_LOGISTICS_DAY,
    "april_sunday_logistics_day": SUNDAY_LOGISTICS_DAY,
    "april_evening_configuration_day": APRIL_EVENING_CONFIGURATION_DAY,
    "may_configuration_and_inventory_day": MAY_CONFIGURATION_AND_INVENTORY_DAY,
    "may_weekend_configuration_and_inventory_day": MAY_CONFIGURATION_AND_INVENTORY_DAY,
    "may_daytime_support_day": MAY_DAYTIME_SUPPORT_DAY,
}


@dataclass(frozen=True)
class TaskHourDistributionDecision:
    """Task-hour distribution selected for one roster-backed Neuron shift."""

    distribution_name: str
    weights: Dict[str, float]
    rule: str
    private_override_used: bool = False


def validate_distribution(weights: Mapping[str, float]) -> None:
    """Raise ValueError if a task-hour distribution is malformed."""
    total = round(sum(float(v) for v in weights.values()), 4)
    if total != 100.0:
        raise ValueError(f"Neuron task-hour distribution must total 100.0, got {total}")
    for task, pct in weights.items():
        if not task or float(pct) < 0:
            raise ValueError(f"Invalid Neuron task-hour distribution entry: {task!r}={pct!r}")


def distribution_for_alias(alias: str) -> Dict[str, float]:
    """Return a named task-hour distribution by alias."""
    key = (alias or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key not in DISTRIBUTION_ALIASES:
        raise KeyError(f"Unknown Neuron task-hour distribution alias: {alias!r}")
    return dict(DISTRIBUTION_ALIASES[key])


def choose_neuron_task_hour_distribution(
    work_date: date,
    *,
    start_hour: Optional[float] = None,
    end_hour: Optional[float] = None,
    private_day_role_override: Optional[str] = None,
) -> TaskHourDistributionDecision:
    """Choose the distribution for a roster-backed Neuron shift.

    Rules are not tech-name based. If a specific date has a deployment field
    team, the private workbook/local config should pass a role label such as
    ``may_deployment_field_team`` for those rows only.
    """

    if private_day_role_override:
        key = private_day_role_override.strip().lower().replace(" ", "_").replace("-", "_")
        return TaskHourDistributionDecision(
            distribution_name=key,
            weights=distribution_for_alias(key),
            rule="private-day-role-override",
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
            return TaskHourDistributionDecision(
                "april_saturday_deployment_day",
                dict(DEPLOYMENT_PLUS_DOCUMENTATION_DAY),
                "april-saturday-deployment",
            )
        if weekday == 6:
            return TaskHourDistributionDecision(
                "april_sunday_logistics_day",
                dict(SUNDAY_LOGISTICS_DAY),
                "april-sunday-logistics",
            )
        if overlaps_evening:
            return TaskHourDistributionDecision(
                "april_evening_configuration_day",
                dict(APRIL_EVENING_CONFIGURATION_DAY),
                "april-evening-configuration",
            )
        if weekday in (0, 2):
            return TaskHourDistributionDecision(
                "april_monday_wednesday_deployment_day",
                dict(DEPLOYMENT_PLUS_DOCUMENTATION_DAY),
                "april-monday-wednesday-deployment",
            )
        if start is not None and start >= 14.0:
            return TaskHourDistributionDecision(
                "april_weekday_after_2pm_deployment_day",
                dict(DEPLOYMENT_PLUS_DOCUMENTATION_DAY),
                "april-weekday-after-2pm-deployment",
            )
        return TaskHourDistributionDecision(
            "general_neuron_support_day",
            dict(GENERAL_NEURON_SUPPORT_DAY),
            "april-general-support",
        )

    if month == 5:
        if weekday >= 5 or overlaps_evening:
            return TaskHourDistributionDecision(
                "may_configuration_and_inventory_day",
                dict(MAY_CONFIGURATION_AND_INVENTORY_DAY),
                "may-weekend-or-evening-configuration-inventory",
            )
        return TaskHourDistributionDecision(
            "may_daytime_support_day",
            dict(MAY_DAYTIME_SUPPORT_DAY),
            "may-daytime-support",
        )

    return TaskHourDistributionDecision(
        "general_neuron_support_day",
        dict(GENERAL_NEURON_SUPPORT_DAY),
        "default-general-support",
    )


def distribute_task_hours(total_hours: float, weights: Mapping[str, float]) -> Dict[str, float]:
    """Split total hours by a validated task-hour distribution."""
    validate_distribution(weights)
    hours = max(float(total_hours or 0.0), 0.0)
    return {task: round(hours * float(pct) / 100.0, 4) for task, pct in weights.items() if pct}
