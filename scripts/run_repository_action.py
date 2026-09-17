#!/usr/bin/env python3
"""Run reviewed repository-local actions without arbitrary shell injection."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "harness" / "repository-actions.v1.json"
DEFAULT_REPORT_ROOT = ROOT / "Outputs" / "repository-actions"


class RepositoryActionError(RuntimeError):
    pass


def load_registry() -> dict[str, Any]:
    try:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepositoryActionError(f"cannot load repository action registry: {exc}") from exc
    if payload.get("schema_version") != "repository-actions/v1":
        raise RepositoryActionError("unsupported repository action registry schema")
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        raise RepositoryActionError("repository action registry must define actions")
    seen: set[str] = set()
    for action in actions:
        action_id = str(action.get("id", "")).strip()
        if not action_id or action_id in seen:
            raise RepositoryActionError(f"invalid or duplicate action id: {action_id!r}")
        seen.add(action_id)
        steps = action.get("steps")
        if not isinstance(steps, list) or not steps:
            raise RepositoryActionError(f"action {action_id} must define steps")
        for step in steps:
            argv = step.get("argv")
            if not isinstance(argv, list) or not argv or any(not isinstance(part, str) or not part for part in argv):
                raise RepositoryActionError(f"action {action_id} has invalid argv")
            if int(step.get("timeout_seconds", 0)) <= 0:
                raise RepositoryActionError(f"action {action_id} has invalid timeout")
    return payload


def resolve_action(payload: dict[str, Any], action_id: str) -> dict[str, Any]:
    for action in payload["actions"]:
        if action["id"] == action_id:
            return action
    raise RepositoryActionError(f"unknown repository action: {action_id}")


def resolve_argv(argv: list[str]) -> list[str]:
    resolved: list[str] = []
    for part in argv:
        if part == "{python}":
            resolved.append(sys.executable)
        elif "{" in part or "}" in part:
            raise RepositoryActionError(f"unsupported action placeholder: {part}")
        else:
            resolved.append(part)
    return resolved


def git_text(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=30)
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def safe_report_path(raw: str | None, action_id: str) -> Path:
    target = Path(raw) if raw else DEFAULT_REPORT_ROOT / f"{action_id}.json"
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise RepositoryActionError("report path must stay inside repository") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def run_action(action: dict[str, Any], registry: dict[str, Any], report_path: Path) -> int:
    results: list[dict[str, Any]] = []
    status = "PASS"
    for step in action["steps"]:
        argv = resolve_argv(step["argv"])
        started = datetime.now(timezone.utc)
        try:
            result = subprocess.run(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=int(step["timeout_seconds"]))
            returncode = result.returncode
            stdout = result.stdout[-12000:]
            stderr = result.stderr[-12000:]
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else ""
            stderr = f"timeout after {step['timeout_seconds']}s"
        finished = datetime.now(timezone.utc)
        results.append({
            "id": step["id"],
            "argv": argv,
            "returncode": returncode,
            "status": "PASS" if returncode == 0 else "FAIL",
            "proof_ceiling": step["proof_ceiling"],
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "stdout_tail": stdout,
            "stderr_tail": stderr,
        })
        if returncode != 0:
            status = "FAIL"
            break
    receipt = {
        "schema_version": registry["receipt_schema_version"],
        "registry_id": registry["registry_id"],
        "registry_sha256": canonical_sha256(registry),
        "action_id": action["id"],
        "mutation_authority": action["mutation_authority"],
        "candidate_head": git_text("rev-parse", "HEAD"),
        "branch": git_text("branch", "--show-current"),
        "base_floor": git_text("rev-parse", "origin/main"),
        "working_tree_status": git_text("status", "--porcelain=v1"),
        "proof_relevance_fingerprint": canonical_sha256({"registry": registry["registry_id"], "action": action}),
        "status": status,
        "steps": results,
        "proof_ceiling": "Repository-local action proof only; hosted runner, deployment, live runtime, device, and operator acceptance remain separately typed unless directly observed.",
    }
    report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"repository action {action['id']}: {status}")
    print(f"receipt: {report_path.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List registered repository-local actions")
    parser.add_argument("--action", help="Registered action id to run")
    parser.add_argument("--report", help="Receipt path inside the repository")
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.list:
            for action in registry["actions"]:
                print(f"{action['id']}: {action['description']}")
            return 0
        if not args.action:
            raise RepositoryActionError("--action is required unless --list is used")
        action = resolve_action(registry, args.action)
        return run_action(action, registry, safe_report_path(args.report, action["id"]))
    except RepositoryActionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
