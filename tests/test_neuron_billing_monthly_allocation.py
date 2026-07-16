"""Tests for sanitized month-specific Neuron task allocation."""
from __future__ import annotations

from datetime import date, time, timedelta

import pytest

from triage.nw_prj_neuron_track_hours.bonita_resolver import BonitaResolution, BonitaShift
from triage.nw_prj_neuron_track_hours.monthly_allocation import apply_monthly_allocation_policies


def _shifts(*, explicit_deployment: bool) -> BonitaResolution:
    people = ["Alpha Tech", "Bravo Tech", "Charlie Tech"]
    start = date(2026, 7, 1)
    shifts = []
    for index in range(36):
        assignment = "Configurations"
        rule = "full-shift-overlaps-configuration-window"
        confidence = "medium"
        if explicit_deployment and index == 30:
            assignment = "Deployments"
            rule = "explicit-deployment"
            confidence = "high"
        shifts.append(BonitaShift(
            month_key="2026-07",
            month_name="July",
            date=start + timedelta(days=index // 3),
            day=(start + timedelta(days=index // 3)).strftime("%a"),
            tech=people[index % 3],
            clock_in="9:00 AM",
            clock_out="5:00 PM",
            total_hours=8.0,
            assignment_type=assignment,
            start_time=time(9),
            end_time=time(17),
            assignment_rule=rule,
            assignment_confidence=confidence,
        ))
    return BonitaResolution(shifts=shifts)


def _counts(resolution: BonitaResolution) -> dict[str, int]:
    result: dict[str, int] = {}
    for shift in resolution.shifts:
        result[shift.assignment_type] = result.get(shift.assignment_type, 0) + 1
    return result


def test_july_policy_recreates_accepted_ratio_without_inventing_deployment() -> None:
    resolved, stats = apply_monthly_allocation_policies(_shifts(explicit_deployment=False), ["2026-07"])
    assert _counts(resolved) == {
        "Configurations": 17,
        "Inventory Management": 9,
        "Survey": 7,
        "Ticket Forwarding": 3,
    }
    assert stats[0].deployment_shift_count == 0
    assert sum(stats[0].category_hours.values()) == 288.0


def test_july_policy_preserves_one_explicit_deployment_and_allocates_rest() -> None:
    resolved, stats = apply_monthly_allocation_policies(_shifts(explicit_deployment=True), ["2026-07"])
    assert _counts(resolved) == {
        "Configurations": 16,
        "Inventory Management": 9,
        "Survey": 7,
        "Ticket Forwarding": 3,
        "Deployments": 1,
    }
    deployment = [shift for shift in resolved.shifts if shift.assignment_type == "Deployments"]
    assert len(deployment) == 1
    assert deployment[0].assignment_rule == "explicit-deployment"
    assert stats[0].deployment_shift_count == 1


def test_july_policy_fails_when_explicit_deployment_cap_is_exceeded() -> None:
    resolution = _shifts(explicit_deployment=True)
    first = resolution.shifts[0]
    resolution.shifts[0] = BonitaShift(
        **{
            **first.__dict__,
            "assignment_type": "Deployments",
            "assignment_rule": "explicit-deployment",
            "assignment_confidence": "high",
        }
    )
    with pytest.raises(ValueError, match="exceed policy maximum"):
        apply_monthly_allocation_policies(resolution, ["2026-07"])
