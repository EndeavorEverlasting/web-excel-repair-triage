from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Iterable


CONFIGURATION_COUNT_SCOPE = "configuration_count"

DIRECT_TASK_EVIDENCE_AUTHORITY = "direct_task_evidence"
DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY = "direct_span_internal_control"
REPORTED_INTERNAL_ALLOCATION_AUTHORITY = "reported_internal_allocation"
DERIVED_INTERNAL_MANAGEMENT_AUTHORITY = "derived_internal_management"
ALLOCATION_AUTHORITIES = frozenset(
    {
        DIRECT_TASK_EVIDENCE_AUTHORITY,
        DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
        REPORTED_INTERNAL_ALLOCATION_AUTHORITY,
        DERIVED_INTERNAL_MANAGEMENT_AUTHORITY,
    }
)
ALLOCATION_RECONCILIATION_TOLERANCE = 1e-6

NEURON_NORMALIZED_HOURS = 1.5
NEURON_DETAILED_MIN_MINUTES = 56
NEURON_DETAILED_MAX_MINUTES = 88
NEURON_RENAME_MIN_MINUTES = 5
NEURON_RENAME_MAX_MINUTES = 10
CYBERNET_DETAILED_MIN_MINUTES = 118
CYBERNET_DETAILED_MAX_MINUTES = 156


def _minutes_to_hours(minutes: int) -> float:
    return round(minutes / 60.0, 10)


def _positive_finite(value: float, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    if number <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return number


def _non_empty(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _evidence_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    cleaned = tuple(_non_empty(value, field_name) for value in values)
    if len(set(cleaned)) != len(cleaned):
        raise ValueError(f"{field_name} must not contain duplicates")
    return cleaned


def _calendar_date(value: date, field_name: str = "work_date") -> date:
    """Normalize datetime inputs to their calendar day before identity checks."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"{field_name} must be a date")


def _staff_date_key(staff_key: str, work_date: date) -> tuple[str, str]:
    normalized_date = _calendar_date(work_date)
    return (
        _non_empty(staff_key, "staff_key").casefold(),
        normalized_date.isoformat(),
    )


@dataclass(frozen=True)
class ConfirmedConfigurationTiming:
    """Translate independently confirmed device counts into direct Configuration time.

    The counts passed here must already have Configuration-count authority. Testing,
    IDT, target, installation, or remaining-work counts are not valid substitutes.
    """

    neuron_count: int
    cybernet_count: int

    def __post_init__(self) -> None:
        for field_name in ("neuron_count", "cybernet_count"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be >= 0")

    @property
    def neuron_normalized_hours(self) -> float:
        return round(self.neuron_count * NEURON_NORMALIZED_HOURS, 10)

    @property
    def cybernet_min_hours(self) -> float:
        return round(
            self.cybernet_count * _minutes_to_hours(CYBERNET_DETAILED_MIN_MINUTES),
            10,
        )

    @property
    def cybernet_max_hours(self) -> float:
        return round(
            self.cybernet_count * _minutes_to_hours(CYBERNET_DETAILED_MAX_MINUTES),
            10,
        )

    @property
    def direct_configuration_min_hours(self) -> float:
        return round(self.neuron_normalized_hours + self.cybernet_min_hours, 10)

    @property
    def direct_configuration_max_hours(self) -> float:
        return round(self.neuron_normalized_hours + self.cybernet_max_hours, 10)

    @property
    def paired_workstation_count(self) -> int:
        """Number of complete Cybernet+Neuron pairs supported by both counts."""

        return min(self.neuron_count, self.cybernet_count)

    def neuron_detailed_range_hours(
        self,
        *,
        include_separate_rename: bool = False,
    ) -> tuple[float, float]:
        min_minutes = NEURON_DETAILED_MIN_MINUTES
        max_minutes = NEURON_DETAILED_MAX_MINUTES
        if include_separate_rename:
            min_minutes += NEURON_RENAME_MIN_MINUTES
            max_minutes += NEURON_RENAME_MAX_MINUTES
        return (
            round(self.neuron_count * _minutes_to_hours(min_minutes), 10),
            round(self.neuron_count * _minutes_to_hours(max_minutes), 10),
        )

    def audit_record(self) -> dict[str, float | int]:
        return {
            "neuron_count": self.neuron_count,
            "cybernet_count": self.cybernet_count,
            "paired_workstation_count": self.paired_workstation_count,
            "neuron_normalized_hours_per_device": NEURON_NORMALIZED_HOURS,
            "neuron_normalized_hours": self.neuron_normalized_hours,
            "neuron_detailed_min_minutes_per_device": NEURON_DETAILED_MIN_MINUTES,
            "neuron_detailed_max_minutes_per_device": NEURON_DETAILED_MAX_MINUTES,
            "neuron_rename_min_minutes_per_device": NEURON_RENAME_MIN_MINUTES,
            "neuron_rename_max_minutes_per_device": NEURON_RENAME_MAX_MINUTES,
            "cybernet_detailed_min_minutes_per_device": CYBERNET_DETAILED_MIN_MINUTES,
            "cybernet_detailed_max_minutes_per_device": CYBERNET_DETAILED_MAX_MINUTES,
            "cybernet_min_hours": self.cybernet_min_hours,
            "cybernet_max_hours": self.cybernet_max_hours,
            "direct_configuration_min_hours": self.direct_configuration_min_hours,
            "direct_configuration_max_hours": self.direct_configuration_max_hours,
        }


@dataclass(frozen=True)
class EvidenceBoundedAllocation:
    """Bound a task allocation by labor and independently supported Configuration scope.

    ``workstations`` must be a confirmed Configuration population. Callers must
    explicitly declare ``scope_kind='configuration_count'``. Testing / IDT,
    target, installation, or generic remaining-work counts fail closed instead of
    being silently converted into Configuration labor.

    Confirmed Configuration evidence may establish that enough Configuration work
    existed to support a larger share of a labor window. It must never create
    labor hours beyond the selected historical labor source of truth.
    """

    workstations: int
    devices_per_workstation: int
    direct_hours_per_device: float
    attendance_hours: float
    scope_kind: str
    explicit_non_configuration_hours: float = 0.0

    def __post_init__(self) -> None:
        if self.scope_kind != CONFIGURATION_COUNT_SCOPE:
            raise ValueError(
                "scope_kind must be 'configuration_count'; testing/IDT, target, "
                "installation, and generic remaining-work counts cannot be used "
                "as Configuration multipliers"
            )
        if self.workstations < 0:
            raise ValueError("workstations must be >= 0")
        if self.devices_per_workstation <= 0:
            raise ValueError("devices_per_workstation must be > 0")
        for field_name in (
            "direct_hours_per_device",
            "attendance_hours",
            "explicit_non_configuration_hours",
        ):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
            if value < 0:
                raise ValueError(f"{field_name} must be >= 0")
        if self.explicit_non_configuration_hours > self.attendance_hours:
            raise ValueError(
                "explicit_non_configuration_hours cannot exceed attendance_hours"
            )

    @property
    def device_count(self) -> int:
        return self.workstations * self.devices_per_workstation

    @property
    def configuration_workload_envelope_hours(self) -> float:
        """Confirmed-population direct Configuration capacity; not labor total."""

        return round(self.device_count * self.direct_hours_per_device, 10)

    @property
    def attendance_remaining_after_explicit_non_configuration(self) -> float:
        return round(
            self.attendance_hours - self.explicit_non_configuration_hours,
            10,
        )

    @property
    def max_defensible_configuration_hours(self) -> float:
        """Largest Configuration allocation allowed by both evidence ceilings.

        This is a ceiling, not a target. Stronger dated evidence can require a lower
        Configuration allocation.
        """

        return round(
            min(
                self.configuration_workload_envelope_hours,
                self.attendance_remaining_after_explicit_non_configuration,
            ),
            10,
        )

    def audit_record(self) -> dict[str, float | int | str]:
        return {
            "scope_kind": self.scope_kind,
            "workstations": self.workstations,
            "devices_per_workstation": self.devices_per_workstation,
            "device_count": self.device_count,
            "direct_hours_per_device": self.direct_hours_per_device,
            "configuration_workload_envelope_hours": self.configuration_workload_envelope_hours,
            "attendance_hours": self.attendance_hours,
            "explicit_non_configuration_hours": self.explicit_non_configuration_hours,
            "attendance_remaining_after_explicit_non_configuration": self.attendance_remaining_after_explicit_non_configuration,
            "max_defensible_configuration_hours": self.max_defensible_configuration_hours,
        }


@dataclass(frozen=True)
class AllocationComponent:
    """One evidence-labeled component inside a single attendance-controlled day.

    Component hours allocate already-proven attendance; they never establish paid
    hours by themselves. Zero-hour placeholders belong in planning/current-state
    records rather than in a closed allocation.
    """

    allocation_id: str
    staff_key: str
    work_date: date
    workstream: str
    hours: float
    authority: str
    evidence_refs: tuple[str, ...]
    internal_only: bool = True
    derivation: str | None = None

    def __post_init__(self) -> None:
        _non_empty(self.allocation_id, "allocation_id")
        _non_empty(self.staff_key, "staff_key")
        _calendar_date(self.work_date)
        _non_empty(self.workstream, "workstream")
        _positive_finite(self.hours, "hours")
        if self.authority not in ALLOCATION_AUTHORITIES:
            raise ValueError(
                "authority must be one of: " + ", ".join(sorted(ALLOCATION_AUTHORITIES))
            )
        _evidence_tuple(self.evidence_refs, "evidence_refs")
        if not isinstance(self.internal_only, bool):
            raise ValueError("internal_only must be boolean")
        if self.authority in {
            DIRECT_SPAN_INTERNAL_CONTROL_AUTHORITY,
            REPORTED_INTERNAL_ALLOCATION_AUTHORITY,
            DERIVED_INTERNAL_MANAGEMENT_AUTHORITY,
        } and not self.internal_only:
            raise ValueError(f"{self.authority} must remain internal_only")
        if self.authority == DERIVED_INTERNAL_MANAGEMENT_AUTHORITY:
            if not self.derivation or not str(self.derivation).strip():
                raise ValueError("derived_internal_management requires derivation")
        elif self.derivation is not None and not str(self.derivation).strip():
            raise ValueError("derivation cannot be blank")

    @property
    def staff_date_key(self) -> tuple[str, str]:
        return _staff_date_key(self.staff_key, self.work_date)

    def audit_record(self) -> dict[str, object]:
        return {
            "allocation_id": self.allocation_id,
            "staff_key": self.staff_key,
            "work_date": _calendar_date(self.work_date).isoformat(),
            "workstream": self.workstream,
            "hours": float(self.hours),
            "authority": self.authority,
            "evidence_refs": list(self.evidence_refs),
            "internal_only": self.internal_only,
            "derivation": self.derivation,
            "paid_hours_authority": False,
        }


def derive_internal_management_remainder(
    *,
    allocation_id: str,
    staff_key: str,
    work_date: date,
    workstream: str,
    attendance_hours: float,
    committed_components: Iterable[AllocationComponent],
    evidence_refs: tuple[str, ...],
) -> AllocationComponent:
    """Create the positive remainder of attendance as an explicitly derived allocation.

    The returned component is internal-only and labels its arithmetic. It is not
    transformed into direct task evidence merely because it closes the day.
    """

    attendance = _positive_finite(attendance_hours, "attendance_hours")
    components = tuple(committed_components)
    if not components:
        raise ValueError("committed_components must not be empty")
    expected_key = _staff_date_key(staff_key, work_date)
    for component in components:
        if component.staff_date_key != expected_key:
            raise ValueError("committed component staff/date must match remainder staff/date")
    committed = round(sum(float(component.hours) for component in components), 10)
    remainder = round(attendance - committed, 10)
    if remainder <= ALLOCATION_RECONCILIATION_TOLERANCE:
        raise ValueError("derived remainder must be > 0 after committed components")
    return AllocationComponent(
        allocation_id=allocation_id,
        staff_key=staff_key,
        work_date=work_date,
        workstream=workstream,
        hours=remainder,
        authority=DERIVED_INTERNAL_MANAGEMENT_AUTHORITY,
        evidence_refs=evidence_refs,
        internal_only=True,
        derivation=(
            f"attendance_hours({attendance:g}) - committed_component_hours({committed:g})"
        ),
    )


@dataclass(frozen=True)
class ClosedAttendanceAllocation:
    """A closed staff/date allocation that must exactly reconcile to attendance.

    Multiple project/workstream components are allowed inside one day. What is
    forbidden is a duplicate component ID or a second closed record for the same
    normalized staff/date, either of which can double-count the labor control.
    """

    staff_key: str
    work_date: date
    attendance_hours: float
    attendance_evidence_refs: tuple[str, ...]
    components: tuple[AllocationComponent, ...]

    def __post_init__(self) -> None:
        _non_empty(self.staff_key, "staff_key")
        _calendar_date(self.work_date)
        attendance = _positive_finite(self.attendance_hours, "attendance_hours")
        _evidence_tuple(self.attendance_evidence_refs, "attendance_evidence_refs")
        if not isinstance(self.components, tuple) or not self.components:
            raise ValueError("components must be a non-empty tuple")

        expected_key = self.staff_date_key
        seen_ids: set[str] = set()
        for component in self.components:
            allocation_id = _non_empty(component.allocation_id, "allocation_id")
            if allocation_id in seen_ids:
                raise ValueError(f"duplicate allocation_id: {allocation_id}")
            seen_ids.add(allocation_id)
            if component.staff_date_key != expected_key:
                raise ValueError("all components must match the closed staff/date")

        allocated = self.allocated_hours
        if not math.isclose(
            allocated,
            attendance,
            rel_tol=0.0,
            abs_tol=ALLOCATION_RECONCILIATION_TOLERANCE,
        ):
            raise ValueError(
                "closed allocation hours must reconcile exactly to attendance_hours; "
                f"allocated={allocated:g}, attendance={attendance:g}"
            )

    @property
    def staff_date_key(self) -> tuple[str, str]:
        return _staff_date_key(self.staff_key, self.work_date)

    @property
    def allocated_hours(self) -> float:
        return round(sum(float(component.hours) for component in self.components), 10)

    def audit_record(self) -> dict[str, object]:
        return {
            "status": "closed",
            "staff_key": self.staff_key,
            "work_date": _calendar_date(self.work_date).isoformat(),
            "attendance_hours": float(self.attendance_hours),
            "attendance_evidence_refs": list(self.attendance_evidence_refs),
            "allocated_hours": self.allocated_hours,
            "reconciled_to_attendance": True,
            "components": [component.audit_record() for component in self.components],
        }


def validate_closed_allocation_set(
    days: Iterable[ClosedAttendanceAllocation],
) -> tuple[ClosedAttendanceAllocation, ...]:
    """Reject duplicate closed staff/date records and duplicate allocation IDs."""

    closed_days = tuple(days)
    seen_staff_dates: set[tuple[str, str]] = set()
    seen_allocation_ids: set[str] = set()
    for day in closed_days:
        if day.staff_date_key in seen_staff_dates:
            staff, work_date = day.staff_date_key
            raise ValueError(f"duplicate closed allocation for staff/date: {staff}/{work_date}")
        seen_staff_dates.add(day.staff_date_key)
        for component in day.components:
            allocation_id = _non_empty(component.allocation_id, "allocation_id")
            if allocation_id in seen_allocation_ids:
                raise ValueError(
                    f"duplicate allocation_id across closed records: {allocation_id}"
                )
            seen_allocation_ids.add(allocation_id)
    return closed_days
