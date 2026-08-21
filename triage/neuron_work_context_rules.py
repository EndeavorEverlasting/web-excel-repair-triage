"""Rule-based Neuron work-context classification.

These rules preserve the operational memory behind Neuron Track Hours artifacts so
future generators do not flatten every included Neuron shift into
``Neuron Installation``. The classifier is intentionally deterministic and
explainable: it uses explicit text signals first, then month/day/time rules.

Submission workbooks should receive the resulting assignment/task label only.
Rule explanations and uncertainty belong in internal audit sidecars, not in the
Bonita-style tracker.

``Deployments`` is a high-risk person/date label. Generic project names, legacy
monthly buckets, deployment trackers, deployment planning/information, or broad
package-level mentions are not sufficient evidence for a shift-level deployment
classification. Outside explicitly registered historical month rules, deployment
requires direct execution language tied to the row evidence.
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

# Lower-risk explicit signals may be taken from row notes/worked label/project text.
# Deployment is deliberately absent and is handled by the stronger direct-execution
# gate below.
_SIGNAL_PATTERNS = (
    (TROUBLESHOOTING, re.compile(r"troubleshoot|incident|issue|fix|repair|imprivata|login|escalat", re.I)),
    (DOCUMENTATION, re.compile(r"document|report|sign[-\s]?off|handoff|summary|qc", re.I)),
    (CLIENT_COORDINATION, re.compile(r"client|coordination|coordinate|meeting|email|call|status|update", re.I)),
    (TICKET_FORWARDING, re.compile(r"ticket|ritm|req\d*|request|forward|routing|queue", re.I)),
    (INVENTORY_MANAGEMENT, re.compile(r"inventory|stock|recon|asset|serial|count|staging|kit|shortage", re.I)),
    (LOGISTICS, re.compile(r"logistics|deliver|delivery|transport|shipment|ship|pickup|drop[-\s]?off|cleanup|clean[-\s]?up|relay", re.I)),
    (CONFIGURATIONS, re.compile(r"config|configuration|configure|image|baseline|autolog|auto[-\s]?log", re.I)),
)

# Direct execution verbs are intentionally narrower than generic "deployment".
# The source row must say that deployment/install/go-live/cutover activity was
# actually performed. A resolved project name is never sufficient by itself.
_DIRECT_DEPLOYMENT_PATTERN = re.compile(
    r"\bdeploy(?:ed|ing)\b|\binstall(?:ed|ing)\b|\bgo[-\s]?live\b|\bcutover\b|\bon[-\s]?site\s+install(?:ation|ing|ed)?\b",
    re.I,
)

EVENING_START_HOUR = 16.0
DAYTIME_LOGISTICS_START = 7.0
DAYTIME_LOGISTICS_END = 17.5


@dataclass(frozen=True)
class WorkContextDecision:
    """Work-context decision returned by the classifier."""

    assignment_type: str
    rule: str
    confidence: str = "medium"


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


def _direct_deployment_signal(notes: str, worked_label: str) -> bool:
    """Return True only for row evidence that describes deployment execution.

    ``resolved_project`` is intentionally excluded: a project or program name that
    happens to contain "deployment" is context, not proof that this shift deployed.
    Bare nouns such as "deployment", "deployment tracker", "deployment support",
    and "deployment information" do not satisfy the direct-action expression.
    """

    evidence_text = " ".join(x for x in (notes, worked_label) if x).strip()
    return bool(_DIRECT_DEPLOYMENT_PATTERN.search(evidence_text))


def classify_neuron_work_context(
    work_date: date,
    start_hour: Optional[float],
    end_hour: Optional[float],
    notes: str = "",
    worked_label: str = "",
    resolved_project: str = "",
) -> WorkContextDecision:
    """Classify a Neuron shift into a realistic task lane.

    Precedence:
    1. Direct deployment execution evidence from row notes/worked label.
    2. Other explicit text signals from notes/worked label/resolved project.
    3. Logistics is allowed only during daytime material movement / cleanup.
    4. Explicitly registered April deployment windows.
    5. May weekend configuration/inventory behavior.
    6. Time-of-day fallback with configurations as the dominant default.

    Generic Deployment nouns and project names never trigger a person/date
    Deployment classification. If no direct deployment evidence exists, the row
    falls through to a lower-risk supported signal or deterministic fallback.
    """

    text = " ".join(x for x in (notes, worked_label, resolved_project) if x).strip()
    explicit = _explicit_signal(text)

    if _direct_deployment_signal(notes, worked_label):
        return WorkContextDecision(DEPLOYMENTS, "direct-deployment-execution-evidence", "high")

    if explicit == LOGISTICS:
        if is_daytime_logistics_window(start_hour, end_hour):
            return WorkContextDecision(LOGISTICS, "explicit-logistics-daytime", "high")
        return WorkContextDecision(CONFIGURATIONS, "logistics-signal-outside-daytime-config-fallback", "medium")

    if explicit:
        return WorkContextDecision(explicit, f"explicit-{explicit.lower().replace(' ', '-')}", "high")

    month = work_date.month
    weekday = work_date.weekday()  # Mon=0, Sat=5
    evening = overlaps_evening(start_hour, end_hour)
    mid = _midpoint(start_hour, end_hour)
    span = _duration(start_hour, end_hour)

    if month == 4:
        if weekday == 5:  # April Saturdays: explicit registered historical rule.
            return WorkContextDecision(DEPLOYMENTS, "april-saturday-deployment", "high")
        if weekday in (0, 2) and evening:  # Registered April Mon/Wed evening windows.
            return WorkContextDecision(DEPLOYMENTS, "april-mon-wed-evening-deployment", "medium")
        if evening:
            return WorkContextDecision(CONFIGURATIONS, "april-evening-configuration", "high")

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
            return WorkContextDecision(TICKET_FORWARDING, "morning-ticket-forwarding", "medium")
        if mid < 14.0:
            return WorkContextDecision(INVENTORY_MANAGEMENT, "daytime-inventory-management", "medium")
        if mid < EVENING_START_HOUR:
            return WorkContextDecision(CLIENT_COORDINATION, "afternoon-client-coordination", "medium")

    return WorkContextDecision(CONFIGURATIONS, "default-configuration-dominant", "low")
