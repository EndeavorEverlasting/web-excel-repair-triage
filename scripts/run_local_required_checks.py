#!/usr/bin/env python3
"""Execute local equivalents of required CI checks (governance-contract + operational-harness).

When GitHub Actions minutes are exhausted or CI providers hit usage limits,
this script provides a deterministic local substitute that runs the same semantic
gates and produces a machine-readable receipt.

Usage:
    python scripts/run_local_required_checks.py [--report PATH]
    python scripts/run_local_required_checks.py --summary

The script delegates to run_validator_profile.py with the 'required_checks' profile,
which mirrors the validators run by:
  - .github/workflows/governance-contract.yml
  - .github/workflows/harness-contract.yml (operational-harness job)

Exit codes:
    0 - all checks passed
    1 - one or more blocking checks failed
    2 - contract/configuration error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_validator_profile import execute_profile, REPO_ROOT as PROFILE_REPO_ROOT

REQUIRED_CHECKS_PROFILE = "required_checks"
DEFAULT_REPORT_PATH = REPO_ROOT / "Outputs" / "local-required-checks-receipt.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help=f"Path to write machine-readable receipt (default: {DEFAULT_REPORT_PATH.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary only, no detailed step output",
    )
    args = parser.parse_args(argv)

    report_path = (
        args.report if args.report.is_absolute() else REPO_ROOT / args.report
    ).resolve()

    print("=== Local Required Checks (governance + operational harness) ===")
    print(f"Profile: {REQUIRED_CHECKS_PROFILE}")
    print(f"Receipt: {report_path.relative_to(REPO_ROOT)}")
    print()

    exit_code, report = execute_profile(
        REQUIRED_CHECKS_PROFILE,
        report_path=report_path,
    )

    if args.summary:
        print()
        print(f"Status: {report['status']}")
        print(f"Steps: {report['observed_step_count']}/{report['required_step_count']}")
        if report.get("failed_validator"):
            print(f"Failed validator: {report['failed_validator']}")
        if report.get("warning_failure_count"):
            print(f"Non-blocking warnings: {report['warning_failure_count']}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
