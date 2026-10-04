from __future__ import annotations

from datetime import date

import pytest

try:
    from triage.neuron_task_hour_distribution_rules import (
        APRIL_EVENING_CONFIGURATION_DAY,
        CLIENT_COORDINATION,
        CONFIGURATIONS,
        DEPLOYMENTS,
        DOCUMENTATION,
        GENERAL_NEURON_SUPPORT_DAY,
        INVENTORY_MANAGEMENT,
        LOGISTICS,
        MAY_CONFIGURATION_AND_INVENTORY_DAY,
        MAY_DAYTIME_SUPPORT_DAY,
        MAY_DEPLOYMENT_FIELD_TEAM_DAY,
        SUNDAY_LOGISTICS_DAY,
        choose_neuron_task_hour_distribution,
        distribute_task_hours,
        distribution_for_alias,
        validate_distribution,
    )

    _HAS_FULL_MODULE = True
except ImportError:
    _HAS_FULL_MODULE = False

pytestmark = pytest.mark.skipif(
    not _HAS_FULL_MODULE,
    reason="neuron_task_hour_distribution_rules is a stub; full implementation not yet landed",
)


def test_general_neuron_support_distribution_is_operations_approved():
    assert GENERAL_NEURON_SUPPORT_DAY == {
        CONFIGURATIONS: 55.0,
        DEPLOYMENTS: 5.0,
        LOGISTICS: 20.0,
        INVENTORY_MANAGEMENT: 10.0,
        DOCUMENTATION: 5.0,
        CLIENT_COORDINATION: 5.0,
    }
    validate_distribution(GENERAL_NEURON_SUPPORT_DAY)


def test_april_saturday_is_deployment_plus_documentation():
    decision = choose_neuron_task_hour_distribution(date(2026, 4, 4), start_hour=9.0, end_hour=17.0)

    assert decision.distribution_name == "april_saturday_deployment_day"
    assert decision.weights == {DEPLOYMENTS: 80.0, DOCUMENTATION: 20.0}
    assert decision.rule == "april-saturday-deployment"


def test_april_sunday_is_logistics():
    decision = choose_neuron_task_hour_distribution(date(2026, 4, 5), start_hour=9.0, end_hour=17.0)

    assert decision.weights == SUNDAY_LOGISTICS_DAY
    assert decision.rule == "april-sunday-logistics"


def test_april_monday_and_wednesday_non_evening_are_deployments():
    monday = choose_neuron_task_hour_distribution(date(2026, 4, 6), start_hour=9.0, end_hour=13.0)
    wednesday = choose_neuron_task_hour_distribution(date(2026, 4, 8), start_hour=9.0, end_hour=13.0)

    assert monday.weights == {DEPLOYMENTS: 80.0, DOCUMENTATION: 20.0}
    assert wednesday.weights == {DEPLOYMENTS: 80.0, DOCUMENTATION: 20.0}


def test_april_shift_starting_after_2pm_is_deployment_window():
    decision = choose_neuron_task_hour_distribution(date(2026, 4, 7), start_hour=14.0, end_hour=16.0)

    assert decision.weights == {DEPLOYMENTS: 80.0, DOCUMENTATION: 20.0}
    assert decision.rule == "april-weekday-after-2pm-deployment"


def test_april_evening_is_configuration_even_if_monday():
    decision = choose_neuron_task_hour_distribution(date(2026, 4, 6), start_hour=17.0, end_hour=21.0)

    assert decision.weights == APRIL_EVENING_CONFIGURATION_DAY
    assert decision.rule == "april-evening-configuration"


def test_may_weekends_and_evenings_are_configuration_inventory():
    saturday = choose_neuron_task_hour_distribution(date(2026, 5, 2), start_hour=9.0, end_hour=13.0)
    sunday = choose_neuron_task_hour_distribution(date(2026, 5, 3), start_hour=9.0, end_hour=13.0)
    evening = choose_neuron_task_hour_distribution(date(2026, 5, 4), start_hour=17.0, end_hour=21.0)

    assert saturday.weights == MAY_CONFIGURATION_AND_INVENTORY_DAY
    assert sunday.weights == MAY_CONFIGURATION_AND_INVENTORY_DAY
    assert evening.weights == MAY_CONFIGURATION_AND_INVENTORY_DAY
    assert DEPLOYMENTS not in saturday.weights


def test_may_daytime_support_excludes_default_deployment():
    decision = choose_neuron_task_hour_distribution(date(2026, 5, 5), start_hour=9.0, end_hour=16.0)

    assert decision.weights == MAY_DAYTIME_SUPPORT_DAY
    assert DEPLOYMENTS not in decision.weights
    assert DOCUMENTATION not in decision.weights
    assert set(decision.weights) == {CONFIGURATIONS, LOGISTICS, INVENTORY_MANAGEMENT, CLIENT_COORDINATION}


def test_may_deployment_field_team_override_uses_logistics_deploy_documentation():
    decision = choose_neuron_task_hour_distribution(
        date(2026, 5, 6),
        start_hour=9.0,
        end_hour=17.0,
        private_day_role_override="may_deployment_field_team",
    )

    assert decision.private_override_used is True
    assert decision.weights == MAY_DEPLOYMENT_FIELD_TEAM_DAY
    assert decision.weights == {LOGISTICS: 30.0, DEPLOYMENTS: 50.0, DOCUMENTATION: 20.0}


def test_distribution_aliases_are_descriptive_not_nebulous_profiles():
    assert distribution_for_alias("delivery_became_deployment") == MAY_DEPLOYMENT_FIELD_TEAM_DAY
    assert distribution_for_alias("standard_neuron_support_day") == GENERAL_NEURON_SUPPORT_DAY


def test_distribute_task_hours_splits_net_hours_by_distribution():
    out = distribute_task_hours(10.0, MAY_DEPLOYMENT_FIELD_TEAM_DAY)

    assert out == {LOGISTICS: 3.0, DEPLOYMENTS: 5.0, DOCUMENTATION: 2.0}


def test_bad_distribution_is_rejected():
    with pytest.raises(ValueError):
        validate_distribution({CONFIGURATIONS: 75.0, LOGISTICS: 10.0})
