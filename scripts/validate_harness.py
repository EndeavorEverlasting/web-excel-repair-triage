#!/usr/bin/env python3
"""Fail-closed validator for the repository operational harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language

MANIFEST_PATH = ROOT / "harness" / "manifest.v1.json"
CAPABILITIES_PATH = ROOT / "harness" / "capabilities.v1.json"
TRIGGERS_PATH = ROOT / "harness" / "triggers.v1.json"
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
REQUIRED_CAPABILITY_IDS = {
    "prompt-language-audit",
    "skill-evaluation",
    "skill-factoring",
    "technician-prompt-kit-acquisition",
}
REQUIRED_TRIGGER_IDS = {
    "prompt-language-change",
    "lazy-next-action-report",
    "skill-quality-unproven",
    "skill-boundary-defect",
    "technician-needs-latest-prompt-kit",
}


class HarnessValidationError(RuntimeError):
    pass


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
            raise HarnessValidationError(f"{relative_path} is missing required text: {phrase}")
    return text


def require_tracked(relative_path: str) -> None:
    if not (ROOT / ".git").exists():
        return
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise HarnessValidationError(f"required harness file is not tracked: {relative_path}")


def validate_manifest() -> dict[str, Any]:
    payload = load_json(MANIFEST_PATH)
    if payload.get("schema_version") != "web-excel-harness/v1":
        raise HarnessValidationError("unsupported harness manifest schema")
    if payload.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise HarnessValidationError("harness manifest repository is not canonical")
    if payload.get("default_branch") != "main":
        raise HarnessValidationError("harness manifest default branch must be main")

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

    skills = payload.get("skills")
    if not isinstance(skills, list) or len(skills) < 4:
        raise HarnessValidationError("harness manifest must register all active skills")
    if len(skills) != len(set(skills)):
        raise HarnessValidationError("harness manifest contains duplicate skill paths")
    for relative_path in skills:
        require_file(str(relative_path))
        require_tracked(str(relative_path))

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
    for relative_path in acquisition.get("required_files", []):
        require_file(str(relative_path))

    safety = acquisition.get("safety", {})
    expected_safety = {
        "clone_when_absent": True,
        "fast_forward_only": True,
        "refuse_dirty_worktree": True,
        "refuse_divergence": True,
        "force_push": False,
        "destructive_reset": False,
        "embedded_credentials": False,
    }
    if safety != expected_safety:
        raise HarnessValidationError("technician acquisition safety contract drifted")

    validation_order = payload.get("validation_order")
    if not isinstance(validation_order, list) or len(validation_order) < 8:
        raise HarnessValidationError("validation_order must contain focused and broad gates")
    if validation_order[0] != "python scripts/validate_harness.py":
        raise HarnessValidationError("harness validator must be the first validation command")
    for required in (
        "python -m unittest tests.test_prompt_language_audit -v",
        "python scripts/evaluate_prompt_language.py --output Outputs/prompt-language-audit.json --summary",
        "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
    ):
        if required not in validation_order:
            raise HarnessValidationError(f"validation_order is missing: {required}")
    if validation_order[-1] != "git diff --check":
        raise HarnessValidationError("git diff --check must close the validation order")
    return payload


def validate_human_contracts() -> None:
    require_text(
        "CODEBASE_MAP.md",
        (
            "## Reading order for a fresh agent",
            "## Primary entry points",
            "CAPABILITIES.md",
            "TRIGGERS.md",
            "scripts/evaluate_prompt_language.py",
            "## Safety boundaries and known traps",
        ),
    )
    require_text(
        "WORKFLOW.md",
        (
            "## 1. Pick up a task",
            "### A. Technician acquisition or update",
            "### C. Harness infrastructure change",
            "### F. Prompt-language audit or repair",
            "### G. Skill-evaluation build",
            "## 3. Validate before committing",
            "## 4. Handle failures",
            "## 6. Handoff contract",
        ),
    )
    require_text(
        "ARTIFACT_REGISTRY.md",
        (
            "## Tracked control-plane artifacts",
            "Capability registry",
            "Prompt-language audit report",
            "## Protected inputs",
            "## Proof boundaries",
        ),
    )
    require_text(
        "CAPABILITIES.md",
        (
            "## Active capabilities",
            "`prompt-language-audit`",
            "`skill-evaluation`",
            "## Proof boundaries",
        ),
    )
    require_text(
        "TRIGGERS.md",
        (
            "## Routing table",
            "`prompt-language-change`",
            "`skill-quality-unproven`",
            "## Collision rule",
        ),
    )
    require_text(
        "harness/reports/CURRENT_STATE.md",
        (
            "## Working surfaces",
            "## Technician acquisition behavior",
            "## Prompt-language audit behavior",
            "## Known gaps",
            "## Proof ceiling",
        ),
    )


def validate_capabilities_and_triggers() -> tuple[dict[str, Any], dict[str, Any]]:
    capability_payload = load_json(CAPABILITIES_PATH)
    if capability_payload.get("schema_version") != "web-excel-capabilities/v1":
        raise HarnessValidationError("unsupported capability registry schema")
    capabilities = capability_payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise HarnessValidationError("capability registry contains no capabilities")
    capability_by_id: dict[str, dict[str, Any]] = {}
    for capability in capabilities:
        capability_id = str(capability.get("id", ""))
        if not capability_id or capability_id in capability_by_id:
            raise HarnessValidationError(f"duplicate or empty capability ID: {capability_id}")
        capability_by_id[capability_id] = capability
        skill = str(capability.get("skill", ""))
        require_file(skill)
        require_tracked(skill)
        if not capability.get("inputs") or not capability.get("outputs"):
            raise HarnessValidationError(f"capability lacks inputs or outputs: {capability_id}")
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
    if set(capability_by_id) != REQUIRED_CAPABILITY_IDS:
        raise HarnessValidationError(
            f"capability IDs drifted: {sorted(capability_by_id)}"
        )

    trigger_payload = load_json(TRIGGERS_PATH)
    if trigger_payload.get("schema_version") != "web-excel-triggers/v1":
        raise HarnessValidationError("unsupported trigger registry schema")
    triggers = trigger_payload.get("triggers")
    if not isinstance(triggers, list) or not triggers:
        raise HarnessValidationError("trigger registry contains no triggers")
    trigger_ids: set[str] = set()
    for trigger in triggers:
        trigger_id = str(trigger.get("id", ""))
        if not trigger_id or trigger_id in trigger_ids:
            raise HarnessValidationError(f"duplicate or empty trigger ID: {trigger_id}")
        trigger_ids.add(trigger_id)
        capability_id = str(trigger.get("capability_id", ""))
        if capability_id not in capability_by_id:
            raise HarnessValidationError(
                f"trigger references unknown capability: {trigger_id} -> {capability_id}"
            )
        skill = str(trigger.get("skill", ""))
        if skill != capability_by_id[capability_id]["skill"]:
            raise HarnessValidationError(f"trigger skill owner drifted: {trigger_id}")
        if not trigger.get("conditions") or not isinstance(trigger.get("forbidden_conditions"), list):
            raise HarnessValidationError(f"trigger conditions are incomplete: {trigger_id}")
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
                f"capability trigger list drifted: {capability_id} registered={sorted(registered)} actual={sorted(actual)}"
            )
    return capability_payload, trigger_payload


def validate_skills(manifest: dict[str, Any], capabilities: dict[str, Any]) -> None:
    index = require_file("SKILLS.md").read_text(encoding="utf-8")
    capability_skill_paths = {
        str(capability["skill"]) for capability in capabilities["capabilities"]
    }
    manifest_skill_paths = {str(path) for path in manifest["skills"]}
    if capability_skill_paths != manifest_skill_paths:
        raise HarnessValidationError("skill ownership differs between manifest and capability registry")
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
    if len(case_ids) != len(set(case_ids)) or any(not case_id for case_id in case_ids):
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
        "raw.githubusercontent.com/endeavoreverlasting/web-excel-repair-triage/main/",
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
        "python scripts/validate_harness.py",
        "python -m unittest tests.test_harness_contract -v",
        "git diff --cached --check",
    ):
        if phrase not in pre_commit:
            raise HarnessValidationError(f"pre-commit hook is missing: {phrase}")
    pre_push = require_file(".githooks/pre-push").read_text(encoding="utf-8")
    for phrase in (
        "python scripts/validate_harness.py",
        "python -m unittest tests.test_harness_contract -v",
        "python -m unittest tests.test_prompt_language_audit -v",
        "python scripts/evaluate_prompt_language.py",
        "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
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


def main() -> int:
    failures: list[str] = []
    manifest: dict[str, Any] = {}
    capabilities: dict[str, Any] = {}

    def run(name: str, check: Any) -> None:
        try:
            check()
        except (HarnessValidationError, evaluate_prompt_language.PromptLanguageAuditError, KeyError, TypeError, ValueError) as exc:
            failures.append(f"{name}: {exc}")
            print(f"[FAIL] {name}: {exc}")
        else:
            print(f"[PASS] {name}")

    print("Operational Harness Validation")
    print("=" * 38)

    def manifest_check() -> None:
        nonlocal manifest
        manifest = validate_manifest()

    def registry_check() -> None:
        nonlocal capabilities
        capabilities, _ = validate_capabilities_and_triggers()

    run("manifest", manifest_check)
    run("human contracts", validate_human_contracts)
    run("capabilities and triggers", registry_check)
    if manifest and capabilities:
        run("skills", lambda: validate_skills(manifest, capabilities))
    else:
        failures.append("skills: prerequisite manifest or capability validation failed")
        print("[FAIL] skills: prerequisite manifest or capability validation failed")
    run("prompt-language eval", validate_prompt_language_eval)
    run("technician acquisition", validate_acquisition_surface)
    run("hooks", validate_hooks)
    run("generator manifest", validate_generator_manifest)

    if failures:
        print("\nHarness validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nHarness validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
