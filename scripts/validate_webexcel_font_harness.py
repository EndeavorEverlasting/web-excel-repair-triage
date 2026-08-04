#!/usr/bin/env python3
"""Validate the complete Aptos/WebExcel operational harness."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "harness" / "webexcel-fonts" / "registry.json"
REQUIRED_PATHS = (
    "configs/webexcel_fonts_v1.json",
    "harness/webexcel-fonts/CODEBASE_MAP.md",
    "harness/webexcel-fonts/WORKFLOWS.md",
    "harness/webexcel-fonts/ARTIFACT_REGISTRY.md",
    "harness/webexcel-fonts/registry.json",
    "scripts/validate_webexcel_fonts.py",
    "scripts/validate_webexcel_font_harness.py",
    "tests/test_webexcel_font_compatibility.py",
    "tests/test_webexcel_font_harness.py",
    ".ai/skills/webexcel-font-compatibility/SKILL.md",
    ".github/workflows/webexcel-font-harness.yml",
    "reports/harness/webexcel-font-compatibility-state.md",
    ".githooks/pre-commit",
    ".githooks/pre-push",
)
REQUIRED_SKILL_SECTIONS = (
    "## Trigger",
    "## Required inputs",
    "## Outputs",
    "## Procedure",
    "## Guardrails",
    "## Validation",
    "## Proof ceiling",
)


class HarnessError(RuntimeError):
    pass


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessError(f"missing JSON: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"invalid JSON: {path.relative_to(ROOT)}: {exc}") from exc


def _require(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise HarnessError(f"missing or empty harness component: {relative}")
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative],
            cwd=ROOT,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0:
            raise HarnessError(f"harness component is not tracked: {relative}")
    return path


def validate() -> dict[str, Any]:
    for relative in REQUIRED_PATHS:
        _require(relative)

    policy = _load(ROOT / "configs" / "webexcel_fonts_v1.json")
    if policy.get("schema") != "webexcel-font-policy/v1":
        raise HarnessError("font policy schema drifted")
    if policy.get("default_font") != "Aptos":
        raise HarnessError("Aptos is not the policy default")
    if "Carlito" not in policy.get("forbidden_fonts", []):
        raise HarnessError("Carlito is not explicitly forbidden")

    registry = _load(REGISTRY)
    if registry.get("schema") != "webexcel-font-harness/v1":
        raise HarnessError("font harness registry schema drifted")
    if registry.get("policy") != "configs/webexcel_fonts_v1.json":
        raise HarnessError("font harness registry does not own the canonical policy")
    registered = set(registry.get("components", {}).values())
    missing_registry = sorted(set(REQUIRED_PATHS[:12]) - registered)
    if missing_registry:
        raise HarnessError(f"registry misses components: {missing_registry}")

    skill = _require(".ai/skills/webexcel-font-compatibility/SKILL.md").read_text(encoding="utf-8")
    for section in REQUIRED_SKILL_SECTIONS:
        if section not in skill:
            raise HarnessError(f"font skill is missing {section}")

    required_mentions = {
        "CODEBASE_MAP.md": ("Aptos", "Carlito", "validate_webexcel_fonts.py"),
        "WORKFLOW.md": ("WebExcel font compatibility", "validate_webexcel_font_harness.py"),
        "ARTIFACT_REGISTRY.md": ("WebExcel font validation report", "Outputs/webexcel-font-validation.json"),
        "SKILLS.md": ("webexcel-font-compatibility", "Aptos"),
        "harness/reports/CURRENT_STATE.md": ("Aptos", "Carlito"),
    }
    for relative, phrases in required_mentions.items():
        text = _require(relative).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                raise HarnessError(f"{relative} is missing harness reference: {phrase}")

    pre_commit = _require(".githooks/pre-commit").read_text(encoding="utf-8")
    pre_push = _require(".githooks/pre-push").read_text(encoding="utf-8")
    for text, name in ((pre_commit, "pre-commit"), (pre_push, "pre-push")):
        if "validate_webexcel_font_harness.py" not in text:
            raise HarnessError(f"{name} does not run the font harness completeness gate")
        if "validate_webexcel_fonts.py --scan-source" not in text:
            raise HarnessError(f"{name} does not run the source font gate")

    workflow = _require(".github/workflows/webexcel-font-harness.yml").read_text(encoding="utf-8")
    for phrase in (
        "validate_webexcel_font_harness.py",
        "tests.test_webexcel_font_compatibility",
        "validate_webexcel_fonts.py --scan-source",
        "git diff --check",
    ):
        if phrase not in workflow:
            raise HarnessError(f"font workflow is missing: {phrase}")

    manifest = _load(ROOT / "harness" / "manifest.v1.json")
    domain = manifest.get("domain_contracts", {}).get("webexcel_font_compatibility")
    if not isinstance(domain, dict):
        raise HarnessError("root harness manifest does not register webexcel_font_compatibility")
    if domain.get("validator") != "scripts/validate_webexcel_fonts.py":
        raise HarnessError("root harness manifest font validator drifted")

    return {
        "schema": "webexcel-font-harness-result/v1",
        "status": "PASS",
        "component_count": len(REQUIRED_PATHS),
        "policy_id": policy["policy_id"],
        "default_font": policy["default_font"],
        "forbidden_fonts": policy["forbidden_fonts"],
        "canonical_report": registry["artifacts"]["validation_report"]["default_path"],
        "proof_ceiling": registry["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Aptos/WebExcel harness.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate()
    except HarnessError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        print(
            f"PASS: Aptos/WebExcel harness complete; components={result['component_count']} "
            f"policy={result['policy_id']}"
        )
        if args.output:
            print(args.output)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
