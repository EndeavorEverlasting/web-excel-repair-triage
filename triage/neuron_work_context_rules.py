"""Rule-based Neuron work-context classification.

These rules preserve the operational memory behind Neuron Track Hours artifacts so
future generators do not flatten every included Neuron shift into a generic label.
The classifier is intentionally deterministic and explainable: it uses explicit
text signals first, then month/day/time rules.

Submission workbooks should receive the resulting assignment/task label only.
Rule explanations and uncertainty belong in internal audit sidecars, not in the
Bonita-style tracker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

CONFIGURATIONS = "Configurations"
INVENTORY_MANAGEMENT = "Inventory Management"
LOGISTICS = "Logistics"
DEPLOYMENTS = "Deployments"
TICKET_FORWARDING = "Ticket Forwarding"
CLIENT_COORDINATION = "Client Coordination"
DOCUMENTATION = "Documentation"
TROUBLESHOOTING = "Troubleshooting / Incident Response"

TASK_CATEGORIES = (
    CONFIGURATIONS,
    INVENTORY_MANAGEMENT,
    LOGISTICS,
    DEPLOYMENTS,
    TICKET_FORWARDING,
    CLIENT_COORDINATION,
    DOCUMENTATION,
    TROUBLESHOOTING,
)

# Explicit text beats heuristic time-of-day rules.
_SIGNAL_PATTERNS = (
    (TROUBLESHOOTING, re.compile(r"troubleshoot|incident|issue|fix|repair|imprivata|login|escalat", re.I)),
    (DOCUMENTATION, re.compile(r"document|report|sign[-\s]?off|handoff|summary|qc", re.I)),
    (CLIENT_COORDINATION, re.compile(r"client|coordination|coordinate|meeting|email|call|status|update", re.I)),
    (TICKET_FORWARDING, re.compile(r"ticket|ritm|req\d*|request|forward|routing|queue", re.I)),
    (DEPLOYMENTS, re.compile(r"deploy|deployment|install|go[-\s]?live|onsite|on[-\s]?site", re.I)),
    (INVENTORY_MANAGEMENT, re.compile(r"inventory|stock|recon|asset|serial|count|staging|kit|shortage", re.I)),
    (LOGISTICS, re.compile(r"logistics|deliver|delivery|transport|shipment|ship|pickup|drop[-\s]?off|cleanup|clean[-\s]?up|relay", re.I)),
    (CONFIGURATIONS, re.compile(r"config|configuration|configure|image|baseline|autolog|auto[-\s]?log", re.I)),
)

EVENING_START_HOUR = 16.0
DAYTIME_LOGISTICS_START = 7.0
DAYTIME_LOGISTICS_END = 17.5

# May coordination / ticket-forwarding became a named lead/coordinator lane.
# Everyone else should fall back to a safer operational lane and appear in the
# resolver review sidecar through the low-confidence decision rule.
_MAY_COORDINATION_NAMES = {
    "khadejah harrison",
    "alejandro perales",
    "rich perez",
    "richard perez",
}
_APRIL_COORDINATION_EXTRA_NAMES = {
    "geoff gerber",
}


@dataclass(frozen=True)
class WorkContextDecision:
    """Work-context decision returned by the classifier."""

    assignment_type: str
    rule: str
    confidence: str = "medium"


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip().lower())


def can_use_coordination_lane(work_date: date, tech_name: str, assignment_type: str) -> bool:
    """Return True when *tech_name* may receive a coordination/ticket lane.

    Final submitted-artifact rule:
    - In May, only Khadejah Harrison, Alejandro Perales, and Rich/Richard Perez
      may receive Client Coordination or Ticket Forwarding.
    - In April, Geoff Gerber may receive Client Coordination because he carried
      that lane before being pulled to another project in May.
    - April Ticket Forwarding is not restricted by this helper.
    """

    name = _normalize_name(tech_name)
    if assignment_type == TICKET_FORWARDING and work_date.month == 5:
        return name in _MAY_COORDINATION_NAMES
    if assignment_type == CLIENT_COORDINATION:
        if work_date.month == 5:
            return name in _MAY_COORDINATION_NAMES
        if work_date.month == 4:
            return name in _MAY_COORDINATION_NAMES or name in _APRIL_COORDINATION_EXTRA_NAMES
    return True


def _restricted_coordination_fallback(
    work_date: date,
    tech_name: str,
    assignment_type: str,
    rule: str,
) -> Optional[WorkContextDecision]:
    if can_use_coordination_lane(work_date, tech_name, assignment_type):
        return None
    safe = INVENTORY_MANAGEMENT if assignment_type == TICKET_FORWARDING else CONFIGURATIONS
    return WorkContextDecision(
        safe,
        f"restricted-{assignment_type.lower().replace(' ', '-')}-fallback:{rule}",
        "low",
    )


def _normalize_hour(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    value = float(value)
    while value < 0:
        value += 24.0
    while value >= 24.0:
        value -= 24.0
    return value


def _duration(start_hour: Optional[float], end_hour: Optional[float]) -> float:
    if start_hour is None or end_hour is None:
        return 0.0
    start = float(start_hour)
    end = float(end_hour)
    diff = end - start
    if diff < 0:
        diff += 24.0
    return diff


def _midpoint(start_hour: Optional[float], end_hour: Optional[float]) -> Optional[float]:
    if start_hour is None or end_hour is None:
        return None
    span = _duration(start_hour, end_hour)
    return _normalize_hour(float(start_hour) + span / 2.0)


def overlaps_evening(start_hour: Optional[float], end_hour: Optional[float]) -> bool:
    """Return True when a shift overlaps the evening configuration window."""

    if start_hour is None or end_hour is None:
        return False
    start = float(start_hour)
    end = float(end_hour)
    if end < start:  # overnight always contains post-day work.
        return True
    return end >= EVENING_START_HOUR or start >= EVENING_START_HOUR


def is_daytime_logistics_window(start_hour: Optional[float], end_hour: Optional[float]) -> bool:
    """Logistics is daytime material movement / cleanup only."""

    if start_hour is None or end_hour is None:
        return False
    start = float(start_hour)
    end = float(end_hour)
    if end < start:
        return False
    return DAYTIME_LOGISTICS_START <= start and end <= DAYTIME_LOGISTICS_END


def _explicit_signal(text: str) -> Optional[str]:
    for assignment_type, pattern in _SIGNAL_PATTERNS:
        if pattern.search(text):
            return assignment_type
    return None


def _decision_with_person_gate(
    work_date: date,
    tech_name: str,
    assignment_type: str,
    rule: str,
    confidence: str = "medium",
) -> WorkContextDecision:
    blocked = _restricted_coordination_fallback(work_date, tech_name, assignment_type, rule)
    if blocked is not None:
        return blocked
    return WorkContextDecision(assignment_type, rule, confidence)


def classify_neuron_work_context(
    work_date: date,
    start_hour: Optional[float],
    end_hour: Optional[float],
    notes: str = "",
    worked_label: str = "",
    resolved_project: str = "",
    tech_name: str = "",
) -> WorkContextDecision:
    """Classify a Neuron shift into a realistic task lane.

    Precedence:
    1. Explicit text signals from notes/worked label/resolved project.
    2. Logistics is allowed only during daytime material movement / cleanup.
    3. April deployment-heavy evening/weekend rules.
    4. May configuration/inventory-heavy weekend/evening rules.
    5. Time-of-day fallback with configurations as the dominant default.

    Person restrictions:
    - May Client Coordination and Ticket Forwarding are lead/coordinator lanes
      restricted to Khadejah Harrison, Alejandro Perales, and Rich/Richard Perez.
    - April Client Coordination also allows Geoff Gerber.
    """

    text = " ".join(x for x in (notes, worked_label, resolved_project) if x).strip()
    explicit = _explicit_signal(text)

    if explicit == LOGISTICS:
        if is_daytime_logistics_window(start_hour, end_hour):
            return WorkContextDecision(LOGISTICS, "explicit-logistics-daytime", "high")
        return WorkContextDecision(CONFIGURATIONS, "logistics-signal-outside-daytime-config-fallback", "medium")

    if explicit and explicit != DEPLOYMENTS:
        return _decision_with_person_gate(
            work_date,
            tech_name,
            explicit,
            f"explicit-{explicit.lower().replace(' ', '-')}",
            "high",
        )

    month = work_date.month
    weekday = work_date.weekday()  # Mon=0, Sat=5
    evening = overlaps_evening(start_hour, end_hour)
    mid = _midpoint(start_hour, end_hour)
    span = _duration(start_hour, end_hour)

    if explicit == DEPLOYMENTS:
        return WorkContextDecision(DEPLOYMENTS, "explicit-deployment", "high")

    if month == 4:
        if weekday == 5:  # April Saturdays.
            return WorkContextDecision(DEPLOYMENTS, "april-saturday-deployment", "high")
        if weekday >= 5:
            return WorkContextDecision(DEPLOYMENTS, "april-weekend-deployment", "medium")
        if weekday in (0, 2) and evening:  # April Monday/Wednesday evening windows.
            return WorkContextDecision(DEPLOYMENTS, "april-mon-wed-evening-deployment", "medium")
        if evening:
            return WorkContextDecision(DEPLOYMENTS, "april-evening-deployment-dominant", "medium")

    if month == 5:
        if weekday >= 5:
            if mid is not None and mid < 14.0:
                return WorkContextDecision(INVENTORY_MANAGEMENT, "may-weekend-inventory", "medium")
            return WorkContextDecision(CONFIGURATIONS, "may-weekend-configuration", "medium")
        if evening:
            return WorkContextDecision(CONFIGURATIONS, "may-evening-configuration", "high")

    # A full weekday shift usually includes configuration work and should not be
    # reduced to logistics or a narrow admin activity without explicit evidence.
    if span >= 7.0 and evening:
        return WorkContextDecision(CONFIGURATIONS, "full-shift-overlaps-configuration-window", "medium")

    if mid is not None:
        if mid < 10.0:
            return _decision_with_person_gate(
                work_date,
                tech_name,
                TICKET_FORWARDING,
                "morning-ticket-forwarding",
                "medium",
            )
        if mid < 14.0:
            return WorkContextDecision(INVENTORY_MANAGEMENT, "daytime-inventory-management", "medium")
        if mid < EVENING_START_HOUR:
            return _decision_with_person_gate(
                work_date,
                tech_name,
                CLIENT_COORDINATION,
                "afternoon-client-coordination",
                "medium",
            )

    return WorkContextDecision(CONFIGURATIONS, "default-configuration-dominant", "low")
