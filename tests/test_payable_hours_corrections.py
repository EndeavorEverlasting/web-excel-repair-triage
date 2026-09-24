from __future__ import annotations

from datetime import date

import pytest

from triage.payable_hours_corrections import (
    PayableHoursCorrection,
    apply_payable_hours_correction,
    parse_correction_row,
)


def test_set_payable_hours_replaces_roster_target():
    correction = PayableHoursCorrection(
        work_date=date(2026, 4, 28),
        staff_name="Richard Perez",
        mode="set_payable_hours",
        hours=14.0,
        reason="Roster had standard placeholder hours; Paylocity shows OT.",
        evidence_source="Paylocity April 2026 PDF",
        evidence_hours=13.98,
    )

    assert apply_payable_hours_correction(8.0, correction) == 14.0


def test_add_payable_hours_is_supported_but_explicit():
    correction = PayableHoursCorrection(
        work_date=date(2026, 4, 28),
        staff_name="Richard Perez",
        mode="add_payable_hours",
        hours=6.0,
        reason="Add missing OT delta.",
    )

    assert apply_payable_hours_correction(8.0, correction) == 14.0


def test_scope_prevents_billing_pollution_when_payroll_delta_only():
    correction = PayableHoursCorrection(
        work_date=date(2026, 4, 28),
        staff_name="Richard Perez",
        mode="set_payable_hours",
        hours=14.0,
        reason="Payroll delta cleanup only.",
        scope="payroll_delta",
    )

    assert apply_payable_hours_correction(8.0, correction, scope="billing") == 8.0
    assert apply_payable_hours_correction(8.0, correction, scope="payroll_delta") == 14.0


def test_both_scope_applies_to_billing_and_payroll_delta():
    correction = PayableHoursCorrection(
        work_date=date(2026, 4, 28),
        staff_name="Richard Perez",
        mode="set_payable_hours",
        hours=14.0,
        reason="Reviewed correction applies everywhere.",
        scope="both",
    )

    assert apply_payable_hours_correction(8.0, correction, scope="billing") == 14.0
    assert apply_payable_hours_correction(8.0, correction, scope="payroll_delta") == 14.0


def test_parse_correction_row_accepts_admin_friendly_columns():
    correction = parse_correction_row({
        "date": "2026-04-29",
        "staff_name": "Richard Perez",
        "mode": "set_payable_hours",
        "hours": "17.00",
        "scope": "payroll_delta",
        "reason": "Roster had standard placeholder hours; Paylocity shows OT.",
        "evidence_source": "Paylocity April 2026 PDF",
        "evidence_hours": "16.95",
        "project_name": "Neuron Deployments",
    })

    assert correction.work_date == date(2026, 4, 29)
    assert correction.staff_name == "Richard Perez"
    assert correction.hours == 17.0
    assert correction.evidence_hours == 16.95
    assert correction.project_name == "Neuron Deployments"


def test_parse_rejects_unknown_mode():
    with pytest.raises(ValueError):
        parse_correction_row({
            "date": "2026-04-29",
            "staff_name": "Richard Perez",
            "mode": "mystery",
            "hours": "17.00",
        })
