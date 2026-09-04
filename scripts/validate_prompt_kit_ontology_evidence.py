#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-ontology-evidence.v1.json"
ONTOLOGY_RUNTIME = ROOT / "docs" / "prompt-kit-ontology.js"
TEACHING_RECORD = ROOT / ".teach" / "learning-records" / "2026-08-29_prompt-kit-ontology.md"
REPORT_SCHEMA = "prompt-kit-ontology-evidence-validation/v1"

REQUIRED_RECORD_KINDS = {
    "invocation",
    "run_result",
    "failure",
    "critique",
    "favorite",
    "feedback",
    "eval",
    "proof_receipt",
}
REQUIRED_LINEAGE_FIELDS = {
    "record_id",
    "record_kind",
    "capability_id",
    "implementation_locator",
    "observed_at",
    "source",
    "subject_ref",
}
EXPECTED_CHAIN = [
    "capability",
    "skill",
    "implementation",
    "invocation",
    "run",
    "evidence",
    "proof_ceiling",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(contract: dict[str, Any], runtime: str, teaching_record: str) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}

    def check(name: str, condition: bool, message: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(message)

    check(
        "contract_schema",
        contract.get("schema_version") == "prompt-kit-ontology-evidence/v1",
        "ontology evidence contract schema mismatch",
    )
    check(
        "relation_chain",
        contract.get("relation_chain") == EXPECTED_CHAIN,
        "ontology evidence relation must preserve capability -> skill -> implementation -> invocation -> run -> evidence -> proof ceiling",
    )
    check(
        "lineage_fields",
        REQUIRED_LINEAGE_FIELDS.issubset(set(contract.get("required_lineage_fields", []))),
        "ontology evidence contract is missing required lineage fields",
    )

    record_kinds = contract.get("record_kinds", {})
    check(
        "record_kind_inventory",
        REQUIRED_RECORD_KINDS == set(record_kinds),
        "ontology evidence record-kind inventory must exactly cover invocation, run result, failure, critique, favorite, feedback, eval, and proof receipt",
    )

    favorite = record_kinds.get("favorite", {})
    check(
        "favorite_is_preference",
        favorite.get("class") == "preference" and favorite.get("preference_signal") is True,
        "favorites must remain explicit preference signals",
    )
    check(
        "favorite_not_proof",
        favorite.get("proof_effect") == "none",
        "favorites must not count as proof",
    )

    failure = record_kinds.get("failure", {})
    check(
        "failure_cannot_raise_proof",
        failure.get("proof_effect") == "lower_or_block",
        "failed runs must lower or block proof rather than raise it",
    )

    critique = record_kinds.get("critique", {})
    check(
        "critique_requires_verification",
        critique.get("proof_effect") == "none_without_independent_verification",
        "critiques require independent verification before contributing proof",
    )

    feedback = record_kinds.get("feedback", {})
    check(
        "feedback_transport_out_of_scope",
        feedback.get("raw_payload_transport") == "out_of_scope",
        "raw feedback transport must remain outside ontology evidence semantics",
    )

    receipt = record_kinds.get("proof_receipt", {})
    check(
        "proof_receipt_immutable",
        receipt.get("immutable") is True and receipt.get("proof_effect") == "supports_observed_claim",
        "proof receipts must be immutable and support only observed claims",
    )

    rules = contract.get("separation_rules", {})
    required_rules = {
        "declared_ceiling_is_not_observed_proof",
        "favorites_are_not_proof",
        "critiques_require_independent_verification",
        "feedback_transport_is_separate",
        "failed_runs_remain_visible",
        "history_is_append_only",
    }
    for rule in sorted(required_rules):
        check(
            f"rule_{rule}",
            rules.get(rule) is True,
            f"ontology evidence separation rule must be true: {rule}",
        )

    authority = contract.get("authority", {})
    check(
        "capability_authority",
        authority.get("declared_proof_ceiling_owner") == "harness/capabilities.v1.json",
        "declared proof ceilings must remain owned by harness/capabilities.v1.json",
    )
    check(
        "runtime_authority",
        authority.get("runtime_view_owner") == "docs/prompt-kit-ontology.js",
        "ontology runtime owner drifted",
    )
    check(
        "transport_authority",
        authority.get("feedback_transport_owner") == "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
        "feedback transport ownership must remain separate from ontology evidence semantics",
    )

    check(
        "runtime_declared_not_history",
        "Declared proof, not run history." in runtime,
        "ontology runtime must continue labeling declared proof separately from run history",
    )
    check(
        "runtime_future_history_layer",
        "separate future evidence/history layer" in runtime,
        "ontology runtime must continue naming evidence/history as a separate layer until live records are wired",
    )
    check(
        "teaching_relation_preserved",
        "trace capability → skill → implementation/prompt → invocation/run → tests/evals/evidence → proof ceiling" in teaching_record,
        "mastered ontology relation is no longer present in the teaching record",
    )
    check(
        "teaching_separation_preserved",
        "later evidence/history layer" in teaching_record and "separate from minimum viable ontology navigation" in teaching_record,
        "mastered ontology evidence/history separation is no longer present in the teaching record",
    )

    return {
        "schema_version": REPORT_SCHEMA,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "proof_ceiling": contract.get("proof_ceiling", ""),
    }


def validate() -> dict[str, Any]:
    contract = load_json(CONTRACT)
    runtime = ONTOLOGY_RUNTIME.read_text(encoding="utf-8")
    teaching_record = TEACHING_RECORD.read_text(encoding="utf-8")
    return validate_payload(contract, runtime, teaching_record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Prompt Kit ontology evidence validation failed: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary or not args.output:
        print(json.dumps({"status": report["status"], "checks": len(report["checks"]), "errors": report["errors"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
