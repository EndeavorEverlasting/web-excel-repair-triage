#!/usr/bin/env python3
"""Fail-closed validator and report writer for the repository operational harness."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language

MANIFEST_PATH = ROOT / "harness" / "manifest.v1.json"
WORKFLOWS_PATH = ROOT / "harness" / "workflows.v1.json"
ARTIFACTS_PATH = ROOT / "harness" / "artifacts.v1.json"
VALIDATORS_PATH = ROOT / "harness" / "validators.v1.json"
CAPABILITIES_PATH = ROOT / "harness" / "capabilities.v1.json"
TRIGGERS_PATH = ROOT / "harness" / "triggers.v1.json"
GIT_PROBE_TIMEOUT_SECONDS = 15
_TRACKED_PATHS_CACHE: set[str] | None = None

REQUIRED_SKILL_SECTIONS = (
    "## Trigger",
    "## Required inputs",
    "## Outputs",
    "## Procedure",
    "## Guardrails",
    "## Validation",
    "## Proof ceiling",
)
FORBIDDEN_ACQUISITION_PATTERNS = (
    "reset --hard",
    "clean -fd",
    "clean -xdf",
    "checkout -f",
    "branch -D",
    "push --force",
    "force-with-lease",
    "stash drop",
    "credential.helper store",
)
REQUIRED_COMPONENT_IDS = {
    "codebase_map",
    "workflow_spec",
    "artifact_registry",
    "skill_index",
    "capability_index",
    "trigger_index",
    "workflow_registry",
    "artifact_registry_machine",
    "validator_registry",
    "capability_registry",
    "trigger_registry",
    "prompt_language_eval_policy",
    "prompt_language_eval_fixtures",
    "prompt_language_eval_runner",
    "prompt_language_eval_tests",
    "validator",
    "contract_tests",
    "pre_commit_hook",
    "pre_push_hook",
    "operator_report",
}
REQUIRED_WORKFLOW_IDS = {
    "technician-acquisition",
    "prompt-kit-change",
    "harness-infrastructure",
    "artifact-engine-change",
    "pr-floor-integration",
    "prompt-language-audit",
    "skill-evaluation",
    "prompt-kit-browser-proof-cleanup",
    "prompt-kit-feedback-afk-routing",
}
REQUIRED_ARTIFACT_IDS = {
    "harness-control-plane",
    "operator-harness-state",
    "prompt-kit-website",
    "harness-completeness-report",
    "prompt-kit-interaction-audit-report",
    "prompt-language-audit-report",
    "workbook-engine-output",
    "prompt-kit-browser-proof-cleanup-report",
    "app-harness-validation-report",
}
REQUIRED_VALIDATOR_IDS = {
    "harness-completeness",
    "harness-contract-tests",
    "prompt-kit-interaction-contract-tests",
    "prompt-kit-interaction-audit",
    "prompt-kit-discovery-audit",
    "prompt-kit-discovery-tests",
    "prompt-language-contract-tests",
    "prompt-language-audit",
    "skill-prompt-registry-tests",
    "prompt-kit-header-contract",
    "prompt-kit-parity",
    "staged-artifact-hygiene",
    "artifact-hygiene",
    "patch-hygiene",
    "patch-hygiene-staged",
    "prompt-kit-browser-proof-cleanup-completeness",
    "prompt-kit-browser-proof-cleanup-tests",
    "prompt-kit-browser-proof-cleanup-powershell-smoke",
    "prompt-kit-responsive-layout-audit",
    "prompt-kit-responsive-layout-tests",
    "app-harness-validation",
    "prompt-kit-feedback-afk-routing-audit",
    "prompt-kit-feedback-afk-routing-tests",
    "operant-product-identity-audit",
    "operant-product-identity-tests",
}
REQUIRED_CAPABILITY_IDS = {
    "harness-infrastructure-maintenance",
    "prompt-language-audit",
    "skill-evaluation",
    "skill-factoring",
    "technician-prompt-kit-acquisition",
    "prompt-kit-browser-proof-scratch-cleanup",
    "prompt-kit-responsive-layout",
    "prompt-kit-feedback-afk-routing",
    "repository-hook-integration",
}
REQUIRED_TRIGGER_IDS = {
    "harness-infrastructure-change",
    "prompt-language-change",
    "lazy-next-action-report",
    "skill-quality-unproven",
    "skill-boundary-defect",
    "technician-needs-latest-prompt-kit",
    "prompt-kit-browser-proof-temp-path",
    "prompt-kit-responsive-overlap",
    "prompt-kit-actionable-feedback",
    "repository-hook-installation-needed",
}
PROTECTED_PATHS = ("Candidates/", "Active/")


class HarnessValidationError(RuntimeError):
    """Raised when the operational harness violates a registered contract."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessValidationError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessValidationError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def require_file(relative_path: str, *, nonempty: bool = True) -> Path:
    path = ROOT / relative_path
    if not path.is_file():
        raise HarnessValidationError(f"missing required file: {relative_path}")
    if nonempty and path.stat().st_size == 0:
        raise HarnessValidationError(f"required file is empty: {relative_path}")
    return path


def require_text(relative_path: str, phrases: tuple[str, ...]) -> str:
    text = require_file(relative_path).read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            raise HarnessValidationError(
                f"{relative_path} is missing required text: {phrase}"
            )
    return text


def _tracked_paths() -> set[str]:
    """Return tracked paths using one bounded, non-interactive, byte-mode Git probe."""
    global _TRACKED_PATHS_CACHE
    if _TRACKED_PATHS_CACHE is not None:
        return _TRACKED_PATHS_CACHE
    if not (ROOT / ".git").exists():
        _TRACKED_PATHS_CACHE = set()
        return _TRACKED_PATHS_CACHE
    command = ["git", "ls-files", "-z"]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=GIT_PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise HarnessValidationError(
            f"tracked-file Git probe timed out after {GIT_PROBE_TIMEOUT_SECONDS}s"
        ) from exc
    except OSError as exc:
        raise HarnessValidationError(f"tracked-file Git probe failed: {exc}") from exc
    if result.returncode != 0:
        raise HarnessValidationError(
            f"tracked-file Git probe exited with code {result.returncode}"
        )
    decoded = result.stdout.decode("utf-8", errors="replace")
    _TRACKED_PATHS_CACHE = {
        item.replace("\\", "/") for item in decoded.split("\0") if item
    }
    return _TRACKED_PATHS_CACHE


def require_tracked(relative_path: str) -> None:
    if not (ROOT / ".git").exists():
        return
    normalized = relative_path.replace("\\", "/")
    if normalized not in _tracked_paths():
        raise HarnessValidationError(
            f"required harness file is not tracked: {relative_path}"
        )


def require_string_list(value: Any, field: str, *, minimum: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise HarnessValidationError(
            f"{field} must be a list with at least {minimum} item(s)"
        )
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise HarnessValidationError(f"{field} contains an empty/non-string item")
        items.append(item.strip())
    if len(items) != len(set(items)):
        raise HarnessValidationError(f"{field} contains duplicate items")
    return items


def validate_manifest() -> dict[str, Any]:
    payload = load_json(MANIFEST_PATH)
    if payload.get("schema_version") != "web-excel-harness/v1":
        raise HarnessValidationError("unsupported harness manifest schema")
    if payload.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise HarnessValidationError("harness manifest repository is not canonical")
    if payload.get("default_branch") != "main":
        raise HarnessValidationError("harness manifest default branch must be main")
    if payload.get("governance") != "AGENTS.md":
        raise HarnessValidationError("harness manifest governance path drifted")

    components = payload.get("components")
    if not isinstance(components, dict):
        raise HarnessValidationError("harness manifest components must be an object")
    missing = sorted(REQUIRED_COMPONENT_IDS - set(components))
    extra = sorted(set(components) - REQUIRED_COMPONENT_IDS)
    if missing or extra:
        raise HarnessValidationError(
            f"harness component registry drifted; missing={missing} extra={extra}"
        )
    for relative_path in components.values():
        require_file(str(relative_path))
        require_tracked(str(relative_path))

    skills = require_string_list(payload.get("skills"), "manifest.skills", minimum=5)
    for relative_path in skills:
        require_file(relative_path)
        require_tracked(relative_path)

    contracts = payload.get("domain_contracts")
    if not isinstance(contracts, dict) or not contracts:
        raise HarnessValidationError("domain_contracts must be a non-empty object")
    for contract_id, contract in contracts.items():
        if not isinstance(contract, dict):
            raise HarnessValidationError(f"domain contract must be an object: {contract_id}")
        for field in ("contract", "validator", "contract_tests", "workflow", "harness_gate"):
            if not isinstance(contract.get(field), str) or not contract[field].strip():
                raise HarnessValidationError(
                    f"domain contract {contract_id} is missing {field}"
                )
        for field in ("contract", "validator", "contract_tests"):
            require_file(str(contract[field]))
            require_tracked(str(contract[field]))

    acquisition = payload.get("technician_acquisition")
    if not isinstance(acquisition, dict):
        raise HarnessValidationError("technician_acquisition contract is missing")
    if acquisition.get("repository_url") != (
        "https://github.com/EndeavorEverlasting/web-excel-repair-triage.git"
    ):
        raise HarnessValidationError("technician acquisition repository URL is not canonical")
    for key in ("launcher", "gui"):
        relative_path = acquisition.get(key)
        if not relative_path:
            raise HarnessValidationError(f"technician acquisition is missing {key}")
        require_file(str(relative_path))
        require_tracked(str(relative_path))
    for relative_path in require_string_list(
        acquisition.get("required_files"), "technician_acquisition.required_files"
    ):
        require_file(relative_path)

    expected_safety = {
        "clone_when_absent": True,
        "fast_forward_only": True,
        "refuse_dirty_worktree": True,
        "refuse_divergence": True,
        "force_push": False,
        "destructive_reset": False,
        "embedded_credentials": False,
    }
    if acquisition.get("safety") != expected_safety:
        raise HarnessValidationError("technician acquisition safety contract drifted")

    validation_order = require_string_list(
        payload.get("validation_order"), "manifest.validation_order", minimum=8
    )
    if validation_order[0] != (
        "python scripts/validate_harness.py "
        "--report Outputs/harness-completeness-report.json"
    ):
        raise HarnessValidationError(
            "harness completeness report must be the first validation command"
        )
    if validation_order[-1] != "git diff --check":
        raise HarnessValidationError("git diff --check must close the validation order")
    return payload


def validate_human_contracts() -> None:
    contracts = {
        "CODEBASE_MAP.md": (
            "## Reading order for a fresh agent",
            "## Repository structure",
            "## Primary entry points",
            "harness/workflows.v1.json",
            "harness/artifacts.v1.json",
            "harness/validators.v1.json",
            "## Build, test, and launch commands",
            "## Safety boundaries and known traps",
        ),
        "WORKFLOW.md": (
            "## 1. Pick up a task",
            "### A. Technician acquisition or update",
            "### C. Harness infrastructure change",
            "### F. Prompt-language audit or repair",
            "### G. Skill-evaluation build",
            "## 3. Validate before committing",
            "## 4. Handle failures",
            "## 6. Handoff contract",
        ),
        "ARTIFACT_REGISTRY.md": (
            "## Tracked control-plane artifacts",
            "Workflow registry",
            "Machine artifact registry",
            "Validator registry",
            "Harness completeness report",
            "## Protected inputs",
            "## Proof boundaries",
        ),
        "SKILLS.md": (
            "## Active repository skills",
            "Harness infrastructure maintenance",
            ".ai/skills/harness-infrastructure-maintenance/SKILL.md",
            "## Required skill-file sections",
        ),
        "CAPABILITIES.md": (
            "## Active capabilities",
            "`harness-infrastructure-maintenance`",
            "`prompt-language-audit`",
            "`skill-evaluation`",
            "## Proof boundaries",
        ),
        "TRIGGERS.md": (
            "## Routing table",
            "`harness-infrastructure-change`",
            "`prompt-language-change`",
            "`skill-quality-unproven`",
            "## Collision rule",
        ),
        "harness/reports/CURRENT_STATE.md": (
            "## Working surfaces",
            "## Validator behavior",
            "## Technician acquisition behavior",
            "## Prompt-language audit behavior",
            "## Known gaps",
            "## Proof ceiling",
            "## Operator next action",
        ),
    }
    for path, phrases in contracts.items():
        require_text(path, phrases)


def validate_workflow_registry() -> dict[str, Any]:
    payload = load_json(WORKFLOWS_PATH)
    if payload.get("schema_version") != "web-excel-workflows/v1":
        raise HarnessValidationError("unsupported workflow registry schema")
    workflows = payload.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        raise HarnessValidationError("workflow registry contains no workflows")
    allowed_anchors = {
        "a-technician-acquisition-or-update",
        "b-prompt-registry-or-website-change",
        "c-harness-infrastructure-change",
        "d-workbook-or-artifact-engine-change",
        "e-pr-floor-cleanup-and-integration",
        "f-prompt-language-audit-or-repair",
        "g-skill-evaluation-build",
        "h-prompt-kit-browser-proof-scratch-cleanup",
        "i-prompt-kit-feedback-afk-routing",
    }
    by_id: dict[str, dict[str, Any]] = {}
    for workflow in workflows:
        if not isinstance(workflow, dict):
            raise HarnessValidationError("workflow entry must be an object")
        workflow_id = str(workflow.get("id", "")).strip()
        if not workflow_id or workflow_id in by_id:
            raise HarnessValidationError(f"duplicate or empty workflow ID: {workflow_id}")
        by_id[workflow_id] = workflow
        document = str(workflow.get("document", "")).strip()
        if not document.startswith("WORKFLOW.md#"):
            raise HarnessValidationError(f"workflow document route is invalid: {workflow_id}")
        if document.split("#", 1)[1] not in allowed_anchors:
            raise HarnessValidationError(
                f"workflow document anchor is unknown: {workflow_id} -> {document}"
            )
        for field in ("trigger", "failure_policy", "validation_profile"):
            if not isinstance(workflow.get(field), str) or not workflow[field].strip():
                raise HarnessValidationError(f"workflow {workflow_id} is missing {field}")
        for field in ("owned_scope", "forbidden_scope", "entry_points", "handoff_fields"):
            require_string_list(workflow.get(field), f"workflow.{workflow_id}.{field}")
    if set(by_id) != REQUIRED_WORKFLOW_IDS:
        raise HarnessValidationError(f"workflow IDs drifted: {sorted(by_id)}")
    return payload


def validate_artifact_registry() -> dict[str, Any]:
    payload = load_json(ARTIFACTS_PATH)
    if payload.get("schema_version") != "web-excel-artifacts/v1":
        raise HarnessValidationError("unsupported artifact registry schema")
    protected = require_string_list(
        payload.get("protected_paths"), "artifacts.protected_paths", minimum=2
    )
    if tuple(protected) != PROTECTED_PATHS:
        raise HarnessValidationError(f"protected artifact paths drifted: {protected}")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise HarnessValidationError("artifact registry contains no artifacts")
    by_id: dict[str, dict[str, Any]] = {}
    kinds: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise HarnessValidationError("artifact entry must be an object")
        artifact_id = str(artifact.get("id", "")).strip()
        if not artifact_id or artifact_id in by_id:
            raise HarnessValidationError(f"duplicate or empty artifact ID: {artifact_id}")
        by_id[artifact_id] = artifact
        kind = str(artifact.get("kind", "")).strip()
        if kind not in {"tracked", "runtime"}:
            raise HarnessValidationError(f"unsupported artifact kind: {artifact_id} -> {kind}")
        kinds.add(kind)
        canonical_path = str(artifact.get("canonical_path", "")).strip()
        if not canonical_path:
            raise HarnessValidationError(f"artifact lacks canonical_path: {artifact_id}")
        if any(canonical_path.startswith(path) for path in PROTECTED_PATHS):
            raise HarnessValidationError(f"artifact writes into a protected path: {artifact_id}")
        for field in ("producer", "validator", "naming", "tracking_policy", "proof_ceiling"):
            if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                raise HarnessValidationError(f"artifact {artifact_id} is missing {field}")
        if kind == "tracked":
            require_file(canonical_path)
            require_tracked(canonical_path)
        elif not (canonical_path.startswith("Outputs/") or canonical_path.startswith("CI:")):
            raise HarnessValidationError(
                f"runtime artifact must use Outputs/ or CI storage: {artifact_id}"
            )
    if set(by_id) != REQUIRED_ARTIFACT_IDS:
        raise HarnessValidationError(f"artifact IDs drifted: {sorted(by_id)}")
    if kinds != {"tracked", "runtime"}:
        raise HarnessValidationError("artifact registry must contain tracked and runtime artifacts")
    return payload


def validate_validator_registry(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = load_json(VALIDATORS_PATH)
    if payload.get("schema_version") != "web-excel-validators/v1":
        raise HarnessValidationError("unsupported validator registry schema")
    validators = payload.get("validators")
    if not isinstance(validators, list) or not validators:
        raise HarnessValidationError("validator registry contains no validators")
    by_id: dict[str, dict[str, Any]] = {}
    for validator in validators:
        if not isinstance(validator, dict):
            raise HarnessValidationError("validator entry must be an object")
        validator_id = str(validator.get("id", "")).strip()
        if not validator_id or validator_id in by_id:
            raise HarnessValidationError(f"duplicate or empty validator ID: {validator_id}")
        by_id[validator_id] = validator
        if validator.get("class") not in {"contract", "test", "build", "lint"}:
            raise HarnessValidationError(f"validator class is invalid: {validator_id}")
        for field in ("command", "output", "proof_ceiling"):
            if not isinstance(validator.get(field), str) or not validator[field].strip():
                raise HarnessValidationError(f"validator {validator_id} is missing {field}")
        if validator.get("blocking") is not True:
            raise HarnessValidationError(f"validator must be blocking: {validator_id}")
    if set(by_id) != REQUIRED_VALIDATOR_IDS:
        raise HarnessValidationError(f"validator IDs drifted: {sorted(by_id)}")
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise HarnessValidationError("validator profiles must be an object")
    for profile_id in ("harness", "pre_commit", "pre_push"):
        ids = require_string_list(profiles.get(profile_id), f"validators.profiles.{profile_id}")
        unknown = sorted(set(ids) - set(by_id))
        if unknown:
            raise HarnessValidationError(
                f"validator profile {profile_id} references unknown IDs: {unknown}"
            )
    harness_commands = [by_id[item]["command"] for item in profiles["harness"]]
    if harness_commands != manifest["validation_order"]:
        raise HarnessValidationError(
            "manifest validation_order differs from validator harness profile"
        )
    if profiles["pre_push"] != profiles["harness"]:
        raise HarnessValidationError("pre_push profile must equal the full harness profile")
    expected_hooks = {
        "pre_commit": (".githooks/pre-commit", "pre_commit", "staged-tree"),
        "pre_push": (".githooks/pre-push", "pre_push", "working-tree"),
    }
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        raise HarnessValidationError("validator hook registry is missing")
    for hook_id, expected in expected_hooks.items():
        hook = hooks.get(hook_id)
        actual = (
            hook.get("path") if isinstance(hook, dict) else None,
            hook.get("profile") if isinstance(hook, dict) else None,
            hook.get("index_mode") if isinstance(hook, dict) else None,
        )
        if actual != expected:
            raise HarnessValidationError(f"hook registry drifted: {hook_id}")
        require_file(expected[0])
        require_tracked(expected[0])
    return payload


def validate_capabilities_and_triggers() -> tuple[dict[str, Any], dict[str, Any]]:
    capability_payload = load_json(CAPABILITIES_PATH)
    if capability_payload.get("schema_version") != "web-excel-capabilities/v1":
        raise HarnessValidationError("unsupported capability registry schema")
    capabilities = capability_payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise HarnessValidationError("capability registry contains no capabilities")
    capability_by_id: dict[str, dict[str, Any]] = {}
    for capability in capabilities:
        if not isinstance(capability, dict):
            raise HarnessValidationError("capability entry must be an object")
        capability_id = str(capability.get("id", "")).strip()
        if not capability_id or capability_id in capability_by_id:
            raise HarnessValidationError(f"duplicate or empty capability ID: {capability_id}")
        capability_by_id[capability_id] = capability
        skill = str(capability.get("skill", ""))
        require_file(skill)
        require_tracked(skill)
        for field in ("trigger_ids", "inputs", "outputs"):
            require_string_list(capability.get(field), f"capability.{capability_id}.{field}")
        implementation = capability.get("implementation")
        if not isinstance(implementation, dict):
            raise HarnessValidationError(f"capability lacks implementation: {capability_id}")
        kind = implementation.get("kind")
        if kind in {"script", "launcher"}:
            require_file(str(implementation.get("path", "")))
        elif kind == "prompt":
            if not str(implementation.get("prompt_id", "")).startswith("P"):
                raise HarnessValidationError(f"prompt capability lacks prompt ID: {capability_id}")
        else:
            raise HarnessValidationError(f"unsupported capability implementation kind: {kind}")
        if not str(capability.get("proof_ceiling", "")).strip():
            raise HarnessValidationError(f"capability lacks proof_ceiling: {capability_id}")
    if set(capability_by_id) != REQUIRED_CAPABILITY_IDS:
        raise HarnessValidationError(f"capability IDs drifted: {sorted(capability_by_id)}")

    trigger_payload = load_json(TRIGGERS_PATH)
    if trigger_payload.get("schema_version") != "web-excel-triggers/v1":
        raise HarnessValidationError("unsupported trigger registry schema")
    triggers = trigger_payload.get("triggers")
    if not isinstance(triggers, list) or not triggers:
        raise HarnessValidationError("trigger registry contains no triggers")
    trigger_ids: set[str] = set()
    for trigger in triggers:
        if not isinstance(trigger, dict):
            raise HarnessValidationError("trigger entry must be an object")
        trigger_id = str(trigger.get("id", "")).strip()
        if not trigger_id or trigger_id in trigger_ids:
            raise HarnessValidationError(f"duplicate or empty trigger ID: {trigger_id}")
        trigger_ids.add(trigger_id)
        capability_id = str(trigger.get("capability_id", ""))
        if capability_id not in capability_by_id:
            raise HarnessValidationError(
                f"trigger references unknown capability: {trigger_id} -> {capability_id}"
            )
        if str(trigger.get("skill", "")) != capability_by_id[capability_id]["skill"]:
            raise HarnessValidationError(f"trigger skill owner drifted: {trigger_id}")
        if not str(trigger.get("workflow", "")).startswith("WORKFLOW.md#"):
            raise HarnessValidationError(f"trigger workflow route is invalid: {trigger_id}")
        require_string_list(trigger.get("conditions"), f"trigger.{trigger_id}.conditions")
        require_string_list(
            trigger.get("forbidden_conditions"),
            f"trigger.{trigger_id}.forbidden_conditions",
        )
    if trigger_ids != REQUIRED_TRIGGER_IDS:
        raise HarnessValidationError(f"trigger IDs drifted: {sorted(trigger_ids)}")
    for capability_id, capability in capability_by_id.items():
        registered = set(capability.get("trigger_ids", []))
        actual = {
            str(trigger["id"])
            for trigger in triggers
            if trigger.get("capability_id") == capability_id
        }
        if registered != actual:
            raise HarnessValidationError(
                f"capability trigger list drifted: {capability_id} "
                f"registered={sorted(registered)} actual={sorted(actual)}"
            )
    return capability_payload, trigger_payload


def validate_skills(manifest: dict[str, Any], capabilities: dict[str, Any]) -> None:
    index = require_file("SKILLS.md").read_text(encoding="utf-8")
    capability_skill_paths = {
        str(capability["skill"]) for capability in capabilities["capabilities"]
    }
    manifest_skill_paths = {str(path) for path in manifest["skills"]}
    if capability_skill_paths != manifest_skill_paths:
        raise HarnessValidationError(
            "skill ownership differs between manifest and capability registry"
        )
    for relative_path in sorted(manifest_skill_paths):
        if relative_path not in index:
            raise HarnessValidationError(f"SKILLS.md does not index {relative_path}")
        text = require_file(relative_path).read_text(encoding="utf-8")
        for section in REQUIRED_SKILL_SECTIONS:
            if section not in text:
                raise HarnessValidationError(f"{relative_path} is missing {section}")
        require_tracked(relative_path)


def validate_prompt_language_eval() -> None:
    policy = evaluate_prompt_language.load_policy()
    if policy.get("capability_id") != "prompt-language-audit":
        raise HarnessValidationError("prompt-language eval capability ID drifted")
    fixture_payload = load_json(
        ROOT / "harness" / "evals" / "fixtures" / "prompt-language-cases.v1.json"
    )
    if fixture_payload.get("schema_version") != "prompt-language-fixtures/v1":
        raise HarnessValidationError("prompt-language fixture schema is invalid")
    cases = fixture_payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 4:
        raise HarnessValidationError("prompt-language fixtures are incomplete")
    case_ids = [str(case.get("id", "")) for case in cases]
    if len(case_ids) != len(set(case_ids)) or any(not item for item in case_ids):
        raise HarnessValidationError("prompt-language fixture IDs are duplicate or empty")
    report = evaluate_prompt_language.evaluate_registry(policy=policy)
    if not report["coverage_complete"]:
        raise HarnessValidationError("prompt-language audit coverage is incomplete")
    if report["prompt_count"] != report["disposition_count"]:
        raise HarnessValidationError("prompt-language disposition count differs from prompt count")
    if report["prompt_count"] != report["effective_prompt_count"]:
        raise HarnessValidationError("canonical and effective prompt counts differ")
    if report["error_count"] != 0:
        raise HarnessValidationError(
            f"prompt-language audit has error findings: {report['error_count']}"
        )
    if "P62" not in {item["prompt_id"] for item in report["prompts"]}:
        raise HarnessValidationError("prompt-language audit did not evaluate P62")


def validate_acquisition_surface() -> None:
    launcher = require_file("Acquire-Latest-PromptKit.cmd").read_text(encoding="utf-8")
    gui = require_file("scripts/Acquire-LatestPromptKit.ps1").read_text(encoding="utf-8")
    combined = f"{launcher}\n{gui}".lower()
    for phrase in (
        "raw.githubusercontent.com/endeavoreverlasting/"
        "web-excel-repair-triage/main/",
        "scripts\\acquire-latestpromptkit.ps1",
        "executionpolicy bypass",
    ):
        if phrase not in launcher.lower():
            raise HarnessValidationError(f"acquisition CMD is missing required behavior: {phrase}")
    for phrase in (
        "git @arguments",
        "'clone', '--branch', $defaultbranch, '--single-branch'",
        "'status', '--porcelain'",
        "'branch', '--show-current'",
        "'fetch', 'origin', $defaultbranch, '--prune'",
        "'rev-list', '--left-right', '--count'",
        "'merge', '--ff-only'",
        "test-requiredfiles",
        "open prompt kit website",
        "open generator selection gui",
    ):
        if phrase not in gui.lower():
            raise HarnessValidationError(f"acquisition GUI is missing required behavior: {phrase}")
    for pattern in FORBIDDEN_ACQUISITION_PATTERNS:
        if pattern.lower() in combined:
            raise HarnessValidationError(
                f"acquisition surface contains destructive or credential pattern: {pattern}"
            )
    if "c:\\users\\" in combined:
        raise HarnessValidationError("acquisition surface embeds a machine-specific user path")


def validate_hooks() -> None:
    pre_commit = require_file(".githooks/pre-commit").read_text(encoding="utf-8")
    for phrase in (
        "git checkout-index --all --prefix=",
        'python scripts/validate_harness.py --report "$HARNESS_REPORT"',
        "python -m unittest tests.test_harness_contract -v",
        "git diff --cached --check",
    ):
        if phrase not in pre_commit:
            raise HarnessValidationError(f"pre-commit hook is missing: {phrase}")
    if 'cd "$staged_tree"' not in pre_commit:
        raise HarnessValidationError("pre-commit hook does not validate the isolated staged tree")
    pre_push = require_file(".githooks/pre-push").read_text(encoding="utf-8")
    for phrase in (
        'python scripts/validate_harness.py --report "$HARNESS_REPORT"',
        "python -m unittest tests.test_harness_contract -v",
        "python -m unittest tests.test_prompt_kit_interactions_contract -v",
        "python scripts/validate_prompt_kit_interactions.py",
        "python scripts/validate_prompt_kit_discovery.py --summary",
        "python -m unittest tests.test_prompt_kit_discovery -v",
        "python -m unittest tests.test_prompt_language_audit -v",
        "python scripts/evaluate_prompt_language.py",
        "python -m unittest tests.test_skill_prompt_registry -v",
        "python tests/test_prompt_kit_header_contract.py",
        "python scripts/build_prompt_kit_registry.py "
        "--output web/prompt-kit/index.html --check",
        "python -m triage.gitignore_hygiene",
        "git diff --check",
    ):
        if phrase not in pre_push:
            raise HarnessValidationError(f"pre-push hook is missing: {phrase}")


def validate_generator_manifest() -> None:
    manifest = load_json(ROOT / "configs" / "prompt_kit" / "generators.v1.json")
    if manifest.get("schema_version") != "prompt-kit-generators/v1":
        raise HarnessValidationError("generator manifest schema is invalid")
    if manifest.get("gui_launcher") != "Run-PromptKitGenerator.cmd":
        raise HarnessValidationError("generator manifest GUI launcher drifted")
    generators = manifest.get("generators")
    if not isinstance(generators, list) or not generators:
        raise HarnessValidationError("generator manifest contains no generators")
    for generator in generators:
        require_file(str(generator["runner"]))
        require_file(str(generator["direct_launcher"]))


def _resolve_report_target(report_path: Path) -> Path:
    target = report_path if report_path.is_absolute() else ROOT / report_path
    resolved = target.resolve(strict=False)
    root = ROOT.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return resolved
    if not relative.parts or relative.parts[0] != "Outputs":
        raise HarnessValidationError(
            "repository-local harness reports must be written under Outputs/"
        )
    return resolved


def write_report(
    report_path: Path,
    *,
    results: list[dict[str, str]],
    manifest: dict[str, Any],
    workflows: dict[str, Any],
    artifacts: dict[str, Any],
    validators: dict[str, Any],
    capabilities: dict[str, Any],
    triggers: dict[str, Any],
) -> None:
    target = _resolve_report_target(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    failures = [result for result in results if result["status"] == "FAIL"]
    payload = {
        "schema_version": "harness-completeness-report/v1",
        "repository": "EndeavorEverlasting/web-excel-repair-triage",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "FAIL" if failures else "PASS",
        "checks": results,
        "failure_count": len(failures),
        "counts": {
            "components": len(manifest.get("components", {})),
            "workflows": len(workflows.get("workflows", [])),
            "artifacts": len(artifacts.get("artifacts", [])),
            "validators": len(validators.get("validators", [])),
            "capabilities": len(capabilities.get("capabilities", [])),
            "triggers": len(triggers.get("triggers", [])),
            "skills": len(manifest.get("skills", [])),
        },
        "proof_ceiling": (
            "Static repository and CI harness proof on the tested checkout; "
            "no product runtime, provider, GUI, protected-target, technician, "
            "deployment, or production proof."
        ),
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the repository operational harness.")
    parser.add_argument(
        "--report",
        type=Path,
        help=(
            "Optional path for a harness-completeness-report/v1 JSON report. "
            "Relative paths are resolved from the repository root."
        ),
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    failures: list[str] = []
    results: list[dict[str, str]] = []
    manifest: dict[str, Any] = {}
    workflows: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    validators: dict[str, Any] = {}
    capabilities: dict[str, Any] = {}
    triggers: dict[str, Any] = {}

    def run(name: str, check: Callable[[], Any]) -> Any:
        try:
            value = check()
        except (
            HarnessValidationError,
            evaluate_prompt_language.PromptLanguageAuditError,
            KeyError,
            OSError,
            TypeError,
            ValueError,
        ) as exc:
            message = str(exc)
            failures.append(f"{name}: {message}")
            results.append({"name": name, "status": "FAIL", "message": message})
            print(f"[FAIL] {name}: {message}")
            return None
        results.append({"name": name, "status": "PASS", "message": "ok"})
        print(f"[PASS] {name}")
        return value

    print("Operational Harness Validation")
    print("=" * 38)
    manifest_value = run("manifest", validate_manifest)
    if manifest_value:
        manifest = manifest_value
    run("human contracts", validate_human_contracts)
    workflows_value = run("workflow registry", validate_workflow_registry)
    if workflows_value:
        workflows = workflows_value
    artifacts_value = run("artifact registry", validate_artifact_registry)
    if artifacts_value:
        artifacts = artifacts_value
    if manifest:
        validators_value = run(
            "validator registry", lambda: validate_validator_registry(manifest)
        )
        if validators_value:
            validators = validators_value
    else:
        run(
            "validator registry",
            lambda: (_ for _ in ()).throw(
                HarnessValidationError("prerequisite manifest validation failed")
            ),
        )
    registry_value = run("capabilities and triggers", validate_capabilities_and_triggers)
    if registry_value:
        capabilities, triggers = registry_value
    if manifest and capabilities:
        run("skills", lambda: validate_skills(manifest, capabilities))
    else:
        run(
            "skills",
            lambda: (_ for _ in ()).throw(
                HarnessValidationError(
                    "prerequisite manifest or capability validation failed"
                )
            ),
        )
    run("prompt-language eval", validate_prompt_language_eval)
    run("technician acquisition", validate_acquisition_surface)
    run("hooks", validate_hooks)
    run("generator manifest", validate_generator_manifest)

    if args.report:
        try:
            write_report(
                args.report,
                results=results,
                manifest=manifest,
                workflows=workflows,
                artifacts=artifacts,
                validators=validators,
                capabilities=capabilities,
                triggers=triggers,
            )
        except (HarnessValidationError, OSError, TypeError, ValueError) as exc:
            failures.append(f"report: {exc}")
            results.append({"name": "report", "status": "FAIL", "message": str(exc)})
            print(f"[FAIL] report: {exc}")

    if failures:
        print("\nHarness validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nHarness validation passed.")
    if args.report:
        print(f"Harness report: {_resolve_report_target(args.report)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
