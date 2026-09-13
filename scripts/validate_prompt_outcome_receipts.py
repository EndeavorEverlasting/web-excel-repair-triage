#!/usr/bin/env python3
"""Deterministic classifier/validator for Prompt Kit outcome receipts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.prompt_outcome_contract import (
        ACTIONABILITY,
        ATTRIBUTION,
        CAUSE_FAMILIES,
        CONFIDENCE,
        ContractError,
        FAILURE_CLASSES,
        INTERVENTIONS,
        RESULTS,
        derive_interaction_metrics,
        load,
        validate_schema_instance,
    )
except ModuleNotFoundError:
    from prompt_outcome_contract import (
        ACTIONABILITY,
        ATTRIBUTION,
        CAUSE_FAMILIES,
        CONFIDENCE,
        ContractError,
        FAILURE_CLASSES,
        INTERVENTIONS,
        RESULTS,
        derive_interaction_metrics,
        load,
        validate_schema_instance,
    )

try:
    from scripts.prompt_outcome_classifier import classify_signals
except ModuleNotFoundError:
    from prompt_outcome_classifier import classify_signals

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "harness/contracts/prompt-outcome-receipt.schema.v1.json"
CONTRACT = ROOT / "harness/contracts/prompt-outcome-classification.v1.json"
FIXTURES = ROOT / "harness/evals/fixtures/prompt-outcome-classification-cases.v1.json"
UPSTREAM = ROOT / "harness/contracts/prompt-kit-feedback-afk-routing.v1.json"


def _allowed_tuples(contract: dict[str, Any], primary: str) -> set[tuple[str, str, str, str]]:
    return {
        (rule["result"], rule["confidence"], rule["attribution"], rule["actionability"])
        for rule in contract["rules"]
        if rule["primary"] == primary
    }


def validate_contract_files() -> None:
    schema, contract, upstream = load(SCHEMA), load(CONTRACT), load(UPSTREAM)

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ContractError("receipt schema dialect drift")
    if schema.get("$id") != "prompt-outcome-receipt/v1":
        raise ContractError("receipt schema identity drift")
    if tuple(schema["$defs"]["failure_class"]["enum"]) != FAILURE_CLASSES:
        raise ContractError("failure class enum drift")
    if tuple(schema["$defs"]["cause_family"]["enum"]) != CAUSE_FAMILIES:
        raise ContractError("cause family enum drift")
    if tuple(schema["$defs"]["intervention"]["enum"]) != INTERVENTIONS:
        raise ContractError("intervention enum drift")
    if tuple(schema["properties"]["result"]["enum"]) != RESULTS:
        raise ContractError("result enum drift")
    if tuple(contract.get("outcome_classes", {})) != FAILURE_CLASSES:
        raise ContractError("classification taxonomy drift")
    if tuple(contract.get("cause_families", {})) != CAUSE_FAMILIES:
        raise ContractError("cause-family taxonomy drift")

    if contract.get("semantic_owner") != "P99" or contract.get("coordination_owner") != "P115":
        raise ContractError("outcome ownership must remain P99 -> P115")

    policy = contract["signal_policy"]
    if policy["ordinary_usage_is_failure"] or policy["ordinary_usage_is_success"]:
        raise ContractError("ordinary usage cannot imply success or failure")

    episode = contract["grounding_episode_policy"]
    if not episode["prompt_reuse_cross_episode_is_neutral"]:
        raise ContractError("cross-episode prompt reuse must remain neutral")
    if not episode["legitimate_iteration_with_evidence_advance_is_neutral"]:
        raise ContractError("legitimate progress iteration must remain neutral")
    if not episode["correction_burden_never_accumulates_across_episode_ids"]:
        raise ContractError("correction burden must be episode-scoped")
    if episode["ordinary_prompt_usage_can_create_correction_event"]:
        raise ContractError("ordinary prompt usage cannot create correction events")

    owners = upstream["semantic_owners"]
    upstream_policy = upstream["friction_policy"]
    if owners.get("usage_and_friction_semantics") != "P99" or owners.get("afk_coordination") != "P115":
        raise ContractError("upstream feedback ownership drift")
    threshold = upstream_policy["evidence_kinds"]["repeated_local_pattern"]["minimum_occurrences"]
    if threshold != policy["repeated_local_pattern_minimum_occurrences"]:
        raise ContractError("repeated-pattern threshold drift")
    if not upstream_policy["raw_usage_is_never_directly_actionable"]:
        raise ContractError("raw ordinary usage must remain non-actionable")

    privacy = contract["privacy_boundary"]
    raw_keys = (
        "raw_prompt_body",
        "raw_response_body",
        "raw_clipboard_content",
        "raw_search_or_typed_content",
        "credentials_or_secrets",
    )
    if any(privacy[key] for key in raw_keys):
        raise ContractError("outcome receipts cannot admit raw/sensitive payload classes")
    if not privacy["correction_events_are_bounded_enums_not_text"]:
        raise ContractError("correction events must remain bounded enums")
    if not privacy["evidence_refs_are_bounded_references_not_raw_payloads"]:
        raise ContractError("outcome evidence must remain bounded references")

    routing = contract["routing_boundary"]
    if not routing["outcome_receipt_is_evidence_not_mutation_authority"]:
        raise ContractError("outcome receipts are evidence, not mutation authority")
    if not routing["P115_owns_reground_protocol"]:
        raise ContractError("P115 must own grounding recovery")

    divergence = contract["interaction_divergence_policy"]
    if set(divergence["correction_action_weights"]) != set(schema["$defs"]["correction_action_kind"]["enum"]):
        raise ContractError("correction action enum/weight drift")
    event_contract = divergence["correction_event_contract"]
    if not all(
        event_contract[key]
        for key in (
            "each_event_is_one_observed_operator_correction",
            "event_count_field_forbidden",
            "corrective_must_be_true",
            "all_events_must_match_interaction_grounding_episode_id",
            "prompt_invocations_are_not_correction_events",
            "task_iterations_are_not_correction_events",
        )
    ):
        raise ContractError("correction-event semantics drift")

    for primary in FAILURE_CLASSES:
        if not _allowed_tuples(contract, primary):
            raise ContractError(f"missing allowed decision tuple for {primary}")


def validate_receipt(receipt: dict[str, Any]) -> None:
    schema, contract = load(SCHEMA), load(CONTRACT)
    validate_schema_instance(receipt, schema)

    result = receipt["result"]
    classification = receipt["classification"]
    primary = classification["primary"]
    secondary = classification["secondary"]
    evidence = receipt["evidence"]

    if primary in secondary:
        raise ContractError("secondary classifications must exclude primary")

    if result == "SUCCESS":
        if (
            primary is not None
            or secondary
            or classification["actionability"] != "INFORMATION_ONLY"
            or classification["attribution"] == "UNOBSERVED"
        ):
            raise ContractError("SUCCESS receipt cannot carry failure/repair/unobserved classification")
        if not evidence:
            raise ContractError("SUCCESS receipt requires at least one evidence reference")
    else:
        if primary is None:
            raise ContractError("non-SUCCESS receipt requires a primary classification")
        observed = (
            result,
            classification["confidence"],
            classification["attribution"],
            classification["actionability"],
        )
        if observed not in _allowed_tuples(contract, primary):
            raise ContractError(f"classification tuple mismatch for {primary}: {observed!r}")
        if primary != "unknown" and not evidence:
            raise ContractError(f"{primary} classification requires at least one evidence reference")

    if classification["attribution"] == "UNOBSERVED" and primary != "unknown":
        raise ContractError("UNOBSERVED attribution is only valid for unknown classification")

    interaction = receipt.get("interaction")
    if interaction is not None:
        expected = derive_interaction_metrics(
            interaction["grounding_episode_id"],
            interaction["response_relevance"],
            interaction["correction_events"],
            [],
            primary or "unknown",
            contract,
        )
        for key in (
            "grounding_episode_id",
            "correction_burden",
            "interaction_yield",
            "divergence_pressure",
            "intervention",
        ):
            if interaction[key] != expected[key]:
                raise ContractError(
                    f"interaction metric mismatch for {key}: expected {expected[key]!r}, observed {interaction[key]!r}"
                )
        if not set(expected["cause_candidates"]).issubset(set(interaction["cause_candidates"])):
            raise ContractError("interaction cause candidates omit required action/symptom causes")


def receipt_from_case(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": "prompt-outcome-receipt/v1",
        "receipt_id": f"fixture/{case['id']}",
        "related_receipt_ids": [],
        "invocation": {
            "invocation_id": f"fixture-invocation/{case['id']}",
            "prompt_id": case.get("prompt_id", "P99"),
            "prompt_revision": "fixture-revision",
            "surface_id": "fixture",
            "mission_id": f"mission/{case['id']}",
            "target_runtime": case.get("target_runtime"),
            "repository": case.get("repository"),
        },
        "observer": {
            "observer_id": "fixture-validator",
            "kind": "validator",
            "surface_id": "prompt-outcome-classifier",
        },
        "observation": {
            "type": "derived",
            "summary": case["purpose"],
            "expected_state": case.get("expected_state"),
            "observed_state": case.get("observed_state"),
            "claimed_state": case.get("claimed_state"),
            "signal_ids": [f"signal/{case['id']}/{index}" for index, _ in enumerate(case["signals"], 1)],
        },
        "result": decision["result"],
        "classification": {
            key: decision[key]
            for key in ("primary", "secondary", "confidence", "attribution", "actionability", "rationale")
        },
        "evidence": json.loads(json.dumps(case.get("evidence", []))),
        "state_transition": case.get("state_transition"),
        "next_state": case.get("next_state"),
        "occurred_at": "2026-09-13T04:30:00Z",
        "retrospective": bool(case.get("retrospective", False)),
    }

    interaction_input = case.get("interaction_input")
    if interaction_input is not None:
        receipt["interaction"] = derive_interaction_metrics(
            interaction_input["grounding_episode_id"],
            interaction_input["response_relevance"],
            json.loads(json.dumps(interaction_input["correction_events"])),
            case["signals"],
            decision["primary"],
        )
    return receipt


def validate_fixtures() -> dict[str, int]:
    contract, fixture = load(CONTRACT), load(FIXTURES)
    if fixture.get("schema_version") != "prompt-outcome-classification-cases/v2":
        raise ContractError("fixture schema_version mismatch")

    counts = {name: 0 for name in FAILURE_CLASSES}
    seen: set[str] = set()

    for case in fixture.get("cases", []):
        if not case.get("id") or case["id"] in seen:
            raise ContractError("fixture ids must be unique/non-empty")
        seen.add(case["id"])

        decision = classify_signals(case["signals"], contract)
        expected = case["expected"]
        for key in ("primary", "result", "confidence", "attribution", "actionability"):
            if decision[key] != expected[key]:
                raise ContractError(
                    f"{case['id']}: expected {key}={expected[key]!r}, observed {decision[key]!r}"
                )
        if sorted(decision["secondary"]) != sorted(expected.get("secondary", [])):
            raise ContractError(f"{case['id']}: secondary classification mismatch")

        receipt = receipt_from_case(case, decision)
        validate_receipt(receipt)

        expected_interaction = case.get("expected_interaction")
        if expected_interaction:
            interaction = receipt["interaction"]
            for key, value in expected_interaction.items():
                if key == "cause_candidates_contains":
                    if not set(value).issubset(set(interaction["cause_candidates"])):
                        raise ContractError(f"{case['id']}: missing expected cause candidate")
                elif interaction[key] != value:
                    raise ContractError(
                        f"{case['id']}: expected interaction {key}={value!r}, observed {interaction[key]!r}"
                    )

        counts[decision["primary"]] += 1

    missing = [name for name, count in counts.items() if not count]
    if missing:
        raise ContractError(f"fixture coverage missing outcome classes: {missing}")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    validate_contract_files()
    counts = validate_fixtures()
    if args.summary:
        print("prompt outcome receipts: PASS | " + " | ".join(f"{key}={counts[key]}" for key in FAILURE_CLASSES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
