from __future__ import annotations

import pytest

from triage.billing_rules import (
    BillingStatus,
    classify_billing_row,
    lunch_deduction,
    net_billable_hours,
)


@pytest.mark.parametrize(
    ("gross", "expected_lunch", "expected_net"),
    [
        (0.0, 0.0, 0.0),
        (5.99, 0.0, 5.99),
        (6.0, 0.5, 5.5),
        (7.5, 0.5, 7.0),
        (8.0, 1.0, 7.0),
        (12.0, 1.0, 11.0),
    ],
)
def test_lunch_policy_boundaries(gross, expected_lunch, expected_net):
    assert lunch_deduction(gross) == pytest.approx(expected_lunch)
    assert net_billable_hours(gross) == pytest.approx(expected_net)


def test_partial_hours_are_bill_actual_net_not_full_day():
    decision = classify_billing_row(gross_hours=7.5, project="Neuron Deployments")

    assert decision.status == BillingStatus.PARTIAL
    assert decision.lunch_deduction == pytest.approx(0.5)
    assert decision.net_hours == pytest.approx(7.0)
    assert "Partial shift" in decision.explanation


def test_unclassified_hours_are_review_not_silent_billing():
    decision = classify_billing_row(gross_hours=8.0, project="")

    assert decision.status == BillingStatus.UNCLASSIFIED_REVIEW
    assert decision.net_hours == pytest.approx(7.0)
    assert "hold" in decision.explanation.lower()


def test_long_shift_keeps_hours_but_flags_review():
    decision = classify_billing_row(gross_hours=13.5, project="Neuron Deployments")

    assert decision.status == BillingStatus.LONG_SHIFT_REVIEW
    assert decision.net_hours == pytest.approx(12.5)
    assert "Long shift" in decision.explanation


def test_paid_holiday_without_roster_work_is_non_billable():
    decision = classify_billing_row(
        gross_hours=0.0,
        project="Paid Holiday / Agilant Admin",
        is_holiday=True,
        has_roster_work=False,
    )

    assert decision.status == BillingStatus.HOLIDAY_NON_BILLABLE
    assert decision.net_hours == pytest.approx(0.0)
    assert decision.lunch_deduction == pytest.approx(0.0)
