from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "harness/contracts/execution-boundary-enforcement.v1.json"
TAXONOMY = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"
MATRIX = ROOT / "harness/evals/execution-boundaries/boundary-regression-matrix.v1.json"
SHARED_POLICY = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"

MARKER = "EXECUTION BOUNDARY ACCOUNTABILITY CONTRACT"
REQUIRED_PUBLIC_FIELDS = ["BOUNDARY", "IMPACT", "PROVED", "RECOVERY", "NEXT"]
REQUIRED_LAYERS = {
    "objective_contract",
    "boundary_capture",
    "normalizer_classifier",
    "append_only_journal",
    "durable_transition_outbox",
    "public_transition_publisher",
    "recovery_router",
    "repository_publisher",
    "regression_learner",
    "finalization_gate",
    "external_supervisor",
}
REQUIRED_CASE_IDS = {
    "EBR-003",  # partial side effect
    "EBR-004",  # safety classifier
    "EBR-005",  # fanout ceiling
    "EBR-011",  # semantic abandonment
    "EBR-013",  # recovery does not erase disclosure
    "EBR-015",  # external hard termination
    "EBR-017",  # proof ceiling
    "EBR-020",  # no repository still discloses
}


class ExecutionBoundaryContractError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ExecutionBoundaryContractError(f"{path.name} must contain a JSON object")
    return data


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty(item) for item in value)


def validate_documents(
    architecture: dict[str, Any],
    taxonomy: dict[str, Any],
    matrix: dict[str, Any],
    shared_policy: dict[str, Any],
) -> dict[str, int]:
    if architecture.get("schema_version") != "execution-boundary-enforcement/v1":
        raise ExecutionBoundaryContractError("architecture schema_version mismatch")
    if architecture.get("contract_id") != "execution-boundary-enforcement":
        raise ExecutionBoundaryContractError("architecture contract_id mismatch")

    invariants = architecture.get("core_invariants")
    if not _string_list(invariants):
        raise ExecutionBoundaryContractError("architecture core invariants missing")
    invariant_text = " ".join(invariants).lower()
    for phrase in ("silence is never", "recovery does not cancel", "out-of-process supervisor"):
        if phrase not in invariant_text:
            raise ExecutionBoundaryContractError(f"architecture missing core invariant: {phrase}")

    states = architecture.get("execution_states")
    if not _string_list(states) or len(states) != len(set(states)):
        raise ExecutionBoundaryContractError("execution states must be a unique non-empty string list")
    for required in (
        "OBJECTIVE_ACTIVE",
        "BOUNDARY_OBSERVED",
        "CHECKPOINTED",
        "PUBLIC_TRANSITION_EMITTED",
        "RECOVERING",
        "FINALIZING",
        "COMPLETE",
        "HARD_TERMINATED_SYNTHETIC",
    ):
        if required not in states:
            raise ExecutionBoundaryContractError(f"required execution state missing: {required}")

    transitions = architecture.get("transition_invariants")
    if not _string_list(transitions):
        raise ExecutionBoundaryContractError("transition invariants missing")
    transition_text = " ".join(transitions)
    if "OBJECTIVE_ACTIVE may reach COMPLETE only through FINALIZING" not in transition_text:
        raise ExecutionBoundaryContractError("direct completion must be forbidden")
    if "PUBLIC_TRANSITION_EMITTED" not in transition_text:
        raise ExecutionBoundaryContractError("material boundary publication transition missing")
    if "external supervisor" not in transition_text.lower():
        raise ExecutionBoundaryContractError("hard termination must be externally supervised")

    envelope = architecture.get("boundary_event_envelope")
    if not isinstance(envelope, dict):
        raise ExecutionBoundaryContractError("boundary event envelope missing")
    required_fields = envelope.get("required_fields")
    expected_fields = {
        "event_id",
        "run_id",
        "objective_id",
        "observed_at",
        "detector",
        "classification_id",
        "materiality",
        "execution_state_before",
        "execution_state_after",
        "impact",
        "side_effect_state",
        "last_proven_checkpoint",
        "public_transition",
        "recovery_disposition",
        "next_action",
        "persistence_disposition",
        "proof_ceiling",
        "event_sequence",
        "dedupe_key",
        "causation_event_id",
        "publication_ack_state",
    }
    if not isinstance(required_fields, list) or set(required_fields) != expected_fields:
        raise ExecutionBoundaryContractError("boundary event envelope required fields drifted")

    layers = architecture.get("architecture_layers")
    if not isinstance(layers, list):
        raise ExecutionBoundaryContractError("architecture layers missing")
    layer_ids = [item.get("id") for item in layers if isinstance(item, dict)]
    if len(layer_ids) != len(set(layer_ids)) or set(layer_ids) != REQUIRED_LAYERS:
        raise ExecutionBoundaryContractError("architecture layer coverage drifted")


    machine = architecture.get("state_machine")
    if not isinstance(machine, dict):
        raise ExecutionBoundaryContractError("machine-readable state machine missing")
    allowed = machine.get("allowed_transitions")
    if not isinstance(allowed, dict) or set(allowed) != set(states):
        raise ExecutionBoundaryContractError("state-machine transition coverage drifted")
    if "COMPLETE" in allowed.get("OBJECTIVE_ACTIVE", []):
        raise ExecutionBoundaryContractError("state machine allows direct active-to-complete transition")
    if machine.get("success_state") != "COMPLETE":
        raise ExecutionBoundaryContractError("COMPLETE must remain the only success state")

    delivery = architecture.get("delivery_contract")
    if not isinstance(delivery, dict) or not _string_list(delivery.get("rules")):
        raise ExecutionBoundaryContractError("durable delivery/outbox contract missing")
    delivery_text = " ".join(delivery["rules"]).lower()
    for phrase in ("dedupe", "user-visible publication", "repository publication"):
        if phrase not in delivery_text:
            raise ExecutionBoundaryContractError(f"delivery contract missing semantic: {phrase}")

    dual_lane = architecture.get("dual_lane_policy")
    if not isinstance(dual_lane, dict) or not _string_list(dual_lane.get("ordering_rules")):
        raise ExecutionBoundaryContractError("dual-lane recovery/systemic sprint policy missing")

    public = architecture.get("public_transition_contract")
    if not isinstance(public, dict) or public.get("required_fields") != REQUIRED_PUBLIC_FIELDS:
        raise ExecutionBoundaryContractError("public transition shape must be BOUNDARY/IMPACT/PROVED/RECOVERY/NEXT")

    composition = architecture.get("composition")
    if not isinstance(composition, dict):
        raise ExecutionBoundaryContractError("composition map missing")
    for key, expected in (
        ("implementation_execution_owner", "P07"),
        ("recurring_process_owner", "P13"),
        ("regression_design_owner", "P94"),
        ("prompt_identity_owner", "P79"),
    ):
        if composition.get(key) != expected:
            raise ExecutionBoundaryContractError(f"composition owner drift: {key}")

    if taxonomy.get("schema_version") != "execution-boundary-taxonomy/v1":
        raise ExecutionBoundaryContractError("taxonomy schema_version mismatch")
    materiality = taxonomy.get("materiality_levels")
    if not isinstance(materiality, dict) or set(materiality) != {"INFO", "MATERIAL", "CRITICAL"}:
        raise ExecutionBoundaryContractError("taxonomy materiality levels drifted")
    recoveries = taxonomy.get("recovery_dispositions")
    terminals = taxonomy.get("terminal_dispositions")
    side_effects = taxonomy.get("side_effect_states")
    if not _string_list(recoveries) or len(recoveries) != len(set(recoveries)):
        raise ExecutionBoundaryContractError("recovery dispositions malformed")
    if not _string_list(terminals) or len(terminals) != len(set(terminals)):
        raise ExecutionBoundaryContractError("terminal dispositions malformed")
    if not _string_list(side_effects) or len(side_effects) != len(set(side_effects)):
        raise ExecutionBoundaryContractError("side-effect states malformed")

    families = taxonomy.get("families")
    if not isinstance(families, list) or len(families) < 10:
        raise ExecutionBoundaryContractError("taxonomy must retain broad family coverage")
    family_ids: set[str] = set()
    class_ids: set[str] = set()
    class_to_family: dict[str, str] = {}
    class_defaults: dict[str, tuple[str, str]] = {}
    for family in families:
        if not isinstance(family, dict) or not _nonempty(family.get("id")):
            raise ExecutionBoundaryContractError("taxonomy family malformed")
        family_id = family["id"]
        if family_id in family_ids:
            raise ExecutionBoundaryContractError(f"duplicate taxonomy family: {family_id}")
        family_ids.add(family_id)
        classes = family.get("classes")
        if not isinstance(classes, list) or not classes:
            raise ExecutionBoundaryContractError(f"taxonomy family has no classes: {family_id}")
        for item in classes:
            if not isinstance(item, dict):
                raise ExecutionBoundaryContractError(f"taxonomy class malformed in {family_id}")
            class_id = item.get("id")
            if not _nonempty(class_id):
                raise ExecutionBoundaryContractError(f"taxonomy class id missing in {family_id}")
            if class_id in class_ids:
                raise ExecutionBoundaryContractError(f"duplicate taxonomy class: {class_id}")
            class_ids.add(class_id)
            class_to_family[class_id] = family_id
            if item.get("default_materiality") not in materiality:
                raise ExecutionBoundaryContractError(f"invalid default materiality: {class_id}")
            if item.get("default_recovery") not in recoveries:
                raise ExecutionBoundaryContractError(f"invalid default recovery: {class_id}")
            if not _nonempty(item.get("description")):
                raise ExecutionBoundaryContractError(f"class description missing: {class_id}")
            class_defaults[class_id] = (item["default_materiality"], item["default_recovery"])

    for required_class in (
        "EC_SEMANTIC_ABANDONMENT",
        "EC_RECOVERY_NOT_DISCLOSED",
        "MT_PARTIAL_SIDE_EFFECT_POSSIBLE",
        "OR_FANOUT_OR_TOOLCALL_CEILING",
        "SP_SAFETY_CLASSIFIER_GATE",
        "VP_PROOF_CEILING_REACHED",
        "HT_HOST_FORCED_TERMINATION",
        "UE_UNCLASSIFIED_MATERIAL_BOUNDARY",
    ):
        if required_class not in class_ids:
            raise ExecutionBoundaryContractError(f"required boundary class missing: {required_class}")

    case_contract = matrix.get("case_contract")
    if not isinstance(case_contract, dict):
        raise ExecutionBoundaryContractError("regression case contract missing")
    required_case_fields = case_contract.get("required_fields")
    if not _string_list(required_case_fields):
        raise ExecutionBoundaryContractError("regression required fields missing")
    cases = matrix.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ExecutionBoundaryContractError("regression cases missing")
    if case_contract.get("minimum_cases") != len(cases):
        raise ExecutionBoundaryContractError("regression minimum_cases must equal retained case count")

    seen_case_ids: set[str] = set()
    covered_classes: set[str] = set()
    covered_families: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ExecutionBoundaryContractError("regression case must be object")
        missing = [field for field in required_case_fields if field not in case]
        if missing:
            raise ExecutionBoundaryContractError(f"regression case missing fields: {case.get('case_id')} {missing}")
        case_id = case.get("case_id")
        if not _nonempty(case_id) or case_id in seen_case_ids:
            raise ExecutionBoundaryContractError(f"duplicate or invalid case_id: {case_id}")
        seen_case_ids.add(case_id)
        classification = case.get("classification")
        if classification not in class_ids:
            raise ExecutionBoundaryContractError(f"unknown regression classification: {case_id} -> {classification}")
        covered_classes.add(classification)
        covered_families.add(class_to_family[classification])
        if case.get("expected_materiality") not in materiality:
            raise ExecutionBoundaryContractError(f"invalid regression materiality: {case_id}")
        if case.get("expected_recovery") not in recoveries:
            raise ExecutionBoundaryContractError(f"invalid regression recovery: {case_id}")
        if not _string_list(case.get("positive_assertions")):
            raise ExecutionBoundaryContractError(f"positive control missing: {case_id}")
        if not _string_list(case.get("negative_assertions")):
            raise ExecutionBoundaryContractError(f"negative control missing: {case_id}")
        if not _string_list(case.get("proof_surfaces")):
            raise ExecutionBoundaryContractError(f"proof surfaces missing: {case_id}")
        if not _nonempty(case.get("proof_ceiling")):
            raise ExecutionBoundaryContractError(f"proof ceiling missing: {case_id}")

    if covered_classes != class_ids:
        missing = sorted(class_ids - covered_classes)
        extra = sorted(covered_classes - class_ids)
        raise ExecutionBoundaryContractError(f"every canonical class requires regression coverage: missing={missing} extra={extra}")
    if covered_families != family_ids:
        raise ExecutionBoundaryContractError("every taxonomy family requires regression coverage")
    if not REQUIRED_CASE_IDS.issubset(seen_case_ids):
        raise ExecutionBoundaryContractError(f"critical bespoke regressions missing: {sorted(REQUIRED_CASE_IDS - seen_case_ids)}")

    # High-risk semantics must remain explicit rather than relying only on generated generic coverage.
    targeted = {case["case_id"]: case for case in cases}
    if targeted["EBR-003"]["expected_recovery"] != "READ_AFTER_WRITE_RECONCILE":
        raise ExecutionBoundaryContractError("partial-write case must reconcile before retry")
    if targeted["EBR-015"]["expected_recovery"] != "SYNTHESIZE_TERMINATION":
        raise ExecutionBoundaryContractError("hard-termination case must be supervisor-synthesized")
    recovery_case_text = " ".join(
        targeted["EBR-013"]["positive_assertions"] + targeted["EBR-013"]["negative_assertions"]
    ).lower()
    if "erase" not in recovery_case_text and "omit" not in recovery_case_text:
        raise ExecutionBoundaryContractError("successful recovery must not erase boundary disclosure")

    if shared_policy.get("applies_to") != "Every prompt in the combined canonical Prompt Kit registry.":
        raise ExecutionBoundaryContractError("shared policy must continue to apply to every prompt")
    suffix = shared_policy.get("next_step_suffix")
    appendix = shared_policy.get("copy_content_appendix")
    if not _nonempty(suffix) or not _nonempty(appendix):
        raise ExecutionBoundaryContractError("shared prompt policy surfaces missing")
    if MARKER not in suffix or MARKER not in appendix:
        raise ExecutionBoundaryContractError("boundary accountability marker missing from shared inheritance surfaces")
    for path in (
        "harness/contracts/execution-boundary-enforcement.v1.json",
        "harness/contracts/execution-boundary-taxonomy.v1.json",
    ):
        if path not in suffix and path not in appendix:
            raise ExecutionBoundaryContractError(f"shared prompt policy missing boundary contract reference: {path}")
    appendix_lower = appendix.lower()
    for phrase in (
        "recovery does not erase",
        "read back authoritative state",
        "silence is never a terminal state",
        "external supervisor",
        "ue_unclassified_material_boundary",
        "dual-lane sprint",
    ):
        if phrase not in appendix_lower:
            raise ExecutionBoundaryContractError(f"shared prompt policy missing required boundary semantic: {phrase}")

    return {
        "families": len(family_ids),
        "classes": len(class_ids),
        "cases": len(cases),
        "layers": len(layer_ids),
    }


def validate_paths(
    architecture_path: Path = ARCHITECTURE,
    taxonomy_path: Path = TAXONOMY,
    matrix_path: Path = MATRIX,
    shared_policy_path: Path = SHARED_POLICY,
) -> dict[str, int]:
    return validate_documents(
        _load(architecture_path),
        _load(taxonomy_path),
        _load(matrix_path),
        _load(shared_policy_path),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate execution-boundary enforcement architecture, taxonomy, regression matrix, and shared Prompt Kit inheritance.")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        summary = validate_paths()
    except (ExecutionBoundaryContractError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"EXECUTION BOUNDARY ENFORCEMENT: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "EXECUTION BOUNDARY ENFORCEMENT: PASS | "
            f"layers={summary['layers']} | "
            f"families={summary['families']} | "
            f"classes={summary['classes']} | "
            f"cases={summary['cases']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
