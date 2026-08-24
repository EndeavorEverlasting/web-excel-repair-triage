#!/usr/bin/env python3
"""Run the repository-owned deterministic automated-test floor."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "harness" / "test-floor.v1.json"
DEFAULT_REPORT = REPO_ROOT / "Outputs" / "deterministic-test-floor-report.json"


class ContractError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return payload


def load_contract(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _read_json(manifest_path)
    if manifest.get("schema_version") != "deterministic-test-floor/v1":
        raise ContractError("unsupported deterministic test-floor schema")

    for field in ("compile_targets", "artifact_imports", "artifact_tests"):
        values = manifest.get(field)
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ContractError(f"{field} must be a non-empty list of strings")

    for rel in manifest["compile_targets"] + manifest["artifact_tests"]:
        if not (REPO_ROOT / rel).exists():
            raise ContractError(f"required test-floor path is missing: {rel}")

    registry_path = REPO_ROOT / str(manifest.get("validator_registry", ""))
    registry = _read_json(registry_path)
    validators = registry.get("validators")
    profiles = registry.get("profiles")
    if not isinstance(validators, list) or not isinstance(profiles, dict):
        raise ContractError("validator registry is missing validators/profiles")

    validator_by_id = {
        str(item.get("id")): item
        for item in validators
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    profile_name = str(manifest.get("validator_profile", ""))
    profile = profiles.get(profile_name)
    if not isinstance(profile, list) or not profile:
        raise ContractError(f"validator profile is missing or empty: {profile_name}")

    resolved: list[dict[str, Any]] = []
    for validator_id in profile:
        item = validator_by_id.get(str(validator_id))
        if item is None:
            raise ContractError(f"validator profile references unknown id: {validator_id}")
        if item.get("blocking") is not True:
            raise ContractError(f"test-floor validator must be blocking: {validator_id}")
        command = item.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ContractError(f"validator has no command: {validator_id}")
        resolved.append(item)
    return manifest, resolved


def command_argv(command: str) -> list[str]:
    argv = shlex.split(command, posix=os.name != "nt")
    if not argv:
        raise ContractError("empty validator command")
    if argv[0].lower() in {"python", "python3", "py"}:
        argv[0] = sys.executable
    return argv


def _git_value(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def run_step(label: str, argv: list[str], env: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    duration = round(time.monotonic() - started, 3)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, file=sys.stderr, end="" if stderr.endswith("\n") else "\n")
    return {
        "label": label,
        "argv": argv,
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "duration_seconds": duration,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def build_steps(manifest: dict[str, Any], validators: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    imports = "; ".join(f"import {name}" for name in manifest["artifact_imports"]) + "; print('artifact imports ok')"
    steps: list[tuple[str, list[str]]] = [
        (
            "python-compile",
            [sys.executable, "-m", "compileall", "-q", *manifest["compile_targets"]],
        ),
        ("artifact-import-smoke", [sys.executable, "-c", imports]),
        (
            "artifact-engine-tests",
            [sys.executable, "-m", "pytest", *manifest["artifact_tests"], "-q"],
        ),
    ]
    for validator in validators:
        steps.append((f"validator:{validator['id']}", command_argv(str(validator["command"]))))

    if _git_value("rev-parse", "--verify", "origin/main"):
        steps.append(("branch-patch-hygiene", ["git", "diff", "--check", "origin/main...HEAD"]))
    else:
        steps.append(("branch-patch-hygiene", ["git", "diff", "--check"]))
    return steps


def run(manifest_path: Path, report_path: Path) -> int:
    try:
        manifest, validators = load_contract(manifest_path)
        steps = build_steps(manifest, validators)
    except ContractError as exc:
        report = {
            "schema_version": "deterministic-test-floor-report/v1",
            "status": "FAIL",
            "failed_step": "contract",
            "error": str(exc),
            "steps": [],
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"TEST FLOOR CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    for key, value in manifest.get("environment", {}).items():
        env[str(key)] = str(value)
    (REPO_ROOT / "Outputs").mkdir(exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": "deterministic-test-floor-report/v1",
        "status": "PASS",
        "failed_step": None,
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "python": sys.version.split()[0],
        "manifest": str(manifest_path.relative_to(REPO_ROOT)) if manifest_path.is_relative_to(REPO_ROOT) else str(manifest_path),
        "validator_profile": manifest["validator_profile"],
        "artifact_test_count": len(manifest["artifact_tests"]),
        "proof_ceiling": manifest.get("proof_ceiling"),
        "steps": [],
    }

    for label, argv in steps:
        print(f"\n=== {label} ===")
        step = run_step(label, argv, env)
        report["steps"].append(step)
        if step["returncode"] != 0:
            report["status"] = "FAIL"
            report["failed_step"] = label
            break

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"\nDETERMINISTIC TEST FLOOR: {report['status']} "
        f"({len(report['steps'])}/{len(steps)} steps observed)"
    )
    print(f"Receipt: {report_path}")
    if report["failed_step"]:
        print(f"Failed step: {report['failed_step']}", file=sys.stderr)
        return 1
    if len(report["steps"]) != len(steps):
        print("TEST FLOOR FAIL: not every required step executed", file=sys.stderr)
        return 3
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic repository test floor.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    manifest = args.manifest if args.manifest.is_absolute() else (REPO_ROOT / args.manifest)
    report = args.report if args.report.is_absolute() else (REPO_ROOT / args.report)
    return run(manifest.resolve(), report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
