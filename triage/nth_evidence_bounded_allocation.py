from __future__ import annotations

from dataclasses import dataclass
import math


CONFIGURATION_COUNT_SCOPE = "configuration_count"

NEURON_NORMALIZED_HOURS = 1.5
NEURON_DETAILED_MIN_MINUTES = 56
NEURON_DETAILED_MAX_MINUTES = 88
NEURON_RENAME_MIN_MINUTES = 5
NEURON_RENAME_MAX_MINUTES = 10
CYBERNET_DETAILED_MIN_MINUTES = 118
CYBERNET_DETAILED_MAX_MINUTES = 156


def _minutes_to_hours(minutes: int) -> float:
    return round(minutes / 60.0, 10)


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
