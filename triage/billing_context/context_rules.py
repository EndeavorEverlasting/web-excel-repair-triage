"""Work-context classification. Spec: docs/BILLING_WORK_CONTEXT_RULES.md"""

from __future__ import annotations

import re
from datetime import date, time
from typing import Optional

RULES_DOC = "docs/BILLING_WORK_CONTEXT_RULES.md"

PLACEHOLDER_LABELS = {
    "neuron installation",
    "installation",
    "neuron install",
    "install",
}

CONFIGURATION_HINTS = {"configure", "configuration", "imaged", "image", "setup", "build"}

ALLOWED_CONTEXTS = {
    "Configuration",
    "Inventory Management",
    "Inventory Management & Logistics",
    "Deployment Support",
    "Incident Response",
    "Ticket Coordination",
    "Client Coordination",
    "Logistics",
    "Mixed Operational Support",
    "Unknown / Needs Review",
}

REQ_PATTERN = re.compile(r"\bREQ\d+\b", re.IGNORECASE)
RITM_PATTERN = re.compile(r"\bRITM\d+\b", re.IGNORECASE)
PM_PATTERN = re.compile(r"\bPM\b", re.IGNORECASE)


def is_placeholder_assignment(value: str | None) -> bool:
    if not value:
        return False
    return str(value).strip().lower() in PLACEHOLDER_LABELS


def normalize_assignment_label(value: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    for label in ALLOWED_CONTEXTS:
        if text.lower() == label.lower():
            return label
    return None


def is_evening(start_time: Optional[time], end_time: Optional[time]) -> bool:
    if start_time and start_time.hour >= 16:
        return True
    if end_time and end_time.hour >= 18:
        return True
    return False


def is_saturday(work_date: date) -> bool:
    return work_date.weekday() == 5


def is_sunday(work_date: date) -> bool:
    return work_date.weekday() == 6


def _hints_configuration(text: str) -> bool:
    raw = (text or "").lower()
    return any(k in raw for k in CONFIGURATION_HINTS)


def classify_from_task_text(text: str) -> tuple[str, str, str]:
    """Returns: work_context, reason, confidence."""
    raw = (text or "").lower()

    if any(k in raw for k in ["configure", "configuration", "imaged", "image", "setup", "build"]):
        return "Configuration", "Task tracker contains configuration/build language.", "high"

    if any(k in raw for k in ["inventory", "warehouse", "stock", "staging", "deliver", "delivery", "pickup", "logistics"]):
        return "Inventory Management & Logistics", "Task tracker contains inventory/logistics language.", "high"

    if any(k in raw for k in ["deploy", "deployment", "go live", "go-live", "floor support"]):
        return "Deployment Support", "Task tracker contains deployment/go-live language.", "high"

    if any(k in raw for k in ["incident", "break/fix", "outage", "urgent", "support issue"]):
        return "Incident Response", "Task tracker contains incident response language.", "high"

    if REQ_PATTERN.search(text or "") or RITM_PATTERN.search(text or "") or "servicenow" in raw or "ticket" in raw:
        return "Ticket Coordination", "Task tracker contains ticket coordination language.", "high"

    if PM_PATTERN.search(text or "") or any(k in raw for k in ["client", "coordination", "coordinate", "follow up", "follow-up"]):
        return "Client Coordination", "Task tracker contains coordination language.", "medium"

    return "Unknown / Needs Review", "No decisive task-tracker context found.", "low"


def classify_by_time_rules(
    work_date: date,
    start_time: Optional[time],
    end_time: Optional[time],
    month: int,
    assignment: str = "",
    notes: str = "",
) -> tuple[str, str, str]:
    hint_text = f"{assignment} {notes}".strip()

    if is_saturday(work_date) and month == 4:
        return "Deployment Support", "April Saturday rule applied.", "medium"

    if is_saturday(work_date) and month >= 5:
        if _hints_configuration(hint_text):
            return "Configuration", "May+ Saturday rule with configuration hints.", "medium"
        return "Inventory Management", "May+ Saturday rule applied.", "medium"

    if is_sunday(work_date):
        return "Logistics", "Sunday rule applied: cleanup and stock movement.", "medium"

    if is_evening(start_time, end_time):
        if _hints_configuration(hint_text):
            return "Configuration", "Evening-hours rule with configuration hints.", "medium"
        return "Inventory Management", "Evening-hours rule applied.", "medium"

    return (
        "Mixed Operational Support",
        "Day-hours rule applied: logistics, inventory, incident response, ticket/client coordination.",
        "medium",
    )


def resolve_work_context(
    *,
    assignment: str,
    task_text: str,
    work_date: date,
    start_time: Optional[time],
    end_time: Optional[time],
) -> tuple[str, str, str]:
    task_context, task_reason, task_conf = classify_from_task_text(task_text)
    assignment_label = normalize_assignment_label(assignment) if assignment and not is_placeholder_assignment(assignment) else None

    if task_context != "Unknown / Needs Review":
        if assignment_label and assignment_label != task_context:
            return (
                "Unknown / Needs Review",
                "Task tracker and assignment disagree; manual review required.",
                "low",
            )
        return task_context, task_reason, task_conf

    if assignment_label:
        return assignment_label, "Non-placeholder assignment retained.", "medium"

    return classify_by_time_rules(
        work_date=work_date,
        start_time=start_time,
        end_time=end_time,
        month=work_date.month,
        assignment=assignment,
        notes=task_text,
    )
