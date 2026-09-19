#!/usr/bin/env python3
"""Privacy-bounded P99/P13/P94 linkage for prompt-runtime-compliance evidence."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "runtime-compliance"
CONTRACT_PATH = EVAL / "linkage-contract.v1.json"
LINKAGE_SCHEMA_PATH = EVAL / "linkage-schema.v1.json"
P99_SCHEMA_PATH = ROOT / "harness" / "contracts" / "prompt-outcome-receipt.schema.v1.json"
REGRESSION_CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-regression-safety.v1.json"


class LinkageError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


CONTRACT = load_json(CONTRACT_PATH)
LINKAGE_SCHEMA = load_json(LINKAGE_SCHEMA_PATH)
P99_SCHEMA = load_json(P99_SCHEMA_PATH)
REGRESSION_CONTRACT = load_json(REGRESSION_CONTRACT_PATH)
LINKAGE_VALIDATOR = Draft202012Validator(LINKAGE_SCHEMA, format_checker=FormatChecker())


def _enum(schema: dict[str, Any], *path: str) -> set[str]:
    node: Any = schema
    for key in path:
        node = node[key]
    return set(node["enum"])


def validate_contract() -> None:
    if CONTRACT.get("schema_version") != "prompt-runtime-compliance-linkage-contract/v1":
        raise LinkageError("linkage contract identity drift")
    if LINKAGE_SCHEMA.get("$id") != "prompt-runtime-compliance-linkage-record/v1":
        raise LinkageError("linkage record schema identity drift")
    Draft202012Validator.check_schema(LINKAGE_SCHEMA)

    p99_results = _enum(P99_SCHEMA, "properties", "result")
    mapped_results = set(CONTRACT["p99"]["result_mapping"].values())
    if not mapped_results.issubset(p99_results):
        raise LinkageError("P99 result mapping contains an unsupported result")
    p99_evidence_kinds = _enum(P99_SCHEMA, "$defs", "evidence", "properties", "kind")
    if CONTRACT["p99"]["evidence_kind"] not in p99_evidence_kinds:
        raise LinkageError("P99 no longer accepts validator evidence")
    p99_failure_classes = _enum(P99_SCHEMA, "$defs", "failure_class")
    hints = set(CONTRACT["p99"]["failure_class_hints"].values())
    hints.add(CONTRACT["p99"]["default_failure_class_hint"])
    if not hints.issubset(p99_failure_classes):
        raise LinkageError("linkage failure-class hint drifted from P99 vocabulary")

    expected_threshold = REGRESSION_CONTRACT["recurrence"]["systemic_threshold"]
    if CONTRACT["regression"]["systemic_threshold"] != expected_threshold:
        raise LinkageError("runtime linkage systemic threshold drifted from P13 contract")
    authority = REGRESSION_CONTRACT["authority"]
    if CONTRACT["regression"]["recurring_process_owner"] != authority["recurring_process_owner"]:
        raise LinkageError("runtime linkage recurring-process owner drifted")
    if CONTRACT["regression"]["regression_design_owner"] != authority["regression_design_owner"]:
        raise LinkageError("runtime linkage regression-design owner drifted")
    if CONTRACT["p99"]["authoritative_classification"] is not False:
        raise LinkageError("runtime linkage must remain evidence, not authoritative P99 classification")


def _failure_hint(rule_id: str) -> str:
    mapping = CONTRACT["p99"]["failure_class_hints"]
    if rule_id in mapping:
        return mapping[rule_id]
    prefix_matches = [
        (prefix, hint)
        for prefix, hint in mapping.items()
        if prefix.endswith(".") and rule_id.startswith(prefix)
    ]
    if prefix_matches:
        return max(prefix_matches, key=lambda item: len(item[0]))[1]
    return CONTRACT["p99"]["default_failure_class_hint"]


def _serious_findings(validation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in validation.get("findings", [])
        if row.get("result") in {"FAIL", "UNKNOWN"}
        and row.get("severity") in {"CRITICAL", "HIGH"}
    ]


def _source_violations(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in receipt.get("violations", [])
        if row.get("result") in {"FAIL", "UNKNOWN"}
        and row.get("status") != "INFORMATIONAL"
    ]


def _regression_required_violations(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in _source_violations(receipt) if row.get("regression_required") is True
    ]


def _regression_family(violations: list[dict[str, Any]]) -> str | None:
    if not violations:
        return None
    families = {str(row["family"]) for row in violations}
    if len(families) == 1:
        return next(iter(families))
    return "REGRESSION"


def build_linkage_record(
    receipt: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    validate_contract()
    receipt_id = str(receipt.get("receipt_id") or "")
    if not receipt_id:
        raise LinkageError("compliance receipt lacks receipt_id")
    if validation.get("receipt_id") != receipt_id:
        raise LinkageError("validation result does not belong to the supplied compliance receipt")
    if validation.get("receipt_schema") != "prompt-runtime-compliance-receipt/v1":
        raise LinkageError("validation result receipt schema identity drift")
    validation_result = str(validation.get("overall_result") or "")
    if validation_result not in CONTRACT["p99"]["result_mapping"]:
        raise LinkageError(f"unsupported compliance validation result: {validation_result!r}")

    scenario_id = str((receipt.get("scenario") or {}).get("scenario_id") or "")
    if not scenario_id:
        raise LinkageError("compliance receipt lacks scenario identity")
    serious = _serious_findings(validation)
    rule_ids = sorted({str(row["rule_id"]) for row in serious})
    hints = sorted({_failure_hint(rule_id) for rule_id in rule_ids})

    source_violations = _source_violations(receipt)
    source_violation_ids = sorted({str(row["violation_id"]) for row in source_violations})
    evidence_refs = sorted(
        {
            str(ref)
            for row in source_violations
            for ref in row.get("evidence_refs", [])
        }
    )

    regression_violations = _regression_required_violations(receipt)
    family = _regression_family(regression_violations)
    regression_refs = sorted(
        {
            str(ref)
            for row in regression_violations
            for ref in row.get("evidence_refs", [])
        }
    )
    occurrence = (
        [{"compliance_receipt_id": receipt_id, "evidence_refs": regression_refs}]
        if regression_violations
        else []
    )

    result_candidate = CONTRACT["p99"]["result_mapping"][validation_result]
    record = {
        "schema_version": "prompt-runtime-compliance-linkage-record/v1",
        "compliance_receipt_id": receipt_id,
        "scenario_id": scenario_id,
        "validation_result": validation_result,
        "p99_result_candidate": result_candidate,
        "p99_evidence_candidate": {
            "kind": CONTRACT["p99"]["evidence_kind"],
            "ref": f"{CONTRACT['p99']['ref_prefix']}{receipt_id}",
            "supports": (
                f"Runtime-compliance validator result {validation_result} for {scenario_id}; "
                f"{len(serious)} critical/high finding(s)."
            ),
        },
        "failure_class_hints": hints,
        "source_violation_ids": source_violation_ids,
        "rule_ids": rule_ids,
        "evidence_refs": evidence_refs,
        "regression": {
            "status": "CANDIDATE" if regression_violations else "NONE",
            "family": family,
            "occurrences": occurrence,
            "systemic_threshold": CONTRACT["regression"]["systemic_threshold"],
            "recurring_process_owner": CONTRACT["regression"]["recurring_process_owner"],
            "regression_design_owner": CONTRACT["regression"]["regression_design_owner"],
        },
        "privacy": {
            "raw_payload_copied": False,
            "violation_messages_copied": False,
            "secret_material_copied": False,
        },
    }
    errors = sorted(LINKAGE_VALIDATOR.iter_errors(record), key=lambda error: list(error.absolute_path))
    if errors:
        detail = "; ".join(error.message for error in errors[:6])
        raise LinkageError(f"linkage record schema rejected generated record: {detail}")
    return record


def _occurrence_key(occurrence: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return (
        str(occurrence["compliance_receipt_id"]),
        tuple(sorted(str(ref) for ref in occurrence.get("evidence_refs", []))),
    )


def aggregate_regressions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validate_contract()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        errors = list(LINKAGE_VALIDATOR.iter_errors(record))
        if errors:
            raise LinkageError("cannot aggregate an invalid linkage record")
        regression = record["regression"]
        if regression["status"] == "NONE":
            continue
        family = regression["family"]
        if not family:
            raise LinkageError("active regression linkage lacks a defect family")
        groups[family].extend(regression["occurrences"])

    threshold = CONTRACT["regression"]["systemic_threshold"]
    output: list[dict[str, Any]] = []
    for family in sorted(groups):
        unique: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        for occurrence in groups[family]:
            unique[_occurrence_key(occurrence)] = occurrence
        occurrences = [unique[key] for key in sorted(unique)]
        output.append(
            {
                "family": family,
                "status": "SYSTEMIC" if len(occurrences) >= threshold else "CANDIDATE",
                "independent_occurrences": len(occurrences),
                "systemic_threshold": threshold,
                "occurrences": occurrences,
                "recurring_process_owner": CONTRACT["regression"]["recurring_process_owner"],
                "regression_design_owner": CONTRACT["regression"]["regression_design_owner"],
            }
        )
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    record = build_linkage_record(load_json(args.receipt), load_json(args.validation))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary:
        print(
            "RUNTIME COMPLIANCE LINKAGE: PASS "
            f"receipt={record['compliance_receipt_id']} "
            f"validation={record['validation_result']} "
            f"regression={record['regression']['status']}"
        )
    elif not args.output:
        print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
