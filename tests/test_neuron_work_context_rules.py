"""Branch coverage for triage.neuron_work_context_rules.classify_neuron_work_context.

Pure-time tests pass empty text so no explicit signal fires; the resolved
project deliberately omits "Neuron Deployments" because the word "deployment"
is itself a DEPLOYMENTS signal.
"""
from __future__ import annotations

from datetime import date

from triage.neuron_work_context_rules import (
    CLIENT_COORDINATION,
    CONFIGURATIONS,
    DEPLOYMENTS,
    DOCUMENTATION,
    INVENTORY_MANAGEMENT,
    LOGISTICS,
    TICKET_FORWARDING,
    TROUBLESHOOTING,
    classify_neuron_work_context,
)


def _c(work_date, start, end, notes="", worked_label="", resolved_project=""):
    return classify_neuron_work_context(
        work_date=work_date,
        start_hour=start,
        end_hour=end,
        notes=notes,
        worked_label=worked_label,
        resolved_project=resolved_project,
    )


# ── explicit text signals (highest precedence) ─────────────────────────────────

def test_daytime_logistics_signal():
    d = _c(date(2026, 3, 3), 8.0, 16.0, notes="logistics relay")
    assert d.assignment_type == LOGISTICS
    assert d.rule == "explicit-logistics-daytime"


def test_evening_logistics_falls_back_to_config():
    d = _c(date(2026, 3, 3), 17.0, 22.0, notes="logistics relay")
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "logistics-signal-outside-daytime-config-fallback"


def test_explicit_troubleshooting_signal_beats_time():
    d = _c(date(2026, 3, 3), 8.0, 9.0, notes="imprivata login issue")
    assert d.assignment_type == TROUBLESHOOTING


def test_explicit_documentation_signal():
    d = _c(date(2026, 3, 3), 8.0, 12.0, notes="sign-off summary handoff")
    assert d.assignment_type == DOCUMENTATION


def test_explicit_deploy_note_beats_time_heuristic():
    # Wednesday morning would otherwise be ticket forwarding.
    d = _c(date(2026, 3, 4), 10.0, 14.0, notes="go-live cutover")
    assert d.assignment_type == DEPLOYMENTS
    assert d.rule == "explicit-deployment"


# ── April month rules ──────────────────────────────────────────────────────────

def test_april_saturday_is_deployments():
    d = _c(date(2026, 4, 4), 9.0, 17.0)
    assert d.assignment_type == DEPLOYMENTS
    assert d.rule == "april-saturday-deployment"


def test_april_monday_evening_is_deployments():
    d = _c(date(2026, 4, 6), 17.0, 21.0)
    assert d.assignment_type == DEPLOYMENTS
    assert d.rule == "april-mon-wed-evening-deployment"


def test_april_wednesday_evening_is_deployments():
    d = _c(date(2026, 4, 8), 18.0, 22.0)
    assert d.assignment_type == DEPLOYMENTS


def test_april_tuesday_evening_is_configurations():
    d = _c(date(2026, 4, 7), 17.0, 21.0)
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "april-evening-configuration"


# ── May month rules ──────────────────────────────────────────────────────────

def test_may_weekend_morning_is_inventory():
    d = _c(date(2026, 5, 2), 8.0, 12.0)
    assert d.assignment_type == INVENTORY_MANAGEMENT
    assert d.rule == "may-weekend-inventory"


def test_may_weekend_evening_is_configurations():
    d = _c(date(2026, 5, 3), 17.0, 22.0)
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "may-weekend-configuration"


def test_may_weekday_evening_is_configurations():
    d = _c(date(2026, 5, 5), 17.0, 21.0)
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "may-evening-configuration"


# ── time-of-day fallback (non-April/May) ───────────────────────────────────────

def test_weekday_morning_is_ticket_forwarding():
    d = _c(date(2026, 3, 3), 8.0, 9.5)
    assert d.assignment_type == TICKET_FORWARDING
    assert d.rule == "morning-ticket-forwarding"


def test_daytime_midday_is_inventory_management():
    d = _c(date(2026, 3, 3), 10.0, 14.0)
    assert d.assignment_type == INVENTORY_MANAGEMENT
    assert d.rule == "daytime-inventory-management"


def test_weekday_afternoon_is_client_coordination():
    d = _c(date(2026, 3, 3), 12.0, 16.0)
    assert d.assignment_type == CLIENT_COORDINATION
    assert d.rule == "afternoon-client-coordination"


def test_full_shift_overlapping_evening_is_configurations():
    d = _c(date(2026, 3, 3), 9.0, 18.0)
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "full-shift-overlaps-configuration-window"


def test_no_times_defaults_to_configurations_low_confidence():
    d = _c(date(2026, 3, 3), None, None)
    assert d.assignment_type == CONFIGURATIONS
    assert d.rule == "default-configuration-dominant"
    assert d.confidence == "low"
