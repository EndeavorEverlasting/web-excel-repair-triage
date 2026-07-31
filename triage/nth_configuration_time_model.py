from __future__ import annotations

from dataclasses import dataclass
import math


_ALLOWED_CONFIGURATION_SOURCES = {
    "configuration_list",
    "dated_configuration_record",
    "operator_confirmed_configuration_count",
}

_FORBIDDEN_CONFIGURATION_SOURCES = {
    "device_testing",
    "idt_testing",
    "testing_remaining",
    "install_date_only",
}


@dataclass(frozen=True)
class ConfigurationTimeBasis:
    """Device-specific direct Configuration timing controls for NTH reconstruction."""

    neuron_normalized_hours: float = 1.5
    neuron_detail_min_minutes: int = 56
    neuron_detail_max_minutes: int = 88
    neuron_rename_min_minutes: int = 5
    neuron_rename_max_minutes: int = 10
    cybernet_min_minutes: int = 118
    cybernet_max_minutes: int = 156

    def __post_init__(self) -> None:
        numeric = (
            self.neuron_normalized_hours,
            self.neuron_detail_min_minutes,
            self.neuron_detail_max_minutes,
            self.neuron_rename_min_minutes,
            self.neuron_rename_max_minutes,
            self.cybernet_min_minutes,
            self.cybernet_max_minutes,
        )
        if any(float(value) < 0 or not math.isfinite(float(value)) for value in numeric):
            raise ValueError("configuration timing values must be finite and non-negative")
        if self.neuron_detail_min_minutes > self.neuron_detail_max_minutes:
            raise ValueError("Neuron detail minimum cannot exceed maximum")
        if self.neuron_rename_min_minutes > self.neuron_rename_max_minutes:
            raise ValueError("Neuron rename minimum cannot exceed maximum")
        if self.cybernet_min_minutes > self.cybernet_max_minutes:
            raise ValueError("Cybernet minimum cannot exceed maximum")

    @property
    def neuron_detail_hours(self) -> tuple[float, float]:
        return (
            self.neuron_detail_min_minutes / 60.0,
            self.neuron_detail_max_minutes / 60.0,
        )

    @property
    def neuron_detail_with_rename_minutes(self) -> tuple[int, int]:
        return (
            self.neuron_detail_min_minutes + self.neuron_rename_min_minutes,
            self.neuron_detail_max_minutes + self.neuron_rename_max_minutes,
        )

    @property
    def cybernet_hours(self) -> tuple[float, float]:
        return (
            self.cybernet_min_minutes / 60.0,
            self.cybernet_max_minutes / 60.0,
        )

    @property
    def paired_workstation_hours(self) -> tuple[float, float]:
        low, high = self.cybernet_hours
        return (
            round(low + self.neuron_normalized_hours, 10),
            round(high + self.neuron_normalized_hours, 10),
        )


def require_configuration_count_source(source_classification: str) -> None:
    """Fail closed when a non-Configuration source is used as a count multiplier."""

    normalized = source_classification.strip().lower()
    if normalized in _FORBIDDEN_CONFIGURATION_SOURCES:
        raise ValueError(
            f"{source_classification!r} cannot be used as a Configuration count source"
        )
    if normalized not in _ALLOWED_CONFIGURATION_SOURCES:
        raise ValueError(
            f"unsupported Configuration count source classification: {source_classification!r}"
        )


def configuration_hours_range(
    *,
    cybernet_configurations: int,
    neuron_configurations: int,
    source_classification: str,
    basis: ConfigurationTimeBasis | None = None,
) -> tuple[float, float]:
    """Translate confirmed configuration counts into a direct-hours range.

    Neurons use the normalized 1.5h allocation. Cybernets preserve the technician
    process range. Testing counts and install-date-only evidence are rejected.
    """

    require_configuration_count_source(source_classification)
    if not isinstance(cybernet_configurations, int) or cybernet_configurations < 0:
        raise ValueError("cybernet_configurations must be a non-negative integer")
    if not isinstance(neuron_configurations, int) or neuron_configurations < 0:
        raise ValueError("neuron_configurations must be a non-negative integer")

    basis = basis or ConfigurationTimeBasis()
    cyber_low, cyber_high = basis.cybernet_hours
    neuron_hours = basis.neuron_normalized_hours * neuron_configurations
    return (
        round(cyber_low * cybernet_configurations + neuron_hours, 10),
        round(cyber_high * cybernet_configurations + neuron_hours, 10),
    )


def paired_configuration_scenario(
    paired_workstations: int,
    *,
    historical_hours: float = 135.0,
    basis: ConfigurationTimeBasis | None = None,
) -> dict[str, float | int]:
    """Scenario math only; caller must not present paired_workstations as recovered fact."""

    if not isinstance(paired_workstations, int) or paired_workstations < 0:
        raise ValueError("paired_workstations must be a non-negative integer")
    if not math.isfinite(float(historical_hours)) or historical_hours <= 0:
        raise ValueError("historical_hours must be finite and > 0")

    basis = basis or ConfigurationTimeBasis()
    low_per_pair, high_per_pair = basis.paired_workstation_hours
    low = low_per_pair * paired_workstations
    high = high_per_pair * paired_workstations
    return {
        "paired_workstations": paired_workstations,
        "configuration_hours_low": round(low, 2),
        "configuration_hours_high": round(high, 2),
        "share_low_percent": round(low / historical_hours * 100.0, 1),
        "share_high_percent": round(high / historical_hours * 100.0, 1),
    }
