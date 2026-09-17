#!/usr/bin/env python3
"""Validate Prompt Kit recurring-defect regression safety.

The retrospective matrix is intentionally not the only intake path. This
validator proves that recurring defects can be registered from repository
history/local gates/review/runtime evidence, are routed to a canonical owner,
and remain connected to repository-owned local proof surfaces.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-regression-safety.v1.json"
REGISTER_PATH = ROOT / "harness" / "evals" / "prompt-regression" / "defect-families.v1.json"
POLICY_PATH = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
TEST_FLOOR_PATH = ROOT / "harness" / "test-floor.v1.json"
REQUIRED_CHECKS_PATH = ROOT / "harness" / "promotion" / "required-checks.v1.json"
PRE_COMMIT_PATH = ROOT / ".githooks" / "pre-commit"
VALIDATORS_PATH = ROOT / "harness" / "validators.v1.json"
FOCUSED_TEST = "tests/test_prompt_regression_safety_prompt.py"


class RegressionSafetyError(ValueError):
    """Raised when the regression-safety contract fails closed."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegressionSafetyError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RegressionSafetyError(f"JSON root must be an object: {path}")
    return payload


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegressionSafetyError(f"{field} must be a non-empty string")
    return value.strip()


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "prompt-regression-safety/v1":
        raise RegressionSafetyError("unsupported prompt regression-safety contract")
    _text(contract.get("contract_id"), "contract_id")
    _text(contract.get("purpose"), "purpose")
    marker = _text(contract.get("prompt_marker"), "prompt_marker")
    if marker != "REGRESSION SAFETY / RECURRING DEFECT CONTRACT":
        raise RegressionSafetyError("unexpected regression-safety prompt marker")

    authority = contract.get("authority")
    if not isinstance(authority, dict):
        raise RegressionSafetyError("authority must be an object")
    required_authority = {
        "prompt_strengthening_owner",
        "recurring_process_owner",
        "regression_design_owner",
        "transcript_judgment_intake_owner",
        "prompt_identity_owner",
        "local_required_check_owner",
        "hosted_provider_is_semantic_owner",
    }
    if set(authority) != required_authority:
        raise RegressionSafetyError("authority fields do not match contract")
    for field in required_authority - {"hosted_provider_is_semantic_owner"}:
        _text(authority.get(field), f"authority.{field}")
    if authority.get("hosted_provider_is_semantic_owner") is not False:
        raise RegressionSafetyError("hosted provider may not become semantic owner")

    recurrence = contract.get("recurrence")
    if not isinstance(recurrence, dict):
        raise RegressionSafetyError("recurrence must be an object")
    threshold = recurrence.get("systemic_threshold")
    if type(threshold) is not int or threshold < 2:
        raise RegressionSafetyError("systemic recurrence threshold must be >= 2")
    sources = recurrence.get("incident_sources")
    if not isinstance(sources, list) or len(sources) < 5 or len(sources) != len(set(sources)):
        raise RegressionSafetyError("incident_sources must be a unique multi-source list")
    for required_source in ("local_validator", "hosted_ci", "code_review", "runtime_observation", "operator_feedback", "retrospective_matrix", "commit_history"):
        if required_source not in sources:
            raise RegressionSafetyError(f"missing incident source: {required_source}")

    loop = contract.get("required_loop")
    expected_loop = [
        "REPAIR_INSTANCE",
        "CLASSIFY_DEFECT_FAMILY",
        "FIND_CANONICAL_OWNER",
        "WRITE_NEGATIVE_FIXTURE",
        "WRITE_POSITIVE_CONTROL",
        "STRENGTHEN_CANONICAL_OWNER",
        "RUN_LOCAL_REQUIRED_CHECKS",
        "RUN_AFFECTED_PROVIDER_PARITY_WHEN_APPLICABLE",
        "INTEGRATE_AND_RETAIN_REGRESSION",
    ]
    if loop != expected_loop:
        raise RegressionSafetyError("required_loop must preserve the canonical defect-to-regression order")

    local_first = contract.get("local_first_proof")
    if not isinstance(local_first, dict):
        raise RegressionSafetyError("local_first_proof must be an object")
    _text(local_first.get("semantic_authority"), "local_first_proof.semantic_authority")
    rules = local_first.get("rules")
    if not isinstance(rules, list) or len(rules) < 4:
        raise RegressionSafetyError("local_first_proof.rules must define local/provider boundaries")
    joined = " ".join(str(item) for item in rules).lower()
    for phrase in ("local profile", "exact base/head", "provider", "merge authority"):
        if phrase not in joined:
            raise RegressionSafetyError(f"local-first proof is missing concept: {phrase}")

    hygiene = contract.get("repository_hygiene")
    if not isinstance(hygiene, dict):
        raise RegressionSafetyError("repository_hygiene must be an object")
    commands = hygiene.get("patch_hygiene_commands")
    expected_commands = {
        "git diff --check",
        "git diff --cached --check",
        "git diff --check {base_sha}...{head_sha}",
    }
    if not isinstance(commands, list) or set(commands) != expected_commands:
        raise RegressionSafetyError("patch-hygiene commands must cover working, staged, and exact candidates")
    _text(contract.get("matrix_boundary"), "matrix_boundary")

    requirements = contract.get("systemic_repair_requirements")
    if not isinstance(requirements, list) or len(requirements) < 6:
        raise RegressionSafetyError("systemic repair requirements are incomplete")
    requirement_text = " ".join(str(item) for item in requirements).lower()
    for phrase in ("negative fixture", "positive control", "shared owner", "deterministic floor", "local required checks"):
        if phrase not in requirement_text:
            raise RegressionSafetyError(f"systemic repair requirement missing: {phrase}")


def validate_register(register: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    if register.get("schema_version") != "prompt-regression-defect-register/v1":
        raise RegressionSafetyError("unsupported defect register schema")
    if register.get("contract") != "harness/contracts/prompt-regression-safety.v1.json":
        raise RegressionSafetyError("defect register must bind canonical contract")
    _text(register.get("evaluation_time"), "evaluation_time")
    families = register.get("families")
    if not isinstance(families, list) or not families:
        raise RegressionSafetyError("defect register must contain at least one family")

    threshold = contract["recurrence"]["systemic_threshold"]
    seen: set[str] = set()
    occurrence_count = 0
    for index, family in enumerate(families):
        if not isinstance(family, dict):
            raise RegressionSafetyError(f"family[{index}] must be an object")
        required = {
            "id",
            "status",
            "classification",
            "recurring_across_repositories",
            "matrix_capture_required",
            "canonical_owner",
            "prompt_strengthening",
            "detector_commands",
            "prevention_surfaces",
            "regression_gate",
            "local_first_requirement",
            "occurrences",
        }
        if set(family) != required:
            raise RegressionSafetyError(f"family[{index}] fields do not match contract")
        family_id = _text(family.get("id"), f"family[{index}].id")
        if family_id in seen:
            raise RegressionSafetyError(f"duplicate defect family: {family_id}")
        seen.add(family_id)
        if family.get("status") != "SYSTEMIC":
            raise RegressionSafetyError(f"registered recurring family must be SYSTEMIC: {family_id}")
        if family.get("prompt_strengthening") != "GLOBAL_SHARED_POLICY":
            raise RegressionSafetyError(f"systemic family must strengthen shared prompt policy: {family_id}")
        if type(family.get("matrix_capture_required")) is not bool:
            raise RegressionSafetyError("matrix_capture_required must be boolean")
        _text(family.get("canonical_owner"), f"{family_id}.canonical_owner")
        _text(family.get("regression_gate"), f"{family_id}.regression_gate")
        _text(family.get("local_first_requirement"), f"{family_id}.local_first_requirement")

        detectors = family.get("detector_commands")
        if not isinstance(detectors, list) or not detectors:
            raise RegressionSafetyError(f"{family_id} requires detector commands")
        prevention = family.get("prevention_surfaces")
        if not isinstance(prevention, list) or len(prevention) < 2:
            raise RegressionSafetyError(f"{family_id} requires shared prevention surfaces")
        occurrences = family.get("occurrences")
        if not isinstance(occurrences, list) or len(occurrences) < threshold:
            raise RegressionSafetyError(
                f"{family_id} needs at least {threshold} evidenced occurrences for SYSTEMIC status"
            )
        occurrence_count += len(occurrences)
        unique_occurrences: set[tuple[str, str]] = set()
        repositories: set[str] = set()
        for occurrence in occurrences:
            if not isinstance(occurrence, dict) or set(occurrence) != {"repository", "commit", "summary"}:
                raise RegressionSafetyError(f"{family_id} occurrence is malformed")
            repository = _text(occurrence.get("repository"), f"{family_id}.occurrence.repository")
            commit = _text(occurrence.get("commit"), f"{family_id}.occurrence.commit")
            _text(occurrence.get("summary"), f"{family_id}.occurrence.summary")
            key = (repository, commit)
            if key in unique_occurrences:
                raise RegressionSafetyError(f"duplicate occurrence in {family_id}: {repository}@{commit}")
            unique_occurrences.add(key)
            repositories.add(repository)
        if family.get("recurring_across_repositories") is True and len(repositories) < 2:
            raise RegressionSafetyError(f"{family_id} claims cross-repo recurrence without two repositories")

        if family_id == "TRAILING_WHITESPACE":
            required_detectors = set(contract["repository_hygiene"]["patch_hygiene_commands"])
            if set(detectors) != required_detectors:
                raise RegressionSafetyError("TRAILING_WHITESPACE must use all canonical patch-hygiene detectors")
            if family.get("matrix_capture_required") is not False:
                raise RegressionSafetyError("whitespace recurrence must not depend on retrospective matrix capture")
            if family.get("recurring_across_repositories") is not True:
                raise RegressionSafetyError("whitespace evidence must preserve cross-repository recurrence")

    return {
        "families": len(families),
        "occurrences": occurrence_count,
        "systemic_threshold": threshold,
    }


def validate_repository_wiring(contract: dict[str, Any]) -> None:
    marker = contract["prompt_marker"]
    policy = load_json(POLICY_PATH)
    appendix = _text(policy.get("copy_content_appendix"), "actionability.copy_content_appendix")
    if marker not in appendix:
        raise RegressionSafetyError("shared actionability policy does not compile the regression-safety marker")
    appendix_lower = appendix.lower()
    for phrase in (
        "negative fixture",
        "positive control",
        "local required-check",
        "matrix is one intake source",
        "git diff --check",
        "hosted provider",
    ):
        if phrase not in appendix_lower:
            raise RegressionSafetyError(f"shared regression-safety prompt contract missing phrase: {phrase}")

    floor = load_json(TEST_FLOOR_PATH)
    if FOCUSED_TEST not in floor.get("self_tests", []):
        raise RegressionSafetyError("focused regression-safety test is not registered in deterministic floor")
    globs = floor.get("prompt_semantic_test_globs", [])
    if not any("prompt" in str(item) for item in globs):
        raise RegressionSafetyError("deterministic floor has no prompt semantic convention")

    pre_commit = PRE_COMMIT_PATH.read_text(encoding="utf-8")
    if "git diff --cached --check" not in pre_commit:
        raise RegressionSafetyError("pre-commit hook must retain staged patch-hygiene proof")

    required_checks = json.dumps(load_json(REQUIRED_CHECKS_PATH), sort_keys=True)
    if "git diff --check {base_sha}...{head_sha}" not in required_checks:
        raise RegressionSafetyError("local required-check contract lacks exact-candidate patch hygiene")

    validators = json.dumps(load_json(VALIDATORS_PATH), sort_keys=True)
    for command in ("git diff --check", "git diff --cached --check"):
        if command not in validators:
            raise RegressionSafetyError(f"validator registry is missing patch hygiene command: {command}")


def validate_all(
    contract: dict[str, Any], register: dict[str, Any], *, check_repository_wiring: bool = True
) -> dict[str, Any]:
    validate_contract(contract)
    summary = validate_register(register, contract)
    if check_repository_wiring:
        validate_repository_wiring(contract)
    return {
        "status": "PASS",
        "schema_version": contract["schema_version"],
        "families": summary["families"],
        "occurrences": summary["occurrences"],
        "systemic_threshold": summary["systemic_threshold"],
        "matrix_is_exhaustive": false if False else False,
        "hosted_provider_is_semantic_owner": contract["authority"]["hosted_provider_is_semantic_owner"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--input", type=Path, default=REGISTER_PATH)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    result = validate_all(load_json(args.contract), load_json(args.input))
    if args.summary:
        print(
            "prompt-regression-safety: PASS "
            f"families={result['families']} "
            f"occurrences={result['occurrences']} "
            f"threshold={result['systemic_threshold']} "
            "matrix_exhaustive=false provider_semantic_owner=false"
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
