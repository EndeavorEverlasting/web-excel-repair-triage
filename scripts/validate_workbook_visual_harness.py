#!/usr/bin/env python3
"""Validate the tracked workbook visual-integrity operational harness."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_workbook_visual_integrity as visual

REQUIRED_PATHS = (
    "configs/workbook_visual_integrity_v1.json",
    "schemas/workbook-visual-profile.schema.json",
    "schemas/workbook-visual-validation-result.schema.json",
    "harness/workbook-visual-integrity/CODEBASE_MAP.md",
    "harness/workbook-visual-integrity/WORKFLOWS.md",
    "harness/workbook-visual-integrity/ARTIFACT_REGISTRY.md",
    "harness/workbook-visual-integrity/registry.json",
    "harness/workbook-visual-integrity/generator-bindings.v1.json",
    "harness/workbook-visual-integrity/fun-triage-contract.v1.json",
    "harness/workbook-visual-integrity/profiles/nth-admin-may-26-29.v1.json",
    "harness/workbook-visual-integrity/profiles/nth-admin-july.v1.json",
    "harness/workbook-visual-integrity/profiles/nth-math-packet.v1.json",
    "scripts/validate_workbook_visual_integrity.py",
    "scripts/validate_workbook_visual_harness.py",
    "tests/test_workbook_visual_integrity.py",
    "tests/test_workbook_visual_harness.py",
    ".ai/skills/workbook-visual-integrity/SKILL.md",
    ".github/workflows/workbook-visual-integrity.yml",
    "reports/harness/workbook-visual-integrity-state.md",
    "harness/manifest.v1.json",
    ".githooks/pre-commit",
    ".githooks/pre-push",
)
REQUIRED_SKILL_SECTIONS = (
    "## Trigger", "## Required inputs", "## Outputs", "## Procedure",
    "## Guardrails", "## Validation", "## Proof ceiling",
)


class HarnessError(RuntimeError):
    pass


def _load(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessError(f"missing JSON: {relative}") from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(f"invalid JSON: {relative}: {exc}") from exc
    if not isinstance(value, dict):
        raise HarnessError(f"JSON root must be an object: {relative}")
    return value


def _require(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise HarnessError(f"missing or empty harness component: {relative}")
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative], cwd=ROOT,
            text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if result.returncode != 0:
            raise HarnessError(f"harness component is not tracked: {relative}")
    return path


def validate() -> dict[str, Any]:
    for relative in REQUIRED_PATHS:
        _require(relative)

    registry = _load("harness/workbook-visual-integrity/registry.json")
    if registry.get("schema") != "workbook-visual-integrity-harness/v1":
        raise HarnessError("visual harness registry schema drifted")
    if registry.get("policy") != "configs/workbook_visual_integrity_v1.json":
        raise HarnessError("visual harness registry does not own the canonical policy")
    if len(registry.get("profiles", [])) != 3:
        raise HarnessError("visual harness registry must register the three current profiles")
    for relative in registry.get("profiles", []):
        _require(str(relative))

    policy = _load("configs/workbook_visual_integrity_v1.json")
    if policy.get("schema") != "workbook-visual-integrity-policy/v1":
        raise HarnessError("visual policy schema drifted")
    if policy.get("fonts", {}).get("default") != "Aptos":
        raise HarnessError("Aptos is not the visual policy default")
    if "Carlito" not in policy.get("fonts", {}).get("forbidden", []):
        raise HarnessError("Carlito is not explicitly forbidden")
    roles = policy.get("semantic_roles", {})
    required_roles = {
        "configuration", "inventory_management", "logistics_material_movement", "deployment",
        "client_coordination", "staging_readiness", "survey_recon", "pm_operational_control",
    }
    if set(roles) != required_roles:
        raise HarnessError(f"canonical semantic roles drifted: {sorted(roles)}")
    fills = [item["fill"] for item in roles.values()]
    if len(fills) != len(set(fills)):
        raise HarnessError("canonical semantic role colors are not unique")

    audit = visual.audit_profiles()
    if audit["status"] != "PASS":
        raise HarnessError(f"visual profile audit failed: {audit['violation_count']} violations")

    skill = _require(".ai/skills/workbook-visual-integrity/SKILL.md").read_text(encoding="utf-8")
    for section in REQUIRED_SKILL_SECTIONS:
        if section not in skill:
            raise HarnessError(f"visual skill is missing {section}")

    manifest = _load("harness/manifest.v1.json")
    domain = manifest.get("domain_contracts", {}).get("workbook_visual_integrity")
    if not isinstance(domain, dict):
        raise HarnessError("root harness manifest does not register workbook_visual_integrity")
    expected_manifest = {
        "policy": "configs/workbook_visual_integrity_v1.json",
        "registry": "harness/workbook-visual-integrity/registry.json",
        "validator": "scripts/validate_workbook_visual_integrity.py",
        "completeness_validator": "scripts/validate_workbook_visual_harness.py",
        "skill": ".ai/skills/workbook-visual-integrity/SKILL.md",
        "ci_workflow": ".github/workflows/workbook-visual-integrity.yml",
    }
    for key, expected in expected_manifest.items():
        if domain.get(key) != expected:
            raise HarnessError(f"root manifest visual domain drifted: {key}")
    validation_order = manifest.get("validation_order", [])
    for command in registry.get("validation_order", [])[:-1]:
        if command not in validation_order:
            raise HarnessError(f"root validation order is missing visual gate: {command}")

    hooks = {
        "pre-commit": _require(".githooks/pre-commit").read_text(encoding="utf-8"),
        "pre-push": _require(".githooks/pre-push").read_text(encoding="utf-8"),
    }
    for name, text in hooks.items():
        if "validate_workbook_visual_harness.py" not in text:
            raise HarnessError(f"{name} does not run visual harness completeness")
        if "validate_workbook_visual_integrity.py --validate-profiles" not in text:
            raise HarnessError(f"{name} does not run visual profile audit")
    if "tests.test_workbook_visual_integrity" not in hooks["pre-push"]:
        raise HarnessError("pre-push does not run visual workbook regressions")

    workflow = _require(".github/workflows/workbook-visual-integrity.yml").read_text(encoding="utf-8")
    for phrase in (
        "validate_workbook_visual_harness.py", "tests.test_workbook_visual_integrity",
        "--validate-profiles", "git diff --check", "workbook-visual-integrity-report",
    ):
        if phrase not in workflow:
            raise HarnessError(f"visual workflow is missing: {phrase}")

    bindings = _load("harness/workbook-visual-integrity/generator-bindings.v1.json")
    if bindings.get("schema") != "workbook-visual-generator-bindings/v1":
        raise HarnessError("generator binding schema drifted")
    if not any(item.get("artifact_family") == "nth-admin-workbook" for item in bindings.get("bindings", [])):
        raise HarnessError("NTH admin generator binding is missing")
    if not any(item.get("artifact_family") == "nth-internal-math-packet" for item in bindings.get("bindings", [])):
        raise HarnessError("NTH Math Packet generator binding is missing")

    cross_repo = _load("harness/workbook-visual-integrity/fun-triage-contract.v1.json")
    if cross_repo.get("producer", {}).get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise HarnessError("Triage producer authority drifted")
    if cross_repo.get("acceptor", {}).get("repository") != "EndeavorEverlasting/FUN":
        raise HarnessError("FUN acceptance authority drifted")
    if cross_repo.get("receipt_contract", {}).get("required_status") != "PASS":
        raise HarnessError("cross-repo visual receipt does not fail closed")

    return {
        "schema": "workbook-visual-integrity-harness-result/v1",
        "status": "PASS",
        "component_count": len(REQUIRED_PATHS),
        "profile_count": len(registry["profiles"]),
        "policy_id": policy["policy_id"],
        "canonical_role_count": len(roles),
        "canonical_report": registry["artifacts"]["workbook_validation"]["default_path"],
        "proof_ceiling": registry["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate workbook visual-integrity harness completeness.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except HarnessError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    elif not args.summary:
        print(text, end="")
    if args.summary:
        print(f"PASS: workbook visual harness complete; components={report['component_count']} profiles={report['profile_count']} roles={report['canonical_role_count']}")
        if args.output:
            print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
