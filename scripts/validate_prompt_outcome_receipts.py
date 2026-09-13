#!/usr/bin/env python3
"""Deterministic validator/classifier for Prompt Kit outcome receipts (stdlib only)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "harness/contracts/prompt-outcome-receipt.schema.v1.json"
CONTRACT = ROOT / "harness/contracts/prompt-outcome-classification.v1.json"
FIXTURES = ROOT / "harness/evals/fixtures/prompt-outcome-classification-cases.v1.json"
UPSTREAM = ROOT / "harness/contracts/prompt-kit-feedback-afk-routing.v1.json"

FAILURE_CLASSES = ("routing","interpretation","execution","progression","durability",
                   "premature-terminal","evidence-promotion","regression","environment","unknown")
RESULTS = ("SUCCESS","PARTIAL","FAILURE","BLOCKED","UNKNOWN")
CONFIDENCE = ("HIGH","MEDIUM","LOW","NONE")
ATTRIBUTION = ("PROVEN","CORRELATED","UNOBSERVED")
ACTIONABILITY = ("INFORMATION_ONLY","REVIEW_CANDIDATE","CONDITIONAL_ACTIONABLE_REPAIR","ACTIONABLE_REPAIR")


class ContractError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must be a JSON object")
    return value


def decision(primary: str, result: str, confidence: str, attribution: str,
             actionability: str, rationale: str, secondary: list[str] | None = None) -> dict[str, Any]:
    return {"primary": primary, "secondary": secondary or [], "result": result,
            "confidence": confidence, "attribution": attribution,
            "actionability": actionability, "rationale": rationale}


def classify_signals(signals: list[dict[str, Any]], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load(CONTRACT)
    if not isinstance(signals, list) or any(not isinstance(s, dict) or not s.get("type") for s in signals):
        raise ContractError("signals must be objects with non-empty type")
    types = {s["type"] for s in signals}
    first = lambda kind: next((s for s in signals if s["type"] == kind), None)

    claim, observed = first("state_claim"), first("state_observation")
    if claim and observed:
        order = contract["evidence_state_order"]
        try:
            over = order.index(claim["state"]) > order.index(observed["state"])
        except ValueError as exc:
            raise ContractError("unknown evidence state") from exc
        if over:
            secondary = ["environment"] if "environment_failure" in types else []
            return decision("evidence-promotion","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                            f"claimed state {claim['state']} exceeds observed state {observed['state']}",secondary)
    if "success_claim_with_unresolved_blocker" in types:
        secondary = ["environment"] if "environment_failure" in types else []
        return decision("evidence-promotion","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "success was claimed across an independently observed unresolved blocker",secondary)

    if {"terminal_claim","safe_successor_observed"} <= types:
        return decision("premature-terminal","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "terminality was claimed while a safe actionable successor remained")

    if "expected_durable_artifact_missing" in types:
        return decision("durability","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "a required durable owner/artifact was deterministically absent")
    transfer = first("manual_context_transfer")
    if transfer and int(transfer.get("occurrence_count",0)) >= 2:
        return decision("durability","FAILURE","MEDIUM","CORRELATED","CONDITIONAL_ACTIONABLE_REPAIR",
                        "repeated manual context transfer indicates the durable continuity owner was bypassed")

    if {"prior_validated_state","same_requirement_broken"} <= types or "provider_revert_for_behavior" in types:
        return decision("regression","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "behavior proven for the same requirement later became broken or was reverted")

    route = first("prompt_replaced_by_canonical_owner")
    if "wrong_owner_or_route" in types:
        return decision("routing","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "repository/review evidence proves the selected owner or route was wrong")
    if route and route.get("replacement_advanced_task") is True:
        return decision("routing","FAILURE","MEDIUM","CORRELATED","CONDITIONAL_ACTIONABLE_REPAIR",
                        "a canonical replacement owner advanced the same task after the original route did not")

    if "explicit_invariant_violation" in types or "review_requirement_miss" in types:
        return decision("interpretation","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "the selected owner violated an explicit invariant or requirement")

    if "deterministic_action_failure" in types and "environment_failure" not in types:
        return decision("execution","FAILURE","HIGH","PROVEN","ACTIONABLE_REPAIR",
                        "the intended action deterministically failed without an external cause")

    repeat = first("same_prompt_same_mission_repeat")
    threshold = int(contract["signal_policy"]["repeated_local_pattern_minimum_occurrences"])
    if repeat and int(repeat.get("occurrence_count",0)) >= threshold and "durable_state_advance" not in types:
        return decision("progression","FAILURE","HIGH","CORRELATED","CONDITIONAL_ACTIONABLE_REPAIR",
                        f"same prompt/mission repeated {repeat.get('occurrence_count')} times without durable state advance")

    if "environment_failure" in types:
        return decision("environment","BLOCKED","HIGH","PROVEN","INFORMATION_ONLY",
                        "an external provider/access/runtime/tooling condition blocked execution")

    return decision("unknown","UNKNOWN","NONE","UNOBSERVED","INFORMATION_ONLY",
                    "available signals do not safely prove a prompt failure class")


def validate_contract_files() -> None:
    schema, contract, upstream = load(SCHEMA), load(CONTRACT), load(UPSTREAM)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("$id") != "prompt-outcome-receipt/v1":
        raise ContractError("receipt schema identity/dialect drift")
    if tuple(schema["$defs"]["failure_class"]["enum"]) != FAILURE_CLASSES:
        raise ContractError("failure class enum drift")
    if tuple(schema["properties"]["result"]["enum"]) != RESULTS:
        raise ContractError("result enum drift")
    if tuple(contract.get("outcome_classes",{})) != FAILURE_CLASSES:
        raise ContractError("classification taxonomy drift")
    if contract.get("semantic_owner") != "P99" or contract.get("coordination_owner") != "P115":
        raise ContractError("outcome ownership must remain P99 -> P115")
    policy = contract["signal_policy"]
    if policy["ordinary_usage_is_failure"] or policy["ordinary_usage_is_success"]:
        raise ContractError("ordinary usage cannot imply success or failure")
    owners, upolicy = upstream["semantic_owners"], upstream["friction_policy"]
    if owners.get("usage_and_friction_semantics") != "P99" or owners.get("afk_coordination") != "P115":
        raise ContractError("upstream feedback ownership drift")
    upstream_threshold = upolicy["evidence_kinds"]["repeated_local_pattern"]["minimum_occurrences"]
    if upstream_threshold != policy["repeated_local_pattern_minimum_occurrences"] or not upolicy["raw_usage_is_never_directly_actionable"]:
        raise ContractError("outcome threshold/raw-usage policy must match upstream feedback contract")
    privacy = contract["privacy_boundary"]
    if any(privacy[k] for k in ("raw_prompt_body","raw_clipboard_content","raw_search_or_typed_content","credentials_or_secrets")):
        raise ContractError("outcome receipts cannot admit raw/sensitive payload classes")
    if not privacy["evidence_refs_are_bounded_references_not_raw_payloads"]:
        raise ContractError("outcome evidence must remain bounded references")
    if not contract["routing_boundary"]["outcome_receipt_is_evidence_not_mutation_authority"]:
        raise ContractError("outcome receipts are evidence, not mutation authority")


def validate_receipt(receipt: dict[str, Any]) -> None:
    required = ("receipt_id","invocation","observer","observation","result","classification","evidence","occurred_at")
    if receipt.get("schema_version") != "prompt-outcome-receipt/v1" or any(k not in receipt for k in required):
        raise ContractError("receipt schema_version/required fields invalid")
    inv = receipt["invocation"]
    pid = str(inv.get("prompt_id",""))
    if not inv.get("invocation_id") or not inv.get("prompt_revision") or not inv.get("surface_id"):
        raise ContractError("invocation identity/revision/surface are required")
    if not (pid.startswith("P") and pid[1:].isdigit() and 2 <= len(pid[1:]) <= 4):
        raise ContractError("prompt_id must match P plus 2-4 digits")

    result, c, evidence = receipt["result"], receipt["classification"], receipt["evidence"]
    primary, secondary = c.get("primary"), c.get("secondary")
    if result not in RESULTS or (primary is not None and primary not in FAILURE_CLASSES):
        raise ContractError("invalid result/primary classification")
    if not isinstance(secondary,list) or len(secondary) != len(set(secondary)) or primary in secondary:
        raise ContractError("secondary classifications must be unique and exclude primary")
    if any(x not in FAILURE_CLASSES for x in secondary):
        raise ContractError("invalid secondary classification")
    if c.get("confidence") not in CONFIDENCE or c.get("attribution") not in ATTRIBUTION or c.get("actionability") not in ACTIONABILITY:
        raise ContractError("invalid confidence/attribution/actionability")
    if not c.get("rationale") or not isinstance(evidence,list):
        raise ContractError("rationale/evidence invalid")

    if result == "SUCCESS":
        if primary is not None or secondary or c["actionability"] != "INFORMATION_ONLY" or c["attribution"] == "UNOBSERVED":
            raise ContractError("SUCCESS receipt cannot carry failure/repair/unobserved classification")
        if not evidence:
            raise ContractError("SUCCESS receipt requires at least one evidence reference")
    elif primary is None:
        raise ContractError("non-SUCCESS receipt requires a primary classification")
    elif primary == "unknown":
        if result != "UNKNOWN" or c["actionability"] not in ("INFORMATION_ONLY","REVIEW_CANDIDATE"):
            raise ContractError("unknown classification cannot be actionable repair")
    elif primary == "environment":
        if result not in ("BLOCKED","FAILURE") or not evidence:
            raise ContractError("environment classification requires blocked/failure evidence")
    elif not evidence:
        raise ContractError(f"{primary} classification requires at least one evidence reference")
    if c["attribution"] == "UNOBSERVED" and primary != "unknown":
        raise ContractError("UNOBSERVED attribution is only valid for unknown classification")


def receipt_from_case(case: dict[str, Any], d: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version":"prompt-outcome-receipt/v1","receipt_id":f"fixture/{case['id']}",
        "related_receipt_ids":[],
        "invocation":{"invocation_id":f"fixture-invocation/{case['id']}","prompt_id":case.get("prompt_id","P99"),
                      "prompt_revision":"fixture-revision","surface_id":"fixture","mission_id":f"mission/{case['id']}",
                      "target_runtime":case.get("target_runtime"),"repository":case.get("repository")},
        "observer":{"observer_id":"fixture-validator","kind":"validator","surface_id":"prompt-outcome-classifier"},
        "observation":{"type":"derived","summary":case["purpose"],"expected_state":case.get("expected_state"),
                       "observed_state":case.get("observed_state"),"claimed_state":case.get("claimed_state"),
                       "signal_ids":[f"signal/{case['id']}/{i}" for i,_ in enumerate(case["signals"],1)]},
        "result":d["result"],
        "classification":{k:d[k] for k in ("primary","secondary","confidence","attribution","actionability","rationale")},
        "evidence":case.get("evidence",[]),"state_transition":case.get("state_transition"),
        "next_state":case.get("next_state"),"occurred_at":"2026-09-13T04:30:00Z",
        "retrospective":bool(case.get("retrospective",False)),
    }


def validate_fixtures() -> dict[str,int]:
    contract, fixture = load(CONTRACT), load(FIXTURES)
    if fixture.get("schema_version") != "prompt-outcome-classification-cases/v1":
        raise ContractError("fixture schema_version mismatch")
    counts, seen = {name:0 for name in FAILURE_CLASSES}, set()
    for case in fixture.get("cases",[]):
        if not case.get("id") or case["id"] in seen:
            raise ContractError("fixture ids must be unique/non-empty")
        seen.add(case["id"])
        d, expected = classify_signals(case["signals"],contract), case["expected"]
        for key in ("primary","result","confidence","attribution","actionability"):
            if d[key] != expected[key]:
                raise ContractError(f"{case['id']}: expected {key}={expected[key]!r}, observed {d[key]!r}")
        if sorted(d["secondary"]) != sorted(expected.get("secondary",[])):
            raise ContractError(f"{case['id']}: secondary classification mismatch")
        validate_receipt(receipt_from_case(case,d))
        counts[d["primary"]] += 1
    missing = [name for name,count in counts.items() if not count]
    if missing:
        raise ContractError(f"fixture coverage missing outcome classes: {missing}")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary",action="store_true")
    args = parser.parse_args()
    validate_contract_files()
    counts = validate_fixtures()
    if args.summary:
        print("prompt outcome receipts: PASS | " + " | ".join(f"{k}={counts[k]}" for k in FAILURE_CLASSES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
