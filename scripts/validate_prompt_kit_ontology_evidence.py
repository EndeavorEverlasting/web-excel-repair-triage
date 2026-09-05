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
HISTORY_SCHEMA = "prompt-kit-ontology-history/v1"

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
RAISING_PROOF_EFFECTS = {
    "supports_observed_claim",
    "support_or_block",
}
FEEDBACK_TRANSPORT_KEYS = {
    "raw_payload",
    "raw_payload_transport",
    "transport_payload",
    "private_payload",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def history_ledger_path(contract: dict[str, Any]) -> Path:
    authority = contract.get("authority") if isinstance(contract.get("authority"), dict) else {}
    relative = str(authority.get("history_ledger", "")).strip()
    if not relative:
        raise ValueError("ontology evidence contract is missing authority.history_ledger")
    return ROOT / relative


def validate_history_records(contract: dict[str, Any], records: list[Any]) -> list[str]:
    errors: list[str] = []
    kinds = contract.get("record_kinds") if isinstance(contract.get("record_kinds"), dict) else {}
    lineage = set(contract.get("required_lineage_fields") or [])
    if not REQUIRED_LINEAGE_FIELDS.issubset(lineage):
        lineage = REQUIRED_LINEAGE_FIELDS
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        label = f"history record {index}"
        if not isinstance(record, dict):
            errors.append(f"{label} is not an object")
            continue
        record_id = str(record.get("record_id", "")).strip()
        if record_id:
            label = f"history record {record_id}"
            if record_id in seen_ids:
                errors.append(f"duplicate history record_id: {record_id}")
            seen_ids.add(record_id)
        missing = sorted(lineage - set(record))
        if missing:
            errors.append(f"{label} missing lineage fields: {', '.join(missing)}")
        kind = record.get("record_kind")
        if kind not in kinds:
            errors.append(f"{label} has unknown record_kind: {kind}")
            continue
        meta = kinds.get(kind) if isinstance(kinds.get(kind), dict) else {}
        expected_effect = meta.get("proof_effect")
        if "proof_effect" in record and record.get("proof_effect") != expected_effect:
            errors.append(f"{label} must not override {kind} proof_effect")
        if kind == "favorite" and record.get("proof_effect", "none") != "none":
            errors.append("favorite history records must not count as proof")
        if kind == "failure" and record.get("proof_effect") in RAISING_PROOF_EFFECTS:
            errors.append("failure records cannot raise proof")
        if kind == "proof_receipt" and record.get("immutable") is False:
            errors.append("proof receipts cannot be marked mutable")
        transport_keys = sorted(FEEDBACK_TRANSPORT_KEYS.intersection(record))
        if transport_keys:
            errors.append(
                f"{label} must not include feedback transport payloads: {', '.join(transport_keys)}"
            )
    return errors


def validate_history_ledger(contract: dict[str, Any], history: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if history.get("schema_version") != HISTORY_SCHEMA:
        errors.append("ontology history ledger schema mismatch")
    if history.get("append_only") is not True:
        errors.append("ontology history ledger must be append-only")
    records = history.get("records")
    if not isinstance(records, list):
        errors.append("ontology history records must be an array")
        return errors
    errors.extend(validate_history_records(contract, records))
    ceiling = str(history.get("proof_ceiling", ""))
    if not records:
        if "empty records array means no" not in ceiling.lower():
            errors.append(
                "empty ontology history ledger must state that no live events are registered"
            )
        if "does not assert that any live event occurred" not in ceiling:
            errors.append("empty ontology history ledger must not claim that live events occurred")
    return errors


def validate_payload(
    contract: dict[str, Any],
    runtime: str,
    teaching_record: str,
    history: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        "history_ledger_authority",
        authority.get("history_ledger") == "docs/prompt-kit-ontology-history.v1.json",
        "ontology history ledger ownership drifted",
    )
    check(
        "transport_authority",
        authority.get("feedback_transport_owner")
        == "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
        "feedback transport ownership must remain separate from ontology evidence semantics",
    )

    check(
        "runtime_declared_not_history",
        "Declared proof, not run history." in runtime,
        "ontology runtime must continue labeling declared proof separately from run history",
    )
    check(
        "runtime_history_wired",
        "Observed history is distinct from declared proof ceilings." in runtime,
        "ontology runtime must render observed history as a distinct layer from declared proof ceilings",
    )
    check(
        "runtime_no_future_layer_placeholder",
        "separate future evidence/history layer" not in runtime,
        "ontology runtime still treats evidence/history as an unwired future layer",
    )
    for kind in sorted(REQUIRED_RECORD_KINDS):
        check(
            f"runtime_kind_{kind}",
            f"'{kind}'" in runtime and "data-kind=" in runtime and "record_kind === kind" in runtime,
            f"ontology runtime must keep {kind} visible as its own evidence class",
        )
    check(
        "runtime_favorite_preference_copy",
        "preference signal" in runtime and "not correctness proof" in runtime,
        "ontology runtime must label Favorites as preference rather than correctness proof",
    )
    check(
        "runtime_local_favorites_source",
        "promptKit.favoritePromptIds.v1" in runtime,
        "ontology runtime must project local Favorites from the existing Favorites store",
    )
    check(
        "runtime_empty_history_copy",
        "No observed" in runtime,
        "ontology runtime must keep an honest empty-history state",
    )
    check(
        "runtime_tab_survives_profile_rebuild",
        "MutationObserver" in runtime and "ensureOntologyTab" in runtime,
        "ontology tab must reattach after profile header rebuilds",
    )
    check(
        "teaching_relation_preserved",
        "trace capability → skill → implementation/prompt → invocation/run → tests/evals/evidence → proof ceiling"
        in teaching_record,
        "mastered ontology relation is no longer present in the teaching record",
    )
    check(
        "teaching_separation_preserved",
        "later evidence/history layer" in teaching_record
        and "separate from minimum viable ontology navigation" in teaching_record,
        "mastered ontology evidence/history separation is no longer present in the teaching record",
    )

    if history is not None:
        history_errors = validate_history_ledger(contract, history)
        check("history_ledger_valid", not history_errors, "; ".join(history_errors) or "history ledger invalid")
        if not history_errors:
            records = history.get("records") if isinstance(history.get("records"), list) else []
            check(
                "canonical_history_is_list",
                isinstance(history.get("records"), list),
                "canonical ontology history records must be a list",
            )
            if not records:
                check(
                    "canonical_history_does_not_fabricate_runs",
                    True,
                    "canonical ontology history fabricated live events",
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
    history = load_json(history_ledger_path(contract))
    return validate_payload(contract, runtime, teaching_record, history)


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
        print(
            json.dumps(
                {"status": report["status"], "checks": len(report["checks"]), "errors": report["errors"]},
                sort_keys=True,
            )
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
