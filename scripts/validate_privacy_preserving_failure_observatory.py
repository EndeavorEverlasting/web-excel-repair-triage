#!/usr/bin/env python3
"""Validate the privacy-preserving failure-observatory prototype."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from scripts.failure_observatory import CAPSULE_KEYS, CLAUSE_BY_BOUNDARY, CONTENT_BEARING_HOOKS, SUPPORTED_CURSOR_HOOKS

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness/contracts/privacy-preserving-failure-observatory.v1.json"
ARCHITECTURE_PATH = ROOT / "harness/contracts/execution-boundary-enforcement.v1.json"
HOOKS_PATH = ROOT / "harness/prototypes/failure-observatory/cursor-hooks.example.json"
CORE_PATHS = [ROOT / "scripts/failure_observatory.py", ROOT / "scripts/cursor_failure_sentinel.py"]
FORBIDDEN_NETWORK_IMPORTS = {"requests", "urllib", "httpx", "aiohttp", "socket", "websockets"}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def validate() -> dict[str, int]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    architecture = json.loads(ARCHITECTURE_PATH.read_text(encoding="utf-8"))
    hooks = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "privacy-preserving-failure-observatory/v1":
        raise ValueError("privacy observatory schema mismatch")
    if contract.get("default_mode") != "LOCAL_ONLY":
        raise ValueError("prototype default must remain LOCAL_ONLY")
    if contract.get("design_choice") != "ALLOWLIST_LOCAL_SENTINEL_PLUS_STRUCTURED_RECEIPT":
        raise ValueError("selected design seam drifted")
    if set(contract.get("contribution_capsule_allowlist", [])) != CAPSULE_KEYS:
        raise ValueError("capsule allowlist drifted")
    configured = set(hooks.get("hooks", {}))
    if configured != SUPPORTED_CURSOR_HOOKS:
        raise ValueError(f"Cursor hook coverage drifted: {sorted(configured ^ SUPPORTED_CURSOR_HOOKS)}")
    if configured & CONTENT_BEARING_HOOKS:
        raise ValueError("content-bearing Cursor hook configured")
    for entries in hooks.get("hooks", {}).values():
        for entry in entries:
            command = entry.get("command", "")
            if "--state-dir .afk-observatory" not in command:
                raise ValueError("Cursor hook example must use isolated state directory")
            if "--state .afk-observatory/state.json" in command:
                raise ValueError("single shared Cursor state file is forbidden")
    for path in CORE_PATHS:
        bad = _imports(path) & FORBIDDEN_NETWORK_IMPORTS
        if bad:
            raise ValueError(f"network-capable imports forbidden in {path.name}: {sorted(bad)}")
    local_correlation = contract.get("local_correlation")
    if not isinstance(local_correlation, dict) or "HMAC-SHA256" not in local_correlation.get("derivation", ""):
        raise ValueError("local HMAC correlation contract missing")
    if "run_key" in contract.get("contribution_capsule_allowlist", []):
        raise ValueError("local run key must never be exportable")
    clause_ids = set(architecture.get("observability_clause_ids", {}))
    required_clauses = set(CLAUSE_BY_BOUNDARY.values())
    if not required_clauses.issubset(clause_ids):
        raise ValueError(f"observatory references unknown execution-boundary clauses: {sorted(required_clauses - clause_ids)}")
    phases = {item["phase"]: item["status"] for item in contract.get("phase_map", [])}
    if phases.get("P2_ANONYMOUS_CONTRIBUTION") != "BLOCKED_BY_PRIVACY_DESIGN_APPROVAL":
        raise ValueError("anonymous contribution must remain separately gated")
    return {
        "hooks": len(configured),
        "capsule_fields": len(CAPSULE_KEYS),
        "modules": len(contract.get("modules", [])),
    }


def main() -> int:
    try:
        summary = validate()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"PRIVACY FAILURE OBSERVATORY: FAIL: {exc}")
        return 1
    print(
        "PRIVACY FAILURE OBSERVATORY: PASS | "
        f"hooks={summary['hooks']} | "
        f"capsule_fields={summary['capsule_fields']} | "
        f"modules={summary['modules']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
