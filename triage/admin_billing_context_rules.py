"""Admin billing context rules.

These rules came out of the 2026-05-20 April billing reconciliation workflow.

The goal is not merely to move rows between workbooks. The goal is to preserve
submission posture:

- admins receive a clean hours-tracker-safe context artifact;
- internal QC and bridge logic stay private;
- Friday is the reporting and submission batch anchor;
- exception rows are resolved with calm operational language;
- OOO and context-only rows must not read like performed work;
- suspicious defensive language is blocked from admin-facing outputs.

This module is workbook-agnostic. Spreadsheet IO belongs in scripts. These
rules should be reusable by both directions:

1. billing summary to admin context
2. admin context to billing summary
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable


FRAMING_LINE = (
    "Submission Posture: Updated April billing summary → "
    "hours-tracker-safe admin context. "
    "Built for consistent Friday reporting/submission review."
)

APPROVED_EXCEPTION_SUMMARY = "Exception rows reconciled and cleared where applicable."
BLANK_ROW_SUMMARY = "Blank-hour OOO/context-only rows reviewed and cleared where applicable."

ADMIN_SUBMISSION_TABS = [
    "01 Admin Summary",
    "02 Tracker Import",
    "03 Friday Batches",
]

INTERNAL_ONLY_TABS = {
    "04 QC Pipeline",
    "QC Pipeline",
    "Internal QC",
    "Bridge Exceptions",
    "Formula Audit",
    "Reconciliation Bridge",
    "Manual Review",
}

FRIDAY_REPORTING_RULE = (
    "Work performed Monday through Friday maps to that Friday's "
    "reporting/submission batch. Weekend work rolls into the next Friday "
    "unless explicitly assigned otherwise."
)

# These phrases are allowed here only because this is the guardrail list.
# They must not be emitted into admin-facing workbook text.
SUSPICIOUS_LANGUAGE = {
    "no invented hours",
    "invented hours",
    "sausage",
    "internal logic",
    "bridge logic",
    "confidence field",
    "inference language",
    "task evidence without attendance",
}

WORK_PERFORMED_TERMS = {
    "configured",
    "configuration",
    "supported",
    "support",
    "deployed",
    "deployment",
    "qa readiness",
    "ticket follow-through",
    "inventory control",
    "field support",
    "build support",
}

STATUS_TEXT = {
    "ooo_cleared": "{date} confirmed OOO. No hours expected; reviewed and cleared.",
    "context_only": "{date} reviewed as context-only. No hours carried; no billing action required.",
    "hours_confirmed": "{date} hours reviewed and carried in billing context.",
    "manual_review": "{date} requires manual review before submission.",
    "exception_cleared": "{date} exception reviewed and cleared where applicable.",
}

SAFE_NOTE_TEXT = {
    "ooo_cleared": "Confirmed OOO for {date}. No billable hours carried for this date.",
    "context_only": "Context-only entry for {date}. No billable hours carried for this date.",
}


@dataclass(frozen=True)
class ContextRowCheck:
    """Result of checking one admin context row."""

    row_number: int | None
    issue_code: str
    message: str
    severity: str = "warning"


def normalize_date(value: object) -> date:
    """Normalize spreadsheet-ish date values into a date."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(stripped, fmt).date()
            except ValueError:
                pass
    raise ValueError(f"Cannot normalize date value: {value!r}")


def display_date(value: object) -> str:
    """Return MM/DD display text for status comments."""

    return normalize_date(value).strftime("%m/%d")


def friday_batch_for(work_date: object) -> date:
    """Map a work date to the Friday reporting/submission batch.

    Monday-Friday work maps to that week's Friday. Saturday-Sunday work maps to
    the next Friday unless an explicit override exists upstream.
    """

    d = normalize_date(work_date)
    weekday = d.weekday()  # Monday=0, Sunday=6

    if weekday <= 4:
        return d + timedelta(days=(4 - weekday))

    return d + timedelta(days=(11 - weekday))


def status_text(status_key: str, work_date: object) -> str:
    """Render an approved status comment."""

    return STATUS_TEXT[status_key].format(date=display_date(work_date))


def safe_note_text(status_key: str, work_date: object) -> str:
    """Render an approved safe billing/admin note."""

    return SAFE_NOTE_TEXT[status_key].format(date=display_date(work_date))


def contains_suspicious_language(text: object) -> bool:
    """Return True when wording should not appear in admin-facing outputs."""

    value = str(text or "").lower()
    return any(term in value for term in SUSPICIOUS_LANGUAGE)


def contains_work_performed_language(text: object) -> bool:
    """Return True when text implies work was performed."""

    value = str(text or "").lower()
    return any(term in value for term in WORK_PERFORMED_TERMS)


def row_looks_ooo(text_values: Iterable[object]) -> bool:
    """Detect whether row text says the person was out of office."""

    combined = " ".join(str(v or "") for v in text_values).lower()
    return "ooo" in combined or "out of office" in combined


def row_looks_context_only(text_values: Iterable[object]) -> bool:
    """Detect whether row text says the row is context-only."""

    combined = " ".join(str(v or "") for v in text_values).lower()
    return "context-only" in combined or "context only" in combined


def validate_context_row(
    *,
    row_number: int | None = None,
    work_date: object,
    hours: object,
    status: object = "",
    admin_action: object = "",
    safe_note: object = "",
) -> list[ContextRowCheck]:
    """Validate one admin context row for submission-safe posture.

    A row can have correct hours and still be bad evidence if the language
    contradicts OOO or context-only status.
    """

    checks: list[ContextRowCheck] = []
    text_values = [status, admin_action, safe_note]
    is_blank_hours = hours in (None, "", 0, 0.0)
    is_ooo = row_looks_ooo(text_values)
    is_context_only = row_looks_context_only(text_values)

    if any(contains_suspicious_language(v) for v in text_values):
        checks.append(
            ContextRowCheck(
                row_number,
                "suspicious_language",
                "Admin-facing row contains defensive or internal wording.",
                "error",
            )
        )

    if str(status or "").strip().upper().startswith("REVIEW"):
        checks.append(
            ContextRowCheck(
                row_number,
                "unresolved_review_status",
                "Submission row still contains unresolved REVIEW status.",
                "error",
            )
        )

    if is_blank_hours and not (is_ooo or is_context_only):
        checks.append(
            ContextRowCheck(
                row_number,
                "blank_hours_without_clearance",
                "Blank-hour row needs OOO or context-only clearance language.",
                "error",
            )
        )

    if is_ooo and contains_work_performed_language(safe_note):
        checks.append(
            ContextRowCheck(
                row_number,
                "ooo_implies_work_performed",
                "OOO row safe note still implies work was performed.",
                "error",
            )
        )

    return checks


def should_keep_admin_tab(sheet_name: str) -> bool:
    """Return True for the three admin-facing submission tabs."""

    return sheet_name in ADMIN_SUBMISSION_TABS


def is_internal_tab(sheet_name: str) -> bool:
    """Return True for tabs that must stay out of admin submission exports."""

    return sheet_name in INTERNAL_ONLY_TABS
