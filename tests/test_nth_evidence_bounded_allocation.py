from __future__ import annotations

import pytest

from triage.nth_evidence_bounded_allocation import EvidenceBoundedAllocation


def test_confirmed_workload_envelope_is_bounded_by_historical_labor():
    allocation = EvidenceBoundedAllocation(
        workstations=4,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=20.0,
    )

    assert allocation.device_count == 8
    assert allocation.configuration_workload_envelope_hours == 16.0
    assert allocation.max_defensible_configuration_hours == 16.0


def test_non_configuration_hours_are_reserved_before_configuration():
    allocation = EvidenceBoundedAllocation(
        workstations=4,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=20.0,
        explicit_non_configuration_hours=8.0,
    )

    assert allocation.attendance_remaining_after_explicit_non_configuration == 12.0
    assert allocation.max_defensible_configuration_hours == 12.0


def test_workload_envelope_can_be_tighter_than_labor():
    allocation = EvidenceBoundedAllocation(
        workstations=2,
        devices_per_workstation=1,
        direct_hours_per_device=1.5,
        attendance_hours=10.0,
        explicit_non_configuration_hours=1.0,
    )

    assert allocation.configuration_workload_envelope_hours == 3.0
    assert allocation.attendance_remaining_after_explicit_non_configuration == 9.0
    assert allocation.max_defensible_configuration_hours == 3.0


def test_audit_record_keeps_workload_and_labor_distinct():
    allocation = EvidenceBoundedAllocation(
        workstations=3,
        devices_per_workstation=1,
        direct_hours_per_device=1.5,
        attendance_hours=8.0,
        explicit_non_configuration_hours=2.0,
    )

    audit = allocation.audit_record()
    assert audit["device_count"] == 3
    assert audit["configuration_workload_envelope_hours"] == 4.5
    assert audit["attendance_hours"] == 8.0
    assert audit["max_defensible_configuration_hours"] == 4.5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"workstations": -1},
        {"devices_per_workstation": 0},
        {"direct_hours_per_device": -1.0},
        {"attendance_hours": -1.0},
        {"explicit_non_configuration_hours": -1.0},
        {"attendance_hours": 5.0, "explicit_non_configuration_hours": 6.0},
    ],
)
def test_invalid_allocation_inputs_fail_closed(kwargs):
    values = {
        "workstations": 3,
        "devices_per_workstation": 1,
        "direct_hours_per_device": 1.5,
        "attendance_hours": 8.0,
        "explicit_non_configuration_hours": 0.0,
    }
    values.update(kwargs)

    with pytest.raises(ValueError):
        EvidenceBoundedAllocation(**values)
