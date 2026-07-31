from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class EvidenceBoundedAllocation:
    """Bound a task allocation by attendance and independently supported workload scope.

    Device/workstation evidence may establish that enough Configuration work existed
    to support a larger share of an attendance window. It must never create labor
    hours beyond the attendance source of truth.
    """

    workstations: int
    devices_per_workstation: int
    direct_hours_per_device: float
    attendance_hours: float
    explicit_non_configuration_hours: float = 0.0

    def __post_init__(self) -> None:
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
        """Full-population direct Configuration capacity; not an attendance total."""

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

    def audit_record(self) -> dict[str, float | int]:
        return {
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
