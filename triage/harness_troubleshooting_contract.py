"""Validate the live-evidence troubleshooting doctrine and canonical P54 prompt."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

DEFAULT_POLICY_PATH = Path(__file__).parents[1] / "configs/harness/operational_discipline_v1.json"
DEFAULT_PROMPT_PATH = Path(__file__).parents[1] / "configs/prompt_kit/v39_p54_troubleshooting_prompt.json"
DEFAULT_ARTIFACT_REGISTRY_PATH = Path(__file__).parents[1] / "configs/harness/artifact_registry_v1.json"

_REQUIRED_CONTEXT_PRECEDENCE = (
    "validated_local_runtime",
    "current_repository",
    "tests_validators_ci_artifacts_logs",
    "git_pr_history",
    "operational_documentation",
    "conversation_memory",
)
_REQUIRED_CLAIM_LABELS = (
    "CONFIRMED",
    "STALE OR UNVERIFIED",
    "HYPOTHESIS",
    "MISSING EVIDENCE",
    "BLOCKED",
)
_REQUIRED_DIAGNOSTIC_LOOP = (
    "reconstruct_current_state",
    "trace_expected_to_terminal_state",
    "identify_first_confirmed_divergence",
    "rank_root_cause_hypotheses",
    "run_smallest_discriminating_check",
    "apply_bounded_repair_when_requested",
    "validate_and_compare",
)
_REQUIRED_PROMPT_MARKERS = (
    "LATEST TRUSTWORTHY CONTEXT",
    "validated local runtime evidence",
    "first confirmed divergence",
    "smallest diagnostic action",
    "Do not freeze repository-specific filenames, commands, or paths into this prompt.",
    "ACTION COMMITMENT",
    "Task-specific execution rules override generic closeout behavior.",
)
_FORBIDDEN_PAYLOAD_MARKERS = (
    "AGENTS.md",
    "HARNESS.md",
    "configs/",
    "tests/",
    "scripts/",
    "python -m",
    "pytest",
    "npm test",
    "pwsh -File",
    "git status --short",
)
_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/(?:home|Users|mnt|tmp)/"),
)
_EXPECTED_ARTIFACT_GENERATOR = "python -m triage.prompt_kit_v39_live_context_generator"
_REQUIRED_ARTIFACT_VALIDATORS = {
    "triage.harness_troubleshooting_contract",
    "triage.prompt_kit_v39_live_context_generator --validate-only",
}


def _load_object(path: str | Path, *, label: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be one JSON object")
    return payload


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    return _load_object(path, label="operational discipline policy")


def load_prompt_contract(path: str | Path = DEFAULT_PROMPT_PATH) -> dict:
    return _load_object(path, label="troubleshooting prompt contract")


def load_artifact_registry(path: str | Path = DEFAULT_ARTIFACT_REGISTRY_PATH) -> dict:
    return _load_object(path, label="artifact registry")


def validate_policy_contract(policy: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    contract = policy.get("troubleshooting_contract")
    if not isinstance(contract, Mapping):
        return ("troubleshooting_contract missing from operational discipline",)
    if contract.get("prompt_id") != "P54":
        issues.append("troubleshooting prompt_id must remain P54")
    if contract.get("canonical_prompt_source") != "configs/prompt_kit/v39_p54_troubleshooting_prompt.json":
        issues.append("canonical troubleshooting prompt source drift")
    if contract.get("generator_entrypoint") != "triage.prompt_kit_v39_live_context_generator":
        issues.append("live-context generator entrypoint drift")
    if tuple(contract.get("context_precedence", ())) != _REQUIRED_CONTEXT_PRECEDENCE:
        issues.append("troubleshooting evidence precedence drift")
    if tuple(contract.get("claim_labels", ())) != _REQUIRED_CLAIM_LABELS:
        issues.append("troubleshooting claim labels drift")
    if tuple(contract.get("diagnostic_loop", ())) != _REQUIRED_DIAGNOSTIC_LOOP:
        issues.append("troubleshooting diagnostic loop drift")
    live = contract.get("live_contract_resolution")
    if not isinstance(live, Mapping):
        issues.append("live contract resolution policy missing")
    else:
        required_true = (
            "derive_paths_commands_and_validators_from_current_repository",
            "prefer_validated_local_runtime_evidence_when_available",
            "conversation_memory_cannot_override_newer_evidence",
        )
        for field in required_true:
            if live.get(field) is not True:
                issues.append(f"live contract rule must be true: {field}")
        if live.get("allow_frozen_repository_specific_paths_or_commands") is not False:
            issues.append("frozen repository-specific paths or commands must be forbidden")
    action = contract.get("action_commitment")
    if not isinstance(action, Mapping):
        issues.append("troubleshooting action commitment missing")
    else:
        if action.get("mutation_required_when_repair_requested") is not True:
            issues.append("repair requests must require mutation")
        if action.get("proof_required_after_mutation") is not True:
            issues.append("repair mutation must require proof")
        if action.get("diagnosis_only_stops_before_mutation") is not True:
            issues.append("diagnosis-only mode must stop before mutation")
    return tuple(issues)


def validate_prompt_contract(contract: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if contract.get("schema_version") != 1:
        issues.append("troubleshooting prompt contract schema_version must be 1")
    if contract.get("contract_id") != "v39-p54-live-evidence-troubleshooting":
        issues.append("troubleshooting prompt contract id drift")
    live = contract.get("live_contract_policy")
    if not isinstance(live, Mapping):
        issues.append("prompt live_contract_policy missing")
    else:
        if live.get("allow_frozen_repository_specific_paths_or_commands") is not False:
            issues.append("prompt contract must reject frozen repository-specific paths and commands")
        for field in (
            "derive_paths_commands_and_validators_from_current_repository",
            "prefer_validated_local_runtime_evidence_when_available",
            "conversation_memory_cannot_override_newer_evidence",
        ):
            if live.get(field) is not True:
                issues.append(f"prompt live contract rule must be true: {field}")
    prompt = contract.get("prompt")
    if not isinstance(prompt, Mapping):
        return tuple([*issues, "prompt object missing"])
    if prompt.get("prompt_id") != "P54":
        issues.append("canonical troubleshooting prompt must replace P54")
    if prompt.get("surface_family") != "standard_ai":
        issues.append("P54 troubleshooting prompt must remain standard_ai")
    if prompt.get("execution_shape") != "chat_prompt":
        issues.append("P54 troubleshooting prompt execution_shape drift")
    if prompt.get("use_for_progress") != "YES":
        issues.append("P54 troubleshooting prompt must remain progress-bearing")
    lines = prompt.get("lines")
    if not isinstance(lines, list) or not lines or any(not isinstance(line, str) for line in lines):
        return tuple([*issues, "P54 troubleshooting prompt requires non-empty string lines"])
    text = "\n".join(lines)
    if not text.startswith("PROMPT SURFACE: STANDARD AI."):
        issues.append("P54 must declare the standard-AI surface")
    if "DIRECTORY GATE" not in text:
        issues.append("P54 troubleshooting prompt requires a directory gate")
    for marker in _REQUIRED_PROMPT_MARKERS:
        if marker.lower() not in text.lower():
            issues.append(f"P54 troubleshooting marker missing: {marker}")
    for marker in _REQUIRED_CLAIM_LABELS:
        if marker not in text:
            issues.append(f"P54 claim label missing: {marker}")
    for marker in _FORBIDDEN_PAYLOAD_MARKERS:
        if marker.lower() in text.lower():
            issues.append(f"P54 freezes repository-specific command or filename: {marker}")
    for pattern in _ABSOLUTE_PATH_PATTERNS:
        if pattern.search(text):
            issues.append(f"P54 contains an absolute path pattern: {pattern.pattern}")
    return tuple(issues)


def validate_artifact_registry(registry: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    artifacts = registry.get("artifacts")
    if not isinstance(artifacts, list):
        return ("artifact registry requires an artifacts list",)
    matches = [item for item in artifacts if isinstance(item, Mapping) and item.get("id") == "ai-harness-prompt-kit-v39"]
    if len(matches) != 1:
        return (f"artifact registry requires exactly one ai-harness-prompt-kit-v39 record; found {len(matches)}",)
    record = matches[0]
    if record.get("generator") != _EXPECTED_ARTIFACT_GENERATOR:
        issues.append("V39 artifact registry must use the live-context generator")
    validators = record.get("validators")
    if not isinstance(validators, list):
        issues.append("V39 artifact registry validators must be a list")
    else:
        missing = sorted(_REQUIRED_ARTIFACT_VALIDATORS - set(validators))
        for validator in missing:
            issues.append(f"V39 artifact registry validator missing: {validator}")
    source_policy = str(record.get("source_policy", ""))
    if "current repository and runtime contracts" not in source_policy:
        issues.append("V39 artifact source policy must require current repository and runtime contracts")
    return tuple(issues)


def validate_all(
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    prompt_path: str | Path = DEFAULT_PROMPT_PATH,
    artifact_registry_path: str | Path = DEFAULT_ARTIFACT_REGISTRY_PATH,
) -> tuple[str, ...]:
    issues: list[str] = []
    try:
        issues.extend(validate_policy_contract(load_policy(policy_path)))
        issues.extend(validate_prompt_contract(load_prompt_contract(prompt_path)))
        issues.extend(validate_artifact_registry(load_artifact_registry(artifact_registry_path)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(str(exc))
    return tuple(issues)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT_PATH)
    parser.add_argument("--artifact-registry", type=Path, default=DEFAULT_ARTIFACT_REGISTRY_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    issues = validate_all(args.policy, args.prompt, args.artifact_registry)
    result = {
        "valid": not issues,
        "policy": str(args.policy),
        "prompt": str(args.prompt),
        "artifact_registry": str(args.artifact_registry),
        "issues": list(issues),
    }
    print(json.dumps(result, indent=2) if args.json or issues else "live-evidence troubleshooting contract: PASS")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
