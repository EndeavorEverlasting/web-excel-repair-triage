#!/usr/bin/env python3
"""Deterministic execution-boundary decision engine used by retained regression fixtures."""
from __future__ import annotations

from typing import Any


class BoundaryEngineError(ValueError):
    pass


FALLBACK_CLASS = "UE_UNCLASSIFIED_MATERIAL_BOUNDARY"
PRIMARY_RECOVERY_SPRINT_STATE = "PRIMARY_RECOVERY_SPRINT_OPENED"
PRIMARY_RECOVERY_SPRINT_FIELDS = (
    "trigger_event_id",
    "parent_objective_id",
    "preserved_outcome",
    "bounded_owned_scope",
    "first_executable_action",
    "completion_gate",
    "return_condition",
)
SPRINT_EXEMPT_CLASSES = {"UC_CANCELLED"}
NORMAL_PATH_PREFIX = [
    "BOUNDARY_OBSERVED",
    "BOUNDARY_CLASSIFIED",
    "CHECKPOINTED",
    "PUBLIC_TRANSITION_EMITTED",
    "RECOVERY_SELECTED",
]
BLOCKED_RECOVERIES = {
    "QUIESCE_UNCHANGED_BLOCKER",
    "WAIT_ON_EXTERNAL_GATE_WITH_DURABLE_HANDOFF",
    "REQUEST_REQUIRED_AUTHORIZATION",
    "HANDOFF_REQUIRED_SUCCESSOR",
    "ABORT_UNSAFE_MUTATION",
}
READBACK_RECOVERIES = {"READ_AFTER_WRITE_RECONCILE"}
REQUIRED_PUBLIC_FIELDS = ["BOUNDARY", "IMPACT", "PROVED", "RECOVERY", "NEXT"]


def _taxonomy_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for family in taxonomy.get("families", []):
        for item in family.get("classes", []):
            class_id = item.get("id")
            if isinstance(class_id, str) and class_id:
                index[class_id] = item
    if FALLBACK_CLASS not in index:
        raise BoundaryEngineError("fallback taxonomy class missing")
    return index


def _layer_ids(architecture: dict[str, Any]) -> set[str]:
    return {
        str(layer.get("id"))
        for layer in architecture.get("architecture_layers", [])
        if isinstance(layer, dict) and layer.get("id")
    }


def _assert_path_supported(path: list[str], architecture: dict[str, Any]) -> None:
    allowed = architecture.get("state_machine", {}).get("allowed_transitions", {})
    if not isinstance(allowed, dict):
        raise BoundaryEngineError("state-machine transitions missing")
    for before, after in zip(path, path[1:]):
        if after not in allowed.get(before, []):
            raise BoundaryEngineError(
                f"state-machine transition unavailable: {before} -> {after}"
            )


def _primary_recovery_sprint(
    input_event: dict[str, Any],
    architecture: dict[str, Any],
    classification: str,
    recovery: str,
    *,
    material: bool,
    hard_termination: bool,
) -> dict[str, str] | None:
    if not material or hard_termination or classification in SPRINT_EXEMPT_CLASSES:
        return None

    contract = architecture.get("boundary_sprint_contract")
    if not isinstance(contract, dict):
        raise BoundaryEngineError("universal boundary sprint contract missing")
    if contract.get("state_transition") != PRIMARY_RECOVERY_SPRINT_STATE:
        raise BoundaryEngineError("boundary sprint state transition drifted")
    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list) or set(required_fields) != set(PRIMARY_RECOVERY_SPRINT_FIELDS):
        raise BoundaryEngineError("boundary sprint required fields drifted")

    event_id = input_event.get("event_id")
    if not isinstance(event_id, str) or not event_id.strip():
        event_id = f"BOUNDARY:{classification}"
    event_id = event_id.strip()
    if len(event_id) > 128:
        raise BoundaryEngineError("boundary event id exceeds bounded sprint identity")

    sprint = {
        "trigger_event_id": event_id,
        "parent_objective_id": "ACTIVE_OBJECTIVE",
        "preserved_outcome": "PRESERVE_PARENT_OBJECTIVE",
        "bounded_owned_scope": "BOUNDARY_RECOVERY_ONLY",
        "first_executable_action": recovery,
        "completion_gate": "RECOVERY_APPLIED_OR_EXACT_BLOCKER_PROVEN",
        "return_condition": "PARENT_OBJECTIVE_RESUMED_OR_EXACT_GATE_RETAINED",
    }
    if set(sprint) != set(PRIMARY_RECOVERY_SPRINT_FIELDS):
        raise BoundaryEngineError("primary recovery sprint shape drifted")
    return sprint


def evaluate_boundary(
    input_event: dict[str, Any],
    architecture: dict[str, Any],
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(input_event, dict):
        raise BoundaryEngineError("input event must be an object")
    index = _taxonomy_index(taxonomy)
    observed = str(input_event.get("observed_classification", "")).strip()
    classification = observed if observed in index else FALLBACK_CLASS
    if input_event.get("process_alive") is False and not classification.startswith("HT_"):
        classification = "HT_HOST_FORCED_TERMINATION"
    spec = index[classification]
    materiality = spec.get("default_materiality")
    recovery = spec.get("default_recovery")
    if materiality not in taxonomy.get("materiality_levels", {}):
        raise BoundaryEngineError(f"invalid class materiality: {classification}")
    if recovery not in taxonomy.get("recovery_dispositions", []):
        raise BoundaryEngineError(f"invalid class recovery: {classification}")

    material = materiality in {"MATERIAL", "CRITICAL"}
    hard_termination = classification.startswith("HT_") or input_event.get("process_alive") is False
    primary_sprint = _primary_recovery_sprint(
        input_event,
        architecture,
        classification,
        recovery,
        material=material,
        hard_termination=hard_termination,
    )
    layers = _layer_ids(architecture)

    if hard_termination:
        path = ["HARD_TERMINATED_SYNTHETIC"]
        supervisor = architecture.get("external_supervisor_contract")
        supervisor_synthesized = isinstance(supervisor, dict) and bool(supervisor.get("rules"))
    else:
        final_state = (
            "QUIESCENT_BLOCKED"
            if recovery in BLOCKED_RECOVERIES
            else "RECOVERING"
        )
        path = [*NORMAL_PATH_PREFIX]
        if primary_sprint is not None:
            path.append(PRIMARY_RECOVERY_SPRINT_STATE)
        path.append(final_state)
        _assert_path_supported(path, architecture)
        supervisor_synthesized = False

    public_fields = architecture.get("public_transition_contract", {}).get("required_fields")
    publisher_available = (
        "public_transition_publisher" in layers
        and public_fields == REQUIRED_PUBLIC_FIELDS
    )
    journal_available = "append_only_journal" in layers
    outbox_available = "durable_transition_outbox" in layers

    repository_available = bool(input_event.get("repository_available", True))
    repository_relevant = bool(input_event.get("repository_relevant", True))
    primary_sprint_required = primary_sprint is not None

    return {
        "classification": classification,
        "materiality": materiality,
        "recovery_disposition": recovery,
        "execution_path": path,
        "checkpoint_required": material,
        "journal_required": material and journal_available,
        "outbox_required": material and outbox_available,
        "public_transition_required": material and publisher_available,
        "repository_persistence_required": material and repository_available and repository_relevant,
        "readback_required": recovery in READBACK_RECOVERIES,
        "redaction_required": classification in {
            "SP_SECRET_OR_PRIVATE_EXPOSURE_RISK",
            "SP_SAFETY_CLASSIFIER_GATE",
        },
        "supervisor_synthesized": hard_termination and supervisor_synthesized,
        "taxonomy_evolution_required": classification == FALLBACK_CLASS,
        "primary_recovery_sprint_required": primary_sprint_required,
        "first_action_execution_required": primary_sprint_required,
        "primary_recovery_sprint": primary_sprint,
        "success_terminal": False,
    }


def assert_case(
    case: dict[str, Any],
    architecture: dict[str, Any],
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    actual = evaluate_boundary(case["input_event"], architecture, taxonomy)
    expected = case["expected_output"]
    if actual != expected:
        raise BoundaryEngineError(
            f"{case.get('case_id', '<unknown>')} executable expectation drift: "
            f"expected={expected!r} actual={actual!r}"
        )
    for forbidden in case.get("forbidden_outputs", []):
        field = forbidden.get("field")
        if field not in actual:
            raise BoundaryEngineError(
                f"{case.get('case_id', '<unknown>')} forbidden field unknown: {field}"
            )
        if actual[field] == forbidden.get("value"):
            raise BoundaryEngineError(
                f"{case.get('case_id', '<unknown>')} negative control violated: "
                f"{field} == {forbidden.get('value')!r}"
            )
    return actual
