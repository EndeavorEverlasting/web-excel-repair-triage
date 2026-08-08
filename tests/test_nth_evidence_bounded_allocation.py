from __future__ import annotations

import pytest

from triage.nth_evidence_bounded_allocation import (
    CONFIGURATION_COUNT_SCOPE,
    ConfirmedConfigurationTiming,
    EvidenceBoundedAllocation,
)


def test_confirmed_configuration_scope_can_bound_workload():
    allocation = EvidenceBoundedAllocation(
        workstations=10,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=80.0,
        scope_kind=CONFIGURATION_COUNT_SCOPE,
        explicit_non_configuration_hours=10.0,
    )

    assert allocation.device_count == 20
    assert allocation.configuration_workload_envelope_hours == 40.0
    assert allocation.attendance_remaining_after_explicit_non_configuration == 70.0
    assert allocation.max_defensible_configuration_hours == 40.0


def test_testing_count_fails_closed_as_configuration_multiplier():
    with pytest.raises(ValueError, match="configuration_count"):
        EvidenceBoundedAllocation(
            workstations=38,
            devices_per_workstation=2,
            direct_hours_per_device=2.0,
            attendance_hours=135.0,
            scope_kind="device_testing",
        )


def test_installation_count_fails_closed_as_configuration_multiplier():
    with pytest.raises(ValueError, match="configuration_count"):
        EvidenceBoundedAllocation(
            workstations=2,
            devices_per_workstation=2,
            direct_hours_per_device=2.0,
            attendance_hours=135.0,
            scope_kind="installation_count",
        )


def test_confirmed_pair_uses_device_specific_timing():
    timing = ConfirmedConfigurationTiming(neuron_count=1, cybernet_count=1)

    assert timing.paired_workstation_count == 1
    assert timing.neuron_normalized_hours == 1.5
    assert timing.cybernet_min_hours == pytest.approx(118 / 60)
    assert timing.cybernet_max_hours == pytest.approx(156 / 60)
    assert timing.direct_configuration_min_hours == pytest.approx(3.4666666667)
    assert timing.direct_configuration_max_hours == pytest.approx(4.1)


def test_two_confirmed_pairs_translate_to_6_93_to_8_20_hours():
    timing = ConfirmedConfigurationTiming(neuron_count=2, cybernet_count=2)

    assert timing.paired_workstation_count == 2
    assert timing.direct_configuration_min_hours == pytest.approx(6.9333333334)
    assert timing.direct_configuration_max_hours == pytest.approx(8.2)


def test_neuron_detailed_range_keeps_optional_rename_separate():
    timing = ConfirmedConfigurationTiming(neuron_count=1, cybernet_count=0)

    assert timing.neuron_detailed_range_hours() == pytest.approx((56 / 60, 88 / 60))
    assert timing.neuron_detailed_range_hours(
        include_separate_rename=True
    ) == pytest.approx((61 / 60, 98 / 60))


def test_audit_record_keeps_confirmed_scope_and_labor_total_distinct():
    allocation = EvidenceBoundedAllocation(
        workstations=4,
        devices_per_workstation=2,
        direct_hours_per_device=2.0,
        attendance_hours=135.0,
        scope_kind=CONFIGURATION_COUNT_SCOPE,
        explicit_non_configuration_hours=30.22,
    )

    audit = allocation.audit_record()

    assert audit["scope_kind"] == CONFIGURATION_COUNT_SCOPE
    assert audit["device_count"] == 8
    assert audit["configuration_workload_envelope_hours"] == 16.0
    assert audit["attendance_hours"] == 135.0
    assert audit["max_defensible_configuration_hours"] == 16.0


def test_timing_audit_record_exposes_device_specific_inputs():
    audit = ConfirmedConfigurationTiming(neuron_count=2, cybernet_count=2).audit_record()

    assert audit["neuron_count"] == 2
    assert audit["cybernet_count"] == 2
    assert audit["paired_workstation_count"] == 2
    assert audit["neuron_normalized_hours_per_device"] == 1.5
    assert audit["cybernet_detailed_min_minutes_per_device"] == 118
    assert audit["cybernet_detailed_max_minutes_per_device"] == 156
    assert audit["direct_configuration_max_hours"] == pytest.approx(8.2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"workstations": -1},
        {"devices_per_workstation": 0},
        {"direct_hours_per_device": -1.0},
        {"attendance_hours": -1.0},
        {"explicit_non_configuration_hours": -1.0},
        {"attendance_hours": 5.0, "explicit_non_configuration_hours": 6.0},
        {"scope_kind": "testing_count"},
    ],
)
def test_invalid_allocation_inputs_fail_closed(kwargs):
    values = {
        "workstations": 4,
        "devices_per_workstation": 2,
        "direct_hours_per_device": 2.0,
        "attendance_hours": 135.0,
        "scope_kind": CONFIGURATION_COUNT_SCOPE,
        "explicit_non_configuration_hours": 0.0,
    }
    values.update(kwargs)

    with pytest.raises(ValueError):
        EvidenceBoundedAllocation(**values)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"neuron_count": -1, "cybernet_count": 0},
        {"neuron_count": 0, "cybernet_count": -1},
        {"neuron_count": 1.5, "cybernet_count": 0},
        {"neuron_count": 0, "cybernet_count": True},
    ],
)
def test_invalid_confirmed_configuration_counts_fail_closed(kwargs):
    with pytest.raises(ValueError):
        ConfirmedConfigurationTiming(**kwargs)
