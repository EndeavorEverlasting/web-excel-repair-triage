#!/usr/bin/env python3
"""Run one repository-owned validator profile without depending on CI."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "harness" / "validators.v1.json"
SCHEMA_VERSION = "web-excel-validators/v1"
REPORT_SCHEMA_VERSION = "validator-profile-report/v1"


class ProfileContractError(RuntimeError):
    """Raised when the validator registry/profile cannot be executed safely."""


def read_registry(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProfileContractError(f"cannot load validator registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProfileContractError("validator registry root must be an object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ProfileContractError(
            f"unsupported validator registry schema: {payload.get('schema_version')!r}"
        )
    return payload, hashlib.sha256(raw).hexdigest()


def resolve_profile(payload: dict[str, Any], profile_name: str) -> list[dict[str, Any]]:
    validators = payload.get("validators")
    profiles = payload.get("profiles")
    if not isinstance(validators, list) or not isinstance(profiles, dict):
        raise ProfileContractError("validator registry is missing validators/profiles")

    by_id: dict[str, dict[str, Any]] = {}
    for item in validators:
        if not isinstance(item, dict):
            raise ProfileContractError("validator entry must be an object")
        validator_id = item.get("id")
        if not isinstance(validator_id, str) or not validator_id.strip():
            raise ProfileContractError("validator entry has no non-empty id")
        if validator_id in by_id:
            raise ProfileContractError(f"duplicate validator id: {validator_id}")
        command = item.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ProfileContractError(f"validator has no command: {validator_id}")
        if not isinstance(item.get("blocking"), bool):
            raise ProfileContractError(
                f"validator blocking flag must be boolean: {validator_id}"
            )
        by_id[validator_id] = item

    selected = profiles.get(profile_name)
    if not isinstance(selected, list) or not selected:
        raise ProfileContractError(f"validator profile is missing or empty: {profile_name}")
    if len(selected) != len(set(map(str, selected))):
        raise ProfileContractError(f"validator profile contains duplicate ids: {profile_name}")

    resolved: list[dict[str, Any]] = []
    for raw_id in selected:
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise ProfileContractError(
                f"validator profile contains invalid id: {profile_name}"
            )
        item = by_id.get(raw_id)
        if item is None:
            raise ProfileContractError(
                f"validator profile references unknown id: {profile_name}:{raw_id}"
            )
        resolved.append(item)
    return resolved


def command_argv(command: str) -> list[str]:
    argv = shlex.split(command, posix=os.name != "nt")
    if not argv:
        raise ProfileContractError("empty validator command")
    if argv[0].lower() in {"python", "python3", "py"}:
        argv[0] = sys.executable
    return argv


def git_value(*args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def run_command(validator: dict[str, Any]) -> dict[str, Any]:
    validator_id = str(validator["id"])
    argv = command_argv(str(validator["command"]))
    print(f"\n=== validator:{validator_id} ===")
    started = time.monotonic()
    result = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    duration = round(time.monotonic() - started, 3)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(
            stderr,
            file=sys.stderr,
            end="" if stderr.endswith("\n") else "\n",
        )
    return {
        "id": validator_id,
        "class": validator.get("class"),
        "command": validator["command"],
        "argv": argv,
        "blocking": validator["blocking"],
        "output": validator.get("output"),
        "proof_ceiling": validator.get("proof_ceiling"),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "duration_seconds": duration,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }


def resolve_report_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    candidate = path if path.is_absolute() else REPO_ROOT / path
    resolved = candidate.resolve()
    repo = REPO_ROOT.resolve()
    if resolved.is_relative_to(repo):
        outputs = (repo / "Outputs").resolve()
        if not resolved.is_relative_to(outputs):
            raise ProfileContractError(
                "repository-local validator profile reports must be written under Outputs/"
            )
    return resolved


def relative_or_absolute(path: Path) -> str:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    return (
        str(resolved.relative_to(repo)).replace("\\", "/")
        if resolved.is_relative_to(repo)
        else str(resolved)
    )


def profile_fingerprint(
    registry_path: Path,
    registry_sha256: str,
    profile_name: str,
    validators: list[dict[str, Any]],
) -> list[dict[str, str]]:
    entries = [
        {
            "kind": "validator_registry",
            "identity": relative_or_absolute(registry_path),
            "revision": registry_sha256,
        },
        {
            "kind": "validator_profile",
            "identity": profile_name,
            "revision": hashlib.sha256(
                "\n".join(str(item["id"]) for item in validators).encode("utf-8")
            ).hexdigest(),
        },
    ]
    entries.extend(
        {
            "kind": "validator",
            "identity": str(item["id"]),
            "revision": hashlib.sha256(
                json.dumps(
                    {
                        "command": item["command"],
                        "blocking": item["blocking"],
                        "output": item.get("output"),
                        "proof_ceiling": item.get("proof_ceiling"),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        for item in validators
    )
    return entries


def execute_profile(
    profile_name: str,
    registry_path: Path = DEFAULT_REGISTRY,
    report_path: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    report_target: Path | None = None
    try:
        report_target = resolve_report_path(report_path)
        registry, registry_sha256 = read_registry(registry_path)
        validators = resolve_profile(registry, profile_name)
    except ProfileContractError as exc:
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "FAIL",
            "failed_validator": "contract",
            "error": str(exc),
            "profile": profile_name,
            "steps": [],
        }
        if report_target is not None:
            report_target.parent.mkdir(parents=True, exist_ok=True)
            report_target.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        print(f"VALIDATOR PROFILE CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2, report

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "PASS",
        "failed_validator": None,
        "profile": profile_name,
        "registry": relative_or_absolute(registry_path),
        "registry_sha256": registry_sha256,
        "commit_sha": git_value("rev-parse", "HEAD"),
        "branch": git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "python": sys.version.split()[0],
        "proof_relevance_fingerprint": profile_fingerprint(
            registry_path, registry_sha256, profile_name, validators
        ),
        "steps": [],
    }

    warning_failures = 0
    for validator in validators:
        step = run_command(validator)
        report["steps"].append(step)
        if step["returncode"] == 0:
            continue
        if validator["blocking"]:
            report["status"] = "FAIL"
            report["failed_validator"] = validator["id"]
            break
        warning_failures += 1

    if report["status"] == "PASS" and warning_failures:
        report["status"] = "PASS_WITH_WARNINGS"
    report["warning_failure_count"] = warning_failures
    report["observed_step_count"] = len(report["steps"])
    report["required_step_count"] = len(validators)

    if report_target is not None:
        report_target.parent.mkdir(parents=True, exist_ok=True)
        report_target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Receipt: {report_target}")

    print(
        f"VALIDATOR PROFILE {profile_name}: {report['status']} "
        f"({len(report['steps'])}/{len(validators)} steps observed)"
    )
    return (1 if report["status"] == "FAIL" else 0), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Named profile from harness/validators.v1.json")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List registered profile names without executing validators.",
    )
    args = parser.parse_args(argv)
    registry_path = (
        args.registry if args.registry.is_absolute() else (REPO_ROOT / args.registry)
    ).resolve()

    if args.list_profiles:
        try:
            payload, _ = read_registry(registry_path)
        except ProfileContractError as exc:
            print(f"VALIDATOR PROFILE CONTRACT FAIL: {exc}", file=sys.stderr)
            return 2
        profiles = payload.get("profiles")
        if not isinstance(profiles, dict):
            print("VALIDATOR PROFILE CONTRACT FAIL: profiles missing", file=sys.stderr)
            return 2
        for name in sorted(profiles):
            print(name)
        return 0

    if not args.profile:
        parser.error("--profile is required unless --list-profiles is used")
    report = args.report
    if report is not None and not report.is_absolute():
        report = REPO_ROOT / report
    code, _ = execute_profile(args.profile, registry_path, report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
