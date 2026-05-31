from datetime import date, time

from triage.billing_context.context_rules import (
    RULES_DOC,
    classify_from_task_text,
    is_placeholder_assignment,
    resolve_work_context,
)


def test_module_docstring_references_rules_doc():
    import triage.billing_context.context_rules as mod

    assert RULES_DOC in mod.__doc__


def test_placeholder_assignment_detected():
    assert is_placeholder_assignment("Neuron Installation")
    assert is_placeholder_assignment("install")
    assert not is_placeholder_assignment("Configuration")


def test_task_text_beats_placeholder():
    context, reason, confidence = resolve_work_context(
        assignment="Neuron Installation",
        task_text="Configured devices and staged inventory for go-live.",
        work_date=date(2026, 5, 12),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    assert context == "Configuration"
    assert confidence == "high"


def test_required_not_ticket_coordination():
    context, _, _ = classify_from_task_text("This is required reading for all techs")
    assert context != "Ticket Coordination"


def test_ten_pm_not_client_coordination():
    context, _, _ = classify_from_task_text("Worked until 10pm on staging")
    assert context != "Client Coordination"


def test_assignment_task_conflict():
    context, reason, _ = resolve_work_context(
        assignment="Configuration",
        task_text="Deployed floor support for go-live.",
        work_date=date(2026, 5, 12),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    assert context == "Unknown / Needs Review"
    assert "disagree" in reason.lower()


def test_may_saturday_rule():
    context, _, _ = resolve_work_context(
        assignment="Neuron Installation",
        task_text="",
        work_date=date(2026, 5, 30),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    assert context == "Inventory Management"


def test_april_saturday_rule():
    context, _, _ = resolve_work_context(
        assignment="Neuron Installation",
        task_text="",
        work_date=date(2026, 4, 25),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    assert context == "Deployment Support"


def test_evening_rule_inventory_management():
    context, _, _ = resolve_work_context(
        assignment="Neuron Installation",
        task_text="",
        work_date=date(2026, 5, 14),
        start_time=time(18, 0),
        end_time=time(22, 0),
    )
    assert context == "Inventory Management"
    assert context != "Logistics"


def test_sunday_logistics():
    context, _, _ = resolve_work_context(
        assignment="Neuron Installation",
        task_text="",
        work_date=date(2026, 5, 31),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    assert context == "Logistics"
