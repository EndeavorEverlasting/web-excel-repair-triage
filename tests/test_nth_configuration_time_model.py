from __future__ import annotations

import pytest

from triage.nth_configuration_time_model import (
    ConfigurationTimeBasis,
    configuration_hours_range,
    paired_configuration_scenario,
    require_configuration_count_source,
)


def test_normalized_neuron_configuration_basis_is_1_5_hours():
    basis = ConfigurationTimeBasis()
    assert basis.neuron_normalized_hours == 1.5
    assert basis.neuron_detail_min_minutes == 56
    assert basis.neuron_detail_max_minutes == 88
    assert basis.neuron_detail_with_rename_minutes == (61, 98)


def test_cybernet_process_range_is_118_to_156_minutes():
    basis = ConfigurationTimeBasis()
    low, high = basis.cybernet_hours
    assert low == pytest.approx(118 / 60)
    assert high == pytest.approx(156 / 60)


def test_paired_workstation_range_is_3_47_to_4_10_hours():
    basis = ConfigurationTimeBasis()
    low, high = basis.paired_workstation_hours
    assert low == pytest.approx(3.4666666667)
    assert high == pytest.approx(4.1)


@pytest.mark.parametrize(
    "source_classification",
    ["device_testing", "idt_testing", "testing_remaining", "install_date_only"],
)
def test_non_configuration_sources_fail_closed(source_classification):
    with pytest.raises(ValueError):
        require_configuration_count_source(source_classification)


def test_device_testing_38_cannot_be_used_as_configuration_multiplier():
    with pytest.raises(ValueError):
        configuration_hours_range(
            cybernet_configurations=38,
            neuron_configurations=38,
            source_classification="device_testing",
        )


def test_confirmed_counts_translate_to_device_specific_hours():
    low, high = configuration_hours_range(
        cybernet_configurations=2,
        neuron_configurations=2,
        source_classification="configuration_list",
    )
    assert low == pytest.approx(6.9333333333)
    assert high == pytest.approx(8.2)


def test_scenario_translation_is_bounded_against_135_hour_historical_tracker():
    scenario = paired_configuration_scenario(4, historical_hours=135.0)
    assert scenario == {
        "paired_workstations": 4,
        "configuration_hours_low": 13.87,
        "configuration_hours_high": 16.4,
        "share_low_percent": 10.3,
        "share_high_percent": 12.1,
    }
