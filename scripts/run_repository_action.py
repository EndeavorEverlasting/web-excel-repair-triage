#!/usr/bin/env python3
"""Run reviewed repository-local actions without arbitrary shell injection."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "harness" / "repository-actions.v1.json"
DEFAULT_REPORT_ROOT = ROOT / "Outputs" / "repository-actions"
CORE_PROOF_INPUTS = (
    "harness/repository-actions.v1.json",
    "harness/contracts/repository-local-proof-continuity.v1.json",
    "scripts/run_repository_action.py",
)


class RepositoryActionError(RuntimeError):
    pass


def normalize_repo_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[0] == ".git"
    ):
        raise RepositoryActionError(f"unsafe proof input path: {value!r}")
    return path.as_posix()


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
        proof_inputs = action.get("proof_inputs")
        if not isinstance(proof_inputs, list) or not proof_inputs:
            raise RepositoryActionError(f"action {action_id} must declare proof_inputs")
        normalized_inputs = [normalize_repo_path(str(value)) for value in proof_inputs]
        if len(normalized_inputs) != len(set(normalized_inputs)):
            raise RepositoryActionError(f"action {action_id} has duplicate proof_inputs")
        steps = action.get("steps")
        if not isinstance(steps, list) or not steps:
            raise RepositoryActionError(f"action {action_id} must define steps")
        for step in steps:
            argv = step.get("argv")
            if not isinstance(argv, list) or not argv or any(
                not isinstance(part, str) or not part for part in argv
            ):
                raise RepositoryActionError(f"action {action_id} has invalid argv")
            if int(step.get("timeout_seconds", 0)) <= 0:
                raise RepositoryActionError(f"action {action_id} has invalid timeout")
    return payload


def resolve_action(payload: dict[str, Any], action_id: str) -> dict[str, Any]:
    for action in payload["actions"]:
        if action["id"] == action_id:
            return action
    raise RepositoryActionError(f"unknown repository action: {action_id}")


def git_required(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed"
        raise RepositoryActionError(detail)
    return result.stdout.strip()


def git_optional(*args: str) -> str:
    try:
        return git_required(*args)
    except RepositoryActionError:
        return "UNKNOWN"


def validate_base_ref(value: str) -> str:
    if (
        not value
        or value.startswith("-")
        or ".." in value
        or "@{" in value
        or not re.fullmatch(r"[A-Za-z0-9._/-]+", value)
    ):
        raise RepositoryActionError(f"unsafe base ref: {value!r}")
    return value


def execution_context(base_ref: str) -> dict[str, str]:
    base_ref = validate_base_ref(base_ref)
    head_sha = git_required("rev-parse", "HEAD")
    base_head_sha = git_required("rev-parse", base_ref)
    comparison_base_sha = git_required("merge-base", head_sha, base_head_sha)
    for label, value in (
        ("candidate head", head_sha),
        ("base-ref head", base_head_sha),
        ("comparison base", comparison_base_sha),
    ):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise RepositoryActionError(f"{label} is not an exact lowercase 40-hex commit: {value!r}")
    return {
        "head_sha": head_sha,
        "base_ref": base_ref,
        "base_head_sha": base_head_sha,
        "base_sha": comparison_base_sha,
    }


def resolve_argv(argv: list[str], context: dict[str, str]) -> list[str]:
    exact = {
        "{python}": sys.executable,
        "{base_sha}": context["base_sha"],
        "{head_sha}": context["head_sha"],
        "{base_head_sha}": context["base_head_sha"],
    }
    resolved: list[str] = []
    for part in argv:
        if part in exact:
            resolved.append(exact[part])
        elif "{" in part or "}" in part:
            if part == "{base_sha}...{head_sha}":
                resolved.append(f"{context['base_sha']}...{context['head_sha']}")
            else:
                raise RepositoryActionError(f"unsupported action placeholder: {part}")
        else:
            resolved.append(part)
    return resolved


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def collect_proof_relevance_inputs(
    action: dict[str, Any], context: dict[str, str]
) -> list[dict[str, str]]:
    declared = [normalize_repo_path(str(value)) for value in action["proof_inputs"]]
    paths = sorted(set(CORE_PROOF_INPUTS).union(declared))
    rows: list[dict[str, str]] = []
    for path in paths:
        blob_sha = git_required("rev-parse", f"{context['head_sha']}:{path}")
        if not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
            raise RepositoryActionError(
                f"proof input {path} did not resolve to an exact tracked blob revision"
            )
        rows.append({"path": path, "blob_sha": blob_sha})
    return rows


def safe_report_path(raw: str | None, action_id: str) -> Path:
    target = Path(raw) if raw else DEFAULT_REPORT_ROOT / f"{action_id}.json"
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    report_root = DEFAULT_REPORT_ROOT.resolve()
    try:
        target.relative_to(report_root)
    except ValueError as exc:
        raise RepositoryActionError(
            "report path must stay inside Outputs/repository-actions"
        ) from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def run_action(
    action: dict[str, Any],
    registry: dict[str, Any],
    report_path: Path,
    *,
    base_ref: str,
) -> int:
    context = execution_context(base_ref)
    proof_inputs = collect_proof_relevance_inputs(action, context)
    target_assumptions = {
        "base_ref": context["base_ref"],
        "base_ref_head": context["base_head_sha"],
        "comparison_base": context["base_sha"],
        "candidate_head": context["head_sha"],
    }
    proof_fingerprint = canonical_sha256(
        {
            "action_id": action["id"],
            "inputs": proof_inputs,
            "target_assumptions": target_assumptions,
        }
    )
    results: list[dict[str, Any]] = []
    status = "PASS"
    for step in action["steps"]:
        argv = resolve_argv(step["argv"], context)
        started = datetime.now(timezone.utc)
        try:
            result = subprocess.run(
                argv,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=int(step["timeout_seconds"]),
            )
            returncode = result.returncode
            stdout = result.stdout[-12000:]
            stderr = result.stderr[-12000:]
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else ""
            stderr = f"timeout after {step['timeout_seconds']}s"
        finished = datetime.now(timezone.utc)
        results.append(
            {
                "id": step["id"],
                "argv": argv,
                "returncode": returncode,
                "status": "PASS" if returncode == 0 else "FAIL",
                "proof_ceiling": step["proof_ceiling"],
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "stdout_tail": stdout,
                "stderr_tail": stderr,
            }
        )
        if returncode != 0:
            status = "FAIL"
            break
    receipt = {
        "schema_version": registry["receipt_schema_version"],
        "registry_id": registry["registry_id"],
        "registry_sha256": canonical_sha256(registry),
        "action_id": action["id"],
        "mutation_authority": action["mutation_authority"],
        "candidate_head": context["head_sha"],
        "branch": git_optional("branch", "--show-current"),
        "base_ref": context["base_ref"],
        "base_ref_head": context["base_head_sha"],
        "comparison_base": context["base_sha"],
        "working_tree_status": git_optional("status", "--porcelain=v1"),
        "proof_relevance_inputs": proof_inputs,
        "target_assumptions": target_assumptions,
        "proof_relevance_fingerprint": proof_fingerprint,
        "proof_freshness": "CURRENT_FOR_RECORDED_INPUT_SET",
        "status": status,
        "steps": results,
        "proof_ceiling": (
            "Repository-local action proof only; hosted runner, deployment, live runtime, "
            "device, and operator acceptance remain separately typed unless directly observed."
        ),
    }
    report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"repository action {action['id']}: {status}")
    print(f"receipt: {report_path.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List registered repository-local actions")
    parser.add_argument("--action", help="Registered action id to run")
    parser.add_argument("--report", help="Receipt path inside Outputs/repository-actions")
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Trusted comparison ref used to derive the merge-base for exact-candidate proof",
    )
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
        return run_action(
            action,
            registry,
            safe_report_path(args.report, action["id"]),
            base_ref=args.base_ref,
        )
    except RepositoryActionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
