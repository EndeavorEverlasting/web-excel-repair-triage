#!/usr/bin/env python3
"""Compile one AFK work request into a deterministic Operant upgrade recipe."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"
REQUEST_SCHEMA = "prompt-kit-afk-work-request/v1"
RECIPE_SCHEMA = "operant-upgrade-recipe/v1"
ALLOWED_EVIDENCE_FIELDS = (
    "signal_id",
    "event_type",
    "value",
    "sequence",
    "timestamp",
    "prompt_id",
    "surface_id",
    "evidence_kind",
    "occurrence_count",
    "source_hash",
)


class UpgradeError(RuntimeError):
    """Fail-closed upgrade-recipe compilation error."""


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def request_digest(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def load_contract() -> dict[str, Any]:
    try:
        payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpgradeError(f"cannot read AFK routing contract: {exc}") from exc
    if payload.get("schema_version") != "prompt-kit-feedback-afk-routing/v1":
        raise UpgradeError("unsupported AFK routing contract schema")
    engine = payload.get("surfaces", {}).get("canonical_upgrade_engine")
    if not isinstance(engine, dict):
        raise UpgradeError("canonical_upgrade_engine surface is not registered")
    if engine.get("path") != "scripts/operant_upgrade.py":
        raise UpgradeError("canonical upgrade engine path drifted")
    if engine.get("recipe_schema") != RECIPE_SCHEMA:
        raise UpgradeError("canonical upgrade recipe schema drifted")
    return payload


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise UpgradeError(f"work request {key} must be a non-empty string")
    return value.strip()


def validate_work_request(raw: object, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise UpgradeError("work request must be a JSON object")
    request = dict(raw)
    if request.get("schema_version") != REQUEST_SCHEMA:
        raise UpgradeError(f"unsupported work-request schema: {request.get('schema_version')!r}")
    if request.get("signal_class") != "ACTIONABLE_REPAIR":
        raise UpgradeError("upgrade engine accepts ACTIONABLE_REPAIR work requests only")

    expected_coordinator = "P115 AFK Feedback-Driven Development Loop Executor"
    if request.get("coordinator") != expected_coordinator:
        raise UpgradeError("work request coordinator is not P115")
    promotion_owner = _require_text(request, "promotion_owner")
    if promotion_owner != "P105/pr-floor-integration":
        raise UpgradeError("work request promotion owner must remain P105/pr-floor-integration")

    contract = contract or load_contract()
    engine = contract["surfaces"]["canonical_upgrade_engine"]
    owner = _require_text(request, "preferred_mutation_owner")
    allowed_owners = engine.get("allowed_mutation_owners")
    if not isinstance(allowed_owners, list) or owner not in allowed_owners:
        raise UpgradeError(f"unsupported mutation owner: {owner!r}")

    _require_text(request, "target")
    _require_text(request, "owned_surface")
    _require_text(request, "acceptance_condition")
    forbidden = request.get("forbidden_scope")
    if not isinstance(forbidden, list) or not forbidden or not all(
        isinstance(item, str) and item.strip() for item in forbidden
    ):
        raise UpgradeError("work request forbidden_scope must be a non-empty string array")

    evidence = request.get("evidence")
    if not isinstance(evidence, dict):
        raise UpgradeError("work request evidence must be a JSON object")
    for key in ("signal_id", "event_type", "value"):
        value = evidence.get(key)
        if not isinstance(value, str) or not value.strip():
            raise UpgradeError(f"work request evidence.{key} must be a non-empty string")
    if evidence.get("event_type") == "operant_friction":
        for key in ("surface_id", "evidence_kind", "occurrence_count"):
            if key not in evidence:
                raise UpgradeError(f"operant friction work request is missing evidence.{key}")
        if not isinstance(evidence["surface_id"], str) or not evidence["surface_id"].strip():
            raise UpgradeError("operant friction evidence.surface_id must be non-empty")
        if evidence["evidence_kind"] not in ("deterministic_runtime_failure", "repeated_local_pattern"):
            raise UpgradeError("operant friction evidence.evidence_kind is unsupported")
        if not isinstance(evidence["occurrence_count"], int) or isinstance(evidence["occurrence_count"], bool):
            raise UpgradeError("operant friction evidence.occurrence_count must be an integer")

    return request


def sanitized_evidence(request: dict[str, Any]) -> dict[str, Any]:
    evidence = request["evidence"]
    result = {key: evidence[key] for key in ALLOWED_EVIDENCE_FIELDS if key in evidence}
    if "private_comment" in evidence:
        result["private_evidence_present"] = True
    return result


def _executor_prompt_id(owner: str) -> str:
    if owner.startswith("P07 "):
        return "P07"
    if owner.startswith("P32 "):
        return "P32"
    raise UpgradeError(f"no canonical executor prompt for mutation owner: {owner!r}")


def compile_recipe(raw: object) -> dict[str, Any]:
    contract = load_contract()
    request = validate_work_request(raw, contract)
    engine = contract["surfaces"]["canonical_upgrade_engine"]
    digest = request_digest(request)
    owner = request["preferred_mutation_owner"]
    prompt_id = _executor_prompt_id(owner)
    validators = engine.get("validators")
    if not isinstance(validators, list) or not validators or not all(
        isinstance(item, str) and item.strip() for item in validators
    ):
        raise UpgradeError("canonical upgrade engine validators are not registered")
    generator = engine.get("generator")
    if not isinstance(generator, dict) or not isinstance(generator.get("command"), list):
        raise UpgradeError("canonical upgrade generator is not registered")

    return {
        "schema_version": RECIPE_SCHEMA,
        "source_request_sha256": digest,
        "source_signal_id": request["evidence"]["signal_id"],
        "status": "READY_FOR_EXECUTOR",
        "target": request["target"],
        "coordinator": request["coordinator"],
        "mutation_owner": owner,
        "promotion_owner": request["promotion_owner"],
        "lane": {
            "branch": f"automation/operant-upgrade-{digest[:12]}",
            "isolation_required": True,
            "force_push_allowed": False,
            "merge_authority": False,
        },
        "scope": {
            "owned": request["owned_surface"],
            "forbidden": list(request["forbidden_scope"]),
            "acceptance_condition": request["acceptance_condition"],
        },
        "evidence": sanitized_evidence(request),
        "canonical_sources": list(engine["canonical_sources"]),
        "executor": {
            "prompt_id": prompt_id,
            "prompt_registry": "docs/prompts.json",
            "instruction": "Consume the exact source work request and execute only the bounded repository mutation it authorizes.",
        },
        "generator": {
            "command": list(generator["command"]),
            "output": generator["output"],
            "condition": generator["condition"],
        },
        "validators": list(validators),
        "integration": {
            "owner": "P105/pr-floor-integration",
            "contract": "harness/contracts/pr-merge-gate.v1.json",
            "validator": "python scripts/validate_pr_merge_gate.py",
        },
        "proof_ceiling": (
            "Recipe compilation proves deterministic ownership/scope/generator/validator routing only. "
            "It does not prove repository mutation, branch creation, generated artifact parity, CI, review, "
            "merge, deployment, live friction derivation, or updater delivery."
        ),
    }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(raw_temp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_recipe(request: object, output_dir: Path) -> tuple[dict[str, Any], Path]:
    recipe = compile_recipe(request)
    digest = recipe["source_request_sha256"]
    path = output_dir / f"recipe-{digest}.json"
    _atomic_write(path, json.dumps(recipe, indent=2, ensure_ascii=False) + "\n")
    return recipe, path


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpgradeError(f"cannot read JSON {path}: {exc}") from exc


def validate_recipe(request: object, recipe: object) -> list[str]:
    try:
        expected = compile_recipe(request)
    except UpgradeError as exc:
        return [str(exc)]
    if not isinstance(recipe, dict):
        return ["recipe must be a JSON object"]
    if recipe != expected:
        return ["recipe does not exactly match deterministic compilation of the source work request"]
    return []


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan_parser = sub.add_parser("plan", help="compile one work request into an immutable recipe")
    plan_parser.add_argument("--request", required=True, type=Path)
    plan_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("Outputs/operant-upgrade/recipes"),
    )

    validate_parser = sub.add_parser("validate", help="recompute and compare one recipe exactly")
    validate_parser.add_argument("--request", required=True, type=Path)
    validate_parser.add_argument("--recipe", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            request = read_json(args.request)
            recipe, path = write_recipe(request, args.output_dir)
            print(
                json.dumps(
                    {
                        "schema_version": "operant-upgrade-plan-result/v1",
                        "status": recipe["status"],
                        "recipe_path": path.as_posix(),
                        "source_request_sha256": recipe["source_request_sha256"],
                        "branch": recipe["lane"]["branch"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "validate":
            findings = validate_recipe(read_json(args.request), read_json(args.recipe))
            if findings:
                print("OPERANT_UPGRADE_RECIPE_FAIL")
                for finding in findings:
                    print(f"- {finding}")
                return 1
            print("OPERANT_UPGRADE_RECIPE_PASS")
            return 0
    except UpgradeError as exc:
        print(f"OPERANT_UPGRADE_FAIL: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
