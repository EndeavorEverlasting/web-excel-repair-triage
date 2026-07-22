#!/usr/bin/env python3
"""Fail-closed validator for the repository operational harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "harness" / "manifest.v1.json"
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
    required_component_ids = {
        "codebase_map",
        "workflow_spec",
        "artifact_registry",
        "skill_index",
        "validator",
        "contract_tests",
        "hook",
        "operator_report",
    }
    missing = sorted(required_component_ids - set(components))
    if missing:
        raise HarnessValidationError(f"harness manifest is missing components: {missing}")
    for relative_path in components.values():
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
    if not isinstance(validation_order, list) or len(validation_order) < 5:
        raise HarnessValidationError("validation_order must contain focused and broad gates")
    if validation_order[0] != "python scripts/validate_harness.py":
        raise HarnessValidationError("harness validator must be the first validation command")
    if validation_order[-1] != "git diff --check":
        raise HarnessValidationError("git diff --check must close the validation order")
    return payload


def validate_human_contracts() -> None:
    require_text(
        "CODEBASE_MAP.md",
        (
            "## Reading order for a fresh agent",
            "## Primary entry points",
            "Acquire-Latest-PromptKit.cmd",
            "## Safety boundaries and known traps",
        ),
    )
    require_text(
        "WORKFLOW.md",
        (
            "## 1. Pick up a task",
            "### A. Technician acquisition or update",
            "## 3. Validate before committing",
            "## 4. Handle failures",
            "## 6. Handoff contract",
        ),
    )
    require_text(
        "ARTIFACT_REGISTRY.md",
        (
            "## Tracked control-plane artifacts",
            "## Generated runtime artifacts",
            "## Protected inputs",
            "## Proof boundaries",
        ),
    )
    require_text(
        "harness/reports/CURRENT_STATE.md",
        (
            "## Working surfaces",
            "## Technician acquisition behavior",
            "## Known gaps",
            "## Proof ceiling",
        ),
    )


def validate_skills() -> None:
    index = require_file("SKILLS.md").read_text(encoding="utf-8")
    skill_paths = (
        ".ai/skills/skill-factoring/SKILL.md",
        ".ai/skills/technician-prompt-kit-acquisition/SKILL.md",
    )
    for relative_path in skill_paths:
        if relative_path not in index:
            raise HarnessValidationError(f"SKILLS.md does not index {relative_path}")
        text = require_file(relative_path).read_text(encoding="utf-8")
        for section in REQUIRED_SKILL_SECTIONS:
            if section not in text:
                raise HarnessValidationError(f"{relative_path} is missing {section}")
        require_tracked(relative_path)


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


def validate_hook() -> None:
    hook = require_file(".githooks/pre-commit").read_text(encoding="utf-8")
    for phrase in (
        "python scripts/validate_harness.py",
        "python -m unittest tests.test_harness_contract -v",
        "git diff --cached --check",
    ):
        if phrase not in hook:
            raise HarnessValidationError(f"pre-commit hook is missing: {phrase}")


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
    checks = (
        ("manifest", validate_manifest),
        ("human contracts", validate_human_contracts),
        ("skills", validate_skills),
        ("technician acquisition", validate_acquisition_surface),
        ("pre-commit hook", validate_hook),
        ("generator manifest", validate_generator_manifest),
    )
    failures: list[str] = []
    print("Operational Harness Validation")
    print("=" * 38)
    for name, check in checks:
        try:
            check()
        except (HarnessValidationError, KeyError, TypeError, ValueError) as exc:
            failures.append(f"{name}: {exc}")
            print(f"[FAIL] {name}: {exc}")
        else:
            print(f"[PASS] {name}")

    if failures:
        print("\nHarness validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nHarness validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
