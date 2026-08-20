#!/usr/bin/env python3
"""Fail-closed validator for the repository Lua embedding-readiness harness."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
LUA_ROOT = ROOT / "harness" / "lua"
MANIFEST_PATH = LUA_ROOT / "manifest.v1.json"
CONTRACT_PATH = LUA_ROOT / "contracts" / "lua-embedding-readiness.v1.json"
ARTIFACTS_PATH = LUA_ROOT / "artifacts.v1.json"
VALIDATORS_PATH = LUA_ROOT / "validators.v1.json"
CAPABILITIES_PATH = LUA_ROOT / "capabilities.v1.json"
TRIGGERS_PATH = LUA_ROOT / "triggers.v1.json"
GIT_PROBE_TIMEOUT_SECONDS = 15
_TRACKED_PATHS_CACHE: set[str] | None = None

EXPECTED_COMPONENTS = {
    "codebase_map": "harness/lua/CODEBASE_MAP.md",
    "workflow_spec": "harness/lua/WORKFLOW.md",
    "artifact_registry": "harness/lua/ARTIFACT_REGISTRY.md",
    "artifact_registry_machine": "harness/lua/artifacts.v1.json",
    "validator_registry": "harness/lua/validators.v1.json",
    "capability_registry": "harness/lua/capabilities.v1.json",
    "trigger_registry": "harness/lua/triggers.v1.json",
    "contract": "harness/lua/contracts/lua-embedding-readiness.v1.json",
    "skill": ".ai/skills/lua-embedding-readiness/SKILL.md",
    "pre_commit_hook": "harness/lua/hooks/pre-commit.sh",
    "pre_push_hook": "harness/lua/hooks/pre-push.sh",
    "operator_report": "harness/lua/reports/CURRENT_STATE.md",
    "validator": "scripts/validate_lua_harness.py",
    "contract_tests": "tests/test_lua_harness_contract.py",
    "ci_workflow": ".github/workflows/lua-harness-contract.yml",
}
EXPECTED_VALIDATOR_IDS = {
    "lua-harness-completeness",
    "lua-harness-contract-tests",
    "patch-hygiene",
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


class LuaHarnessValidationError(RuntimeError):
    """Raised when the Lua readiness harness violates its contract."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LuaHarnessValidationError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise LuaHarnessValidationError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def require_file(relative_path: str) -> Path:
    path = ROOT / relative_path
    if not path.is_file():
        raise LuaHarnessValidationError(f"missing required file: {relative_path}")
    if path.stat().st_size == 0:
        raise LuaHarnessValidationError(f"required file is empty: {relative_path}")
    return path


def tracked_paths() -> set[str]:
    global _TRACKED_PATHS_CACHE
    if _TRACKED_PATHS_CACHE is not None:
        return _TRACKED_PATHS_CACHE
    if not (ROOT / ".git").exists():
        _TRACKED_PATHS_CACHE = set()
        return _TRACKED_PATHS_CACHE
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LuaHarnessValidationError(f"tracked-file Git probe failed: {exc}") from exc
    if result.returncode != 0:
        raise LuaHarnessValidationError(
            f"tracked-file Git probe exited with code {result.returncode}"
        )
    _TRACKED_PATHS_CACHE = {
        item.replace("\\", "/")
        for item in result.stdout.decode("utf-8", errors="replace").split("\0")
        if item
    }
    return _TRACKED_PATHS_CACHE


def require_tracked(relative_path: str) -> None:
    if not (ROOT / ".git").exists():
        return
    if relative_path.replace("\\", "/") not in tracked_paths():
        raise LuaHarnessValidationError(
            f"required Lua harness file is not tracked: {relative_path}"
        )


def require_string_list(value: Any, field: str, minimum: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise LuaHarnessValidationError(f"{field} must contain at least {minimum} item(s)")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise LuaHarnessValidationError(f"{field} contains an empty/non-string item")
        items.append(item.strip())
    if len(items) != len(set(items)):
        raise LuaHarnessValidationError(f"{field} contains duplicate items")
    return items


def validate_contract_payload(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "lua-embedding-readiness/v1":
        raise LuaHarnessValidationError("unsupported Lua embedding contract schema")
    if contract.get("contract_id") != "lua-embedding-readiness":
        raise LuaHarnessValidationError("Lua contract ID drifted")
    if contract.get("runtime_status") != "not_implemented":
        raise LuaHarnessValidationError(
            "harness sprint must not claim a product Lua runtime is implemented"
        )

    expected_sections: dict[str, dict[str, Any]] = {
        "architecture": {
            "embedding_model": "language-as-library",
            "host_owns_main_loop": True,
            "script_owns_main_loop": False,
            "performance_critical_code_owner": "host",
            "dynamic_logic_owner": "lua",
        },
        "state_isolation": {
            "independent_vm_states": True,
            "state_destroy_isolated": True,
            "explicit_release_required": True,
        },
        "error_handling": {
            "script_errors_allowed": True,
            "host_catches_script_errors": True,
            "host_owns_rollback": True,
            "cleanup_on_error": True,
        },
        "execution": {
            "precompiled_bytecode_allowed": True,
            "small_interpreter_dispatch_preferred": True,
            "jit_required": False,
            "deoptimization_requires_reconstructible_state": True,
        },
        "type_system": {
            "runtime_type_checks": True,
            "internal_type_discipline_required": True,
        },
        "sandbox": {
            "default_os_library": False,
            "default_io_library": False,
            "default_native_module_loading": False,
            "host_api_policy": "allow-list",
            "expose_only_required_host_functions": True,
        },
        "design_philosophy": {
            "feature_policy": "exclude-by-default",
            "prefer_host_solution_before_script_complexity": True,
            "auditable_non_magical_semantics": True,
            "indexing": "lua-1-based",
        },
        "ai_auditability": {
            "human_auditable_generated_code": True,
            "hidden_mechanisms_forbidden": True,
        },
        "implementation_boundary": {
            "product_runtime_present": False,
            "product_code_allowed_in_harness_sprint": False,
            "host_language_is_selected_by_product_lane": True,
            "lua_distribution_is_selected_by_product_lane": True,
        },
    }
    for section, expected in expected_sections.items():
        actual = contract.get(section)
        if actual != expected:
            raise LuaHarnessValidationError(
                f"Lua design contract drifted in {section}: expected={expected!r} actual={actual!r}"
            )
    proof = require_string_list(
        contract.get("required_runtime_proof"), "contract.required_runtime_proof", 8
    )
    joined = " ".join(proof).lower()
    for phrase in (
        "independent lua vm states",
        "script error",
        "explicitly released",
        "os, io",
        "allow-listed",
        "main execution loop",
        "runtime type checks",
        "human audit",
    ):
        if phrase not in joined:
            raise LuaHarnessValidationError(
                f"runtime proof checklist is missing required concept: {phrase}"
            )
    if not str(contract.get("proof_ceiling", "")).strip():
        raise LuaHarnessValidationError("Lua contract lacks a proof ceiling")


def validate_manifest() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    if manifest.get("schema_version") != "lua-embedding-harness/v1":
        raise LuaHarnessValidationError("unsupported Lua harness manifest schema")
    if manifest.get("domain") != "lua-embedding-readiness":
        raise LuaHarnessValidationError("Lua harness domain drifted")
    if manifest.get("runtime_status") != "not_implemented":
        raise LuaHarnessValidationError("Lua harness runtime status must remain not_implemented")
    if manifest.get("parent_workflow") != "harness-infrastructure":
        raise LuaHarnessValidationError("Lua harness parent workflow drifted")
    if manifest.get("components") != EXPECTED_COMPONENTS:
        raise LuaHarnessValidationError("Lua harness component inventory drifted")
    for relative_path in EXPECTED_COMPONENTS.values():
        require_file(relative_path)
        require_tracked(relative_path)
    order = require_string_list(manifest.get("validation_order"), "manifest.validation_order", 6)
    if order[0] != (
        "python -m py_compile scripts/validate_lua_harness.py tests/test_lua_harness_contract.py"
    ):
        raise LuaHarnessValidationError("Lua validation must begin with compilation")
    if order[-1] != "git diff --check":
        raise LuaHarnessValidationError("Lua validation must end with git diff --check")
    return manifest


def validate_machine_registries() -> None:
    artifacts = load_json(ARTIFACTS_PATH)
    if artifacts.get("schema_version") != "lua-harness-artifacts/v1":
        raise LuaHarnessValidationError("Lua artifact registry schema drifted")
    artifact_items = artifacts.get("artifacts")
    if not isinstance(artifact_items, list):
        raise LuaHarnessValidationError("Lua artifact registry must contain a list")
    by_artifact = {str(item.get("id")): item for item in artifact_items if isinstance(item, dict)}
    if set(by_artifact) != {"lua-harness-control-plane", "lua-embedding-readiness-report"}:
        raise LuaHarnessValidationError("Lua artifact IDs drifted")
    if by_artifact["lua-harness-control-plane"].get("canonical_path") != "harness/lua/manifest.v1.json":
        raise LuaHarnessValidationError("Lua control-plane artifact path drifted")
    if by_artifact["lua-embedding-readiness-report"].get("canonical_path") != "Outputs/lua-embedding-readiness.json":
        raise LuaHarnessValidationError("Lua readiness report path drifted")

    validators = load_json(VALIDATORS_PATH)
    if validators.get("schema_version") != "lua-harness-validators/v1":
        raise LuaHarnessValidationError("Lua validator registry schema drifted")
    validator_items = validators.get("validators")
    if not isinstance(validator_items, list):
        raise LuaHarnessValidationError("Lua validator registry must contain a list")
    by_validator = {str(item.get("id")): item for item in validator_items if isinstance(item, dict)}
    if set(by_validator) != EXPECTED_VALIDATOR_IDS:
        raise LuaHarnessValidationError("Lua validator IDs drifted")
    if validators.get("profiles", {}).get("lua") != [
        "lua-harness-completeness",
        "lua-harness-contract-tests",
        "patch-hygiene",
    ]:
        raise LuaHarnessValidationError("Lua validator profile order drifted")
    for item in by_validator.values():
        if item.get("blocking") is not True:
            raise LuaHarnessValidationError(f"Lua validator must be blocking: {item.get('id')}")

    capabilities = load_json(CAPABILITIES_PATH)
    if capabilities.get("schema_version") != "lua-harness-capabilities/v1":
        raise LuaHarnessValidationError("Lua capability registry schema drifted")
    capability_items = capabilities.get("capabilities")
    if not isinstance(capability_items, list) or len(capability_items) != 1:
        raise LuaHarnessValidationError("Lua harness must expose one capability")
    capability = capability_items[0]
    if capability.get("id") != "lua-embedding-readiness":
        raise LuaHarnessValidationError("Lua capability ID drifted")
    if capability.get("skill") != ".ai/skills/lua-embedding-readiness/SKILL.md":
        raise LuaHarnessValidationError("Lua capability skill owner drifted")
    if capability.get("trigger_ids") != ["lua-embedding-request"]:
        raise LuaHarnessValidationError("Lua capability trigger list drifted")
    if capability.get("implementation") != {
        "kind": "script",
        "path": "scripts/validate_lua_harness.py",
    }:
        raise LuaHarnessValidationError("Lua capability implementation drifted")

    triggers = load_json(TRIGGERS_PATH)
    if triggers.get("schema_version") != "lua-harness-triggers/v1":
        raise LuaHarnessValidationError("Lua trigger registry schema drifted")
    trigger_items = triggers.get("triggers")
    if not isinstance(trigger_items, list) or len(trigger_items) != 1:
        raise LuaHarnessValidationError("Lua harness must expose one trigger")
    trigger = trigger_items[0]
    if trigger.get("id") != "lua-embedding-request":
        raise LuaHarnessValidationError("Lua trigger ID drifted")
    if trigger.get("capability_id") != "lua-embedding-readiness":
        raise LuaHarnessValidationError("Lua trigger capability owner drifted")
    if trigger.get("skill") != capability.get("skill"):
        raise LuaHarnessValidationError("Lua trigger skill owner drifted")
    if trigger.get("workflow") != "harness/lua/WORKFLOW.md":
        raise LuaHarnessValidationError("Lua trigger workflow drifted")
    require_string_list(trigger.get("conditions"), "trigger.conditions", 3)
    require_string_list(trigger.get("forbidden_conditions"), "trigger.forbidden_conditions", 3)


def validate_human_surfaces() -> None:
    required: dict[str, tuple[str, ...]] = {
        "harness/lua/CODEBASE_MAP.md": (
            "## Reading order",
            "## Design invariants",
            "Language as a library",
            "Independent states",
            "Sandbox by allow-list",
            "AI auditability",
        ),
        "harness/lua/WORKFLOW.md": (
            "## 1. Pick up a Lua task",
            "## 2. Establish the host/script boundary",
            "## 3. Validate readiness before product implementation",
            "## 4. Product-lane handoff",
            "## 5. Failure handling",
            "## 6. Handoff fields",
        ),
        "harness/lua/ARTIFACT_REGISTRY.md": (
            "## Tracked control-plane artifacts",
            "## Runtime evidence artifact",
            "Outputs/lua-embedding-readiness.json",
            "## Proof boundary",
        ),
        "harness/lua/reports/CURRENT_STATE.md": (
            "Runtime status: NOT IMPLEMENTED",
            "## What is working",
            "## What is missing",
            "## Proof ceiling",
        ),
    }
    for relative_path, phrases in required.items():
        text = require_file(relative_path).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                raise LuaHarnessValidationError(
                    f"{relative_path} is missing required text: {phrase}"
                )

    skill = require_file(".ai/skills/lua-embedding-readiness/SKILL.md").read_text(
        encoding="utf-8"
    )
    for section in REQUIRED_SKILL_SECTIONS:
        if section not in skill:
            raise LuaHarnessValidationError(f"Lua skill is missing {section}")
    lower = skill.lower()
    for phrase in (
        "host in control",
        "default-deny",
        "do not expose os, io",
        "independent vm states",
        "human audit",
        "1-based indexing",
    ):
        if phrase not in lower:
            raise LuaHarnessValidationError(f"Lua skill is missing guardrail concept: {phrase}")


def validate_root_registration() -> None:
    root_manifest = load_json(ROOT / "harness" / "manifest.v1.json")
    registration = root_manifest.get("domain_contracts", {}).get("lua_embedding_readiness")
    expected = {
        "contract": "harness/lua/contracts/lua-embedding-readiness.v1.json",
        "validator": "scripts/validate_lua_harness.py",
        "contract_tests": "tests/test_lua_harness_contract.py",
        "workflow": "WORKFLOW.md#c-harness-infrastructure-change",
        "harness_gate": "python scripts/validate_lua_harness.py --output Outputs/lua-embedding-readiness.json --summary",
        "domain_manifest": "harness/lua/manifest.v1.json",
        "skill": ".ai/skills/lua-embedding-readiness/SKILL.md",
        "operator_report": "harness/lua/reports/CURRENT_STATE.md",
    }
    if registration != expected:
        raise LuaHarnessValidationError("root harness Lua domain registration drifted")


def validate_repository() -> None:
    validate_manifest()
    contract = load_json(CONTRACT_PATH)
    if not isinstance(contract, dict):
        raise LuaHarnessValidationError("Lua embedding contract must be an object")
    validate_contract_payload(contract)
    validate_machine_registries()
    validate_human_surfaces()
    validate_root_registration()


def resolve_report_target(path: Path) -> Path:
    target = path if path.is_absolute() else ROOT / path
    target = target.resolve()
    root = ROOT.resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return target
    outputs = (ROOT / "Outputs").resolve()
    try:
        target.relative_to(outputs)
    except ValueError as exc:
        raise LuaHarnessValidationError(
            "repository-local Lua readiness reports must be written under Outputs/"
        ) from exc
    return target


def write_report(path: Path, checks: list[dict[str, str]], failures: list[str]) -> None:
    target = resolve_report_target(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lua-embedding-readiness-report/v1",
        "repository": "EndeavorEverlasting/web-excel-repair-triage",
        "domain": "lua-embedding-readiness",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "FAIL" if failures else "PASS",
        "runtime_status": "not_implemented",
        "checks": checks,
        "failure_count": len(failures),
        "proof_ceiling": (
            "Harness readiness and static contract proof only; no Lua runtime, "
            "sandbox, VM isolation, memory-release, bytecode, JIT, or application proof."
        ),
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Lua embedding readiness harness.")
    parser.add_argument("--output", type=Path, help="Optional JSON report output path.")
    parser.add_argument("--summary", action="store_true", help="Print compact result summary.")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    checks: list[dict[str, str]] = []
    failures: list[str] = []

    def run(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (LuaHarnessValidationError, KeyError, OSError, TypeError, ValueError) as exc:
            message = str(exc)
            checks.append({"name": name, "status": "FAIL", "message": message})
            failures.append(f"{name}: {message}")
            if not args.summary:
                print(f"[FAIL] {name}: {message}")
        else:
            checks.append({"name": name, "status": "PASS", "message": "ok"})
            if not args.summary:
                print(f"[PASS] {name}")

    run("manifest", validate_manifest)
    run("design contract", lambda: validate_contract_payload(load_json(CONTRACT_PATH)))
    run("machine registries", validate_machine_registries)
    run("human surfaces", validate_human_surfaces)
    run("root registration", validate_root_registration)

    if args.output:
        try:
            write_report(args.output, checks, failures)
        except (LuaHarnessValidationError, OSError, TypeError, ValueError) as exc:
            failures.append(f"report: {exc}")
            checks.append({"name": "report", "status": "FAIL", "message": str(exc)})

    if args.summary:
        print(
            f"Lua embedding readiness: {'FAIL' if failures else 'PASS'}; "
            f"runtime_status=not_implemented; checks={len(checks)}; failures={len(failures)}"
        )
    if failures:
        if not args.summary:
            print("Lua harness validation failed:")
            for failure in failures:
                print(f"- {failure}")
        return 1
    if not args.summary:
        print("Lua harness validation passed; product runtime remains not implemented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
