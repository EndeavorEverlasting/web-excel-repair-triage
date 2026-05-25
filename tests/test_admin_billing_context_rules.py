from datetime import date

from triage.admin_billing_context_rules import (
    APPROVED_EXCEPTION_SUMMARY,
    FRAMING_LINE,
    contains_suspicious_language,
    friday_batch_for,
    safe_note_text,
    status_text,
    validate_context_row,
)


def test_friday_batch_weekday_maps_to_same_week_friday():
    assert friday_batch_for(date(2026, 4, 1)) == date(2026, 4, 3)
    assert friday_batch_for(date(2026, 4, 3)) == date(2026, 4, 3)


def test_friday_batch_weekend_maps_to_next_friday():
    assert friday_batch_for(date(2026, 4, 4)) == date(2026, 4, 10)
    assert friday_batch_for(date(2026, 4, 5)) == date(2026, 4, 10)


def test_submission_posture_uses_approved_framing():
    assert FRAMING_LINE == (
        "Submission Posture: Updated April billing summary → "
        "hours-tracker-safe admin context. "
        "Built for consistent Friday reporting/submission review."
    )


def test_framing_line_has_no_control_characters():
    assert all(ord(ch) >= 32 or ch in "\t\n\r" for ch in FRAMING_LINE)


def test_no_invented_hours_is_blocked_language():
    assert contains_suspicious_language(
        "Blank-hour OOO/context-only rows reviewed and cleared; no invented hours."
    )


def test_approved_exception_summary_is_not_suspicious():
    assert not contains_suspicious_language(APPROVED_EXCEPTION_SUMMARY)


def test_ooo_status_and_note_are_submission_safe():
    assert status_text("ooo_cleared", date(2026, 4, 1)) == (
        "04/01 confirmed OOO. No hours expected; reviewed and cleared."
    )
    assert safe_note_text("ooo_cleared", date(2026, 4, 1)) == (
        "Confirmed OOO for 04/01. No billable hours carried for this date."
    )


def test_blank_hours_without_clearance_is_error():
    issues = validate_context_row(
        row_number=7,
        work_date=date(2026, 4, 1),
        hours="",
        status="OK",
        admin_action="Keep",
        safe_note="Configuration support",
    )
    assert any(issue.issue_code == "blank_hours_without_clearance" for issue in issues)


def test_ooo_row_with_work_performed_language_is_error():
    issues = validate_context_row(
        row_number=7,
        work_date=date(2026, 4, 1),
        hours="",
        status="04/01 confirmed OOO. No hours expected; reviewed and cleared.",
        admin_action="Keep",
        safe_note="Configuration support and QA readiness",
    )
    assert any(issue.issue_code == "ooo_implies_work_performed" for issue in issues)


def test_clean_ooo_row_has_no_issues():
    issues = validate_context_row(
        row_number=7,
        work_date=date(2026, 4, 1),
        hours="",
        status="04/01 confirmed OOO. No hours expected; reviewed and cleared.",
        admin_action="Keep",
        safe_note="Confirmed OOO for 04/01. No billable hours carried for this date.",
    )
    assert issues == []
