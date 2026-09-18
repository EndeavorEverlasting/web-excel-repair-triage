#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "harness/contracts/prompt-strength.v1.json"
DEFAULT_MATRIX = ROOT / "harness/evals/prompt-strength/adversarial-regression-matrix.v1.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PROFILE_NAMES = {"exhaustive", "efficient"}
DEPENDENCY_KEYS = {"quality_history_dependency", "local_proof_dependency", "p07_identity_dependency"}


class PromptStrengthError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise PromptStrengthError(f"{path} must contain a JSON object")
    return data


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_string(item) for item in value)


def _validate_dependency_snapshots(contract: dict[str, Any]) -> None:
    owners = contract.get("supporting_owners")
    if not isinstance(owners, dict):
        raise PromptStrengthError("supporting_owners missing")
    for key in DEPENDENCY_KEYS:
        item = owners.get(key)
        if not isinstance(item, dict):
            raise PromptStrengthError(f"dependency snapshot missing or untyped: {key}")
        if not isinstance(item.get("pr"), int) or isinstance(item.get("pr"), bool) or item["pr"] < 1:
            raise PromptStrengthError(f"dependency PR invalid: {key}")
        sha = item.get("head_sha_at_reconciliation")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise PromptStrengthError(f"dependency revision invalid: {key}")
        if item.get("state") not in {"OPEN_EXTERNAL_OWNER", "INTEGRATED"}:
            raise PromptStrengthError(f"dependency state invalid: {key}")
        if not _nonempty_string(item.get("content_anchor")):
            raise PromptStrengthError(f"dependency content anchor missing: {key}")
        integration_sha = item.get("integration_sha")
        if item["state"] == "INTEGRATED":
            if not isinstance(integration_sha, str) or not SHA_RE.fullmatch(integration_sha):
                raise PromptStrengthError(f"integrated dependency lacks integration SHA: {key}")
        elif integration_sha is not None:
            raise PromptStrengthError(f"open dependency must not claim integration SHA: {key}")


def validate_documents(contract: dict[str, Any], matrix: dict[str, Any]) -> dict[str, int]:
    if contract.get("schema_version") != "prompt-strength/v1":
        raise PromptStrengthError("contract schema_version drifted")
    if matrix.get("schema_version") != "prompt-strength-adversarial-matrix/v1":
        raise PromptStrengthError("matrix schema_version drifted")

    _validate_dependency_snapshots(contract)

    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise PromptStrengthError("contract dimensions must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    required_dimension_fields = {"id", "class", "summary", "required_in", "weakening_forbidden", "evidence_terms"}
    for item in dimensions:
        if not isinstance(item, dict):
            raise PromptStrengthError("dimension must be an object")
        missing = sorted(required_dimension_fields - set(item))
        if missing:
            raise PromptStrengthError(f"dimension missing required fields: {missing}")
        dim_id = item["id"]
        if not _nonempty_string(dim_id):
            raise PromptStrengthError("dimension id missing")
        if dim_id in by_id:
            raise PromptStrengthError(f"duplicate dimension: {dim_id}")
        if not _nonempty_string(item["class"]):
            raise PromptStrengthError(f"dimension class missing: {dim_id}")
        if not _nonempty_string(item["summary"]):
            raise PromptStrengthError(f"dimension summary missing: {dim_id}")
        if type(item["weakening_forbidden"]) is not bool:
            raise PromptStrengthError(f"dimension weakening_forbidden must be boolean: {dim_id}")
        required_in = item["required_in"]
        if not _string_list(required_in):
            raise PromptStrengthError(f"dimension required_in missing: {dim_id}")
        if len(set(required_in)) != len(required_in) or any(profile not in PROFILE_NAMES for profile in required_in):
            raise PromptStrengthError(f"invalid profile on dimension: {dim_id}")
        evidence_terms = item["evidence_terms"]
        if not _string_list(evidence_terms):
            raise PromptStrengthError(f"dimension evidence_terms missing: {dim_id}")
        normalized_terms = [term.strip().lower() for term in evidence_terms]
        if len(set(normalized_terms)) != len(normalized_terms):
            raise PromptStrengthError(f"duplicate dimension evidence_terms: {dim_id}")
        by_id[dim_id] = item

    profiles = contract.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != PROFILE_NAMES:
        raise PromptStrengthError("profiles must contain exactly exhaustive and efficient")
    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise PromptStrengthError(f"profile must be an object: {profile_name}")
        if not _nonempty_string(profile.get("mode")):
            raise PromptStrengthError(f"profile mode missing: {profile_name}")
        if not _string_list(profile.get("required_dimensions")):
            raise PromptStrengthError(f"profile required_dimensions missing: {profile_name}")

    exhaustive = profiles["exhaustive"]["required_dimensions"]
    efficient = profiles["efficient"]["required_dimensions"]
    all_ids = set(by_id)
    if set(exhaustive) != all_ids or len(exhaustive) != len(all_ids):
        missing = sorted(all_ids - set(exhaustive))
        extra = sorted(set(exhaustive) - all_ids)
        raise PromptStrengthError(f"exhaustive profile coverage drift: missing={missing} extra={extra}")

    efficient_required = {dim_id for dim_id, item in by_id.items() if "efficient" in item["required_in"]}
    if set(efficient) != efficient_required or len(efficient) != len(efficient_required):
        missing = sorted(efficient_required - set(efficient))
        extra = sorted(set(efficient) - efficient_required)
        raise PromptStrengthError(f"efficient profile non-weakening drift: missing={missing} extra={extra}")

    validation = contract.get("validation")
    if not isinstance(validation, dict):
        raise PromptStrengthError("validation contract missing")
    focused_tests = validation.get("focused_tests")
    if focused_tests != "tests/test_prompt_strength_contract_prompt.py":
        raise PromptStrengthError("focused prompt-strength test path drifted from semantic-floor convention")

    representation = contract.get("representation_invariants")
    parallelism = contract.get("parallelism_invariants")
    if not isinstance(representation, dict) or representation.get("generated_html_is_authority") is not False:
        raise PromptStrengthError("generated HTML must not become prompt authority")
    if not isinstance(parallelism, dict):
        raise PromptStrengthError("parallelism invariants missing")
    if parallelism.get("considered_parallelism_is_proof") is not False:
        raise PromptStrengthError("considered parallelism must not count as dispatch proof")
    if parallelism.get("serial_tool_calls_are_parallelism") is not False:
        raise PromptStrengthError("serial tool calls must not count as parallelism")

    source_floor = matrix.get("source_floor")
    if not isinstance(source_floor, dict):
        raise PromptStrengthError("matrix source_floor missing")
    observed_main = source_floor.get("observed_default_head_at_reconciliation")
    if not isinstance(observed_main, str) or not SHA_RE.fullmatch(observed_main):
        raise PromptStrengthError("matrix reconciliation head must be an exact SHA")
    dependencies = source_floor.get("active_dependencies")
    expected_dependency_keys = {"p07_effective_identity", "local_proof_continuity", "quality_history"}
    if not isinstance(dependencies, dict) or set(dependencies) != expected_dependency_keys:
        raise PromptStrengthError("matrix dependency snapshots incomplete")
    for key, item in dependencies.items():
        if not isinstance(item, dict):
            raise PromptStrengthError(f"matrix dependency snapshot untyped: {key}")
        if not isinstance(item.get("pr"), int) or isinstance(item.get("pr"), bool) or item["pr"] < 1:
            raise PromptStrengthError(f"matrix dependency PR invalid: {key}")
        sha = item.get("head_sha_at_reconciliation")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise PromptStrengthError(f"matrix dependency revision invalid: {key}")
        if item.get("state") not in {"OPEN_EXTERNAL_OWNER", "INTEGRATED"}:
            raise PromptStrengthError(f"matrix dependency state invalid: {key}")

    case_contract = matrix.get("case_contract")
    if not isinstance(case_contract, dict):
        raise PromptStrengthError("matrix case contract incomplete")
    required_fields = case_contract.get("required_fields")
    allowed_families_raw = case_contract.get("allowed_defect_families")
    minimum = case_contract.get("minimum_cases")
    if not _string_list(required_fields) or not _string_list(allowed_families_raw):
        raise PromptStrengthError("matrix case contract incomplete")
    allowed_families = set(allowed_families_raw)
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        raise PromptStrengthError("matrix minimum_cases invalid")

    cases = matrix.get("cases")
    if not isinstance(cases, list) or len(cases) < minimum:
        raise PromptStrengthError(f"matrix requires at least {minimum} cases")

    seen_cases: set[str] = set()
    coverage: dict[str, int] = {dim_id: 0 for dim_id in all_ids}
    silent_stop_case_seen = False
    for case in cases:
        if not isinstance(case, dict):
            raise PromptStrengthError("case must be an object")
        missing_fields = [field for field in required_fields if field not in case]
        if missing_fields:
            raise PromptStrengthError(f"case missing fields: {case.get('case_id')} {missing_fields}")
        case_id = case["case_id"]
        if not _nonempty_string(case_id):
            raise PromptStrengthError("case_id missing")
        if case_id in seen_cases:
            raise PromptStrengthError(f"duplicate case_id: {case_id}")
        seen_cases.add(case_id)
        if case["defect_family"] not in allowed_families:
            raise PromptStrengthError(f"invalid defect family: {case_id}")
        if not _string_list(case["profiles"]):
            raise PromptStrengthError(f"case profiles malformed: {case_id}")
        if any(profile not in PROFILE_NAMES for profile in case["profiles"]):
            raise PromptStrengthError(f"case uses unsupported profile: {case_id}")
        if not _string_list(case["positive_assertions"]) or not _string_list(case["negative_assertions"]):
            raise PromptStrengthError(f"case requires string-list positive and negative assertions: {case_id}")
        if not _string_list(case["dimensions"]):
            raise PromptStrengthError(f"case dimensions malformed: {case_id}")
        if len(set(case["dimensions"])) != len(case["dimensions"]):
            raise PromptStrengthError(f"case has duplicate dimensions: {case_id}")
        if not _string_list(case["canonical_owners"]):
            raise PromptStrengthError(f"case canonical_owners malformed: {case_id}")
        if not _string_list(case["proof_surfaces"]):
            raise PromptStrengthError(f"case proof_surfaces malformed: {case_id}")
        if not _nonempty_string(case["stimulus"]):
            raise PromptStrengthError(f"case stimulus missing: {case_id}")

        case_corpus = " ".join(
            [case["title"], case["stimulus"]]
            + case["positive_assertions"]
            + case["negative_assertions"]
        ).lower()
        for dim_id in case["dimensions"]:
            if dim_id not in all_ids:
                raise PromptStrengthError(f"unknown dimension {dim_id} in {case_id}")
            evidence_terms = [term.lower() for term in by_id[dim_id]["evidence_terms"]]
            if not any(term in case_corpus for term in evidence_terms):
                raise PromptStrengthError(
                    f"case dimension lacks semantic evidence: {case_id} -> {dim_id}"
                )
            coverage[dim_id] += 1

        ceiling = case.get("proof_ceiling", "").lower()
        if "model obedience" not in ceiling or "unproven" not in ceiling:
            raise PromptStrengthError(f"case proof ceiling must preserve model-obedience boundary: {case_id}")
        if case_id == "PSA-031":
            silent_stop_case_seen = all(term in case_corpus for term in ("stop", "boundary", "silent"))

    uncovered = sorted(dim_id for dim_id, count in coverage.items() if count == 0)
    if uncovered:
        raise PromptStrengthError(f"adversarial matrix lacks dimension coverage: {uncovered}")
    if not silent_stop_case_seen:
        raise PromptStrengthError("matrix must retain PSA-031 silent-stop boundary regression")

    matrix_ceiling = matrix.get("proof_ceiling", "").lower()
    contract_ceiling = contract.get("proof_ceiling", "").lower()
    for label, ceiling in (("contract", contract_ceiling), ("matrix", matrix_ceiling)):
        if "model obedience" not in ceiling or "does not prove" not in ceiling:
            raise PromptStrengthError(f"{label} proof ceiling is too strong")

    return {
        "dimensions": len(all_ids),
        "efficient_dimensions": len(efficient_required),
        "cases": len(cases),
        "covered_dimensions": sum(1 for count in coverage.values() if count),
    }


def validate_paths(contract_path: Path = DEFAULT_CONTRACT, matrix_path: Path = DEFAULT_MATRIX) -> dict[str, int]:
    contract = _load(contract_path)
    matrix = _load(matrix_path)
    summary = validate_documents(contract, matrix)
    focused = ROOT / contract["validation"]["focused_tests"]
    if not focused.is_file():
        raise PromptStrengthError(f"focused test missing: {focused.relative_to(ROOT)}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Prompt Kit prompt-strength contract and adversarial matrix.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        summary = validate_paths(args.contract, args.matrix)
    except (PromptStrengthError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"PROMPT STRENGTH: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "PROMPT STRENGTH: PASS | "
            f"dimensions={summary['dimensions']} | "
            f"efficient_dimensions={summary['efficient_dimensions']} | "
            f"cases={summary['cases']} | "
            f"covered_dimensions={summary['covered_dimensions']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
