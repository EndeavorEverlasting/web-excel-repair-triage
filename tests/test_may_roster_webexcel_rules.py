"""Overnight-punch and unassigned-hours rule tests (pure logic)."""
from __future__ import annotations

from datetime import date

from triage.may_roster_webexcel.roster_rules import (
    STATUS_MALFORMED,
    STATUS_NEUTRAL,
    STATUS_OVERNIGHT,
    STATUS_OK,
    UNASSIGNED_LABEL,
    build_unassigned_rows,
    classify_punch,
    compute_overnight_gross,
    is_unassigned,
)


def test_overnight_morning_to_after_midnight_not_malformed():
    cls = classify_punch("8:30 AM", "1:00 AM")
    assert cls.status == STATUS_OVERNIGHT
    assert cls.is_overnight is True
    assert cls.gross_hours == 16.5


def test_overnight_evening_to_midnight_not_malformed():
    cls = classify_punch("5:15 PM", "12:00 AM")
    assert cls.status == STATUS_OVERNIGHT
    # 17.25 -> 24:00 wraps: (24 - 17.25) + 0 = 6.75
    assert cls.gross_hours == 6.75


def test_blank_blank_is_neutral():
    cls = classify_punch(None, None)
    assert cls.status == STATUS_NEUTRAL


def test_blank_sunday_with_populated_monday_sunday_stays_neutral():
    # Sunday cell pair is blank/blank; Monday is a separate classification call.
    sunday = classify_punch("", "")
    assert sunday.status == STATUS_NEUTRAL
    monday = classify_punch("9:00 AM", "5:00 PM")
    assert monday.status == STATUS_OK


def test_single_missing_punch_is_malformed():
    assert classify_punch("9:00 AM", None).status == STATUS_MALFORMED
    assert classify_punch(None, "5:00 PM").status == STATUS_MALFORMED


def test_non_time_punch_is_malformed():
    assert classify_punch("ASK MGR", "5:00 PM").status == STATUS_MALFORMED


def test_equal_punches_zero_duration_malformed():
    assert classify_punch("9:00 AM", "9:00 AM").status == STATUS_MALFORMED


def test_absurd_duration_is_malformed_not_overnight():
    # 10:00 AM -> 9:00 AM = 23h wrap -> absurd.
    cls = classify_punch("10:00 AM", "9:00 AM")
    assert cls.status == STATUS_MALFORMED


def test_compute_overnight_gross_wraps():
    assert compute_overnight_gross(20.0, 4.0) == 8.0
    assert compute_overnight_gross(9.0, 17.0) == 8.0


def test_is_unassigned_zero_project_with_paid_hours():
    assert is_unassigned(10.5, "0") is True
    assert is_unassigned(9.0, "") is True
    assert is_unassigned(8.0, "Neuron Deployments") is False
    assert is_unassigned(0.0, "0") is False


def test_is_unassigned_exempts_pto_and_weekend():
    assert is_unassigned(8.0, "", day_type="PTO") is False
    assert is_unassigned(8.0, "", day_type="weekend-no-work") is False


def test_build_unassigned_rows_names_names():
    records = [
        {"tech": "Md Suhan Newaz", "date": date(2026, 5, 2), "paid_hours": 10.5, "project": "0"},
        {"tech": "Md Suhan Newaz", "date": date(2026, 5, 9), "paid_hours": 9.0, "project": "0"},
        {"tech": "Jane Tech", "date": date(2026, 5, 2), "paid_hours": 8.0, "project": "Neuron Deployments"},
    ]
    rows = build_unassigned_rows(records)
    assert len(rows) == 2
    assert all(r.status == UNASSIGNED_LABEL for r in rows)
    assert rows[0].tech == "Md Suhan Newaz"
    assert rows[0].date == date(2026, 5, 2)
    assert rows[0].paid_hours == 10.5
    # Every row names the tech, date, and hours.
    d = rows[0].to_dict()
    assert d["Tech"] and d["Date"] and d["Actual Paid Hours"]
