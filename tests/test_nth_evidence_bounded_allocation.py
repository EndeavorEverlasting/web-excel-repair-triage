from __future__ import annotations

import pytest

from triage.nth_evidence_bounded_allocation import EvidenceBoundedAllocation


def test_38_workstations_two_devices_two_hours_produces_152_hour_envelope():
    allocation = EvidenceBoundedAllocation(
        workstations=38,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=125.0,
    )

    assert allocation.device_count == 76
    assert allocation.configuration_workload_envelope_hours == 152.0
    assert allocation.max_defensible_configuration_hours == 125.0


def test_dated_non_configuration_hours_are_reserved_before_configuration():
    allocation = EvidenceBoundedAllocation(
        workstations=38,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=125.0,
        explicit_non_configuration_hours=27.0,
    )

    assert allocation.configuration_workload_envelope_hours == 152.0
    assert allocation.attendance_remaining_after_explicit_non_configuration == 98.0
    assert allocation.max_defensible_configuration_hours == 98.0


def test_workload_envelope_can_be_tighter_than_attendance():
    allocation = EvidenceBoundedAllocation(
        workstations=10,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=80.0,
        explicit_non_configuration_hours=10.0,
    )

    assert allocation.configuration_workload_envelope_hours == 40.0
    assert allocation.attendance_remaining_after_explicit_non_configuration == 70.0
    assert allocation.max_defensible_configuration_hours == 40.0


def test_audit_record_keeps_scope_and_attendance_distinct():
    allocation = EvidenceBoundedAllocation(
        workstations=38,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=125.0,
        explicit_non_configuration_hours=20.0,
    )

    audit = allocation.audit_record()

    assert audit["device_count"] == 76
    assert audit["configuration_workload_envelope_hours"] == 152.0
    assert audit["attendance_hours"] == 125.0
    assert audit["max_defensible_configuration_hours"] == 105.0


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
        "workstations": 38,
        "devices_per_workstation": 2,
        "direct_hours_per_device": 2.0,
        "attendance_hours": 125.0,
        "explicit_non_configuration_hours": 0.0,
    }
    values.update(kwargs)

    with pytest.raises(ValueError):
        EvidenceBoundedAllocation(**values)
