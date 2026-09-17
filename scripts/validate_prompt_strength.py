#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "harness/contracts/prompt-strength.v1.json"
DEFAULT_MATRIX = ROOT / "harness/evals/prompt-strength/adversarial-regression-matrix.v1.json"


class PromptStrengthError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise PromptStrengthError(f"{path} must contain a JSON object")
    return data


def validate_documents(contract: dict[str, Any], matrix: dict[str, Any]) -> dict[str, int]:
    if contract.get("schema_version") != "prompt-strength/v1":
        raise PromptStrengthError("contract schema_version drifted")
    if matrix.get("schema_version") != "prompt-strength-adversarial-matrix/v1":
        raise PromptStrengthError("matrix schema_version drifted")

    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise PromptStrengthError("contract dimensions must be a non-empty list")

    by_id: dict[str, dict[str, Any]] = {}
    for item in dimensions:
        if not isinstance(item, dict):
            raise PromptStrengthError("dimension must be an object")
        dim_id = item.get("id")
        if not isinstance(dim_id, str) or not dim_id:
            raise PromptStrengthError("dimension id missing")
        if dim_id in by_id:
            raise PromptStrengthError(f"duplicate dimension: {dim_id}")
        required_in = item.get("required_in")
        if not isinstance(required_in, list) or not required_in:
            raise PromptStrengthError(f"dimension required_in missing: {dim_id}")
        if any(profile not in {"exhaustive", "efficient"} for profile in required_in):
            raise PromptStrengthError(f"invalid profile on dimension: {dim_id}")
        by_id[dim_id] = item

    profiles = contract.get("profiles")
    if not isinstance(profiles, dict):
        raise PromptStrengthError("profiles missing")
    exhaustive = profiles.get("exhaustive", {}).get("required_dimensions")
    efficient = profiles.get("efficient", {}).get("required_dimensions")
    if not isinstance(exhaustive, list) or not isinstance(efficient, list):
        raise PromptStrengthError("profile required_dimensions missing")

    all_ids = set(by_id)
    if set(exhaustive) != all_ids:
        missing = sorted(all_ids - set(exhaustive))
        extra = sorted(set(exhaustive) - all_ids)
        raise PromptStrengthError(f"exhaustive profile coverage drift: missing={missing} extra={extra}")

    efficient_required = {dim_id for dim_id, item in by_id.items() if "efficient" in item["required_in"]}
    if set(efficient) != efficient_required:
        missing = sorted(efficient_required - set(efficient))
        extra = sorted(set(efficient) - efficient_required)
        raise PromptStrengthError(f"efficient profile non-weakening drift: missing={missing} extra={extra}")

    if contract.get("representation_invariants", {}).get("generated_html_is_authority") is not False:
        raise PromptStrengthError("generated HTML must not become prompt authority")
    if contract.get("parallelism_invariants", {}).get("considered_parallelism_is_proof") is not False:
        raise PromptStrengthError("considered parallelism must not count as dispatch proof")
    if contract.get("parallelism_invariants", {}).get("serial_tool_calls_are_parallelism") is not False:
        raise PromptStrengthError("serial tool calls must not count as parallelism")

    cases = matrix.get("cases")
    if not isinstance(cases, list):
        raise PromptStrengthError("matrix cases missing")
    minimum = matrix.get("case_contract", {}).get("minimum_cases")
    if not isinstance(minimum, int) or len(cases) < minimum:
        raise PromptStrengthError(f"matrix requires at least {minimum} cases")

    required_fields = matrix.get("case_contract", {}).get("required_fields")
    allowed_families = set(matrix.get("case_contract", {}).get("allowed_defect_families", []))
    if not isinstance(required_fields, list) or not allowed_families:
        raise PromptStrengthError("matrix case contract incomplete")

    seen_cases: set[str] = set()
    coverage: dict[str, int] = {dim_id: 0 for dim_id in all_ids}
    for case in cases:
        if not isinstance(case, dict):
            raise PromptStrengthError("case must be an object")
        missing_fields = [field for field in required_fields if field not in case]
        if missing_fields:
            raise PromptStrengthError(f"case missing fields: {case.get('case_id')} {missing_fields}")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id:
            raise PromptStrengthError("case_id missing")
        if case_id in seen_cases:
            raise PromptStrengthError(f"duplicate case_id: {case_id}")
        seen_cases.add(case_id)
        if case["defect_family"] not in allowed_families:
            raise PromptStrengthError(f"invalid defect family: {case_id}")
        if not case["positive_assertions"] or not case["negative_assertions"]:
            raise PromptStrengthError(f"case requires positive and negative assertions: {case_id}")
        if not case["dimensions"]:
            raise PromptStrengthError(f"case dimensions missing: {case_id}")
        for dim_id in case["dimensions"]:
            if dim_id not in all_ids:
                raise PromptStrengthError(f"unknown dimension {dim_id} in {case_id}")
            coverage[dim_id] += 1
        ceiling = case.get("proof_ceiling", "").lower()
        if "model obedience" not in ceiling or "unproven" not in ceiling:
            raise PromptStrengthError(f"case proof ceiling must preserve model-obedience boundary: {case_id}")

    uncovered = sorted(dim_id for dim_id, count in coverage.items() if count == 0)
    if uncovered:
        raise PromptStrengthError(f"adversarial matrix lacks dimension coverage: {uncovered}")

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
    return validate_documents(_load(contract_path), _load(matrix_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Prompt Kit prompt-strength contract and adversarial matrix.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    summary = validate_paths(args.contract, args.matrix)
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
