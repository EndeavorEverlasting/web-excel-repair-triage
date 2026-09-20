#!/usr/bin/env python3
"""Validate Prompt Kit recurring-defect regression safety.

The retrospective matrix is intentionally not the only intake path. This
validator proves that recurring defects can be registered from repository
history/local gates/review/runtime evidence, are routed to a canonical owner,
and remain connected to repository-owned local proof surfaces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-regression-safety.v1.json"
REGISTER_PATH = ROOT / "harness" / "evals" / "prompt-regression" / "defect-families.v1.json"
POLICY_PATH = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
TEST_FLOOR_PATH = ROOT / "harness" / "test-floor.v1.json"
REQUIRED_CHECKS_PATH = ROOT / "harness" / "promotion" / "required-checks.v1.json"
PRE_COMMIT_PATH = ROOT / ".githooks" / "pre-commit"
GITATTRIBUTES_PATH = ROOT / ".gitattributes"
VALIDATORS_PATH = ROOT / "harness" / "validators.v1.json"
FOCUSED_TEST = "tests/test_prompt_regression_safety_prompt.py"
COVERAGE_BASELINE_PATH = ROOT / "harness" / "evals" / "prompt-regression" / "prompt-coverage-baseline.v1.json"
SEMANTIC_PROFILES_PATH = ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json"
OVERRIDE_REGISTRY_PATH = ROOT / "registry" / "prompts" / "prompt-overrides.v1.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
KNOWN_UNPROFILED_SEED_SHA256 = "75d6746dc6310b157fb7526f20939c849b1b0c05dc07f863c58d5ac30c6c4cfd"
CANONICAL_LF_PATTERNS = [".gitattributes","*.py","*.json","*.md","*.yml","*.yaml","*.toml","*.ini","*.cfg","*.js","*.css","*.html","*.sh","*.ps1","*.txt","*.csv","*.tsv","*.xml","*.sha256","*.webmanifest"]
CANONICAL_CRLF_PATTERNS = ["*.cmd","*.bat"]
CANONICAL_BINARY_PATTERNS = ["*.xlsx","*.xlsm","*.xlsb","*.xls","*.docx","*.pptx","*.pdf","*.zip","*.png","*.jpg","*.jpeg","*.gif","*.webp"]


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


def _string_list(value: Any, field: str, *, min_items: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise RegressionSafetyError(f"{field} must be a list with at least {min_items} item(s)")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_text(item, f"{field}[{index}]"))
    if len(result) != len(set(result)):
        raise RegressionSafetyError(f"{field} must contain unique strings")
    return result


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}".encode("ascii") + bytes([0])
    return hashlib.sha1(header + data).hexdigest()


def _string_list_sha256(values: list[str]) -> str:
    canonical = json.dumps(sorted(values), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_operational_prompts() -> list[dict[str, Any]]:
    import sys

    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    from scripts import build_prompt_kit_registry as prompt_registry

    return [dict(prompt) for prompt in prompt_registry.load_prompt_registry()]


def _owner_text(prompt: dict[str, Any], fields: list[str]) -> str:
    values: list[str] = []
    for field in fields:
        value = prompt.get(field, "")
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return " ".join(values).casefold()


def _contains_owner_term(text: str, term: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(term.casefold())}(?![A-Za-z0-9_])",
        text,
    ) is not None


def _validate_coverage_baseline_shape(
    baseline: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    if baseline.get("schema_version") != "prompt-regression-coverage-baseline/v1":
        raise RegressionSafetyError("unsupported prompt regression coverage baseline")
    if baseline.get("baseline_id") != "prompt-regression-coverage-ratchet":
        raise RegressionSafetyError("unexpected prompt regression coverage baseline_id")

    ratchet = contract["prompt_coverage_ratcheting"]
    for field in ("operational_loader", "semantic_profile_owner", "override_registry"):
        if baseline.get(field) != ratchet[field]:
            raise RegressionSafetyError(f"coverage baseline {field} drifted from contract")

    operational_count = baseline.get("operational_prompt_count")
    accepted_count = baseline.get("accepted_profile_count")
    if type(operational_count) is not int or operational_count < 1:
        raise RegressionSafetyError("coverage baseline operational_prompt_count must be positive")
    if type(accepted_count) is not int or accepted_count < 1:
        raise RegressionSafetyError("coverage baseline accepted_profile_count must be positive")

    debt = _string_list(
        baseline.get("known_unprofiled_prompt_ids"),
        "coverage_baseline.known_unprofiled_prompt_ids",
        min_items=1,
    )
    seed_sha = baseline.get("known_unprofiled_seed_sha256")
    if seed_sha != KNOWN_UNPROFILED_SEED_SHA256:
        raise RegressionSafetyError("coverage baseline known-unprofiled debt seed identity drifted")
    if _string_list_sha256(debt) != KNOWN_UNPROFILED_SEED_SHA256:
        raise RegressionSafetyError(
            "coverage baseline known-unprofiled debt seed is immutable; new IDs cannot be allowlisted"
        )
    if operational_count - accepted_count != len(debt):
        raise RegressionSafetyError(
            "coverage baseline counts must exactly explain known unprofiled debt"
        )

    classification = baseline.get("closeout_or_review_classification")
    if not isinstance(classification, dict):
        raise RegressionSafetyError("coverage baseline closeout_or_review_classification must be an object")
    if classification.get("fields") != ratchet["closeout_or_review_owner_fields"]:
        raise RegressionSafetyError("coverage baseline owner fields drifted from contract")
    for field in ("closeout_terms", "review_terms"):
        _string_list(classification.get(field), f"coverage_baseline.{field}")

    owner_ids = _string_list(
        baseline.get("closeout_or_review_owner_ids"),
        "coverage_baseline.closeout_or_review_owner_ids",
    )
    unprofiled_owner_ids = _string_list(
        baseline.get("closeout_or_review_unprofiled_ids"),
        "coverage_baseline.closeout_or_review_unprofiled_ids",
    )
    if not set(unprofiled_owner_ids).issubset(owner_ids):
        raise RegressionSafetyError("closeout/review unprofiled IDs must be owner IDs")
    if not set(unprofiled_owner_ids).issubset(debt):
        raise RegressionSafetyError("closeout/review unprofiled IDs must be known debt")

    blob_sha = baseline.get("override_registry_git_blob_sha1")
    if not isinstance(blob_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
        raise RegressionSafetyError("coverage baseline override blob must be lowercase 40-hex")

    bindings = baseline.get("override_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise RegressionSafetyError("coverage baseline override_bindings must be non-empty")
    seen: set[str] = set()
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            raise RegressionSafetyError(f"override binding[{index}] must be an object")
        prompt_id = _text(binding.get("prompt_id"), f"override binding[{index}].prompt_id")
        if prompt_id in seen:
            raise RegressionSafetyError(f"duplicate override binding: {prompt_id}")
        seen.add(prompt_id)
        _string_list(binding.get("required_markers"), f"{prompt_id}.required_markers")
        marker_match_mode = binding.get("marker_match_mode")
        if marker_match_mode not in {"SUBSTRING", "EXACT_LINE"}:
            raise RegressionSafetyError(
                f"{prompt_id}.marker_match_mode must be SUBSTRING or EXACT_LINE"
            )
        refs = _string_list(
            binding.get("focused_regression_refs"),
            f"{prompt_id}.focused_regression_refs",
        )
        if FOCUSED_TEST not in refs and prompt_id != "P02":
            raise RegressionSafetyError(
                f"{prompt_id} must retain the shared deterministic-floor regression gate"
            )

    _text(baseline.get("proof_ceiling"), "coverage_baseline.proof_ceiling")


def validate_prompt_coverage_ratchet(
    contract: dict[str, Any],
    baseline: dict[str, Any] | None = None,
    *,
    operational_prompts: list[dict[str, Any]] | None = None,
    profiles_data: dict[str, Any] | None = None,
    override_payload: dict[str, Any] | None = None,
    override_bytes: bytes | None = None,
) -> dict[str, Any]:
    ratchet = contract.get("prompt_coverage_ratcheting")
    if not isinstance(ratchet, dict):
        raise RegressionSafetyError("prompt_coverage_ratcheting must be an object")

    baseline = load_json(COVERAGE_BASELINE_PATH) if baseline is None else baseline
    _validate_coverage_baseline_shape(baseline, contract)

    operational_prompts = (
        _load_operational_prompts() if operational_prompts is None else operational_prompts
    )
    operational_ids: list[str] = []
    for index, prompt in enumerate(operational_prompts):
        if not isinstance(prompt, dict):
            raise RegressionSafetyError(f"operational prompt[{index}] must be an object")
        prompt_id = _text(prompt.get("id"), f"operational prompt[{index}].id")
        operational_ids.append(prompt_id)
    if len(operational_ids) != len(set(operational_ids)):
        raise RegressionSafetyError("operational Prompt Kit contains duplicate prompt IDs")

    profiles_data = load_json(SEMANTIC_PROFILES_PATH) if profiles_data is None else profiles_data
    rows = profiles_data.get("profiles")
    if not isinstance(rows, list):
        raise RegressionSafetyError("semantic profile owner must define profiles")
    accepted_ids = [
        _text(row.get("prompt_id"), "semantic profile prompt_id")
        for row in rows
        if isinstance(row, dict) and row.get("profile_status") == "ACCEPTED"
    ]
    if len(accepted_ids) != len(set(accepted_ids)):
        raise RegressionSafetyError("semantic coverage has duplicate ACCEPTED prompt IDs")
    accepted_set = set(accepted_ids)

    current_unprofiled = [prompt_id for prompt_id in operational_ids if prompt_id not in accepted_set]
    known_debt = set(baseline["known_unprofiled_prompt_ids"])
    new_debt = sorted(set(current_unprofiled) - known_debt)
    if new_debt:
        raise RegressionSafetyError(
            "new unprofiled operational prompt(s) escaped the semantic coverage ratchet: "
            + ", ".join(new_debt)
        )
    if len(accepted_ids) < int(baseline["accepted_profile_count"]):
        raise RegressionSafetyError(
            "accepted semantic profile count regressed below the coverage baseline"
        )

    classification = baseline["closeout_or_review_classification"]
    owner_fields = classification["fields"]
    closeout_terms = classification["closeout_terms"]
    review_terms = classification["review_terms"]
    current_owner_ids: list[str] = []
    for prompt in operational_prompts:
        text = _owner_text(prompt, owner_fields)
        if any(_contains_owner_term(text, term) for term in (*closeout_terms, *review_terms)):
            current_owner_ids.append(str(prompt["id"]))

    if set(current_owner_ids) != set(baseline["closeout_or_review_owner_ids"]):
        raise RegressionSafetyError(
            "closeout OR review owner set drifted; refresh the reviewed coverage baseline"
        )
    current_owner_unprofiled = [
        prompt_id for prompt_id in current_owner_ids if prompt_id not in accepted_set
    ]
    unexpected_owner_debt = sorted(
        set(current_owner_unprofiled) - set(baseline["closeout_or_review_unprofiled_ids"])
    )
    if unexpected_owner_debt:
        raise RegressionSafetyError(
            "new closeout/review owner lacks an accepted semantic profile: "
            + ", ".join(unexpected_owner_debt)
        )

    if override_payload is None:
        override_payload = load_json(OVERRIDE_REGISTRY_PATH)
    if override_bytes is None:
        override_bytes = OVERRIDE_REGISTRY_PATH.read_bytes()
    if _git_blob_sha1(override_bytes) != baseline["override_registry_git_blob_sha1"]:
        raise RegressionSafetyError(
            "effective override registry drifted from reviewed coverage baseline"
        )

    overrides = override_payload.get("overrides")
    if not isinstance(overrides, list):
        raise RegressionSafetyError("override registry must define overrides")
    by_id: dict[str, dict[str, Any]] = {}
    for row in overrides:
        if not isinstance(row, dict):
            raise RegressionSafetyError("override registry row must be an object")
        prompt_id = _text(row.get("id"), "override prompt id")
        if prompt_id in by_id:
            raise RegressionSafetyError(f"duplicate override prompt: {prompt_id}")
        by_id[prompt_id] = row

    bindings = {item["prompt_id"]: item for item in baseline["override_bindings"]}
    if set(by_id) != set(bindings):
        raise RegressionSafetyError(
            "override registry IDs drifted from effective regression bindings"
        )
    for prompt_id, row in by_id.items():
        binding = bindings[prompt_id]
        copy_content = str(row.get("copyContent", ""))
        marker_mode = binding["marker_match_mode"]
        exact_lines = {line.strip() for line in copy_content.splitlines()}
        for marker in binding["required_markers"]:
            marker_present = marker in copy_content if marker_mode == "SUBSTRING" else marker in exact_lines
            if not marker_present:
                raise RegressionSafetyError(
                    f"{prompt_id} effective override lost required regression marker: {marker}"
                )
        for ref in binding["focused_regression_refs"]:
            path = (ROOT / ref).resolve()
            try:
                path.relative_to(ROOT)
            except ValueError as exc:
                raise RegressionSafetyError(
                    f"{prompt_id} regression ref escapes repository: {ref}"
                ) from exc
            if not path.is_file():
                raise RegressionSafetyError(
                    f"{prompt_id} regression ref is missing: {ref}"
                )

    return {
        "operational_prompts": len(operational_ids),
        "accepted_profiles": len(accepted_ids),
        "unprofiled_prompts": len(current_unprofiled),
        "closeout_or_review_owners": len(current_owner_ids),
        "closeout_or_review_unprofiled": len(current_owner_unprofiled),
        "override_bindings": len(bindings),
    }


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

    family_contract = contract.get("defect_family_contract")
    if not isinstance(family_contract, dict):
        raise RegressionSafetyError("defect_family_contract must be an object")
    if set(family_contract) != {
        "allowed_statuses",
        "allowed_classifications",
        "allowed_prompt_strengthening",
        "occurrence_commit_format",
    }:
        raise RegressionSafetyError("defect_family_contract fields do not match schema")
    _string_list(family_contract.get("allowed_statuses"), "defect_family_contract.allowed_statuses")
    _string_list(
        family_contract.get("allowed_classifications"),
        "defect_family_contract.allowed_classifications",
    )
    allowed_prompt_strengthening = _string_list(
        family_contract.get("allowed_prompt_strengthening"),
        "defect_family_contract.allowed_prompt_strengthening",
    )
    if set(allowed_prompt_strengthening) != {"GLOBAL_SHARED_POLICY", "SCOPED_SHARED_POLICY"}:
        raise RegressionSafetyError(
            "allowed_prompt_strengthening must preserve global and scoped shared-policy modes only"
        )
    if family_contract.get("occurrence_commit_format") != "lowercase-40-hex":
        raise RegressionSafetyError("occurrence_commit_format must be lowercase-40-hex")

    recurrence = contract.get("recurrence")
    if not isinstance(recurrence, dict):
        raise RegressionSafetyError("recurrence must be an object")
    threshold = recurrence.get("systemic_threshold")
    if type(threshold) is not int or threshold < 2:
        raise RegressionSafetyError("systemic recurrence threshold must be >= 2")
    sources = _string_list(recurrence.get("incident_sources"), "recurrence.incident_sources", min_items=5)
    for required_source in (
        "local_validator",
        "local_required_check",
        "hosted_ci",
        "code_review",
        "runtime_observation",
        "operator_feedback",
        "retrospective_matrix",
        "commit_history",
    ):
        if required_source not in sources:
            raise RegressionSafetyError(f"missing incident source: {required_source}")
    _text(recurrence.get("rule"), "recurrence.rule")

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
    rules = _string_list(local_first.get("rules"), "local_first_proof.rules", min_items=4)
    joined = " ".join(rules).lower()
    for phrase in ("local profile", "exact base/head", "provider", "merge authority"):
        if phrase not in joined:
            raise RegressionSafetyError(f"local-first proof is missing concept: {phrase}")

    hygiene = contract.get("repository_hygiene")
    if not isinstance(hygiene, dict):
        raise RegressionSafetyError("repository_hygiene must be an object")
    commands = _string_list(hygiene.get("patch_hygiene_commands"), "repository_hygiene.patch_hygiene_commands")
    expected_commands = {
        "git diff --check",
        "git diff --cached --check",
        "git diff --check {base_sha}...{head_sha}",
    }
    if set(commands) != expected_commands:
        raise RegressionSafetyError("patch-hygiene commands must cover working, staged, and exact candidates")
    _text(hygiene.get("rule"), "repository_hygiene.rule")

    line_policy = hygiene.get("line_ending_policy")
    if not isinstance(line_policy, dict):
        raise RegressionSafetyError("repository_hygiene.line_ending_policy must be an object")
    required_line_policy = {
        "owner",
        "text_default",
        "lf_patterns",
        "crlf_patterns",
        "binary_patterns",
        "rule",
    }
    if set(line_policy) != required_line_policy:
        raise RegressionSafetyError("line-ending policy fields do not match contract")
    if line_policy.get("owner") != ".gitattributes":
        raise RegressionSafetyError("line-ending policy owner must be .gitattributes")
    if line_policy.get("text_default") != "* text=auto eol=lf":
        raise RegressionSafetyError("line-ending policy must retain * text=auto eol=lf")
    lf_patterns = _string_list(line_policy.get("lf_patterns"), "repository_hygiene.line_ending_policy.lf_patterns")
    crlf_patterns = _string_list(line_policy.get("crlf_patterns"), "repository_hygiene.line_ending_policy.crlf_patterns")
    binary_patterns = _string_list(line_policy.get("binary_patterns"), "repository_hygiene.line_ending_policy.binary_patterns")
    if lf_patterns != CANONICAL_LF_PATTERNS:
        raise RegressionSafetyError("line-ending LF pattern inventory drifted")
    if crlf_patterns != CANONICAL_CRLF_PATTERNS:
        raise RegressionSafetyError("line-ending CRLF pattern inventory drifted")
    if binary_patterns != CANONICAL_BINARY_PATTERNS:
        raise RegressionSafetyError("line-ending binary pattern inventory drifted")
    _text(line_policy.get("rule"), "repository_hygiene.line_ending_policy.rule")

    _text(contract.get("matrix_boundary"), "matrix_boundary")

    ratchet = contract.get("prompt_coverage_ratcheting")
    if not isinstance(ratchet, dict):
        raise RegressionSafetyError("prompt_coverage_ratcheting must be an object")
    expected_ratchet_fields = {
        "baseline",
        "operational_loader",
        "semantic_profile_owner",
        "override_registry",
        "closeout_or_review_owner_fields",
        "rules",
    }
    if set(ratchet) != expected_ratchet_fields:
        raise RegressionSafetyError("prompt_coverage_ratcheting fields do not match contract")
    if ratchet.get("baseline") != "harness/evals/prompt-regression/prompt-coverage-baseline.v1.json":
        raise RegressionSafetyError("coverage ratchet baseline path changed unexpectedly")
    if ratchet.get("operational_loader") != "scripts.build_prompt_kit_registry.load_prompt_registry":
        raise RegressionSafetyError("coverage ratchet must audit the live operational registry")
    if ratchet.get("semantic_profile_owner") != "harness/prompt-topology/prompt-capability-profiles.v1.json":
        raise RegressionSafetyError("coverage ratchet semantic profile owner changed")
    if ratchet.get("override_registry") != "registry/prompts/prompt-overrides.v1.json":
        raise RegressionSafetyError("coverage ratchet override owner changed")
    if ratchet.get("closeout_or_review_owner_fields") != [
        "name", "class", "sprintRole", "useWhen", "keywords"
    ]:
        raise RegressionSafetyError("coverage ratchet owner-classification fields drifted")
    ratchet_rules = _string_list(ratchet.get("rules"), "prompt_coverage_ratcheting.rules", min_items=5)
    joined_ratchet_rules = " ".join(ratchet_rules).lower()
    for phrase in ("may shrink", "override", "closeout", "review", "prevention"):
        if phrase not in joined_ratchet_rules:
            raise RegressionSafetyError(f"coverage ratchet rules missing concept: {phrase}")

    requirements = _string_list(
        contract.get("systemic_repair_requirements"),
        "systemic_repair_requirements",
        min_items=6,
    )
    requirement_text = " ".join(requirements).lower()
    for phrase in ("negative fixture", "positive control", "shared owner", "deterministic floor", "local required checks"):
        if phrase not in requirement_text:
            raise RegressionSafetyError(f"systemic repair requirement missing: {phrase}")
    _text(contract.get("proof_ceiling"), "proof_ceiling")


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
    family_contract = contract["defect_family_contract"]
    allowed_statuses = set(family_contract["allowed_statuses"])
    allowed_classifications = set(family_contract["allowed_classifications"])
    allowed_strengthening = set(family_contract["allowed_prompt_strengthening"])
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

        if family.get("status") not in allowed_statuses:
            raise RegressionSafetyError(f"invalid defect-family status: {family_id}")
        if family.get("classification") not in allowed_classifications:
            raise RegressionSafetyError(f"invalid defect-family classification: {family_id}")
        if family.get("prompt_strengthening") not in allowed_strengthening:
            raise RegressionSafetyError(f"invalid prompt-strengthening mode: {family_id}")
        if type(family.get("recurring_across_repositories")) is not bool:
            raise RegressionSafetyError("recurring_across_repositories must be boolean")
        if type(family.get("matrix_capture_required")) is not bool:
            raise RegressionSafetyError("matrix_capture_required must be boolean")
        _text(family.get("canonical_owner"), f"{family_id}.canonical_owner")
        _text(family.get("regression_gate"), f"{family_id}.regression_gate")
        _text(family.get("local_first_requirement"), f"{family_id}.local_first_requirement")

        detectors = _string_list(family.get("detector_commands"), f"{family_id}.detector_commands")
        prevention = _string_list(family.get("prevention_surfaces"), f"{family_id}.prevention_surfaces", min_items=2)
        if family.get("prompt_strengthening") == "GLOBAL_SHARED_POLICY" and contract["authority"]["prompt_strengthening_owner"] not in prevention:
            raise RegressionSafetyError(f"{family_id} must include the global prompt-strengthening owner")

        occurrences = family.get("occurrences")
        if not isinstance(occurrences, list) or len(occurrences) < threshold:
            raise RegressionSafetyError(
                f"{family_id} needs at least {threshold} evidenced occurrences for SYSTEMIC status"
            )
        occurrence_count += len(occurrences)
        unique_occurrences: set[tuple[str, str]] = set()
        repositories: set[str] = set()
        for occurrence_index, occurrence in enumerate(occurrences):
            if not isinstance(occurrence, dict) or set(occurrence) != {"repository", "commit", "summary"}:
                raise RegressionSafetyError(f"{family_id} occurrence is malformed")
            repository = _text(
                occurrence.get("repository"),
                f"{family_id}.occurrences[{occurrence_index}].repository",
            )
            commit = _text(
                occurrence.get("commit"),
                f"{family_id}.occurrences[{occurrence_index}].commit",
            )
            if not COMMIT_RE.fullmatch(commit):
                raise RegressionSafetyError(f"{family_id} occurrence commit must be lowercase 40-hex")
            _text(
                occurrence.get("summary"),
                f"{family_id}.occurrences[{occurrence_index}].summary",
            )
            key = (repository, commit)
            if key in unique_occurrences:
                raise RegressionSafetyError(f"duplicate occurrence in {family_id}: {repository}@{commit}")
            unique_occurrences.add(key)
            repositories.add(repository)
        if family.get("recurring_across_repositories") and len(repositories) < 2:
            raise RegressionSafetyError(f"{family_id} claims cross-repo recurrence without two repositories")

        if family_id == "TRAILING_WHITESPACE":
            required_detectors = set(contract["repository_hygiene"]["patch_hygiene_commands"])
            if set(detectors) != required_detectors:
                raise RegressionSafetyError("TRAILING_WHITESPACE must use all canonical patch-hygiene detectors")
            if family.get("classification") != "PATCH_HYGIENE":
                raise RegressionSafetyError("TRAILING_WHITESPACE must remain PATCH_HYGIENE")
            if family.get("matrix_capture_required") is not False:
                raise RegressionSafetyError("whitespace recurrence must not depend on retrospective matrix capture")
            if family.get("recurring_across_repositories") is not True:
                raise RegressionSafetyError("whitespace evidence must preserve cross-repository recurrence")

    line_ending_family = next(
        (family for family in families if family.get("id") == "LINE_ENDING_DRIFT"),
        None,
    )
    if line_ending_family is None:
        raise RegressionSafetyError("defect register must retain LINE_ENDING_DRIFT systemic family")
    if line_ending_family.get("classification") != "PATCH_HYGIENE":
        raise RegressionSafetyError("LINE_ENDING_DRIFT must remain PATCH_HYGIENE")
    if line_ending_family.get("matrix_capture_required") is not False:
        raise RegressionSafetyError("LINE_ENDING_DRIFT must not depend on retrospective matrix capture")
    if ".gitattributes" not in line_ending_family.get("prevention_surfaces", []):
        raise RegressionSafetyError("LINE_ENDING_DRIFT must retain .gitattributes prevention owner")

    return {
        "families": len(families),
        "occurrences": occurrence_count,
        "systemic_threshold": threshold,
    }


def validate_repository_wiring(
    contract: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    floor: dict[str, Any] | None = None,
    required_checks: dict[str, Any] | None = None,
    validators: dict[str, Any] | None = None,
    pre_commit_text: str | None = None,
    gitattributes_text: str | None = None,
) -> None:
    marker = contract["prompt_marker"]
    policy = load_json(POLICY_PATH) if policy is None else policy
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

    floor = load_json(TEST_FLOOR_PATH) if floor is None else floor
    if FOCUSED_TEST not in floor.get("self_tests", []):
        raise RegressionSafetyError("focused regression-safety test is not registered in deterministic floor")
    globs = _string_list(floor.get("prompt_semantic_test_globs"), "test_floor.prompt_semantic_test_globs")
    if not any("prompt" in item for item in globs):
        raise RegressionSafetyError("deterministic floor has no prompt semantic convention")

    pre_commit_text = PRE_COMMIT_PATH.read_text(encoding="utf-8") if pre_commit_text is None else pre_commit_text
    if "git diff --cached --check" not in pre_commit_text:
        raise RegressionSafetyError("pre-commit hook must retain staged patch-hygiene proof")

    gitattributes_text = (
        GITATTRIBUTES_PATH.read_text(encoding="utf-8")
        if gitattributes_text is None
        else gitattributes_text
    )
    attribute_lines = [
        line.strip()
        for line in gitattributes_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    line_policy = contract["repository_hygiene"]["line_ending_policy"]
    expected_attribute_lines = [line_policy["text_default"]]
    expected_attribute_lines.extend(f"{pattern} text eol=lf" for pattern in line_policy["lf_patterns"])
    expected_attribute_lines.extend(f"{pattern} text eol=crlf" for pattern in line_policy["crlf_patterns"])
    expected_attribute_lines.extend(f"{pattern} binary" for pattern in line_policy["binary_patterns"])
    if attribute_lines != expected_attribute_lines:
        raise RegressionSafetyError(
            "line-ending policy must exactly match contracted .gitattributes order and rules"
        )

    required_checks = load_json(REQUIRED_CHECKS_PATH) if required_checks is None else required_checks
    destinations = required_checks.get("destinations")
    if not isinstance(destinations, dict) or not isinstance(destinations.get("main"), dict):
        raise RegressionSafetyError("promotion policy must define destinations.main")
    main_policy = destinations["main"]
    exact_commands = _string_list(
        main_policy.get("exact_candidate_commands"),
        "promotion.destinations.main.exact_candidate_commands",
    )
    exact_patch_command = "git diff --check {base_sha}...{head_sha}"
    if exact_patch_command not in exact_commands:
        raise RegressionSafetyError("local required-check executable list lacks exact-candidate patch hygiene")

    validators = load_json(VALIDATORS_PATH) if validators is None else validators
    rows = validators.get("validators")
    if not isinstance(rows, list):
        raise RegressionSafetyError("validator registry must define validators")
    by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RegressionSafetyError(f"validator[{index}] must be an object")
        validator_id = _text(row.get("id"), f"validator[{index}].id")
        if validator_id in by_id:
            raise RegressionSafetyError(f"duplicate validator id: {validator_id}")
        by_id[validator_id] = row
    expected_validator_commands = {
        "patch-hygiene": "git diff --check",
        "patch-hygiene-staged": "git diff --cached --check",
    }
    for validator_id, command in expected_validator_commands.items():
        row = by_id.get(validator_id)
        if row is None or row.get("command") != command or row.get("blocking") is not True:
            raise RegressionSafetyError(
                f"validator {validator_id} must remain blocking with command: {command}"
            )

    profiles = validators.get("profiles")
    if not isinstance(profiles, dict):
        raise RegressionSafetyError("validator registry must define profiles")
    pre_commit_profile = _string_list(profiles.get("pre_commit"), "validators.profiles.pre_commit")
    pre_push_profile = _string_list(profiles.get("pre_push"), "validators.profiles.pre_push")
    if "patch-hygiene-staged" not in pre_commit_profile:
        raise RegressionSafetyError("pre_commit profile must retain patch-hygiene-staged")
    if "patch-hygiene" not in pre_push_profile:
        raise RegressionSafetyError("pre_push profile must retain patch-hygiene")


def validate_all(
    contract: dict[str, Any], register: dict[str, Any], *, check_repository_wiring: bool = True
) -> dict[str, Any]:
    validate_contract(contract)
    summary = validate_register(register, contract)
    coverage = validate_prompt_coverage_ratchet(contract)
    if check_repository_wiring:
        validate_repository_wiring(contract)
    return {
        "status": "PASS",
        "schema_version": contract["schema_version"],
        "families": summary["families"],
        "occurrences": summary["occurrences"],
        "systemic_threshold": summary["systemic_threshold"],
        "matrix_is_exhaustive": False,
        "hosted_provider_is_semantic_owner": contract["authority"]["hosted_provider_is_semantic_owner"],
        "coverage": coverage,
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
            f"operational={result['coverage']['operational_prompts']} "
            f"accepted_profiles={result['coverage']['accepted_profiles']} "
            f"unprofiled={result['coverage']['unprofiled_prompts']} "
            f"closeout_review={result['coverage']['closeout_or_review_owners']} "
            f"overrides={result['coverage']['override_bindings']} "
            "matrix_exhaustive=false provider_semantic_owner=false"
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
