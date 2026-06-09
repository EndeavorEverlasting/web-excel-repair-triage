"""Hours-basis policy regressions.

These tests protect the split between billing math and operational tracking:

* Billing Summary and Delta Dashboard use net hours.
* Neuron Track Hours uses gross hours.
"""
from __future__ import annotations

from triage.hours_basis_policy import (
    HOURS_BASIS_GROSS,
    HOURS_BASIS_NET,
    hours_basis_for,
    lunch_deduction,
    net_hours_from_gross,
)
from triage.roster_parser import _lunch_deduction as roster_lunch_deduction


def test_lunch_deduction_policy_thresholds():
    assert lunch_deduction(8.0) == 1.0
    assert lunch_deduction(7.99) == 0.5
    assert lunch_deduction(6.0) == 0.5
    assert lunch_deduction(5.99) == 0.0


def test_net_hours_from_gross_policy():
    assert net_hours_from_gross(9.0) == 8.0
    assert net_hours_from_gross(7.5) == 7.0
    assert net_hours_from_gross(4.0) == 4.0


def test_roster_parser_lunch_policy_matches_canonical_policy():
    for gross in (0.0, 4.0, 5.99, 6.0, 7.5, 8.0, 9.0, 12.25):
        assert roster_lunch_deduction(gross) == lunch_deduction(gross)


def test_billing_and_delta_artifacts_use_net_hours():
    assert hours_basis_for("admin_billing_summary") == HOURS_BASIS_NET
    assert hours_basis_for("billing_summary") == HOURS_BASIS_NET
    assert hours_basis_for("delta_dashboard") == HOURS_BASIS_NET
    assert hours_basis_for("payroll_delta_dashboard") == HOURS_BASIS_NET


def test_neuron_track_hours_uses_gross_hours():
    assert hours_basis_for("neuron_track_hours") == HOURS_BASIS_GROSS
    assert hours_basis_for("bonita_neuron_track_hours") == HOURS_BASIS_GROSS
