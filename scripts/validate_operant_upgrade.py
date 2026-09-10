#!/usr/bin/env python3
"""Validate the canonical Operant upgrade-engine contract and deterministic recipe boundary."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import operant_upgrade  # noqa: E402

CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"
TEST_PATH = ROOT / "tests" / "test_operant_upgrade.py"


def fixture() -> dict:
    return {
        "schema_version": "prompt-kit-afk-work-request/v1",
        "created_at": "2026-09-10T03:20:00Z",
        "coordinator": "P115 AFK Feedback-Driven Development Loop Executor",
        "preferred_mutation_owner": "P07 Repo Sprint Executor",
        "signal_class": "ACTIONABLE_REPAIR",
        "target": "Operant surface tutorial",
        "evidence": {
            "signal_id": "validator-friction-signal",
            "event_type": "operant_friction",
            "value": "route_miss",
            "surface_id": "tutorial",
            "evidence_kind": "repeated_local_pattern",
            "occurrence_count": 3,
            "sequence": 1,
            "timestamp": "2026-09-10T03:20:00Z",
            "source_hash": "b" * 64,
            "private_comment": "must not enter the recipe",
        },
        "owned_surface": "Resolve the smallest current canonical owner before mutation.",
        "acceptance_condition": "Repair only the current owning surface and retain regression proof.",
        "forbidden_scope": ["raw usage/session/navigation history", "force push"],
        "telemetry_semantic_owner": "P99",
        "promotion_owner": "P105/pr-floor-integration",
    }


def validate() -> list[str]:
    findings: list[str] = []
    required_paths = (
        ROOT / "scripts" / "operant_upgrade.py",
        CONTRACT_PATH,
        WORKFLOW_PATH,
        TEST_PATH,
        ROOT / "docs" / "prompts.json",
        ROOT / "build_prompt_kit.py",
        ROOT / "harness" / "contracts" / "pr-merge-gate.v1.json",
        ROOT / "scripts" / "validate_pr_merge_gate.py",
    )
    for path in required_paths:
        if not path.exists():
            findings.append(f"missing canonical upgrade dependency: {path.relative_to(ROOT)}")

    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        engine = contract["surfaces"]["canonical_upgrade_engine"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return findings + [f"cannot read canonical upgrade-engine contract: {exc}"]

    expected = {
        "primary_surface": "agent_harness",
        "path": "scripts/operant_upgrade.py",
        "recipe_schema": "operant-upgrade-recipe/v1",
        "validator": "scripts/validate_operant_upgrade.py",
        "output_dir": "Outputs/operant-upgrade/recipes",
        "mutation_authority": False,
        "merge_authority": False,
    }
    for key, value in expected.items():
        if engine.get(key) != value:
            findings.append(f"canonical upgrade engine {key} drifted: {engine.get(key)!r}")

    if engine.get("allowed_mutation_owners") != [
        "P07 Repo Sprint Executor",
        "P32 GNHF Validation and CI Repair",
    ]:
        findings.append("canonical upgrade mutation-owner allowlist drifted")

    generator = engine.get("generator")
    if not isinstance(generator, dict) or generator.get("command") != [
        "python",
        "build_prompt_kit.py",
        "--output",
        "web/prompt-kit/index.html",
    ]:
        findings.append("canonical Operant generated-site command drifted")

    validators = engine.get("validators")
    if not isinstance(validators, list):
        findings.append("canonical upgrade validators must be a list")
    else:
        for command in (
            "python scripts/validate_prompt_kit_feedback_afk_routing.py --summary",
            "python scripts/validate_operant_upgrade.py --summary",
            "python -m unittest tests.test_operant_upgrade tests.test_prompt_kit_feedback_afk_routing tests.test_operant_friction_repository_dispatch_adapter -v",
            "git diff --check",
        ):
            if command not in validators:
                findings.append(f"canonical upgrade validator missing: {command}")

    try:
        recipe_a = operant_upgrade.compile_recipe(fixture())
        recipe_b = operant_upgrade.compile_recipe(json.loads(json.dumps(fixture())))
        if recipe_a != recipe_b:
            findings.append("canonical upgrade recipe compilation is non-deterministic")
        encoded = json.dumps(recipe_a, sort_keys=True)
        if "must not enter the recipe" in encoded:
            findings.append("private feedback text leaked into canonical upgrade recipe")
        if recipe_a.get("lane", {}).get("merge_authority") is not False:
            findings.append("canonical upgrade recipe gained merge authority")
        if recipe_a.get("promotion_owner") != "P105/pr-floor-integration":
            findings.append("canonical upgrade recipe promotion owner drifted")
    except operant_upgrade.UpgradeError as exc:
        findings.append(f"canonical upgrade fixture did not compile: {exc}")

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8") if WORKFLOW_PATH.exists() else ""
    for marker in (
        "PROMPT_KIT_AFK_WORKER_ARGV_JSON",
        "scripts/operant_upgrade.py",
        "Outputs/operant-upgrade",
        "contents: read",
    ):
        if marker not in workflow:
            findings.append(f"remote adapter workflow missing canonical upgrade marker: {marker}")
    for forbidden in ("contents: write", "pull-requests: write"):
        if forbidden in workflow:
            findings.append(f"remote adapter workflow gained forbidden authority: {forbidden}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    findings = validate()
    if findings:
        print("OPERANT_UPGRADE_ENGINE_FAIL")
        for finding in findings:
            print(f"- {finding}")
        return 1
    if args.summary:
        print("OPERANT_UPGRADE_ENGINE_PASS recipe=operant-upgrade-recipe/v1 owner=P07/P32 promotion=P105")
    else:
        print("OPERANT_UPGRADE_ENGINE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
