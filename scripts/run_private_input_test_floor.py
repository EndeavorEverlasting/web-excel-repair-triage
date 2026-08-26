#!/usr/bin/env python3
"""Run registered private-input regressions without treating absent operator files as green."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "harness" / "test-floor.v1.json"
DEFAULT_REPORT = REPO_ROOT / "Outputs" / "private-input-test-floor-report.json"


class ContractError(RuntimeError):
    pass


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


def load_requirements(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load private-input manifest: {exc}") from exc
    if manifest.get("schema_version") != "deterministic-test-floor/v1":
        raise ContractError("unsupported deterministic test-floor schema")

    allowed = manifest.get("allowed_artifact_skip_reasons")
    artifact_tests = manifest.get("artifact_tests")
    raw = manifest.get("private_input_requirements")
    if not isinstance(allowed, list) or not isinstance(artifact_tests, list):
        raise ContractError("test-floor skip/test owners are malformed")
    if not isinstance(raw, list) or not raw:
        raise ContractError("private_input_requirements must be a non-empty list")

    records: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_selectors: set[str] = set()
    seen_reasons: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ContractError("private input requirement must be an object")
        record = {
            key: str(item.get(key, "")).strip()
            for key in ("id", "input_path", "test_selector", "missing_reason")
        }
        if any(not value for value in record.values()):
            raise ContractError("private input requirement has an empty required field")

        rel = PurePosixPath(record["input_path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ContractError(
                f"private input path must stay repository-relative: {record['input_path']}"
            )

        selector = record["test_selector"]
        test_file = selector.split("::", 1)[0]
        if "::" not in selector or test_file not in artifact_tests:
            raise ContractError(
                f"private test selector is not owned by artifact_tests: {selector}"
            )
        if record["missing_reason"] not in allowed:
            raise ContractError(
                f"private input reason is not registered: {record['missing_reason']}"
            )
        if (
            record["id"] in seen_ids
            or selector in seen_selectors
            or record["missing_reason"] in seen_reasons
        ):
            raise ContractError("private input ids, selectors, and reasons must be unique")

        seen_ids.add(record["id"])
        seen_selectors.add(selector)
        seen_reasons.add(record["missing_reason"])
        records.append(record)

    if seen_reasons != set(allowed):
        raise ContractError(
            "private input requirements must exactly own the registered private skip reasons"
        )
    return manifest, records


def missing_requirements(
    records: list[dict[str, str]], repo_root: Path = REPO_ROOT
) -> list[dict[str, str]]:
    return [
        record
        for record in records
        if not (repo_root / record["input_path"]).is_file()
    ]


def pytest_argv(records: list[dict[str, str]]) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        *[record["test_selector"] for record in records],
        "-q",
        "-rs",
    ]


def _pytest_skip_count(stdout: str) -> int:
    matches = re.findall(r"\b(\d+) skipped\b", stdout)
    return int(matches[-1]) if matches else 0


def run(manifest_path: Path, report_path: Path) -> int:
    try:
        manifest, records = load_requirements(manifest_path)
    except ContractError as exc:
        report = {
            "schema_version": "private-input-test-floor-report/v1",
            "status": "FAIL",
            "failed_step": "contract",
            "error": str(exc),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"PRIVATE INPUT CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2

    missing = missing_requirements(records)
    report: dict[str, Any] = {
        "schema_version": "private-input-test-floor-report/v1",
        "status": "BLOCKED" if missing else "PASS",
        "failed_step": "private-input-readiness" if missing else None,
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "required_input_ids": [record["id"] for record in records],
        "missing_input_ids": [record["id"] for record in missing],
        "test_selectors": [record["test_selector"] for record in records],
        "proof_ceiling": (
            "Private-input regression PASS is available only when all registered operator inputs "
            "are present. This gate never proves production, privileged-device, secret-bearing, "
            "or operator acceptance behavior."
        ),
        "test": None,
    }

    if missing:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("PRIVATE INPUT TEST FLOOR: BLOCKED")
        print("Missing registered input ids: " + ", ".join(report["missing_input_ids"]))
        print(f"Receipt: {report_path}")
        return 3

    env = os.environ.copy()
    for key, value in manifest.get("environment", {}).items():
        env[str(key)] = str(value)

    argv = pytest_argv(records)
    result = subprocess.run(
        argv,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, file=sys.stderr, end="" if stderr.endswith("\n") else "\n")

    skip_count = _pytest_skip_count(stdout)
    status = "PASS" if result.returncode == 0 and skip_count == 0 else "FAIL"
    report["status"] = status
    report["failed_step"] = None if status == "PASS" else "private-input-regressions"
    report["test"] = {
        "argv": argv,
        "returncode": result.returncode,
        "skip_count": skip_count,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PRIVATE INPUT TEST FLOOR: {status}")
    print(f"Receipt: {report_path}")
    return 0 if status == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run registered private-input regressions fail-closed."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    manifest = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    report = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    return run(manifest.resolve(), report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
