#!/usr/bin/env python3
"""Validate prompt-registry harness contracts and protected output routing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOT = ROOT / "harness" / "prompt-registry"
DOMAIN_MANIFEST = DOMAIN_ROOT / "manifest.v1.json"
ROOT_MANIFEST = ROOT / "harness" / "manifest.v1.json"
CAPABILITIES = DOMAIN_ROOT / "capabilities.v1.json"
TRIGGERS = DOMAIN_ROOT / "triggers.v1.json"
PROFILE_SCHEMA = DOMAIN_ROOT / "execution-profile.v1.json"
CANARY = ROOT / "harness" / "contracts" / "conversation-canary.v1.json"
EFFICIENCY_POLICY = DOMAIN_ROOT / "prompt-efficiency-eval.v1.json"
EFFICIENCY_FIXTURES = DOMAIN_ROOT / "fixtures" / "prompt-efficiency-cases.v1.json"
PROTECTED_OUTPUT_ROOTS = (ROOT / "Candidates", ROOT / "Active")

REQUIRED_COMPONENT_IDS = {
    "codebase_map", "workflow_spec", "artifact_registry",
    "capability_registry", "trigger_registry", "execution_profile",
    "conversation_canary_contract", "prompt_efficiency_policy",
    "prompt_efficiency_fixtures", "contract_validator", "profile_engine",
    "auditor", "prompt_efficiency_contracts", "prompt_efficiency_cases",
    "prompt_efficiency_judge", "prompt_efficiency_engine",
    "prompt_efficiency_cli", "contract_tests", "prompt_efficiency_tests",
    "operator_report", "prompt_efficiency_operator_report", "pre_push_hook",
    "ci_workflow",
}
REQUIRED_SKILL_SECTIONS = (
    "## Trigger", "## Required inputs", "## Outputs", "## Procedure",
    "## Guardrails", "## Validation", "## Proof ceiling",
)


class PromptRegistryHarnessError(RuntimeError):
    """Raised when the domain harness or registry is structurally invalid."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptRegistryHarnessError(
            f"missing file: {path.relative_to(ROOT)}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise PromptRegistryHarnessError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def require_file(relative_path: str) -> Path:
    path = ROOT / relative_path
    if not path.is_file() or path.stat().st_size == 0:
        raise PromptRegistryHarnessError(f"missing or empty file: {relative_path}")
    return path


def validate_output_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    for protected in PROTECTED_OUTPUT_ROOTS:
        try:
            resolved.relative_to(protected.resolve())
        except ValueError:
            continue
        raise PromptRegistryHarnessError(
            "output path is inside protected input root: "
            f"{protected.relative_to(ROOT)}"
        )
    return resolved


def _validate_root_registration() -> None:
    root_manifest = load_json(ROOT_MANIFEST)
    registration = root_manifest.get("domain_contracts", {}).get(
        "prompt_registry_passage"
    )
    if not isinstance(registration, dict):
        raise PromptRegistryHarnessError(
            "root harness manifest does not register prompt_registry_passage"
        )
    expected = {
        "manifest": "harness/prompt-registry/manifest.v1.json",
        "conversation_canary_contract":
            "harness/contracts/conversation-canary.v1.json",
        "auditor": "scripts/audit_prompt_registry_harness.py",
        "contract_tests": "tests/test_prompt_registry_harness.py",
        "workflow": "harness/prompt-registry/WORKFLOW.md",
        "prompt_efficiency_policy":
            "harness/prompt-registry/prompt-efficiency-eval.v1.json",
        "prompt_efficiency_evaluator": "scripts/evaluate_prompt_efficiency.py",
        "prompt_efficiency_tests": "tests/test_prompt_efficiency_eval.py",
    }
    for key, value in expected.items():
        if registration.get(key) != value:
            raise PromptRegistryHarnessError(
                f"root prompt-registry registration drifted: {key}"
            )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != "prompt-registry-harness/v1":
        raise PromptRegistryHarnessError("unsupported domain manifest schema")
    if manifest.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise PromptRegistryHarnessError("domain manifest repository is not canonical")
    if manifest.get("domain") != "prompt-registry":
        raise PromptRegistryHarnessError("domain manifest name drifted")
    components = manifest.get("components")
    if not isinstance(components, dict) or set(components) != REQUIRED_COMPONENT_IDS:
        drift = sorted(set(components or {}) ^ REQUIRED_COMPONENT_IDS)
        raise PromptRegistryHarnessError(f"domain component drift: {drift}")
    for relative_path in components.values():
        require_file(str(relative_path))
    sources = manifest.get("canonical_prompt_sources")
    if not isinstance(sources, list) or len(sources) < 4:
        raise PromptRegistryHarnessError(
            "domain manifest canonical_prompt_sources are incomplete"
        )
    for relative_path in sources:
        require_file(str(relative_path))
    expected_artifacts = {
        "audit", "strict_canary_audit", "prompt_efficiency_audit",
        "prompt_efficiency_strict_audit", "prompt_efficiency_judge_packets",
        "prompt_efficiency_judge_results",
    }
    artifacts = manifest.get("runtime_artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != expected_artifacts:
        raise PromptRegistryHarnessError("domain runtime artifact registry drifted")
    for relative_path in artifacts.values():
        if not str(relative_path).startswith("Outputs/"):
            raise PromptRegistryHarnessError(
                f"runtime artifact must live under Outputs/: {relative_path}"
            )
    order = manifest.get("validation_order")
    if not isinstance(order, list) or len(order) < 9:
        raise PromptRegistryHarnessError("domain validation order is incomplete")
    required_commands = (
        "python -m unittest tests.test_prompt_registry_harness -v",
        "python -m unittest tests.test_prompt_efficiency_eval -v",
        "python scripts/audit_prompt_registry_harness.py --output "
        "Outputs/prompt-registry-harness-audit.json --summary",
        "python scripts/evaluate_prompt_efficiency.py --output "
        "Outputs/prompt-efficiency-eval.json --emit-judge-packets "
        "Outputs/prompt-efficiency-judge-packets.json --summary",
        "python scripts/validate_harness.py",
        "python scripts/build_prompt_kit_registry.py --output "
        "web/prompt-kit/index.html --check",
        "git diff --check",
    )
    for command in required_commands:
        if command not in order:
            raise PromptRegistryHarnessError(
                f"domain validation order is missing: {command}"
            )
    if order[-1] != "git diff --check":
        raise PromptRegistryHarnessError(
            "domain validation order must close with git diff --check"
        )
    if not str(manifest.get("strict_efficiency_gate", "")).startswith(
        "python scripts/evaluate_prompt_efficiency.py"
    ):
        raise PromptRegistryHarnessError("strict efficiency gate is missing")


def _validate_skills(manifest: dict[str, Any]) -> None:
    skill_paths = manifest.get("skills")
    if not isinstance(skill_paths, list) or len(skill_paths) != 7:
        raise PromptRegistryHarnessError(
            "domain manifest does not register all scoped skills"
        )
    if len(skill_paths) != len(set(skill_paths)):
        raise PromptRegistryHarnessError("duplicate scoped skill paths")
    for relative_path in skill_paths:
        text = require_file(str(relative_path)).read_text(encoding="utf-8")
        for heading in REQUIRED_SKILL_SECTIONS:
            if heading not in text:
                raise PromptRegistryHarnessError(
                    f"{relative_path} missing {heading}"
                )


def _validate_capabilities_and_triggers() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    payload = load_json(CAPABILITIES)
    if payload.get("schema_version") != "prompt-registry-capabilities/v1":
        raise PromptRegistryHarnessError("unsupported domain capability schema")
    items = payload.get("capabilities")
    if not isinstance(items, list) or not items:
        raise PromptRegistryHarnessError("domain capability registry is empty")
    capability_by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        capability_id = str(item.get("id", ""))
        if not capability_id or capability_id in capability_by_id:
            raise PromptRegistryHarnessError(
                f"duplicate or empty capability: {capability_id}"
            )
        capability_by_id[capability_id] = item
        require_file(str(item.get("skill", "")))
        if not item.get("inputs") or not item.get("outputs"):
            raise PromptRegistryHarnessError(
                f"capability lacks I/O: {capability_id}"
            )
        implementation = item.get("implementation")
        if not isinstance(implementation, dict):
            raise PromptRegistryHarnessError(
                f"capability lacks implementation contract: {capability_id}"
            )
        if implementation.get("kind") not in {"contract", "skill", "script"}:
            raise PromptRegistryHarnessError(
                f"unsupported domain capability implementation: {capability_id}"
            )
        require_file(str(implementation.get("path", "")))
        if item.get("status") != "canonical":
            raise PromptRegistryHarnessError(
                f"domain capability must be canonical: {capability_id}"
            )
    if "prompt-efficiency-evaluation" not in capability_by_id:
        raise PromptRegistryHarnessError(
            "prompt-efficiency-evaluation capability is missing"
        )

    trigger_payload = load_json(TRIGGERS)
    if trigger_payload.get("schema_version") != "prompt-registry-triggers/v1":
        raise PromptRegistryHarnessError("unsupported domain trigger schema")
    triggers = trigger_payload.get("triggers")
    if not isinstance(triggers, list) or not triggers:
        raise PromptRegistryHarnessError("domain trigger registry is empty")
    trigger_ids: set[str] = set()
    for trigger in triggers:
        trigger_id = str(trigger.get("id", ""))
        if not trigger_id or trigger_id in trigger_ids:
            raise PromptRegistryHarnessError(
                f"duplicate or empty trigger: {trigger_id}"
            )
        trigger_ids.add(trigger_id)
        capability_id = str(trigger.get("capability_id", ""))
        if capability_id not in capability_by_id:
            raise PromptRegistryHarnessError(
                f"trigger references unknown capability: {trigger_id} -> {capability_id}"
            )
        if trigger.get("skill") != capability_by_id[capability_id]["skill"]:
            raise PromptRegistryHarnessError(f"trigger skill drift: {trigger_id}")
        if not trigger.get("conditions"):
            raise PromptRegistryHarnessError(
                f"trigger lacks positive conditions: {trigger_id}"
            )
        if not isinstance(trigger.get("forbidden_conditions"), list):
            raise PromptRegistryHarnessError(
                f"trigger forbidden conditions are not a list: {trigger_id}"
            )
    for capability_id, capability in capability_by_id.items():
        registered = set(capability.get("trigger_ids", []))
        actual = {
            str(item["id"])
            for item in triggers
            if item.get("capability_id") == capability_id
        }
        if registered != actual:
            raise PromptRegistryHarnessError(
                f"capability trigger drift: {capability_id} "
                f"registered={sorted(registered)} actual={sorted(actual)}"
            )
    return capability_by_id, triggers


def _validate_profile_and_canary() -> tuple[dict[str, Any], dict[str, Any]]:
    profile = load_json(PROFILE_SCHEMA)
    if profile.get("schema_version") != "prompt-execution-profile/v1":
        raise PromptRegistryHarnessError("unsupported execution profile schema")
    if not profile.get("required_fields") or not profile.get("forbidden_fields"):
        raise PromptRegistryHarnessError("execution profile fields are incomplete")
    enums = profile.get("enums")
    if not isinstance(enums, dict):
        raise PromptRegistryHarnessError("execution profile enums are missing")
    for field in ("impact_class", "context_class", "proof_class"):
        if not isinstance(enums.get(field), list) or not enums[field]:
            raise PromptRegistryHarnessError(
                f"execution profile enum is missing: {field}"
            )
    canary = load_json(CANARY)
    if canary.get("schema_version") != "conversation-canary-contract/v1":
        raise PromptRegistryHarnessError("unsupported canary contract schema")
    expected_lines = [
        "OBJECTIVE: <the current concrete objective>",
        "REPOS: <canonical owner/repository names with active branch when known, "
        "separated by semicolons; or none>",
    ]
    if canary.get("required_first_nonempty_lines") != expected_lines:
        raise PromptRegistryHarnessError("conversation canary prefix drifted")
    return profile, canary


def _validate_efficiency_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    policy = load_json(EFFICIENCY_POLICY)
    if policy.get("schema_version") != "prompt-efficiency-eval-policy/v1":
        raise PromptRegistryHarnessError("unsupported prompt-efficiency policy schema")
    if set(policy.get("evaluation_lanes", {})) != {
        "code_based", "llm_judge", "human", "user"
    }:
        raise PromptRegistryHarnessError("prompt-efficiency eval lanes drifted")
    if set(policy.get("rubrics", {})) != {
        "prompt-registry", "model-response"
    }:
        raise PromptRegistryHarnessError("prompt-efficiency rubrics drifted")
    judge = policy.get("judge")
    if not isinstance(judge, dict) or int(judge.get("minimum_judges_per_case", 0)) < 1:
        raise PromptRegistryHarnessError("prompt-efficiency judge contract is invalid")
    fixtures = load_json(EFFICIENCY_FIXTURES)
    if fixtures.get("schema_version") != "prompt-efficiency-fixtures/v1":
        raise PromptRegistryHarnessError("unsupported prompt-efficiency fixture schema")
    cases = fixtures.get("cases")
    if not isinstance(cases, list) or len(cases) < 4:
        raise PromptRegistryHarnessError("prompt-efficiency fixtures are incomplete")
    case_ids = [str(case.get("id", "")) for case in cases]
    if any(not item for item in case_ids) or len(case_ids) != len(set(case_ids)):
        raise PromptRegistryHarnessError(
            "prompt-efficiency fixture IDs are empty or duplicate"
        )
    target_kinds = {str(case.get("target_kind", "")) for case in cases}
    if target_kinds != {"prompt-registry", "model-response"}:
        raise PromptRegistryHarnessError(
            "prompt-efficiency fixtures do not cover both target kinds"
        )
    return policy, fixtures


def validate_domain_harness() -> dict[str, Any]:
    manifest = load_json(DOMAIN_MANIFEST)
    _validate_root_registration()
    _validate_manifest(manifest)
    _validate_skills(manifest)
    capabilities, triggers = _validate_capabilities_and_triggers()
    profile_schema, canary = _validate_profile_and_canary()
    efficiency_policy, efficiency_fixtures = _validate_efficiency_contract()
    return {
        "manifest": manifest,
        "capabilities": capabilities,
        "triggers": triggers,
        "profile_schema": profile_schema,
        "canary": canary,
        "efficiency_policy": efficiency_policy,
        "efficiency_fixtures": efficiency_fixtures,
    }
