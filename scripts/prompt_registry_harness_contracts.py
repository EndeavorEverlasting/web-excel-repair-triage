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
PROTECTED_OUTPUT_ROOTS = (ROOT / "Candidates", ROOT / "Active")

REQUIRED_COMPONENT_IDS = {
    "codebase_map",
    "workflow_spec",
    "artifact_registry",
    "capability_registry",
    "trigger_registry",
    "execution_profile",
    "conversation_canary_contract",
    "contract_validator",
    "profile_engine",
    "auditor",
    "contract_tests",
    "operator_report",
    "pre_push_hook",
    "ci_workflow",
}
REQUIRED_SKILL_SECTIONS = (
    "## Trigger",
    "## Required inputs",
    "## Outputs",
    "## Procedure",
    "## Guardrails",
    "## Validation",
    "## Proof ceiling",
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


def validate_domain_harness() -> dict[str, Any]:
    manifest = load_json(DOMAIN_MANIFEST)
    if manifest.get("schema_version") != "prompt-registry-harness/v1":
        raise PromptRegistryHarnessError("unsupported domain manifest schema")
    if manifest.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise PromptRegistryHarnessError(
            "domain manifest repository is not canonical"
        )
    if manifest.get("domain") != "prompt-registry":
        raise PromptRegistryHarnessError("domain manifest name drifted")

    root_manifest = load_json(ROOT_MANIFEST)
    domain_registration = (
        root_manifest.get("domain_contracts", {}).get("prompt_registry_passage")
    )
    if not isinstance(domain_registration, dict):
        raise PromptRegistryHarnessError(
            "root harness manifest does not register prompt_registry_passage"
        )
    expected_registration = {
        "manifest": "harness/prompt-registry/manifest.v1.json",
        "conversation_canary_contract":
            "harness/contracts/conversation-canary.v1.json",
        "auditor": "scripts/audit_prompt_registry_harness.py",
        "contract_tests": "tests/test_prompt_registry_harness.py",
        "workflow": "harness/prompt-registry/WORKFLOW.md",
    }
    for key, value in expected_registration.items():
        if domain_registration.get(key) != value:
            raise PromptRegistryHarnessError(
                f"root prompt-registry registration drifted: {key}"
            )

    components = manifest.get("components")
    if not isinstance(components, dict) or set(components) != REQUIRED_COMPONENT_IDS:
        drift = sorted(set(components or {}) ^ REQUIRED_COMPONENT_IDS)
        raise PromptRegistryHarnessError(f"domain component drift: {drift}")
    for relative_path in components.values():
        require_file(str(relative_path))

    canonical_sources = manifest.get("canonical_prompt_sources")
    if not isinstance(canonical_sources, list) or len(canonical_sources) < 4:
        raise PromptRegistryHarnessError(
            "domain manifest canonical_prompt_sources are incomplete"
        )
    for relative_path in canonical_sources:
        require_file(str(relative_path))

    runtime_artifacts = manifest.get("runtime_artifacts")
    if not isinstance(runtime_artifacts, dict) or set(runtime_artifacts) != {
        "audit",
        "strict_canary_audit",
    }:
        raise PromptRegistryHarnessError("domain runtime artifact registry drifted")
    for relative_path in runtime_artifacts.values():
        if not str(relative_path).startswith("Outputs/"):
            raise PromptRegistryHarnessError(
                f"runtime artifact must live under Outputs/: {relative_path}"
            )

    validation_order = manifest.get("validation_order")
    if not isinstance(validation_order, list) or len(validation_order) < 7:
        raise PromptRegistryHarnessError("domain validation order is incomplete")
    for required_command in (
        "python -m unittest tests.test_prompt_registry_harness -v",
        "python scripts/audit_prompt_registry_harness.py --output "
        "Outputs/prompt-registry-harness-audit.json --summary",
        "python scripts/validate_harness.py",
        "python scripts/build_prompt_kit_registry.py --output "
        "web/prompt-kit/index.html --check",
        "git diff --check",
    ):
        if required_command not in validation_order:
            raise PromptRegistryHarnessError(
                f"domain validation order is missing: {required_command}"
            )
    if validation_order[-1] != "git diff --check":
        raise PromptRegistryHarnessError(
            "domain validation order must close with git diff --check"
        )

    skill_paths = manifest.get("skills")
    if not isinstance(skill_paths, list) or len(skill_paths) < 6:
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

    capability_payload = load_json(CAPABILITIES)
    if capability_payload.get("schema_version") != (
        "prompt-registry-capabilities/v1"
    ):
        raise PromptRegistryHarnessError(
            "unsupported domain capability schema"
        )
    capability_list = capability_payload.get("capabilities")
    if not isinstance(capability_list, list) or not capability_list:
        raise PromptRegistryHarnessError(
            "domain capability registry is empty"
        )
    capability_by_id: dict[str, dict[str, Any]] = {}
    for item in capability_list:
        capability_id = str(item.get("id", ""))
        if not capability_id or capability_id in capability_by_id:
            raise PromptRegistryHarnessError(
                f"duplicate or empty capability: {capability_id}"
            )
        capability_by_id[capability_id] = item
        skill = str(item.get("skill", ""))
        require_file(skill)
        if not item.get("inputs") or not item.get("outputs"):
            raise PromptRegistryHarnessError(
                f"capability lacks I/O: {capability_id}"
            )
        implementation = item.get("implementation")
        if not isinstance(implementation, dict):
            raise PromptRegistryHarnessError(
                f"capability lacks implementation contract: {capability_id}"
            )
        kind = str(implementation.get("kind", ""))
        implementation_path = str(implementation.get("path", ""))
        if kind not in {"contract", "skill", "script"}:
            raise PromptRegistryHarnessError(
                "unsupported domain capability implementation: "
                f"{capability_id} -> {kind}"
            )
        require_file(implementation_path)
        if str(item.get("status", "")) != "canonical":
            raise PromptRegistryHarnessError(
                f"domain capability must be canonical: {capability_id}"
            )

    trigger_payload = load_json(TRIGGERS)
    if trigger_payload.get("schema_version") != "prompt-registry-triggers/v1":
        raise PromptRegistryHarnessError("unsupported domain trigger schema")
    trigger_list = trigger_payload.get("triggers")
    if not isinstance(trigger_list, list) or not trigger_list:
        raise PromptRegistryHarnessError("domain trigger registry is empty")
    trigger_ids: set[str] = set()
    for trigger in trigger_list:
        trigger_id = str(trigger.get("id", ""))
        if not trigger_id or trigger_id in trigger_ids:
            raise PromptRegistryHarnessError(
                f"duplicate or empty trigger: {trigger_id}"
            )
        trigger_ids.add(trigger_id)
        capability_id = str(trigger.get("capability_id", ""))
        if capability_id not in capability_by_id:
            raise PromptRegistryHarnessError(
                "trigger references unknown capability: "
                f"{trigger_id} -> {capability_id}"
            )
        if trigger.get("skill") != capability_by_id[capability_id]["skill"]:
            raise PromptRegistryHarnessError(
                f"trigger skill drift: {trigger_id}"
            )
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
            for item in trigger_list
            if item.get("capability_id") == capability_id
        }
        if registered != actual:
            raise PromptRegistryHarnessError(
                "capability trigger drift: "
                f"{capability_id} registered={sorted(registered)} "
                f"actual={sorted(actual)}"
            )

    profile_schema = load_json(PROFILE_SCHEMA)
    if profile_schema.get("schema_version") != "prompt-execution-profile/v1":
        raise PromptRegistryHarnessError(
            "unsupported execution profile schema"
        )
    required_fields = profile_schema.get("required_fields")
    forbidden_fields = profile_schema.get("forbidden_fields")
    if not isinstance(required_fields, list) or not required_fields:
        raise PromptRegistryHarnessError(
            "execution profile required_fields are missing"
        )
    if not isinstance(forbidden_fields, list) or not forbidden_fields:
        raise PromptRegistryHarnessError(
            "execution profile forbidden_fields are missing"
        )
    enums = profile_schema.get("enums")
    if not isinstance(enums, dict):
        raise PromptRegistryHarnessError("execution profile enums are missing")
    for field in ("impact_class", "context_class", "proof_class"):
        if not isinstance(enums.get(field), list) or not enums[field]:
            raise PromptRegistryHarnessError(
                f"execution profile enum is missing: {field}"
            )

    canary = load_json(CANARY)
    if canary.get("schema_version") != "conversation-canary-contract/v1":
        raise PromptRegistryHarnessError(
            "unsupported canary contract schema"
        )
    if canary.get("required_first_nonempty_lines") != [
        "OBJECTIVE: <the current concrete objective>",
        "REPOS: <canonical owner/repository names with active branch when known, "
        "separated by semicolons; or none>",
    ]:
        raise PromptRegistryHarnessError(
            "conversation canary prefix drifted"
        )
    return {
        "manifest": manifest,
        "capabilities": capability_by_id,
        "triggers": trigger_list,
        "profile_schema": profile_schema,
        "canary": canary,
    }
