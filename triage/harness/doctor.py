"""Doctor environment checks and configuration audit for the local harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from triage.path_policy import repo_root
from triage.gitignore_hygiene import scan_tracked_binaries
from .registry import get_workflow_registry_path, get_artifact_registry_path


def run_doctor() -> bool:
    """Run diagnostics and return True if environment is healthy."""
    print("=== HARNESS DOCTOR DIAGNOSTICS ===")
    issues: List[str] = []
    successes: List[str] = []

    # 1. Python library imports
    print("\nChecking Python libraries:")
    for lib in ("openpyxl", "lxml", "pytest"):
        try:
            __import__(lib)
            successes.append(f"Import {lib}: OK")
            print(f"  [PASS] {lib} is installed")
        except ImportError:
            issues.append(f"Missing Python library: {lib}")
            print(f"  [FAIL] {lib} is missing")

    # 2. Git CLI availability and state
    print("\nChecking Git CLI:")
    try:
        res = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(repo_root()),
            check=True,
        )
        successes.append("Git CLI: OK")
        print("  [PASS] git command runs successfully")
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        issues.append(f"Git execution failure: {exc}")
        print("  [FAIL] git command failed or is not available")

    # 3. Gitignore Hygiene
    print("\nChecking Gitignore hygiene:")
    try:
        report = scan_tracked_binaries(root=repo_root())
        if not report.ok:
            for finding in report.findings:
                msg = f"{finding.path}: {finding.reason}"
                issues.append(f"Gitignore hygiene: {msg}")
                print(f"  [FAIL] {msg}")
        else:
            successes.append("Gitignore hygiene: OK")
            print("  [PASS] gitignore hygiene passes")
    except Exception as exc:
        issues.append(f"Gitignore hygiene check crashed: {exc}")
        print(f"  [FAIL] {exc}")

    # 4. Harness Registries Validation
    print("\nChecking Harness Registries:")
    for name, path in (
        ("Workflows", get_workflow_registry_path()),
        ("Artifacts", get_artifact_registry_path()),
    ):
        if not path.is_file():
            issues.append(f"Registry missing: {name} registry at {path}")
            print(f"  [FAIL] {name} registry is missing")
        else:
            try:
                content = json.loads(path.read_text(encoding="utf-8"))
                successes.append(f"Registry {name}: Valid JSON")
                print(f"  [PASS] {name} registry contains valid JSON")
            except json.JSONDecodeError as exc:
                issues.append(f"Registry corrupt: {name} registry has corrupt JSON: {exc}")
                print(f"  [FAIL] {name} registry has corrupt JSON")

    # 5. Output policy check
    print("\nChecking Output Policy directories:")
    outputs_dir = repo_root() / "Outputs"
    if not outputs_dir.is_dir():
        print("  [INFO] Outputs/ directory does not exist yet (will be created during run)")
    else:
        print("  [PASS] Outputs/ directory exists")

    print("\n=== SUMMARY ===")
    if issues:
        print(f"{len(issues)} failure(s) detected:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print(f"All {len(successes)} diagnostic gates passed successfully.")
    return True

