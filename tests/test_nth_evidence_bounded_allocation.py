from __future__ import annotations

from datetime import date

import pytest

from triage.nth_evidence_bounded_allocation import (
    CONFIGURATION_COUNT_SCOPE,
    DERIVED_INTERNAL_MANAGEMENT_AUTHORITY,
    DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
    REPORTED_INTERNAL_ALLOCATION_AUTHORITY,
    AllocationComponent,
    ClosedAttendanceAllocation,
    ConfirmedConfigurationTiming,
    EvidenceBoundedAllocation,
    derive_internal_management_remainder,
    validate_closed_allocation_set,
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


def _component(
    allocation_id: str,
    *,
    hours: float,
    workstream: str = "Program Support",
    authority: str = REPORTED_INTERNAL_ALLOCATION_AUTHORITY,
    staff_key: str = "synthetic-tech",
    work_date: date = date(2026, 1, 15),
    derivation: str | None = None,
) -> AllocationComponent:
    return AllocationComponent(
        allocation_id=allocation_id,
        staff_key=staff_key,
        work_date=work_date,
        workstream=workstream,
        hours=hours,
        authority=authority,
        evidence_refs=(f"EVID-{allocation_id}",),
        internal_only=True,
        derivation=derivation,
    )


@pytest.mark.parametrize("hours", [0.0, -0.1, float("inf"), float("nan")])
def test_closed_allocation_component_rejects_zero_negative_or_nonfinite_hours(hours):
    with pytest.raises(ValueError, match="hours must"):
        _component("BAD-HOURS", hours=hours)


def test_direct_span_is_internal_allocation_control_not_paid_hours_authority():
    component = _component(
        "DIRECT-SPAN",
        hours=3.2,
        workstream="Inventory / Reconciliation",
        authority=DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
    )

    audit = component.audit_record()
    assert audit["hours"] == 3.2
    assert audit["authority"] == DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY
    assert audit["internal_only"] is True
    assert audit["paid_hours_authority"] is False


def test_internal_remainder_is_explicitly_derived_and_stays_internal():
    reported = _component("REPORTED", hours=1.0, workstream="Training / Acclimation")
    direct_span = _component(
        "DIRECT-SPAN",
        hours=3.2,
        workstream="Inventory / Reconciliation",
        authority=DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
    )

    remainder = derive_internal_management_remainder(
        allocation_id="DERIVED-REMAINDER",
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 15),
        workstream="Program Support / Management Control",
        attendance_hours=8.0,
        committed_components=(reported, direct_span),
        evidence_refs=("ATTENDANCE-CONTROL", "INTERNAL-ALLOCATION-RULE"),
    )

    assert remainder.hours == pytest.approx(3.8)
    assert remainder.authority == DERIVED_INTERNAL_MANAGEMENT_AUTHORITY
    assert remainder.internal_only is True
    assert remainder.derivation == "attendance_hours(8) - committed_component_hours(4.2)"
    assert remainder.audit_record()["paid_hours_authority"] is False


def test_derived_remainder_rejects_zero_or_negative_remainder():
    committed = (_component("ALL", hours=8.0),)
    with pytest.raises(ValueError, match="derived remainder must be > 0"):
        derive_internal_management_remainder(
            allocation_id="NO-REMAINDER",
            staff_key="synthetic-tech",
            work_date=date(2026, 1, 15),
            workstream="Program Support",
            attendance_hours=8.0,
            committed_components=committed,
            evidence_refs=("ATTENDANCE-CONTROL",),
        )


def test_multiple_project_components_can_share_one_closed_attendance_day():
    reported = _component("A", hours=1.0, workstream="Training / Acclimation")
    direct_span = _component(
        "B",
        hours=3.2,
        workstream="Inventory / Reconciliation",
        authority=DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
    )
    remainder = derive_internal_management_remainder(
        allocation_id="C",
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 15),
        workstream="Program Support / Management Control",
        attendance_hours=8.0,
        committed_components=(reported, direct_span),
        evidence_refs=("ATTENDANCE-CONTROL",),
    )

    closed = ClosedAttendanceAllocation(
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 15),
        attendance_hours=8.0,
        attendance_evidence_refs=("ROSTER-ATTENDANCE",),
        components=(reported, direct_span, remainder),
    )

    assert closed.allocated_hours == pytest.approx(8.0)
    assert closed.audit_record()["reconciled_to_attendance"] is True
    assert len(closed.components) == 3


@pytest.mark.parametrize(
    ("components", "attendance_hours"),
    [
        ((_component("UNDER-A", hours=2.0), _component("UNDER-B", hours=3.0)), 8.0),
        ((_component("OVER-A", hours=4.5), _component("OVER-B", hours=4.0)), 8.0),
    ],
)
def test_closed_allocation_must_reconcile_exactly_to_attendance(components, attendance_hours):
    with pytest.raises(ValueError, match="reconcile exactly"):
        ClosedAttendanceAllocation(
            staff_key="synthetic-tech",
            work_date=date(2026, 1, 15),
            attendance_hours=attendance_hours,
            attendance_evidence_refs=("ROSTER-ATTENDANCE",),
            components=components,
        )


def test_closed_attendance_rejects_zero_hours():
    with pytest.raises(ValueError, match="attendance_hours must be > 0"):
        ClosedAttendanceAllocation(
            staff_key="synthetic-tech",
            work_date=date(2026, 1, 15),
            attendance_hours=0.0,
            attendance_evidence_refs=("ROSTER-ATTENDANCE",),
            components=(_component("A", hours=1.0),),
        )


def test_closed_day_rejects_duplicate_allocation_ids():
    first = _component("DUP", hours=4.0, workstream="Configuration")
    second = _component("DUP", hours=4.0, workstream="Program Support")
    with pytest.raises(ValueError, match="duplicate allocation_id"):
        ClosedAttendanceAllocation(
            staff_key="synthetic-tech",
            work_date=date(2026, 1, 15),
            attendance_hours=8.0,
            attendance_evidence_refs=("ROSTER-ATTENDANCE",),
            components=(first, second),
        )


def test_closed_day_rejects_component_from_other_staff_or_date():
    other_day = _component(
        "OTHER",
        hours=8.0,
        staff_key="other-tech",
        work_date=date(2026, 1, 16),
    )
    with pytest.raises(ValueError, match="match the closed staff/date"):
        ClosedAttendanceAllocation(
            staff_key="synthetic-tech",
            work_date=date(2026, 1, 15),
            attendance_hours=8.0,
            attendance_evidence_refs=("ROSTER-ATTENDANCE",),
            components=(other_day,),
        )


def test_closed_allocation_set_rejects_duplicate_staff_date_records():
    component_a = _component("DAY-A", hours=8.0)
    component_b = _component("DAY-B", hours=8.0)
    first = ClosedAttendanceAllocation(
        staff_key="Synthetic-Tech",
        work_date=date(2026, 1, 15),
        attendance_hours=8.0,
        attendance_evidence_refs=("ROSTER-A",),
        components=(component_a,),
    )
    second = ClosedAttendanceAllocation(
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 15),
        attendance_hours=8.0,
        attendance_evidence_refs=("ROSTER-B",),
        components=(component_b,),
    )

    with pytest.raises(ValueError, match="duplicate closed allocation for staff/date"):
        validate_closed_allocation_set((first, second))


def test_closed_allocation_set_rejects_duplicate_allocation_id_across_days():
    first = ClosedAttendanceAllocation(
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 15),
        attendance_hours=8.0,
        attendance_evidence_refs=("ROSTER-A",),
        components=(_component("GLOBAL-DUP", hours=8.0),),
    )
    second_component = _component(
        "GLOBAL-DUP",
        hours=8.0,
        work_date=date(2026, 1, 16),
    )
    second = ClosedAttendanceAllocation(
        staff_key="synthetic-tech",
        work_date=date(2026, 1, 16),
        attendance_hours=8.0,
        attendance_evidence_refs=("ROSTER-B",),
        components=(second_component,),
    )

    with pytest.raises(ValueError, match="duplicate allocation_id across closed records"):
        validate_closed_allocation_set((first, second))
