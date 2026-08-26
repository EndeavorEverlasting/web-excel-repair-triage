#!/usr/bin/env python3
"""Run registered private-input regressions without treating absent operator files as green."""
from __future__ import annotations

import argparse
import ast
import hashlib
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


def _assignment_names(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for item in target.elts:
            names.update(_assignment_names(item))
        return names
    return set()


def validate_selector_source(record: dict[str, str]) -> None:
    parts = record["test_selector"].split("::")
    if len(parts) != 2 or not parts[1].isidentifier():
        raise ContractError(
            f"private test selector must name one top-level test function: {record['test_selector']}"
        )
    test_file, node_name = parts
    source_path = REPO_ROOT / test_file
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(source_path))
    except (OSError, SyntaxError) as exc:
        raise ContractError(f"cannot inspect private test selector source: {exc}") from exc

    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == node_name
        ),
        None,
    )
    if function is None:
        raise ContractError(f"private test node does not exist: {record['test_selector']}")

    function_constants = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    if record["missing_reason"] not in function_constants:
        raise ContractError(
            f"private test node is not bound to its registered skip reason: {record['test_selector']}"
        )

    input_names: set[str] = set()
    for statement in tree.body:
        value: ast.expr | None = None
        targets: list[ast.expr] = []
        if isinstance(statement, ast.Assign):
            value = statement.value
            targets = list(statement.targets)
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            value = statement.value
            targets = [statement.target]
        if value is None:
            continue
        constants = {
            node.value
            for node in ast.walk(value)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        if record["input_path"] in constants:
            for target in targets:
                input_names.update(_assignment_names(target))

    if not input_names:
        raise ContractError(
            f"registered private input path is not declared by selector source: {record['test_selector']}"
        )
    function_names = {
        node.id for node in ast.walk(function) if isinstance(node, ast.Name)
    }
    if not input_names.intersection(function_names):
        raise ContractError(
            f"private test node does not reference its registered input binding: {record['test_selector']}"
        )


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

        validate_selector_source(record)
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_artifacts(
    records: list[dict[str, str]], repo_root: Path = REPO_ROOT
) -> list[dict[str, str]]:
    return [
        {
            "id": record["id"],
            "path": record["input_path"],
            "sha256": _sha256_file(repo_root / record["input_path"]),
        }
        for record in records
    ]


def tracked_dirty_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ContractError("cannot determine tracked git state for private-input proof")
    return [line[3:] for line in result.stdout.splitlines() if len(line) >= 4]


def _write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


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
        _write_report(report_path, report)
        print(f"PRIVATE INPUT CONTRACT FAIL: {exc}", file=sys.stderr)
        return 2

    missing = missing_requirements(records)
    commit_sha = _git_value("rev-parse", "HEAD")
    branch = _git_value("rev-parse", "--abbrev-ref", "HEAD")
    report: dict[str, Any] = {
        "schema_version": "private-input-test-floor-report/v1",
        "status": "BLOCKED" if missing else "PASS",
        "failed_step": "private-input-readiness" if missing else None,
        "commit_sha": commit_sha,
        "branch": branch,
        "required_input_ids": [record["id"] for record in records],
        "missing_input_ids": [record["id"] for record in missing],
        "test_selectors": [record["test_selector"] for record in records],
        "input_artifacts": None,
        "proof_ceiling": (
            "Private-input regression PASS is available only when all registered operator inputs "
            "are present, hashed, unchanged through the run, and tested from a clean tracked tree. "
            "This gate never proves production, privileged-device, secret-bearing, or operator acceptance behavior."
        ),
        "test": None,
    }

    if missing:
        _write_report(report_path, report)
        print("PRIVATE INPUT TEST FLOOR: BLOCKED")
        print("Missing registered input ids: " + ", ".join(report["missing_input_ids"]))
        print(f"Receipt: {report_path}")
        return 3

    if not commit_sha:
        report["status"] = "BLOCKED"
        report["failed_step"] = "git-identity-unavailable"
        _write_report(report_path, report)
        print("PRIVATE INPUT TEST FLOOR: BLOCKED (git identity unavailable)")
        print(f"Receipt: {report_path}")
        return 4

    try:
        dirty_before = tracked_dirty_paths()
    except ContractError as exc:
        report["status"] = "BLOCKED"
        report["failed_step"] = "git-state-unavailable"
        report["error"] = str(exc)
        _write_report(report_path, report)
        print(f"PRIVATE INPUT TEST FLOOR: BLOCKED ({exc})")
        print(f"Receipt: {report_path}")
        return 4
    if dirty_before:
        report["status"] = "BLOCKED"
        report["failed_step"] = "tracked-state-dirty"
        report["dirty_tracked_paths"] = dirty_before
        _write_report(report_path, report)
        print("PRIVATE INPUT TEST FLOOR: BLOCKED (tracked tree is dirty)")
        print(f"Receipt: {report_path}")
        return 4

    before_artifacts = input_artifacts(records)
    report["input_artifacts"] = before_artifacts

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
    skip_count = _pytest_skip_count(stdout)
    after_artifacts = input_artifacts(records)
    input_mutated = after_artifacts != before_artifacts

    try:
        dirty_after = tracked_dirty_paths()
    except ContractError:
        dirty_after = ["<git-state-unavailable>"]

    if input_mutated:
        status = "FAIL"
        failed_step = "private-input-mutated"
    elif dirty_after:
        status = "FAIL"
        failed_step = "tracked-state-mutated"
    elif result.returncode != 0 or skip_count != 0:
        status = "FAIL"
        failed_step = "private-input-regressions"
    else:
        status = "PASS"
        failed_step = None

    report["status"] = status
    report["failed_step"] = failed_step
    report["test"] = {
        "returncode": result.returncode,
        "skip_count": skip_count,
        "output_redacted": True,
    }
    if dirty_after:
        report["dirty_tracked_paths_after"] = dirty_after
    _write_report(report_path, report)

    print(f"PRIVATE INPUT TEST FLOOR: {status}")
    if status != "PASS":
        print(
            "Private pytest output was intentionally redacted; use the registered selector(s) "
            "only inside the authorized private-input environment for diagnosis."
        )
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
